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
# PSM 6:
#   Assumes a relatively uniform block of text.
#
# PSM 11:
#   Sparse text / separated text regions.
#
# Government certificates often contain tables and separated
# labels, so trying both is useful.
OCR_CONFIGURATIONS = (
    "--psm 6",
    "--psm 11",
)


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
    image: Image.Image,
    config: str,
) -> tuple[float, str]:
    """
    Run OCR and calculate an approximate OCR quality score.

    The score is based on Tesseract's token-level confidence.

    Returns:
        (confidence_score, extracted_text)
    """

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
    # Small bonus for useful text quantity.
    #
    # This prevents a very short OCR result containing only
    # one high-confidence word from always winning.
    # --------------------------------------------------------

    token_count = len(
        text_parts
    )

    if token_count >= 20:

        quantity_bonus = 5.0

    elif token_count >= 10:

        quantity_bonus = 3.0

    elif token_count >= 5:

        quantity_bonus = 1.0

    else:

        quantity_bonus = 0.0

    score = min(
        100.0,
        average_confidence
        + quantity_bonus,
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
    # Build OCR candidates.
    # --------------------------------------------------------

    base_images = [
        (
            "original",
            _prepare_original(
                original
            ),
        ),
        (
            "grayscale",
            _prepare_grayscale(
                original
            ),
        ),
        (
            "enhanced",
            _prepare_enhanced(
                original
            ),
        ),
        (
            "threshold",
            _prepare_threshold(
                original
            ),
        ),
    ]

    candidates = []

    # ========================================================
    # Run all OCR candidates.
    # ========================================================

    for (
        image_name,
        image,
    ) in base_images:

        # ----------------------------------------------------
        # OCR both normal and upscaled versions.
        # ----------------------------------------------------

        images_to_test = [
            (
                image_name,
                image,
            ),
            (
                f"{image_name}_upscaled",
                _resize_for_ocr(
                    image
                ),
            ),
        ]

        for (
            variant_name,
            ocr_image,
        ) in images_to_test:

            for config in OCR_CONFIGURATIONS:

                try:

                    score, text = (
                        _calculate_ocr_confidence(
                            ocr_image,
                            config,
                        )
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