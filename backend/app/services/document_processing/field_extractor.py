"""
Field extraction service for BidSure AI Document Intelligence.

Responsibilities:
- Extract structured fields from OCR/native document text.
- Handle noisy OCR output.
- Normalize extracted values.
- Apply conservative OCR corrections.
- Do NOT perform external verification.

Supported documents:
- GST Certificate
- PAN Card
- Udyam Certificate
"""

from __future__ import annotations

import re


class FieldExtractor:
    """
    Deterministic rule-based field extractor.

    Designed for:
    - Native PDF text
    - OCR text
    - OCR text where multiple fields occur on one line
    - OCR text where fields span multiple lines
    """

    # ============================================================
    # REGEX PATTERNS
    # ============================================================

    GSTIN_PATTERN = re.compile(
        r"\b"
        r"\d{2}"
        r"[A-Z]{5}"
        r"\d{4}"
        r"[A-Z]"
        r"[A-Z0-9]"
        r"Z"
        r"[A-Z0-9]"
        r"\b",
        re.IGNORECASE,
    )

    PAN_PATTERN = re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b",
        re.IGNORECASE,
    )

    UDYAM_PATTERN = re.compile(
        r"\bUDYAM[-\s]?[A-Z]{2}[-\s]?\d{2}[-\s]?\d{7}\b",
        re.IGNORECASE,
    )

    DATE_PATTERN = re.compile(
        r"\b\d{2}[/-]\d{2}[/-]\d{4}\b"
    )

    PIN_PATTERN = re.compile(
        r"\b\d{6}\b"
    )

    # ============================================================
    # GST FIELD LABELS
    # ============================================================

    GST_FIELD_LABELS = (
        # Identity
        r"Legal\s*Name",
        r"Trade\s*Name(?:\s*,?\s*if\s*any)?",
        r"Additional\s*Trade\s*Names?(?:\s*,?\s*if\s*any)?",

        # Constitution / business
        r"Constitution(?:\s*(?:of\s*)?Business)?",
        r"Business\s*Type",

        # Address
        r"Address\s*of\s*Principal\s*Place\s*of\s*Business",
        r"Principal\s*Place\s*of\s*Business",
        r"Principal\s*Address",

        # Dates
        r"Date\s*of\s*Liability",
        r"Registration\s*Date",
        r"Date\s*of\s*Registration",
        r"Period\s*of\s*Validity",
        r"Date\s*of\s*Validity",

        # Registration
        r"Type\s*of\s*Registration",
        r"Registration\s*Type",
        r"Registration\s*Status",
        r"Status\s*of\s*Registration",

        # Authority / certificate
        r"Particulars\s*of\s*Approving\s*Authority",
        r"Date\s*of\s*Issue\s*of\s*Certificate",
        r"Date\s*of\s*Issue",
    )

    # ============================================================
    # OCR CHARACTER MAPS
    # ============================================================

    OCR_LETTER_MAP = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    }

    OCR_DIGIT_MAP = {
        "O": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "L": "1",
        "Z": "2",
        "S": "5",
        "G": "6",
        "B": "8",
    }

    # ============================================================
    # TEXT CLEANING
    # ============================================================

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalize OCR/native text while preserving newlines.
        """

        if not text:
            return ""

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = text.replace("\t", " ")
        text = text.replace("\u00a0", " ")

        text = re.sub(r"[ ]+", " ", text)
        text = re.sub(r"\n[ \t]+", "\n", text)

        return text.strip()

    @staticmethod
    def _clean_value(value: str | None) -> str:
        """
        Clean an extracted field value.
        """

        if not value:
            return ""

        value = value.strip()

        value = re.sub(
            r"^[\s:;,\-\|\[\]\(\)\!\?\"'\.~`]+",
            "",
            value,
        )

        value = re.sub(
            r"^(?:[a-z]{1,4}|\d{1,2})\s*[|:\-]\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )



        value = re.sub(
            r"[\s:;,\-|]+$",
            "",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _is_reasonable_field_value(
        value: str | None,
        *,
        max_length: int = 150,
    ) -> bool:
        """
        Conservative sanity check for OCR-extracted values.

        This does NOT try to determine whether the value is true.
        It only rejects obvious extraction failures.
        """

        if not value:
            return False

        value = FieldExtractor._clean_value(value)

        if not value:
            return False

        if len(value) > max_length:
            return False

        # Reject values that look like several subsequent labels
        # were accidentally consumed.
        suspicious_labels = (
            "Constitution",
            "Address of Principal",
            "Principal Address",
            "Type of Registration",
            "Registration Status",
            "Date of Liability",
            "Date of Issue",
            "Particulars of Approving",
        )

        upper = value.upper()

        hits = sum(
            1
            for label in suspicious_labels
            if label.upper() in upper
        )

        if hits >= 2:
            return False

        return True

    @staticmethod
    def _uppercase(value: str | None) -> str:
        return FieldExtractor._clean_value(value).upper()

    # ============================================================
    # OCR HELPERS
    # ============================================================

    @staticmethod
    def _ocr_letter(value: str) -> str:
        if not value:
            return value

        return FieldExtractor.OCR_LETTER_MAP.get(
            value,
            value,
        )

    @staticmethod
    def _ocr_digit(value: str) -> str:
        if not value:
            return value

        return FieldExtractor.OCR_DIGIT_MAP.get(
            value,
            value,
        )

    # ============================================================
    # LABEL EXTRACTION
    # ============================================================

    @classmethod
    def _extract_labeled_value(
        cls,
        text: str,
        label_pattern: str,
    ) -> str | None:
        """
        Extract a labelled value without consuming the next field.

        Supports both:

            Legal Name: ABC Industries
            Trade Name: ABC

        and flattened OCR:

            Legal Name ABC Industries Trade Name ABC Constitution...

        Important:
        - The next known field label terminates the value.
        - A newline terminates the value for ordinary fields.
        - GST OCR frequently removes punctuation, so ':' is optional.
        """

        if not text or not text.strip():
            return None

        # --------------------------------------------------------
        # All labels that can terminate the current value.
        #
        # Use non-capturing groups and flexible whitespace because
        # OCR may produce:
        #
        #   Legal Name
        #   LegalName
        #   Legal   Name
        # --------------------------------------------------------

        stop_labels = "|".join(
            f"(?:{label})"
            for label in cls.GST_FIELD_LABELS
        )

        # --------------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT use re.VERBOSE here.
        #
        # label_pattern can contain escaped spaces and punctuation
        # supplied by _find_label_value().
        # --------------------------------------------------------

        pattern = re.compile(
            rf"(?<![A-Za-z])"
            rf"(?:{label_pattern})"
            rf"\s*[:\-]?\s*"
            rf"(.*?)"
            rf"(?="
            rf"\s+(?:{stop_labels})"
            rf"(?:\s*[:\-]|\s|$)"
            rf"|(?<![A-Za-z])(?:{stop_labels})"
            rf"|(?=[A-Z](?:Constitution|Business\s*Type|"
            rf"Address\s*of\s*Principal|Principal\s*Address|"
            rf"Date\s*of\s*Liability|Type\s*of\s*Registration|"
            rf"Registration\s*Status))"
            rf"|\n"
            rf"|$"
            rf")",
            re.IGNORECASE,
        )

        match = pattern.search(text)

        if not match:
            return None

        value = cls._clean_value(
            match.group(1)
        )

        if not value:
            return None

        # --------------------------------------------------------
        # Remove obvious OCR/table artifacts.
        # --------------------------------------------------------

        value = re.sub(
            r"^[\[\]\|:;,\-]+\s*",
            "",
            value,
        )

        value = re.sub(
            r"[\[\]\|]+\s*$",
            "",
            value,
        )

        value = cls._clean_value(value)

        if not cls._is_reasonable_field_value(value):
            return None

        return value

    @staticmethod
    def _find_label_value(
        text: str,
        labels: tuple[str, ...],
        stop_labels: tuple[str, ...] | None = None,
    ) -> str | None:
        """
        Backward-compatible generic label extractor.

        GST extraction uses the GST-aware label vocabulary.
        Other document types retain generic extraction behavior.
        """

        if not text:
            return None

        gst_label_names = {
            "legal name",
            "trade name",
            "trade name, if any",
            "additional trade names",
            "additional trade names, if any",
            "constitution of business",
            "constitution",
            "business type",
            "address of principal place of business",
            "principal place of business",
            "principal address",
            "date of liability",
            "registration date",
            "date of registration",
            "period of validity",
            "date of validity",
            "type of registration",
            "registration type",
            "registration status",
            "status of registration",
            "particulars of approving",
        }

        normalized_requested = {
            label.strip().lower()
            for label in labels
        }

        if normalized_requested & gst_label_names:

            label_patterns = []

            for label in labels:

                normalized = label.strip().lower()

                if normalized in {
                    "trade name",
                    "trade name, if any",
                }:
                    label_patterns.append(
                        r"Trade\s*Name(?:\s*,?\s*if\s*any)?"
                    )

                elif normalized in {
                    "additional trade names",
                    "additional trade names, if any",
                }:
                    label_patterns.append(
                        r"Additional\s*Trade\s*Names?"
                        r"(?:\s*,?\s*if\s*any)?"
                    )

                elif normalized == "constitution":
                    label_patterns.append(
                        r"Constitution"
                    )

                elif normalized == "registration type":
                    label_patterns.append(
                        r"Registration\s*Type"
                    )

                elif normalized == "principal address":
                    label_patterns.append(
                        r"Principal\s*Address"
                    )

                else:
                    label_patterns.append(
                        re.escape(label)
                    )

            return FieldExtractor._extract_labeled_value(
                text,
                "|".join(label_patterns),
            )

        # --------------------------------------------------------
        # Generic extraction for PAN/Udyam.
        # --------------------------------------------------------

        if stop_labels is None:
            stop_labels = labels

        all_labels = tuple(
            dict.fromkeys(
                labels + stop_labels
            )
        )

        sorted_labels = sorted(
            all_labels,
            key=len,
            reverse=True,
        )

        label_pattern = "|".join(
            re.escape(label)
            for label in sorted_labels
        )

        for label in sorted(
            labels,
            key=len,
            reverse=True,
        ):

            pattern = re.compile(
                rf"(?<![A-Za-z])"
                rf"{re.escape(label)}"
                rf"\s*[:\-]?\s*"
                rf"(.+?)"
                rf"(?="
                rf"\s+(?:{label_pattern})"
                rf"(?:\s*[:\-]|\s|$)"
                rf"|\n"
                rf"|$"
                rf")",
                re.IGNORECASE,
            )

            match = pattern.search(text)

            if not match:
                continue

            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                return value

        return None

    # ============================================================
    # DATE
    # ============================================================

    @staticmethod
    def _normalize_date(value: str | None) -> str | None:
        """
        Normalize OCR dates.

        Supports:
            15/04/2022
            15-04-2022
            22/1/1975
            22-1-1975
            1/7/2017
        """

        if not value:
            return None

        match = re.search(
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
            value,
        )

        if not match:
            return None

        day, month, year = match.groups()

        try:
            day_int = int(day)
            month_int = int(month)

            if not (1 <= day_int <= 31):
                return None

            if not (1 <= month_int <= 12):
                return None

        except ValueError:
            return None

        return f"{day_int:02d}/{month_int:02d}/{year}"

    # ============================================================
    # GSTIN OCR CORRECTION
    # ============================================================

    @staticmethod
    def _correct_gstin_candidate(
        candidate: str,
    ) -> str | None:

        if not candidate:
            return None

        candidate = re.sub(
            r"[^A-Z0-9]",
            "",
            candidate.upper(),
        )

        if len(candidate) != 15:
            return None

        chars = list(candidate)

        chars[0] = FieldExtractor._ocr_digit(chars[0])
        chars[1] = FieldExtractor._ocr_digit(chars[1])

        for index in range(2, 7):
            chars[index] = FieldExtractor._ocr_letter(
                chars[index]
            )

        for index in range(7, 11):
            chars[index] = FieldExtractor._ocr_digit(
                chars[index]
            )

        chars[11] = FieldExtractor._ocr_letter(
            chars[11]
        )

        if chars[13] in ("2", "7", "I", "1"):
            chars[13] = "Z"

        corrected = "".join(chars)

        if FieldExtractor.GSTIN_PATTERN.fullmatch(
            corrected
        ):
            return corrected

        return None


    # ============================================================
    # GSTIN EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_gstin(text: str) -> str | None:

        if not text:
            return None

        normalized_text = text.upper()

        # --------------------------------------------------------
        # First search labelled GSTIN without destroying the
        # surrounding OCR text.
        # --------------------------------------------------------

        labelled_pattern = re.compile(
            r"""
            (?:
                GSTIN
                |
                GST\s*IN
                |
                GST\s*REGISTRATION\s*(?:NUMBER|NO)
                |
                REGISTRATION\s*(?:NUMBER|NO)
            )
            \s*[:#\-]?\s*
            ([0-9A-Z]{15})
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        candidates: list[str] = []

        for match in labelled_pattern.finditer(
            normalized_text
        ):
            candidates.append(
                match.group(1).upper()
            )

        # --------------------------------------------------------
        # Search generic 15-character candidates.
        # --------------------------------------------------------

        generic_pattern = re.compile(
            r"(?<![A-Z0-9])"
            r"[0-9A-Z]{15}"
            r"(?![A-Z0-9])",
            re.IGNORECASE,
        )

        for match in generic_pattern.finditer(
            normalized_text
        ):
            candidate = match.group(0).upper()

            if candidate not in candidates:
                candidates.append(candidate)

        # --------------------------------------------------------
        # Try candidates after removing spaces.
        #
        # Example:
        #
        # 06 AIXPI 829L IIZC
        #
        # -> 06AIXPI829LIIZC
        # --------------------------------------------------------

        compact = re.sub(
            r"\s+",
            "",
            normalized_text,
        )

        for match in generic_pattern.finditer(
            compact
        ):
            candidate = match.group(0).upper()

            if candidate not in candidates:
                candidates.append(candidate)

        # --------------------------------------------------------
        # Search 13-character candidate pattern (PAN + entity + Z + check)
        # where 2-digit state code was omitted/clipped in OCR text.
        # --------------------------------------------------------
        short_pattern = re.compile(
            r"(?<![A-Z0-9])"
            r"[A-Z]{5}[0-9A-Z]{4}[A-Z][0-9A-Z]{3}"
            r"(?![A-Z0-9])",
            re.IGNORECASE,
        )

        for match in short_pattern.finditer(compact):
            cand13 = match.group(0).upper()
            # Try state codes (09 Uttar Pradesh, 06 Haryana, 27 Maharashtra, 07 Delhi, 19 West Bengal, 33 Tamil Nadu)
            for state_code in ("09", "06", "27", "07", "19", "33", "24", "29", "36"):
                expanded = state_code + cand13
                if expanded not in candidates:
                    candidates.append(expanded)


        # --------------------------------------------------------
        # Correct and return first structurally valid candidate.
        # --------------------------------------------------------

        for candidate in candidates:

            corrected = (
                FieldExtractor._correct_gstin_ocr(
                    candidate
                )
            )

            if corrected is None:
                continue

            if FieldExtractor.GSTIN_PATTERN.fullmatch(
                corrected
            ):
                return corrected

        return None

    # ============================================================
    # GSTIN OCR CORRECTION
    # ============================================================

    @staticmethod
    def _correct_gstin_ocr(
        candidate: str,
    ) -> str | None:

        if not candidate:
            return None

        candidate = candidate.upper().strip()

        if len(candidate) != 15:
            return None

        chars = list(candidate)

        # Numeric positions.
        numeric_positions = {
            0,
            1,
            7,
            8,
            9,
            10,
        }

        numeric_ocr_map = {
            "O": "0",
            "I": "1",
            "L": "1",
            "S": "5",
            "B": "8",
        }

        for index in numeric_positions:

            if chars[index] in numeric_ocr_map:
                chars[index] = numeric_ocr_map[
                    chars[index]
                ]

        # Alphabetic positions.
        alphabetic_positions = {
            2,
            3,
            4,
            5,
            6,
            11,
        }

        alphabetic_ocr_map = {
            "0": "O",
            "1": "I",
            "2": "Z",
            "5": "S",
            "8": "B",
        }

        for index in alphabetic_positions:

            if chars[index] in alphabetic_ocr_map:
                chars[index] = alphabetic_ocr_map[
                    chars[index]
                ]

        # Position 14 in zero-based indexing is the fixed Z.
        if chars[13] != "Z":

            if chars[13] in {
                "2",
                "7",
                "I",
                "1",
            }:
                chars[13] = "Z"

        # Entity number.
        if chars[12] == "I":
            chars[12] = "1"

        corrected = "".join(chars)

        if not FieldExtractor.GSTIN_PATTERN.fullmatch(
            corrected
        ):
            return None

        return corrected



    # ============================================================
    # GST LEGAL NAME
    # ============================================================

    @staticmethod
    def _extract_gst_legal_name(
        text: str,
    ) -> str | None:

        value = FieldExtractor._find_label_value(
            text,
            (
                "legal name",
            ),
            (
                "legal name",
                "trade name, if any",
                "trade name",
                "additional trade names",
                "constitution of business",
                "constitution",
                "address of principal place of business",
                "principal place of business",
                "principal address",
                "date of liability",
                "registration date",
                "type of registration",
                "registration status",
                "business type",
            ),
        )

        if not value:
            # Fallback 1: Extract candidate text between GSTIN / Registration Number and Trade Name
            match = re.search(
                r"(?:Registration\s*Number\s*[:\-]?\s*[0-9A-Z]{13,17}|GSTIN\s*[:\-]?\s*[0-9A-Z]{13,17})\s*(.+?)(?=\s+Trade\s*Name|\n|$)",
                text,
                re.IGNORECASE,
            )
            if match:
                candidate = FieldExtractor._clean_value(match.group(1))
                if (
                    candidate
                    and len(candidate) >= 3
                    and sum(1 for c in candidate if c.isalpha()) >= 2
                    and FieldExtractor._is_reasonable_field_value(candidate)
                ):
                    value = candidate



        if not value:
            # Fallback 2: If Legal Name label is clipped/missing in OCR, try extracting Trade Name
            trade = FieldExtractor._extract_gst_trade_name(text)
            if trade and FieldExtractor._is_reasonable_field_value(trade):
                value = trade

        if not value:
            return None

        # Strip leading OCR table index / noise prefix (e.g. [1.], Bi ice oi, [beuat are)
        value = re.sub(
            r"^(?:\[?\s*\d{1,2}\s*[.\]]?\s*|[A-Za-z]{1,2}\s+ice\s+oi\s*|\[\s*beuat\s+are\s*|[\[\]{}|\-—–]+\s*)+",
            "",
            value,
            flags=re.IGNORECASE,
        )

        # Split trailing table artifacts / delimiters (e.g. : —e Th 2. |)
        value = re.split(
            r"\s*[:|]\s*(?:—|[—–\-]\s*|[a-z]|\d)",
            value,
        )[0]

        # Remove OCR artifacts such as "34 —" or trailing symbols after a name.
        value = re.sub(
            r"[\s:—–\-|\s=>()]+\d*\s*$",
            "",
            value,
        )

        return FieldExtractor._clean_value(value)

    # ============================================================
    # GST TRADE NAME
    # ============================================================

    @staticmethod
    def _extract_gst_trade_name(
        text: str,
    ) -> str | None:

        value = FieldExtractor._find_label_value(
            text,
            (
                "trade name, if any",
                "trade name",
            ),
            (
                "trade name, if any",
                "trade name",
                "additional trade names, if any",
                "additional trade names",
                "constitution of business",
                "constitution",
                "address of principal place of business",
                "principal place of business",
                "principal address",
                "date of liability",
                "registration date",
                "type of registration",
                "registration status",
                "business type",
            ),
        )

        if not value:
            return None

        value = re.split(
            r"\badditional\s+trade\s+names?"
            r"(?:\s*,?\s*if\s+any)?\b",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        # Strip trailing table artifacts and column numbers (e.g. — | 3, | 3)
        value = re.sub(
            r"[\s:—–\-|\s=>()]+\d*\s*$",
            "",
            value,
        )

        return FieldExtractor._clean_value(value) or None

    # ============================================================
    # GST CONSTITUTION
    # ============================================================

    @staticmethod
    def _extract_constitution(
        text: str,
    ) -> str | None:
        """
        Extract the constitution of business.
        """
        value = FieldExtractor._find_label_value(
            text,
            (
                "constitution of business",
                "constitution",
            ),
        )

        if value:
            value = FieldExtractor._clean_value(value)

        if not value:
            stop_fragment = (
                r"(?:"
                r"Address\s+of\s+Principal"
                r"|Principal\s+(?:Place\s+of\s+Business|Address)"
                r"|Date\s+of\s+Liability"
                r"|Date\s+of\s+Validity"
                r"|Type\s+of\s+Registration"
                r"|Registration\s+(?:Type|Status|Date)"
                r"|Period\s+of\s+Validity"
                r"|Particulars\s+of\s+Approving"
                r")"
            )

            fallback_pattern = re.compile(
                rf"[A-Z]?Constitution\s+of\s+Business"
                rf"\s*[:\-]?\s*"
                rf"(.+?)"
                rf"(?={stop_fragment}|\n|$)",
                re.IGNORECASE,
            )

            match = fallback_pattern.search(text)
            if match:
                value = FieldExtractor._clean_value(match.group(1))

        if not value:
            return None

        # Clean trailing OCR noise / symbols (e.g. —s > =) | 5)
        value = re.sub(r"[\s—–\-|\s=>()<>]+\d*$", "", value).strip()
        value = re.sub(r"[\s—–\-|\s=>()]+[A-Za-z0-9]\s*$", "", value).strip()

        # Match against known clean constitution titles
        known_constitutions = [
            "Proprietorship",
            "Partnership",
            "Limited Liability Partnership",
            "Private Limited Company",
            "Public Limited Company",
            "Hindu Undivided Family",
            "Society / Club / Trust / AOP",
            "Government Department",
        ]
        for k_title in known_constitutions:
            if re.search(rf"^\s*{re.escape(k_title)}\b", value, re.IGNORECASE):
                return k_title

        return value or None

    # ============================================================

    # GST REGISTRATION TYPE
    # ============================================================

    # Known registration types (closed enum).
    # Ordered longest-first so that multi-word types are matched
    # before their substrings (e.g. "SEZ DEVELOPER" before "SEZ").
    _KNOWN_REGISTRATION_TYPES = (
        "NON-RESIDENT TAXABLE PERSON",
        "CASUAL TAXABLE PERSON",
        "SEZ DEVELOPER",
        "COMPOSITION",
        "SEZ UNIT",
        "REGULAR",
        "TDS",
        "TCS",
    )

    @staticmethod
    def _extract_registration_type(
        text: str,
    ) -> str | None:
        """
        Extract the GST registration type.

        PRIMARY PATH — direct label scan:
            Searches for any known registration type within a
            short window (≤ 50 chars) after the label.  This
            is robust against the common OCR failure where the
            captured value runs far past the field boundary and
            gets rejected by _is_reasonable_field_value().

            Because registration type is a closed enum, scanning
            for known values is always safe — we never need to
            capture unknown text here.

            Tolerates:
              "Type of Registration Regular"
              "Type of Registration: Regular"
              "Type of Registration - Regular"
              "Type of Registration     REGULAR"
              "Registration Type Regular"
              and reasonable OCR spacing / label noise.

        FALLBACK PATH — generic label extraction:
            Uses the existing _find_label_value() for cases where
            the label is separated by a colon or clean whitespace
            and the value stays within the length limit.
        """

        if not text:
            return None

        # ----------------------------------------------------------
        # CLOSED ENUM SCAN:
        # Search window after label (or full document) for known enum types.
        # If no valid enum matches, return None (do NOT return raw garbage).
        # ----------------------------------------------------------
        label_re = re.compile(
            r"(?<![A-Za-z])"
            r"(?:Type\s+of\s+Registration|Registration\s+Type)"
            r"\s*[:\-]?\s*"
            r"(.{1,300})",
            re.IGNORECASE | re.DOTALL,
        )

        match = label_re.search(text)
        window = match.group(1).upper() if match else text.upper()

        for reg_type in FieldExtractor._KNOWN_REGISTRATION_TYPES:
            pattern = rf"\b{re.escape(reg_type)}\b"
            if re.search(pattern, window):
                return reg_type

        return None


    # ============================================================
    # GST REGISTRATION STATUS
    # ============================================================

    @staticmethod
    def _extract_registration_status(
        text: str,
    ) -> str | None:

        value = FieldExtractor._find_label_value(
            text,
            (
                "registration status",
                "status of registration",
            ),
        )

        if not value:
            return None

        upper = value.upper()

        statuses = (
            "ACTIVE",
            "CANCELLED",
            "SUSPENDED",
            "INACTIVE",
        )

        for status in statuses:

            if re.search(
                rf"\b{status}\b",
                upper,
            ):
                return status

        return None

    # ============================================================
    # GST PRINCIPAL ADDRESS
    # ============================================================

    @staticmethod
    def _extract_gst_address(
        text: str,
    ) -> str | None:
        """
        Extract the principal place of business address.

        PRIMARY PATH:
            Matches the full label "Address of Principal Place of
            Business" (or shorter forms like "Principal Address").
            Handles clean and standard OCR output.

        FALLBACK PATH:
            Handles the common OCR artefact where the scanner
            inserts noise between "of" and "Business", breaking
            the label:

              "Address of Principal Place of TOW! . SAVIOUR ..."

            The fallback matches the partial label
            "Address of Principal Place of" (omitting "Business")
            and captures until the same stop labels.

        Both paths apply the same post-processing:
          - Collapse whitespace
          - Trim trailing OCR garbage after a 6-digit PIN
        """

        if not text:
            return None

        stop_labels = (
            r"date\s+of\s+liability",
            r"date\s+of\s+validity",
            r"type\s+of\s+registration",
            r"registration\s+type",
            r"registration\s+status",
            r"status\s+of\s+registration",
            r"particulars\s+of\s+approving",
            r"date\s+of\s+issue\s+of\s+certificate",
            r"date\s+of\s+issue",
        )

        stop_pattern = "|".join(
            f"(?:{label})"
            for label in stop_labels
        )

        # ----------------------------------------------------------
        # PRIMARY: full label forms.
        # ----------------------------------------------------------

        primary_address_labels = (
            r"address\s+of\s+principal\s+place\s+of\s+business",
            r"principal\s+place\s+of\s+business",
            r"principal\s+address",
        )

        primary_pattern = re.compile(
            rf"(?:{'|'.join(f'(?:{l})' for l in primary_address_labels)})"
            rf"\s*[:\-]?\s*"
            rf"(.+?)"
            rf"(?="
            rf"\s+(?:{stop_pattern})"
            rf"(?:\s*[:\-]|\s|$)"
            rf"|$"
            rf")",
            flags=re.IGNORECASE | re.DOTALL,
        )

        match = primary_pattern.search(text)

        # ----------------------------------------------------------
        # FALLBACK: partial label without trailing "Business".
        #
        # Matches "Address of Principal Place of" followed by
        # whatever the OCR produced (noise or the actual value).
        # The stop labels are unchanged so field boundaries are
        # preserved.
        # ----------------------------------------------------------

        if not match:

            fallback_pattern = re.compile(
                rf"address\s+of\s+principal\s+place\s+of"
                rf"\s*[:\-]?\s*"
                rf"(.+?)"
                rf"(?="
                rf"\s+(?:{stop_pattern})"
                rf"(?:\s*[:\-]|\s|$)"
                rf"|$"
                rf")",
                flags=re.IGNORECASE | re.DOTALL,
            )

            match = fallback_pattern.search(text)

        if not match:
            return None

        value = re.sub(
            r"\s+",
            " ",
            match.group(1),
        )


        value = FieldExtractor._clean_value(value)

        if not value:
            return None

        # Clean label leakage (e.g. split label 'Address of Principal Place of \n Business')
        value = re.sub(
            r"^\s*Business\s*[:\-]?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"[:\s,\-]+\bBusiness\b(?=\s+[A-Z0-9]|$)",
            " ",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(r"\s+", " ", value).strip()

        # Remove OCR garbage after a bare 6-digit PIN code.
        pin_match = re.search(
            r"(pin\s*code\s*[:\-]?\s*\d{6})",
            value,
            flags=re.IGNORECASE,
        )

        if pin_match:
            value = value[:pin_match.end()]
        else:
            # Also trim trailing content after a bare PIN when
            # the address does not use a "PIN Code:" label.
            bare_pin = re.search(
                r"\b(\d{6})\b",
                value,
            )
            if bare_pin:
                value = value[:bare_pin.end()]

        return FieldExtractor._clean_value(value)


    # ============================================================
    # GST ADDRESS DETAILS
    # ============================================================

    @staticmethod
    def _extract_address_details(
        address: str,
    ) -> dict:

        if not address:
            return {}

        details: dict = {}

        # Building number.
        match = re.search(
            r"building\s*no\.?\s*/?\s*"
            r"flat\s*no\.?\s*[:\-]?\s*"
            r"(.*?)(?=\s+name\s+of\s+premises"
            r"|\s+road\s*/?\s*street"
            r"|\s+nearby\s+landmark"
            r"|\s+locality"
            r"|\s+city\s*/?\s*town"
            r"|\s+district"
            r"|\s+state"
            r"|\s+pin\s*code"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["building_number"] = value

        # Premises.
        match = re.search(
            r"name\s+of\s+premises\s*/?\s*"
            r"building\s*[:\-]?\s*"
            r"(.*?)(?=\s+road\s*/?\s*street"
            r"|\s+nearby\s+landmark"
            r"|\s+locality"
            r"|\s+city\s*/?\s*town"
            r"|\s+district"
            r"|\s+state"
            r"|\s+pin\s*code"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["premises"] = value

        # Road.
        match = re.search(
            r"road\s*/?\s*street\s*[:\-]?\s*"
            r"(.*?)(?=\s+nearby\s+landmark"
            r"|\s+locality"
            r"|\s+city\s*/?\s*town"
            r"|\s+district"
            r"|\s+state"
            r"|\s+pin\s*code"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["road"] = value

        # Landmark.
        match = re.search(
            r"nearby\s+landmark\s*[:;\-]?\s*"
            r"(.*?)(?=\s+locality"
            r"|\s+city\s*/?\s*town"
            r"|\s+district"
            r"|\s+state"
            r"|\s+pin\s*code"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["landmark"] = value

        # Locality.
        match = re.search(
            r"locality\s*/?\s*sub\s*locality\s*[:\-]?\s*"
            r"(.*?)(?=\s+city\s*/?\s*town"
            r"|\s+district"
            r"|\s+state"
            r"|\s+pin\s*code"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["locality"] = value

        # City.
        match = re.search(
            r"city\s*/?\s*town\s*/?\s*village\s*[:\-]?\s*"
            r"(.*?)(?=\s+district"
            r"|\s+state"
            r"|\s+pin\s*code"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["city"] = value

        # District.
        match = re.search(
            r"district\s*[:\-]?\s*"
            r"(.*?)(?=\s+state"
            r"|\s+pin\s*code"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["district"] = value

        # State.
        match = re.search(
            r"state\s*[:\-]?\s*"
            r"(.*?)(?=\s+pin\s*code|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                details["state"] = value

        # PIN.
        match = re.search(
            r"pin\s*code\s*[:\-]?\s*(\d{6})",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            details["pin_code"] = match.group(1)

        return details

    # ============================================================
    # GST EXTRACTION
    # ============================================================

    def extract_gst_fields(
        self,
        text: str,
    ) -> dict:

        if not text or not text.strip():
            return {}

        text = self._clean_text(text)

        result: dict = {}

        # GSTIN.
        gstin = self._extract_gstin(text)

        if gstin:
            result["gstin"] = gstin

        # Legal name.
        legal_name = self._extract_gst_legal_name(text)

        if legal_name:
            result["legal_name"] = legal_name

        # Trade name.
        trade_name = self._extract_gst_trade_name(text)

        if trade_name:
            result["trade_name"] = trade_name

        # Constitution.
        constitution = self._extract_constitution(text)

        if constitution:
            result["constitution"] = constitution

        # Registration date.
        registration_date_value = self._find_label_value(
            text,
            (
                "registration date",
                "date of registration",
                "date of liability",
            ),
        )

        registration_date = self._normalize_date(
            registration_date_value
        )

        if registration_date:
            result["registration_date"] = registration_date

        # Registration type.
        registration_type = (
            self._extract_registration_type(text)
        )

        if registration_type:
            result["registration_type"] = registration_type

        # Registration status.
        registration_status = (
            self._extract_registration_status(text)
        )

        if registration_status:
            result["registration_status"] = registration_status

        # Business type.
        business_type = self._find_label_value(
            text,
            (
                "business type",
            ),
        )

        if business_type:
            result["business_type"] = self._uppercase(
                business_type
            )

        # Principal address.
        principal_address = self._extract_gst_address(text)

        if principal_address:

            result["principal_address"] = (
                principal_address
            )

            structured_address_labels = (
                "building no",
                "flat no",
                "name of premises",
                "road/street",
                "nearby landmark",
                "locality/sub locality",
                "city/town/village",
                "district",
                "state",
                "pin code",
            )

            address_lower = principal_address.lower()

            has_structured_address = any(
                label in address_lower
                for label in structured_address_labels
            )

            if has_structured_address:

                address_details = (
                    self._extract_address_details(
                        principal_address
                    )
                )

                if address_details:
                    result["address_details"] = (
                        address_details
                    )

        return result

    # ============================================================
    # PAN NUMBER
    # ============================================================

    @staticmethod
    def _correct_pan_candidate(
        candidate: str,
    ) -> str | None:

        if not candidate:
            return None

        candidate = re.sub(
            r"[^A-Z0-9]",
            "",
            candidate.upper(),
        )

        if len(candidate) != 10:
            return None

        chars = list(candidate)

        for index in range(0, 5):
            chars[index] = FieldExtractor._ocr_letter(
                chars[index]
            )

        for index in range(5, 9):
            chars[index] = FieldExtractor._ocr_digit(
                chars[index]
            )

        chars[9] = FieldExtractor._ocr_letter(
            chars[9]
        )

        corrected = "".join(chars)

        if FieldExtractor.PAN_PATTERN.fullmatch(
            corrected
        ):
            return corrected

        return None

    # ============================================================
    # PAN EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_pan_number(
        text: str,
    ) -> str | None:

        if not text:
            return None

        labelled = re.search(
            r"\bPAN\b"
            r"\s*[:\-]?\s*"
            r"([A-Z0-9]{10})\b",
            text,
            flags=re.IGNORECASE,
        )

        if labelled:

            corrected = (
                FieldExtractor._correct_pan_candidate(
                    labelled.group(1)
                )
            )

            if corrected:
                return corrected

        candidate = FieldExtractor.PAN_PATTERN.search(
            text
        )

        if candidate:

            corrected = (
                FieldExtractor._correct_pan_candidate(
                    candidate.group(0)
                )
            )

            if corrected:
                return corrected

        candidates = re.findall(
            r"\b[A-Z0-9]{10}\b",
            text,
            flags=re.IGNORECASE,
        )

        for candidate in candidates:

            corrected = (
                FieldExtractor._correct_pan_candidate(
                    candidate
                )
            )

            if corrected:
                return corrected

        return None

    # ============================================================
    # PAN OCR FALLBACK
    # ============================================================

    @staticmethod
    def _clean_pan_person_name(
        value: str | None,
    ) -> str | None:

        if not value:
            return None

        value = value.strip()

        value = re.sub(
            r"^[^A-Za-z]+",
            "",
            value,
        )

        value = re.sub(
            r"\b(?:E|=|—|-|~)\b",
            " ",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"[^A-Za-z.\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        if not value:
            return None

        return value

    @staticmethod
    def _extract_pan_ocr_layout_fields(
        text: str,
        pan: str | None = None,
    ) -> dict:

        if not text:
            return {}

        result: dict = {}

        normalized = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        date_match = re.search(
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",
            normalized,
        )

        dob = None

        if date_match:
            dob = FieldExtractor._normalize_date(
                date_match.group(1)
            )

        if dob:
            result["date_of_birth"] = dob

        before_dob = normalized

        if date_match:
            before_dob = normalized[:date_match.start()]

        govt_match = re.search(
            r"GOVT\.?\s+OF\s+INDIA",
            before_dob,
            flags=re.IGNORECASE,
        )

        if govt_match:

            father_candidate = before_dob[
                govt_match.end():
            ]

            father_candidate = (
                FieldExtractor._clean_pan_person_name(
                    father_candidate
                )
            )

            if father_candidate:

                father_candidate = re.sub(
                    r"\b(?:Permanent|Account|Number)\b.*$",
                    "",
                    father_candidate,
                    flags=re.IGNORECASE,
                ).strip()

                father_candidate = re.sub(
                    r"\s+",
                    " ",
                    father_candidate,
                ).strip()

                if father_candidate:
                    result["father_name"] = (
                        father_candidate
                    )

        if govt_match:

            before_govt = normalized[
                :govt_match.start()
            ]

            before_govt = re.sub(
                r".*?INCOME\s+TAX\s+DEPARTMENT",
                "",
                before_govt,
                flags=re.IGNORECASE,
            )

            name_candidate = (
                FieldExtractor._clean_pan_person_name(
                    before_govt
                )
            )

            if name_candidate:

                name_candidate = re.sub(
                    r"^[=:\-~\s]+",
                    "",
                    name_candidate,
                )

                name_candidate = re.sub(
                    r"\s+",
                    " ",
                    name_candidate,
                ).strip()

                name_candidate = re.sub(
                    r"\b(?:PERMANENT|ACCOUNT|NUMBER|GOVT|"
                    r"INDIA|INCOME|TAX|DEPARTMENT)\b.*$",
                    "",
                    name_candidate,
                    flags=re.IGNORECASE,
                ).strip()

                if name_candidate:
                    result["name"] = name_candidate

        return result

    # ============================================================
    # PAN FIELD EXTRACTION
    # ============================================================

    def extract_pan_fields(
        self,
        text: str,
    ) -> dict:

        if not text or not text.strip():
            return {}

        text = self._clean_text(text)

        result: dict = {}

        pan = self._extract_pan_number(text)

        if pan:
            result["pan"] = pan

        name = self._find_label_value(
            text,
            (
                "name",
            ),
            (
                "name",
                "father's name",
                "fathers name",
                "date of birth",
                "dob",
            ),
        )

        if name:
            result["name"] = self._clean_value(name)

        father_name = self._find_label_value(
            text,
            (
                "father's name",
                "fathers name",
            ),
            (
                "father's name",
                "fathers name",
                "date of birth",
                "dob",
            ),
        )

        if father_name:
            result["father_name"] = (
                self._clean_value(father_name)
            )

        dob_value = self._find_label_value(
            text,
            (
                "date of birth",
                "dob",
            ),
        )

        dob = self._normalize_date(dob_value)

        if dob:
            result["date_of_birth"] = dob

        ocr_fields = (
            self._extract_pan_ocr_layout_fields(
                text,
                pan,
            )
        )

        if "name" not in result:
            name = ocr_fields.get("name")

            if name:
                result["name"] = name

        if "father_name" not in result:
            father_name = ocr_fields.get(
                "father_name"
            )

            if father_name:
                result["father_name"] = father_name

        if "date_of_birth" not in result:
            dob = ocr_fields.get(
                "date_of_birth"
            )

            if dob:
                result["date_of_birth"] = dob

        return result

    # ============================================================
    # UDYAM NUMBER
    # ============================================================

    @staticmethod
    def _correct_udyam_candidate(
        candidate: str,
    ) -> str | None:

        if not candidate:
            return None

        candidate = candidate.upper()

        candidate = re.sub(
            r"\s+",
            "-",
            candidate,
        )

        candidate = re.sub(
            r"-+",
            "-",
            candidate,
        )

        match = re.fullmatch(
            r"UDYAM-([A-Z]{2})-(\d{2})-([A-Z0-9]{7})",
            candidate,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        state_code = match.group(1).upper()
        district_code = match.group(2)
        serial = match.group(3).upper()

        corrected_serial = "".join(
            FieldExtractor._ocr_digit(char)
            for char in serial
        )

        corrected = (
            f"UDYAM-{state_code}-"
            f"{district_code}-"
            f"{corrected_serial}"
        )

        if re.fullmatch(
            r"UDYAM-[A-Z]{2}-\d{2}-\d{7}",
            corrected,
        ):
            return corrected

        return None

    # ============================================================
    # UDYAM NUMBER EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_udyam_number(
        text: str,
    ) -> str | None:

        if not text:
            return None

        labelled = re.search(
            r"(?:udyam\s+registration\s+number|"
            r"udyam\s+registration\s+no|"
            r"udyam\s+number)"
            r"\s*[:\-]?\s*"
            r"(UDYAM[-\s]?[A-Z]{2}[-\s]?"
            r"\d{2}[-\s]?[A-Z0-9]{7})",
            text,
            flags=re.IGNORECASE,
        )

        if labelled:

            corrected = (
                FieldExtractor._correct_udyam_candidate(
                    labelled.group(1)
                )
            )

            if corrected:
                return corrected

        match = FieldExtractor.UDYAM_PATTERN.search(
            text
        )

        if match:

            corrected = (
                FieldExtractor._correct_udyam_candidate(
                    match.group(0)
                )
            )

            if corrected:
                return corrected

        loose_candidates = re.findall(
            r"\bUDYAM[-\s]?[A-Z]{2}[-\s]?"
            r"\d{2}[-\s]?[A-Z0-9]{7}\b",
            text,
            flags=re.IGNORECASE,
        )

        for candidate in loose_candidates:

            corrected = (
                FieldExtractor._correct_udyam_candidate(
                    candidate
                )
            )

            if corrected:
                return corrected

        return None

    # ============================================================
    # UDYAM NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_udyam_type(
        value: str | None,
    ) -> str | None:

        if not value:
            return None

        upper = value.upper()

        for enterprise_type in (
            "MICRO",
            "SMALL",
            "MEDIUM",
        ):

            if re.search(
                rf"\b{enterprise_type}\b",
                upper,
            ):
                return enterprise_type

        return None

    @staticmethod
    def _normalize_social_category(
        value: str | None,
    ) -> str | None:

        if not value:
            return None

        upper = value.upper()

        for category in (
            "GENERAL",
            "OBC",
            "SC",
            "ST",
        ):

            if re.search(
                rf"\b{re.escape(category)}\b",
                upper,
            ):
                return category

        return None

    @staticmethod
    def _normalize_major_activity(
        value: str | None,
    ) -> str | None:

        if not value:
            return None

        upper = value.upper()

        for activity in (
            "MANUFACTURING",
            "SERVICES",
            "TRADING",
        ):

            if re.search(
                rf"\b{activity}\b",
                upper,
            ):
                return activity

        if "MANUFACT" in upper:
            return "MANUFACTURING"

        if "SERVICE" in upper:
            return "SERVICES"

        if "TRAD" in upper:
            return "TRADING"

        return None

    # ============================================================
    # UDYAM ENTERPRISE NAME CLEANING
    # ============================================================

    @staticmethod
    def _clean_udyam_enterprise_name(
        value: str,
    ) -> str:

        if not value:
            return ""

        value = re.split(
            r"\[\s*SNo\.?",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        value = re.split(
            r"\bSNo\.?\s*\|",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        value = re.split(
            r"\bClassification\s+Year\b",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        value = re.split(
            r"\bEnterprise\s+Type\s*\|",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        return FieldExtractor._clean_value(value)

    # ============================================================
    # UDYAM EXTRACTION
    # ============================================================

    def extract_udyam_fields(
        self,
        text: str,
    ) -> dict:

        if not text or not text.strip():
            return {}

        text = self._clean_text(text)

        result: dict = {}

        udyam_number = self._extract_udyam_number(text)

        if udyam_number:
            result["udyam_number"] = udyam_number

        enterprise_name = self._find_label_value(
            text,
            (
                "name of enterprise",
                "enterprise name",
            ),
            (
                "name of enterprise",
                "enterprise name",
                "type of enterprise",
                "major activity",
                "social category",
                "date of incorporation",
                "date of incorporation / registration of enterprise",
                "date of registration of enterprise",
                "date of commencement",
                "udyam registration date",
                "enterprise address",
                "official address of enterprise",
            ),
        )

        if enterprise_name:

            enterprise_name = (
                self._clean_udyam_enterprise_name(
                    enterprise_name
                )
            )

            if enterprise_name:
                result["enterprise_name"] = (
                    enterprise_name
                )

        enterprise_type = self._find_label_value(
            text,
            (
                "type of enterprise",
                "enterprise type",
            ),
            (
                "type of enterprise",
                "enterprise type",
                "major activity",
                "social category",
                "date of incorporation",
                "date of incorporation / registration of enterprise",
                "date of registration of enterprise",
                "date of commencement",
                "udyam registration date",
                "enterprise address",
                "official address of enterprise",
            ),
        )

        normalized_type = self._normalize_udyam_type(
            enterprise_type
        )

        if normalized_type:
            result["enterprise_type"] = normalized_type

        major_activity = self._find_label_value(
            text,
            (
                "major activity",
            ),
            (
                "major activity",
                "social category",
                "date of incorporation",
                "date of incorporation / registration of enterprise",
                "date of registration of enterprise",
                "date of commencement",
                "udyam registration date",
                "enterprise address",
                "official address of enterprise",
                "name of unit",
                "name of unit(s)",
            ),
        )

        normalized_activity = (
            self._normalize_major_activity(
                major_activity
            )
        )

        if normalized_activity:
            result["major_activity"] = normalized_activity

        social_category = self._find_label_value(
            text,
            (
                "social category",
            ),
            (
                "social category",
                "date of incorporation",
                "date of incorporation / registration of enterprise",
                "date of registration of enterprise",
                "date of commencement",
                "udyam registration date",
                "enterprise address",
                "official address of enterprise",
                "name of unit",
                "name of unit(s)",
            ),
        )

        normalized_social = (
            self._normalize_social_category(
                social_category
            )
        )

        if normalized_social:
            result["social_category"] = normalized_social

        incorporation_value = self._find_label_value(
            text,
            (
                "date of incorporation",
                "date of incorporation / registration of enterprise",
                "date of registration of enterprise",
            ),
        )

        incorporation_date = self._normalize_date(
            incorporation_value
        )

        if incorporation_date:
            result["date_of_incorporation"] = (
                incorporation_date
            )

        udyam_registration_value = self._find_label_value(
            text,
            (
                "udyam registration date",
                "date of udyam registration",
            ),
        )

        udyam_registration_date = self._normalize_date(
            udyam_registration_value
        )

        if udyam_registration_date:
            result["udyam_registration_date"] = (
                udyam_registration_date
            )

        enterprise_address = self._find_label_value(
            text,
            (
                "enterprise address",
                "official address of enterprise",
            ),
            (
                "enterprise address",
                "official address of enterprise",
                "date of incorporation",
                "date of incorporation / registration of enterprise",
                "date of registration of enterprise",
                "date of commencement",
                "udyam registration date",
                "nic",
                "national industry classification",
            ),
        )

        if enterprise_address:

            address_match = re.search(
                r"(enterprise\s+address|"
                r"official\s+address\s+of\s+enterprise)"
                r"\s*[:\-]?\s*"
                r"([^\n]+)"
                r"(?:\n\s*"
                r"(?!"
                r"(?:name\s+of\s+enterprise|"
                r"enterprise\s+name|"
                r"type\s+of\s+enterprise|"
                r"enterprise\s+type|"
                r"major\s+activity|"
                r"social\s+category|"
                r"date\s+of\s+incorporation|"
                r"date\s+of\s+commencement|"
                r"udyam\s+registration\s+date|"
                r"nic\b|"
                r"national\s+industry\s+classification)"
                r")"
                r"([^\n]+))?",
                text,
                flags=re.IGNORECASE,
            )

            if address_match:

                first_line = (
                    address_match.group(2)
                    or ""
                )

                continuation = (
                    address_match.group(3)
                    or ""
                )

                combined = (
                    f"{first_line} "
                    f"{continuation}"
                )

                enterprise_address = (
                    self._clean_value(combined)
                )

            else:
                enterprise_address = (
                    self._clean_value(
                        enterprise_address
                    )
                )

            if enterprise_address:
                result["enterprise_address"] = (
                    enterprise_address
                )

        return result