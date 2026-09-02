"""
OCR service for BidSure AI Document Intelligence.

This module extracts text from:
- JPG
- JPEG
- PNG
- Scanned PDF

Team 1 responsibility:
- Load documents
- Perform OCR
- Improve OCR robustness
- Return raw extracted text

This module does NOT:
- classify documents
- extract structured fields
- verify government registrations
- prove document authenticity

For photographed documents, multiple OCR strategies are used
to improve robustness against:
- lighting variation
- low contrast
- camera noise
- small text
- mild blur
- different document layouts

Scanned PDF behavior is intentionally kept conservative so that
existing PDF extraction remains stable.
"""

import re
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


# ============================================================
# CONFIGURATION
# ============================================================

SUPPORTED_IMAGE_FORMATS = {
    ".jpg",
    ".jpeg",
    ".png",
}

# OCR configurations for photographed documents.
#
# PSM 3: Fully automatic page segmentation (ideal for full page layout).
# PSM 4: Single column of text of variable sizes (ideal for certificates).
# PSM 6: Assumes a uniform block of text (ideal for structured table rows).
# PSM 11: Sparse text (ideal for sparse multi-column layout table cells).
OCR_CONFIGURATIONS = (
    "--psm 3",
    "--psm 4",
    "--psm 6",
    "--psm 11",
)


# ============================================================
# IMAGE PREPROCESSING
# ============================================================
def _get_image_ocr_candidates(
    file_path: str,
) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {SUPPORTED_IMAGE_FORMATS}"
        )
    with Image.open(path) as image:
        original = image.copy()

    orig_rgb = _prepare_original(original)
    enhanced = _prepare_enhanced(original)
    threshold = _prepare_threshold(original)

    images_to_test = [
        ("original_upscaled", _resize_for_ocr(orig_rgb)),
        ("enhanced_upscaled", _resize_for_ocr(enhanced)),
        ("threshold_upscaled", _resize_for_ocr(threshold)),
        ("original", orig_rgb),
    ]

    candidates = []
    for variant_name, ocr_image in images_to_test:
        for config in OCR_CONFIGURATIONS:
            try:
                score, text = _calculate_ocr_confidence(ocr_image, config)
            except Exception:
                continue
            if not text.strip():
                continue
            candidates.append(
                {
                    "score": score,
                    "text": text.strip(),
                    "variant": variant_name,
                    "config": config,
                }
            )

    if not candidates:
        return []

    candidates.sort(
        key=lambda candidate: (
            candidate["score"],
            len(candidate["text"]),
        ),
        reverse=True,
    )
    return candidates


def extract_text_and_candidates_from_image(
    file_path: str,
) -> tuple[str, list[dict]]:
    candidates = _get_image_ocr_candidates(file_path)
    if not candidates:
        return "", []
    return candidates[0]["text"], candidates


def extract_text_from_image(
    file_path: str,
) -> str:
    primary_text, _ = extract_text_and_candidates_from_image(file_path)
    return primary_text



# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def _prepare_original(
    image: Image.Image,
) -> Image.Image:
    """
    Prepare the original image without aggressive processing.

    This preserves the original document appearance and can
    sometimes outperform heavily processed images.
    """

    return image.convert("RGB")


def _prepare_grayscale(
    image: Image.Image,
) -> Image.Image:
    """
    Create a grayscale high-contrast version.

    Useful for:
    - photographed certificates
    - faded text
    - uneven lighting
    - gray backgrounds
    """

    processed = image.convert("L")

    processed = ImageOps.autocontrast(
        processed
    )

    processed = processed.filter(
        ImageFilter.SHARPEN
    )

    return processed


def _prepare_enhanced(
    image: Image.Image,
) -> Image.Image:
    """
    Create an enhanced grayscale image.

    Applies:
    - grayscale
    - autocontrast
    - moderate contrast enhancement
    - moderate sharpness enhancement

    The enhancement is intentionally conservative.
    """

    processed = image.convert("L")

    processed = ImageOps.autocontrast(
        processed
    )

    contrast = ImageEnhance.Contrast(
        processed
    )

    processed = contrast.enhance(
        1.35
    )

    sharpness = ImageEnhance.Sharpness(
        processed
    )

    processed = sharpness.enhance(
        1.5
    )

    return processed


def _prepare_threshold(
    image: Image.Image,
) -> Image.Image:
    """
    Create a binary black/white version.

    Otsu-style thresholding is approximated using the image
    histogram.

    This can help when:
    - text is dark
    - background is light
    - contrast is otherwise poor

    It is kept as one OCR candidate rather than being forced
    onto every document.
    """

    grayscale = image.convert("L")

    grayscale = ImageOps.autocontrast(
        grayscale
    )

    histogram = grayscale.histogram()

    total_pixels = sum(
        histogram
    )

    if total_pixels == 0:
        return grayscale

    weighted_sum = sum(
        index * count
        for index, count in enumerate(
            histogram
        )
    )

    sum_background = 0
    weight_background = 0

    best_threshold = 128
    best_variance = -1.0

    for threshold in range(256):

        weight_background += histogram[
            threshold
        ]

        if weight_background == 0:
            continue

        weight_foreground = (
            total_pixels
            - weight_background
        )

        if weight_foreground == 0:
            break

        sum_background += (
            threshold
            * histogram[threshold]
        )

        mean_background = (
            sum_background
            / weight_background
        )

        mean_foreground = (
            weighted_sum
            - sum_background
        ) / weight_foreground

        between_class_variance = (
            weight_background
            * weight_foreground
            * (
                mean_background
                - mean_foreground
            ) ** 2
        )

        if (
            between_class_variance
            > best_variance
        ):

            best_variance = (
                between_class_variance
            )

            best_threshold = threshold

    thresholded = grayscale.point(
        lambda pixel: (
            255
            if pixel > best_threshold
            else 0
        )
    )

    return thresholded


def _resize_for_ocr(
    image: Image.Image,
) -> Image.Image:
    """
    Upscale small photographed documents.

    Tesseract generally benefits when small characters occupy
    more pixels.

    The original image is preserved; this creates a separate
    OCR candidate.
    """

    width, height = image.size

    # Avoid unnecessarily huge images.
    max_dimension = 4000

    scale = 2.0

    new_width = int(
        width * scale
    )

    new_height = int(
        height * scale
    )

    if (
        new_width > max_dimension
        or new_height > max_dimension
    ):

        reduction = min(
            max_dimension / new_width,
            max_dimension / new_height,
        )

        new_width = int(
            new_width * reduction
        )

        new_height = int(
            new_height * reduction
        )

    return image.resize(
        (
            new_width,
            new_height,
        ),
        Image.Resampling.LANCZOS,
    )


# ============================================================
# OCR CONFIDENCE
# ============================================================

def _calculate_ocr_confidence(
    image: Image.Image | None,
    config: str,
    raw_text: str | None = None,
) -> tuple[float, str]:
    """
    Run OCR and calculate an approximate OCR quality score.

    The score is based on Tesseract's token-level confidence.

    Returns:
        (confidence_score, extracted_text)
    """

    if raw_text is not None:
        extracted_text = raw_text.strip()
        confidences = [80.0]
    else:
        if image is None:
            return 0.0, ""
        data = pytesseract.image_to_data(
            image,
            config=config,
            output_type=pytesseract.Output.DICT,
        )

        text_parts = []

        confidences = []

        text_values = data.get(
            "text",
            [],
        )

        confidence_values = data.get(
            "conf",
            [],
        )

        for (
            text_value,
            confidence_value,
        ) in zip(
            text_values,
            confidence_values,
        ):

            text_value = (
                text_value or ""
            ).strip()

            if not text_value:
                continue

            text_parts.append(
                text_value
            )

            try:

                confidence = float(
                    confidence_value
                )

            except (
                ValueError,
                TypeError,
            ):

                continue

            if confidence >= 0:

                confidences.append(
                    confidence
                )

        extracted_text = " ".join(
            text_parts
        ).strip()

    if not confidences:

        return (
            0.0,
            extracted_text,
        )

    average_confidence = (
        sum(confidences)
        / len(confidences)
    )

    # --------------------------------------------------------
    # COMPOSITE DOCUMENT-INDEPENDENT OCR QUALITY SCORE
    #
    # Raw Tesseract confidence alone can be misleading because
    # sparse text mode (--psm 11) often reports high confidence
    # on isolated garbage symbols.
    #
    # We combine 5 generic signals:
    #   1. Base Tesseract token confidence (scaled 0..35)
    #   2. Generic document label richness (scaled 0..35)
    #   3. Identifier candidate presence (bonus 10-15)
    #   4. Structured page segmentation mode bonus (+5 for --psm 6/4/3)
    #   5. Symbol garbage penalty (-0..-40 for high non-ASCII / noise)
    # --------------------------------------------------------

    # 1. Base confidence (0..35)
    base_conf_component = (average_confidence / 100.0) * 35.0

    # 2. Generic business/government document label keywords
    generic_keywords = (
        "registration", "certificate", "government", "gst", "gstin",
        "legal name", "trade name", "constitution", "address", "principal",
        "liability", "validity", "date of", "type of", "number", "place of business",
        "pan", "father", "date of birth", "udyam", "enterprise", "proprietorship",
        "partnership", "limited", "regular", "active", "form", "india", "particulars",
        "issuing", "authority"
    )
    text_lower = extracted_text.lower()
    matched_keywords = sum(1 for kw in generic_keywords if kw in text_lower)
    keyword_component = min(35.0, matched_keywords * 3.0)

    # 3. Structural candidate identifier bonus
    identifier_bonus = 0.0
    if re.search(r"\b\d{2}[A-Za-z0-9]{13}\b", extracted_text):
        identifier_bonus = 15.0
    elif re.search(r"\b[A-Za-z]{5}\d{4}[A-Za-z]\b", extracted_text):
        identifier_bonus = 10.0
    elif re.search(r"\bUDYAM-[A-Za-z]{2}-\d{2}-\d{7}\b", extracted_text, re.IGNORECASE):
        identifier_bonus = 15.0

    # 3b. Proportional structured date evidence bonus (+3.0)
    # A small tie-breaker bonus that prefers OCR candidates containing recognizable dates
    # (e.g. DD/MM/YYYY) when two candidates are otherwise virtually identical in score.
    # +3.0 is equivalent to a single keyword match, ensuring it cannot cause a poor candidate
    # to beat a clean high-quality candidate.
    date_bonus = 0.0
    if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", extracted_text):
        date_bonus = 3.0

    # 4. Symbol noise / non-ASCII penalty
    total_len = max(1, len(extracted_text))
    garbage_chars = sum(
        1 for c in extracted_text
        if ord(c) > 127 or c in "€$¥£¢§¶©®™~`^{}[]<>\\|"
    )
    garbage_penalty = (garbage_chars / total_len) * 40.0

    # 5. Generic Structural Label & Key-Value Structure Bonus
    # Reward OCR outputs containing key-value structures, colons, or label separators
    # common across GST, PAN, Udyam, and other official documents without document-specific coupling.
    structural_label_bonus = 0.0
    label_structure_matches = len(
        re.findall(
            r"\b(?:Name|Address|Registration|Date|Number|Type|Category|GSTIN|PAN|Udyam|Details|Centre|Department)\s*[:\-|\u2014]\s*\S+",
            extracted_text,
            re.IGNORECASE,
        )
    )
    structural_label_bonus = min(20.0, label_structure_matches * 4.0)

    # 6. Label Integrity & Mangled Header Penalty
    # Detect common OCR fragmentation where PSM mode mangles field headers
    # e.g., '[ 1 [isos Name', 'beuat are', etc.
    mangled_label_penalty = 0.0
    mangled_patterns = (
        r"\[\s*\d*\s*\[",
        r"isos\s+name",
        r"beuat\s+are",
    )
    for pattern in mangled_patterns:
        if re.search(pattern, extracted_text, re.IGNORECASE):
            mangled_label_penalty += 15.0

    score = max(
        0.0,
        min(
            100.0,
            base_conf_component
            + keyword_component
            + identifier_bonus
            + date_bonus
            + structural_label_bonus
            - garbage_penalty
            - mangled_label_penalty,
        ),
    )




    return (
        score,
        extracted_text,
    )



# ============================================================
# IMAGE OCR
# ============================================================

def extract_text_from_image(
    file_path: str,
) -> str:
    """
    Extract text from JPG, JPEG, or PNG using multi-pass OCR.

    Multiple OCR candidates are generated using:

        1. Original image
        2. Grayscale image
        3. Enhanced image
        4. Thresholded image

    Each candidate is tested with:

        PSM 6
        PSM 11

    The candidate with the strongest OCR confidence is selected.

    This is intended for real-world photographed documents such
    as:

        GST certificates
        PAN cards
        Udyam certificates

    Args:
        file_path:
            Path to the image.

    Returns:
        Best OCR-extracted text.
    """

    path = Path(
        file_path
    )

    # --------------------------------------------------------
    # Check file existence.
    # --------------------------------------------------------

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    # --------------------------------------------------------
    # Check supported format.
    # --------------------------------------------------------

    if path.suffix.lower() not in (
        SUPPORTED_IMAGE_FORMATS
    ):

        raise ValueError(
            f"Unsupported image format: "
            f"{path.suffix}. "
            f"Supported formats: "
            f"{SUPPORTED_IMAGE_FORMATS}"
        )

    # --------------------------------------------------------
    # Open image.
    # --------------------------------------------------------

    with Image.open(path) as image:

        original = image.copy()

    # --------------------------------------------------------
    # Build OCR candidate images (original + upscaled variants).
    # --------------------------------------------------------

    orig_rgb = _prepare_original(original)
    enhanced = _prepare_enhanced(original)
    threshold = _prepare_threshold(original)

    images_to_test = [
        ("original_upscaled", _resize_for_ocr(orig_rgb)),
        ("enhanced_upscaled", _resize_for_ocr(enhanced)),
        ("threshold_upscaled", _resize_for_ocr(threshold)),
        ("original", orig_rgb),
    ]

    candidates = []

    # ========================================================
    # Run all OCR candidates.
    # ========================================================

    for variant_name, ocr_image in images_to_test:

        for config in OCR_CONFIGURATIONS:

            try:

                score, text = _calculate_ocr_confidence(
                    ocr_image,
                    config,
                )

            except Exception:
                continue

            if not text.strip():
                continue

            candidates.append(
                {
                    "score": score,
                    "text": text.strip(),
                    "variant": variant_name,
                    "config": config,
                }
            )




    # ========================================================
    # Fallback.
    # ========================================================

    if not candidates:

        return ""

    # ========================================================
    # Select strongest OCR candidate.
    # ========================================================

    candidates.sort(
        key=lambda candidate: (
            candidate["score"],
            len(
                candidate["text"]
            ),
        ),
        reverse=True,
    )

    best_candidate = (
        candidates[0]
    )

    return best_candidate[
        "text"
    ]


# ============================================================
# SCANNED PDF OCR
# ============================================================

def extract_text_from_scanned_pdf(
    file_path: str,
) -> str:
    """
    Extract text from a scanned PDF using OCR.

    IMPORTANT:

    Scanned PDFs intentionally retain the existing OCR path:

        PDF page
            ↓
        2x rendering
            ↓
        RGB image
            ↓
        Tesseract default configuration

    We do not use the multi-pass photograph pipeline here.

    This preserves the current scanned-PDF behavior and avoids
    unnecessarily changing existing PDF extraction results.

    Args:
        file_path:
            Path to the scanned PDF.

    Returns:
        Extracted text from all PDF pages.
    """

    path = Path(
        file_path
    )

    # --------------------------------------------------------
    # Check file existence.
    # --------------------------------------------------------

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    # --------------------------------------------------------
    # Check PDF format.
    # --------------------------------------------------------

    if path.suffix.lower() != ".pdf":

        raise ValueError(
            "Expected a PDF file"
        )

    # --------------------------------------------------------
    # Open PDF.
    # --------------------------------------------------------

    pdf = pymupdf.open(
        file_path
    )

    extracted_pages = []

    try:

        # ====================================================
        # Process every page.
        # ====================================================

        for page in pdf:

            # ------------------------------------------------
            # Render page at 2x resolution.
            # ------------------------------------------------

            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(
                    2,
                    2,
                )
            )

            # ------------------------------------------------
            # Convert to PIL image.
            # ------------------------------------------------

            image = Image.frombytes(
                "RGB",
                [
                    pixmap.width,
                    pixmap.height,
                ],
                pixmap.samples,
            )

            # ------------------------------------------------
            # Preserve existing PDF OCR behavior.
            # ------------------------------------------------

            text = pytesseract.image_to_string(
                image
            )

            if text.strip():

                extracted_pages.append(
                    text.strip()
                )

    finally:

        pdf.close()

    # --------------------------------------------------------
    # Combine pages.
    # --------------------------------------------------------

    return "\n\n".join(
        extracted_pages
    )