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
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Le[g|a|r]*al\s*Name",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Tr[a-z]{1,3}\s*Name(?:\s*,?\s*if\s*any)?",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Trade\s*Name(?:\s*,?\s*if\s*any)?",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Additional\s*Trade\s*Names?(?:\s*,?\s*if\s*any)?",

        # Constitution / business
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Constitution(?:\s*(?:of\s*)?Business)?",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Business\s*Type",

        # Address
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Address\s*of\s*Principal\s*Place\s*of\s*Business",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Add?r[e|i]{1,3}ss\s+of\s+P[r|e]in[a-z]*al\s+(?:P[l|m]ace\s+of\s+)?Business",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Principal\s*Place\s*of\s*Business",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Principal\s*Address",

        # Dates
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Date\s*of\s*Liability",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Thate\s*e[f|t]\s*Liability",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Registration\s*Date",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Date\s*of\s*Registration",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Period\s*of\s*Validity",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Date\s*of\s*Validity",

        # Registration
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Type\s*of\s*Registration",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Registration\s*Type",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Registration\s*Status",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Status\s*of\s*Registration",

        # Authority / certificate
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Particulars\s*of\s*Approving\s*Authority",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Date\s*of\s*Issue\s*of\s*Certificate",
        r"(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Date\s*of\s*Issue",
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
                |
                tn\s*NUMBER
            )
            \s*[:#\-=\(\[\{>\s]*
            ([0-9A-Z\(\)\[\]\{\}\:;\-\.\s]{13,22})
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        candidates: list[str] = []

        for match in labelled_pattern.finditer(
            normalized_text
        ):
            raw = match.group(1)
            cleaned = re.sub(r"[^A-Z0-9]", "", raw.upper())
            if len(cleaned) == 14 and cleaned[0].isdigit():
                cleaned = "0" + cleaned
            if len(cleaned) == 15 and cleaned not in candidates:
                candidates.append(cleaned)

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

        # Truncate at next field label or table row boundary (e.g. 2. Trade Name, 2 Trae Name, 3. Constitution)
        value = re.split(
            r"\s+(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?(?:Tr[a-z]{1,3}\s*Name|Trade\s*Name|Constitution|Address|Date|Type|Period|Particulars)",
            value,
            flags=re.IGNORECASE,
        )[0]

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

        # Truncate at next field label or table row boundary
        value = re.split(
            r"\s+(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?(?:Additional\s*Trade|Constitution|Address|Date|Type|Period|Particulars)",
            value,
            flags=re.IGNORECASE,
        )[0]

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

    @staticmethod
    def _score_gst_trade_name_candidate(
        val: str | None,
        base_ocr_score: float,
        frequency_count: int,
    ) -> float:
        if not val or not val.strip():
            return -100.0

        score = base_ocr_score / 10.0

        # Penalize non-ASCII and corrupt OCR symbols
        garbage_symbols = set("€“”«»|[]{}\\%~`_#$^&*")
        garbage_count = sum(1 for char in val if char in garbage_symbols)
        score -= (garbage_count * 25.0)

        non_ascii_count = sum(1 for char in val if ord(char) > 127)
        score -= (non_ascii_count * 20.0)

        words = val.split()
        if len(words) >= 2:
            score += 15.0

        entity_suffixes = (
            "LLP",
            "LIMITED",
            "PVT LTD",
            "PRIVATE LIMITED",
            "INC",
            "CORP",
            "PARTNERSHIP",
            "COMPANY",
            "ENTERPRISES",
            "TRADERS",
            "INDUSTRIES",
            "SERVICES",
        )
        if any(suf in val.upper() for suf in entity_suffixes):
            score += 25.0

        # Reward candidate consistency across multiple independent OCR passes
        if frequency_count > 1:
            score += (frequency_count - 1) * 15.0

        return score

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

        # Match against known clean constitution titles (including common OCR typo variants)
        known_constitutions = [
            ("Proprietorship", r"Proprietorship"),
            ("Partnership", r"Partnership"),
            ("Limited Liability Partnership", r"Li[m|n]ited\s+Li[a-z]{4,8}ty\s+Partnership"),
            ("Private Limited Company", r"Private\s+Limited\s+Company"),
            ("Public Limited Company", r"Public\s+Limited\s+Company"),
            ("Hindu Undivided Family", r"Hindu\s+Undivided\s+Family"),
            ("Society / Club / Trust / AOP", r"Society\s*/?\s*Club"),
            ("Government Department", r"Government\s+Department"),
        ]
        for k_title, k_pattern in known_constitutions:
            if re.search(rf"^\s*{k_pattern}\b", value, re.IGNORECASE):
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

        # Reusable OCR-tolerant label boundary components
        loc_label = r"loca[a-z1l]{1,4}ty(?:\s*/?\s*sub\s*loca[a-z1l]{1,4}ty)?"
        premises_label = r"(?:name\s+of\s+)?premises\s*/?\s*bu[il1]{1,3}ding"
        road_label = r"road\s*/?\s*street"
        landmark_label = r"(?:nearby\s+)?landm[a-z1l]{1,3}k"
        city_label = r"c[it1]{1,2}y\s*/?\s*town(?:\s*/?\s*v[il1]{1,3}lage)?"
        district_label = r"d[is1]{1,2}tr[ic1]{1,2}t"
        state_label = r"state"
        pin_label = r"pin\s*code"

        # Building number.
        match = re.search(
            r"bu[il1]{1,3}ding\s*no\.?\s*/?\s*f[la1]{1,2}t\s*no\.?\s*[:\-]?\s*"
            rf"(.*?)(?=\s+{premises_label}"
            rf"|\s+{road_label}"
            rf"|\s+{landmark_label}"
            rf"|\s+{loc_label}"
            rf"|\s+{city_label}"
            rf"|\s+{district_label}"
            rf"|\s+{state_label}"
            rf"|\s+{pin_label}"
            r"|$)",
            address,
            flags=re.IGNORECASE,
        )

        if match:
            value = FieldExtractor._clean_value(
                match.group(1)
            )

            if value:
                # Strip trailing isolated single-letter noise tokens (e.g. "44 x a" -> "44")
                value = re.sub(r"\s+[a-z](?:\s+[a-z])+$", "", value, flags=re.IGNORECASE).strip()
                if value:
                    details["building_number"] = value

        # Premises.
        match = re.search(
            rf"{premises_label}\s*[:\-]?\s*"
            rf"(.*?)(?=\s+{road_label}"
            rf"|\s+{landmark_label}"
            rf"|\s+{loc_label}"
            rf"|\s+{city_label}"
            rf"|\s+{district_label}"
            rf"|\s+{state_label}"
            rf"|\s+{pin_label}"
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
            rf"{road_label}\s*[:\-]?\s*"
            rf"(.*?)(?=\s+{landmark_label}"
            rf"|\s+{loc_label}"
            rf"|\s+{city_label}"
            rf"|\s+{district_label}"
            rf"|\s+{state_label}"
            rf"|\s+{pin_label}"
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
            rf"{landmark_label}\s*[:;\-]?\s*"
            rf"(.*?)(?=\s+{loc_label}"
            rf"|\s+{city_label}"
            rf"|\s+{district_label}"
            rf"|\s+{state_label}"
            rf"|\s+{pin_label}"
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
            rf"{loc_label}\s*[:\-]?\s*"
            rf"(.*?)(?=\s+{city_label}"
            rf"|\s+{district_label}"
            rf"|\s+{state_label}"
            rf"|\s+{pin_label}"
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
            rf"{city_label}\s*[:\-]?\s*"
            rf"(.*?)(?=\s+{district_label}"
            rf"|\s+{state_label}"
            rf"|\s+{pin_label}"
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
            rf"{district_label}\s*[:\-]?\s*"
            rf"(.*?)(?=\s+{state_label}"
            rf"|\s+{pin_label}"
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
            rf"{state_label}\s*[:\-]?\s*"
            rf"(.*?)(?=\s+{pin_label}|$)",
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
        ocr_candidates: list[dict | str] | None = None,
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
            result["principal_address"] = principal_address

        # ========================================================
        # MULTI-CANDIDATE RECOVERY FOR GST FIELDS
        # ========================================================
        if ocr_candidates:
            entity_suffixes = (
                "LLP",
                "LIMITED",
                "PVT LTD",
                "PRIVATE LIMITED",
                "INC",
                "CORP",
                "PARTNERSHIP",
                "COMPANY",
            )

            primary_legal = result.get("legal_name")
            is_suspicious_legal = (
                not primary_legal
                or not any(suf in (primary_legal or "").upper() for suf in entity_suffixes)
            )

            if is_suspicious_legal:
                scored_legals: list[tuple[float, str]] = []
                for c in ocr_candidates:
                    cand_text = c.get("text", "") if isinstance(c, dict) else str(c)
                    cand_score = c.get("score", 50.0) if isinstance(c, dict) else 50.0

                    v1 = self._extract_gst_legal_name(cand_text)

                    v2 = None
                    m = re.search(
                        r"([^\n]+)\s*\n\s*(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Le[g|a|r]*al\s*Name",
                        cand_text,
                        re.IGNORECASE,
                    )
                    if m:
                        raw_v = m.group(1).strip()
                        cleaned_v = self._clean_value(
                            re.sub(
                                r"^(?:\[?\s*\d{1,2}\s*[.\]]?\s*|[A-Za-z]{1,2}\s+ice\s+oi\s*|\[\s*beuat\s+are\s*|[\[\]{}|\-—–]+\s*)+",
                                "",
                                raw_v,
                                flags=re.IGNORECASE,
                            )
                        )
                        if cleaned_v and len(cleaned_v) >= 3 and self._is_reasonable_field_value(cleaned_v):
                            v2 = cleaned_v

                    for v in set(filter(None, (v1, v2))):
                        sc = cand_score / 10.0
                        if any(suf in v.upper() for suf in entity_suffixes):
                            sc += 30.0
                        if len(v.split()) >= 2:
                            sc += 10.0
                        scored_legals.append((sc, v))

                if scored_legals:
                    scored_legals.sort(key=lambda x: x[0], reverse=True)
                    top_score, top_legal = scored_legals[0]
                    top_legals = [v for sc, v in scored_legals if sc >= top_score - 5.0]
                    distinct_top_names = {re.sub(r"[^A-Z]", "", v.upper()) for v in top_legals}
                    if len(distinct_top_names) <= 2:
                        result["legal_name"] = top_legal

            # -----------------------------------------------------
            # Trade name multi-candidate recovery
            # -----------------------------------------------------
            primary_trade = result.get("trade_name")
            extracted_trades: list[tuple[str, float]] = []
            for c in ocr_candidates:
                cand_text = c.get("text", "") if isinstance(c, dict) else str(c)
                cand_score = c.get("score", 50.0) if isinstance(c, dict) else 50.0

                v1 = self._extract_gst_trade_name(cand_text)
                v2 = None
                m = re.search(
                    r"([^\n]+)\s*\n\s*(?:\[?\s*\d{1,2}\s*[.\]]?\s*)?Tr[a-z]{1,3}\s*Name",
                    cand_text,
                    re.IGNORECASE,
                )
                if m:
                    raw_v = m.group(1).strip()
                    cleaned_v = self._clean_value(
                        re.sub(
                            r"^(?:\[?\s*\d{1,2}\s*[.\]]?\s*|[A-Za-z]{1,2}\s+ice\s+oi\s*|\[\s*beuat\s+are\s*|[\[\]{}|\-—–]+\s*)+",
                            "",
                            raw_v,
                            flags=re.IGNORECASE,
                        )
                    )
                    if cleaned_v and len(cleaned_v) >= 3 and self._is_reasonable_field_value(cleaned_v):
                        v2 = cleaned_v

                for v in set(filter(None, (v1, v2))):
                    extracted_trades.append((v, cand_score))

            if extracted_trades:
                from collections import Counter

                norm_counts = Counter(re.sub(r"[^A-Z0-9]", "", v.upper()) for v, _ in extracted_trades)

                primary_score = (
                    FieldExtractor._score_gst_trade_name_candidate(
                        primary_trade,
                        50.0,
                        norm_counts.get(re.sub(r"[^A-Z0-9]", "", (primary_trade or "").upper()), 1),
                    )
                    if primary_trade
                    else -100.0
                )

                scored_trades = [
                    (
                        FieldExtractor._score_gst_trade_name_candidate(
                            v,
                            sc,
                            norm_counts.get(re.sub(r"[^A-Z0-9]", "", v.upper()), 1),
                        ),
                        v,
                    )
                    for v, sc in extracted_trades
                ]
                scored_trades.sort(key=lambda x: x[0], reverse=True)
                top_alt_score, top_alt_trade = scored_trades[0]

                if top_alt_score > primary_score + 15.0 and top_alt_score > 0.0:
                    result["trade_name"] = top_alt_trade

            if not result.get("principal_address"):
                for c in ocr_candidates:
                    cand_text = c.get("text", "") if isinstance(c, dict) else str(c)
                    addr = self._extract_gst_address(cand_text)
                    if addr and len(addr) >= 15:
                        result["principal_address"] = addr
                        break

            if not result.get("registration_date"):
                for c in ocr_candidates:
                    cand_text = c.get("text", "") if isinstance(c, dict) else str(c)
                    val_dt = self._find_label_value(
                        cand_text,
                        ("registration date", "date of registration", "date of liability"),
                    )
                    dt = self._normalize_date(val_dt)
                    if dt:
                        result["registration_date"] = dt
                        break

        # Re-check address details if address was set/updated
        principal_address = result.get("principal_address")
        if principal_address:
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

        # Truncate at explicit DOB labels, explicit separators (//), or date patterns
        value = re.split(
            r"(?://|\bDate\s+of\s+Birth\b|\bDOB\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b)",
            value,
            flags=re.IGNORECASE,
        )[0].strip()

        # Remove leading/trailing non-alphabetic characters
        value = re.sub(r"^[^A-Za-z]+", "", value)
        value = re.sub(r"[^A-Za-z]+$", "", value)

        # Remove common document header / label noise words
        header_noise_pattern = (
            r"\b(?:INCOME|TAX|DEPARTMENT|GOVT|INDIA|PERMANENT|ACCOUNT|"
            r"NUMBER|SIGNATURE|CARD|OFFICIAL|GOVERNMENT)\b"
        )
        value = re.sub(header_noise_pattern, " ", value, flags=re.IGNORECASE)

        # Clean noise punctuation/symbols
        value = re.sub(r"\b(?:E|=|—|-|~)\b", " ", value, flags=re.IGNORECASE)
        value = re.sub(r"[^A-Za-z.\s]", " ", value)
        value = re.sub(r"\s+", " ", value).strip()

        # Pop trailing isolated lowercase / non-uppercase noise tokens
        tokens = value.split()
        while tokens and (tokens[-1].islower() or (len(tokens[-1]) <= 2 and not tokens[-1].isupper())):
            tokens.pop()
        value = " ".join(tokens).strip()

        if not value or len(value) < 2:
            return None

        # Reject single lowercase words (e.g. OCR artifacts like "eat", "pos")
        if re.fullmatch(r"[a-z]{1,5}", value):
            return None

        # Reject string if it consists only of isolated 1-2 char noise tokens
        tokens = value.split()
        valid_tokens = [t for t in tokens if len(t) > 2 or t.isupper()]
        if not valid_tokens:
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

        # Date of birth extraction
        date_match = re.search(
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",
            text,
        )

        dob = None

        if date_match:
            dob = FieldExtractor._normalize_date(
                date_match.group(1)
            )

        if dob:
            result["date_of_birth"] = dob

        # ------------------------------------------------------------
        # PATH 1: Multi-line structural extraction (if text contains newlines)
        # ------------------------------------------------------------
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) > 1:
            govt_idx = -1
            for i, line in enumerate(lines):
                if re.search(r"GOVT\.?\s+OF\s+INDIA", line, re.IGNORECASE):
                    govt_idx = i
                    break

            if govt_idx != -1:
                candidate_lines = []
                for line in lines[govt_idx + 1:]:
                    if re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", line):
                        break
                    if re.search(r"\b(?:PERMANENT|ACCOUNT|NUMBER|SIGNATURE|CARD)\b", line, re.IGNORECASE):
                        break
                    cleaned = FieldExtractor._clean_pan_person_name(line)
                    if cleaned:
                        candidate_lines.append(cleaned)

                if len(candidate_lines) >= 2:
                    result["name"] = candidate_lines[0]
                    result["father_name"] = candidate_lines[1]
                    return result
                elif len(candidate_lines) == 1:
                    result["name"] = candidate_lines[0]
                    return result

        # ------------------------------------------------------------
        # PATH 2: Layout extraction for single-line or collapsed layout text
        # ------------------------------------------------------------
        normalized = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        before_dob = normalized

        if date_match:
            before_dob = normalized[:date_match.start()]

        govt_match = re.search(
            r"GOVT\.?\s+OF\s+INDIA",
            before_dob,
            flags=re.IGNORECASE,
        )

        if govt_match:
            after_govt = before_dob[govt_match.end():].strip()

            after_govt = re.sub(
                r"\b(?:Permanent|Account|Number|Signature)\b.*$",
                "",
                after_govt,
                flags=re.IGNORECASE,
            ).strip()

            noise_pattern = (
                r"\b(?:INCOME|TAX|DEPARTMENT|GOVT|INDIA|PERMANENT|ACCOUNT|"
                r"NUMBER|SIGNATURE|CARD|OFFICIAL|GOVERNMENT)\b"
            )

            matches = list(re.finditer(r"\b([A-Z]{2,}(?:\s+[A-Z]{2,})+)\b", after_govt))
            blocks = []
            valid_matches = []
            for m in matches:
                b = m.group(1).strip()
                if not re.search(noise_pattern, b, re.IGNORECASE):
                    cleaned = FieldExtractor._clean_pan_person_name(b)
                    if cleaned and len(cleaned.split()) >= 2:
                        blocks.append(cleaned)
                        valid_matches.append(m)

            if len(blocks) >= 2 and len(valid_matches) >= 2:
                m1, m2 = valid_matches[0], valid_matches[1]
                between = after_govt[m1.end():m2.start()]
                if re.search(r"[A-Za-z0-9]", between):
                    result["name"] = blocks[0]
                    result["father_name"] = blocks[1]
                else:
                    cleaned_all = FieldExtractor._clean_pan_person_name(after_govt)
                    if cleaned_all:
                        result["name"] = cleaned_all
            elif blocks:
                result["name"] = blocks[0]
            else:
                cleaned_all = FieldExtractor._clean_pan_person_name(after_govt)
                if cleaned_all:
                    result["name"] = cleaned_all

            if "name" not in result:
                before_govt = normalized[:govt_match.start()]
                before_govt = re.sub(
                    r".*?INCOME\s+TAX\s+DEPARTMENT",
                    "",
                    before_govt,
                    flags=re.IGNORECASE,
                )
                candidate = FieldExtractor._clean_pan_person_name(before_govt)
                if candidate:
                    result["name"] = candidate

        return result

    # ============================================================
    # PAN FIELD EXTRACTION
    # ============================================================

    def extract_pan_fields(
        self,
        text: str,
        ocr_candidates: list[dict | str] | None = None,
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
            cleaned_name = self._clean_pan_person_name(name)
            if cleaned_name:
                result["name"] = cleaned_name

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

        # ========================================================
        # MULTI-CANDIDATE RECOVERY FOR PAN FIELDS
        # ========================================================
        if ocr_candidates:
            from collections import Counter

            # 1. Multi-candidate DOB consensus
            dobs: list[str] = []
            for c in ocr_candidates:
                cand_text = c.get("text", "") if isinstance(c, dict) else str(c)
                m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", cand_text)
                if m:
                    dt = self._normalize_date(m.group(1))
                    if dt:
                        dobs.append(dt)

            if dobs:
                dob_counts = Counter(dobs)
                top_dob, top_count = dob_counts.most_common(1)[0]
                primary_dob = result.get("date_of_birth")
                if top_count > dob_counts.get(primary_dob, 0):
                    result["date_of_birth"] = top_dob

            # 2. Multi-candidate name & father_name recovery if missing
            if "name" not in result or "father_name" not in result:
                for c in ocr_candidates:
                    cand_text = c.get("text", "") if isinstance(c, dict) else str(c)
                    cand_layout = self._extract_pan_ocr_layout_fields(cand_text, pan=pan)
                    if "name" not in result and "name" in cand_layout:
                        result["name"] = cand_layout["name"]
                    if "father_name" not in result and "father_name" in cand_layout:
                        result["father_name"] = cand_layout["father_name"]
                    if "name" in result and "father_name" in result:
                        break

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
            r"\bU?\s*DYAM[-\s]?[A-Z]{2}[-\s]?"
            r"\d{2}[-\s]?[A-Z0-9]{7}\b",
            text,
            flags=re.IGNORECASE,
        )

        for candidate in loose_candidates:

            standardized = re.sub(
                r"^U\s*DYAM",
                "UDYAM",
                candidate,
                flags=re.IGNORECASE,
            )

            corrected = (
                FieldExtractor._correct_udyam_candidate(
                    standardized
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

        stop_patterns = (
            r"\[\s*SNo\.?",
            r"\bSNo\.?\s*\|",
            r"\bClassification\s+Year\b",
            r"\bEnterprise\s+Type\s*\|",
            r"\bOwner\s+Name\b",
            r"\bPAN\b",
            r"\bDo\s+you\s+have\s+GSTIN\b",
            r"\bEmail\s+Id\b",
            r"\bMobile\s+No\b",
            r"\bSocial\s+Category\b",
            r"\bGender\b",
            r"\bSpecially\s+Abled\b",
            r"\bDate\s+of\s+Incorporation\b",
            r"\bDate\s+of\s+Commencement\b",
        )

        for pattern in stop_patterns:
            value = re.split(
                pattern,
                value,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]

        cleaned = FieldExtractor._clean_value(value)
        # Strip leading/trailing OCR quotation, guillemet, bracket, and boundary symbol artifacts
        cleaned = re.sub(
            r"^[|\:_—\-«»“”‘’\"'\s]+|[|\:_—\-«»“”‘’\"'\s]+$",
            "",
            cleaned,
        ).strip()
        return cleaned

    @staticmethod
    def _score_udyam_enterprise_name_candidate(
        val: str | None,
        base_ocr_score: float,
        frequency_count: int,
    ) -> float:
        if not val or not val.strip():
            return -100.0

        val = val.strip()
        score = base_ocr_score / 10.0

        # Penalize non-ASCII and corrupt OCR symbols
        garbage_symbols = set("€“”«»|[]{}\\%~`_#$^&*")
        garbage_count = sum(1 for char in val if char in garbage_symbols)
        score -= (garbage_count * 25.0)

        non_ascii_count = sum(1 for char in val if ord(char) > 127)
        score -= (non_ascii_count * 20.0)

        # Penalize label contamination
        label_contaminants = (
            "OWNER NAME",
            "PAN",
            "GSTIN",
            "ENTERPRISE TYPE",
            "SNO",
            "PROPRIETARY",
            "SOCIAL CATEGORY",
            "GENDER",
            "MOBILE",
            "EMAIL",
            "DATE OF INCORPORATION",
        )
        upper_val = val.upper()
        if any(c in upper_val for c in label_contaminants):
            score -= 50.0

        words = val.split()
        if len(words) >= 2:
            score += 15.0

        entity_suffixes = (
            "CARE",
            "ENTERPRISES",
            "TRADERS",
            "INDUSTRIES",
            "SERVICES",
            "SOLUTIONS",
            "LIMITED",
            "LTD",
            "PVT",
            "LLP",
            "COMPANY",
            "PARTNERSHIP",
            "STORE",
            "MART",
            "WORKS",
            "CREATIONS",
            "AGENCY",
            "DESIGNS",
            "TECH",
            "TECHNOLOGIES",
        )
        if any(suf in upper_val for suf in entity_suffixes):
            score += 20.0

        if frequency_count > 1:
            score += (frequency_count - 1) * 15.0

        return score

    @staticmethod
    def _clean_udyam_official_address(text: str) -> str:
        if not text:
            return ""

        stop_patterns = (
            r"\bMobile\s+No\.?\b",
            r"\bMobile\b",
            r"\bEmail\s+Id\b",
            r"\bEmail\b",
            r"\bNational\s+Industry\s+Classification\b",
            r"\bNIC\s+Code\b",
            r"\bAre\s+you\s+interested\b",
            r"\bGovernment\s+e-Market\b",
            r"\bGeM\b",
            r"\bTReDS\b",
            r"\bNational\s+Career\s+Service\b",
            r"\bNCS\b",
            r"\bDistrict\s+Industries\s+Centre\b",
            r"\bMSME-DFO\b",
            r"\bDate\s+of\s+Printing\b",
            r"\bDate\s+of\s+Udyam\s+Registration\b",
            r"\bUnits?\b",
        )

        block = text
        for pattern in stop_patterns:
            block = re.split(pattern, block, maxsplit=1, flags=re.IGNORECASE)[0]

        # Truncate at PIN if present
        pin_match = re.search(r"(\bPin\s*[:\-]?\s*\d{6}|\b\d{6}\b)", block, re.IGNORECASE)
        if pin_match:
            block = block[:pin_match.end()]

        sub_labels = [
            r"(?:Flat|Fiat|Fia|Fla|Flau)[\s/'’‘`]*Door[\s/'’‘`]*Block\s*(?:No\.?)?",
            r"(?:Name\s+of\s+)?Premises[\s/'’‘`]*Building",
            r"Village[\s/'’‘`]*Town",
            r"Village[\s/'’‘`]*Tow",
            r"\bBlock\b",
            r"Road[\s/'’‘`]*Street[\s/'’‘`]*Lane",
            r"City",
            r"State",
            r"District",
            r"Pin\s*Code",
            r"Pin",
        ]
        pattern = r"(?:^|[\n\[\]\|\{\}\_\t\s])(?:" + "|".join(sub_labels) + r")\s*[:|\-\[\{]?\s*"
        block = re.sub(pattern, " ", block, flags=re.IGNORECASE)

        # Clean OCR table delimiters / bracket artifacts
        block = re.sub(r"[\[\]\{\}\|_~“„”«»]", " ", block)

        # Filter out isolated lowercase OCR noise tokens
        valid_lowercase = {"near", "opposite", "behind", "next", "above", "below", "floor", "road", "street", "lane", "city", "post", "dist", "district", "via", "at", "po"}
        tokens = block.split()
        filtered = []
        for token in tokens:
            clean_tok = re.sub(r"^[^\w]+|[^\w]+$", "", token)
            if clean_tok.islower() and len(clean_tok) >= 3 and clean_tok not in valid_lowercase:
                continue
            filtered.append(token)
        block = " ".join(filtered)

        block = re.sub(r"\s+[:\.]+\s+", " ", block)
        block = re.sub(r"\s*,\s*", ", ", block)
        block = re.sub(r"\s+", " ", block).strip()
        block = re.sub(r"^[,\.\:\-\|\s]+|[,\.\:\-\|\s]+$", "", block)
        return block

    @staticmethod
    def _extract_udyam_official_address(text: str) -> str | None:
        if not text:
            return None
        match = re.search(
            r"(?:(?:Off?ici?al|[A-Za-z0-9]{2,8}\s+ar?e?s?|tia)?\s*add?ress\s+of\s+Enterprise|Enterprise\s+Address)\s*[:|\-]?\s*(.+)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None
        raw_addr = match.group(1)
        cleaned = FieldExtractor._clean_udyam_official_address(raw_addr)
        return cleaned if len(cleaned) >= 10 else None

    @staticmethod
    def _score_udyam_address_candidate(
        val: str | None,
        base_ocr_score: float,
    ) -> float:
        if not val or len(val) < 10:
            return -100.0
        score = base_ocr_score / 10.0
        if re.search(r"\b\d{6}\b", val):
            score += 30.0
        garbage_symbols = set("€“”«»|[]{}\\%~`_#$^&*")
        score -= sum(15.0 for char in val if char in garbage_symbols)

        # Reward specific office/flat/door number pattern (e.g. OFFICE NO 102, FLAT NO 5)
        if re.search(r"\b(?:OFFICE|FLAT|DOOR|PLOT|SHOP)\s+(?:NO\.?|NUMBER)?\s*\d+", val, re.IGNORECASE):
            score += 25.0

        if re.search(r"\bOFFICE\b|\bFLAT\b|\bDOOR\b", val, re.IGNORECASE):
            score += 15.0
        if re.search(r"\bFLOOR\b|\bBUILDING\b|\bPREMISES\b", val, re.IGNORECASE):
            score += 15.0
        if re.search(r"\bROAD\b|\bSTREET\b|\bLANE\b", val, re.IGNORECASE):
            score += 10.0
        return score

    # ============================================================
    # UDYAM EXTRACTION
    # ============================================================

    def extract_udyam_fields(
        self,
        text: str,
        ocr_candidates: list[dict] | None = None,
    ) -> dict:

        if not text or not text.strip():
            return {}

        text = self._clean_text(text)

        result: dict = {}

        # 1. Udyam Number
        udyam_number = self._extract_udyam_number(text)
        if not udyam_number and ocr_candidates:
            for cand in ocr_candidates:
                cand_text = cand.get("text", "") if isinstance(cand, dict) else str(cand)
                udyam_number = self._extract_udyam_number(cand_text)
                if udyam_number:
                    break

        if udyam_number:
            result["udyam_number"] = udyam_number

        # 2. Enterprise Name with alternate OCR recovery
        name_labels = (
            "name of enterprise",
            "name af enterprise",
            "name of enerprise",
            "name af enerprise",
            "enterprise name",
        )
        stop_name_labels = (
            "name of enterprise",
            "enterprise name",
            "type of enterprise",
            "owner name",
            "pan",
            "do you have gstin",
            "email id",
            "mobile no",
            "social category",
            "gender",
            "specially abled",
            "major activity",
            "date of incorporation",
            "date of incorporation / registration of enterprise",
            "date of registration of enterprise",
            "date of commencement",
            "udyam registration date",
            "enterprise address",
            "official address of enterprise",
        )

        all_ocr_sources: list[tuple[str, float]] = [(text, 50.0)]
        if ocr_candidates:
            for cand in ocr_candidates:
                if isinstance(cand, dict):
                    cand_t = cand.get("text", "")
                    cand_s = float(cand.get("score", 40.0))
                else:
                    cand_t = str(cand)
                    cand_s = 40.0
                if cand_t and cand_t.strip():
                    all_ocr_sources.append((cand_t, cand_s))

        name_candidates: list[tuple[str, float]] = []
        for src_text, src_score in all_ocr_sources:
            raw_name = self._find_label_value(
                src_text,
                name_labels,
                stop_name_labels,
            )
            if raw_name:
                cleaned_name = self._clean_udyam_enterprise_name(raw_name)
                if cleaned_name and len(cleaned_name) >= 3:
                    name_candidates.append((cleaned_name, src_score))

        if name_candidates:
            counts: dict[str, int] = {}
            for name_val, _ in name_candidates:
                counts[name_val] = counts.get(name_val, 0) + 1

            scored_names: list[tuple[float, str]] = []
            for name_val, src_score in name_candidates:
                sc = self._score_udyam_enterprise_name_candidate(
                    name_val,
                    src_score,
                    counts.get(name_val, 1),
                )
                scored_names.append((sc, name_val))

            scored_names.sort(key=lambda x: x[0], reverse=True)
            best_sc, best_name = scored_names[0]
            if best_sc > 0:
                result["enterprise_name"] = best_name

        # 3. Enterprise Type
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

        normalized_type = self._normalize_udyam_type(enterprise_type)
        if normalized_type:
            result["enterprise_type"] = normalized_type

        # 4. Major Activity
        major_activity = self._find_label_value(
            text,
            ("major activity",),
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

        normalized_activity = self._normalize_major_activity(major_activity)
        if normalized_activity:
            result["major_activity"] = normalized_activity

        # 5. Social Category
        social_category = self._find_label_value(
            text,
            ("social category",),
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

        normalized_social = self._normalize_social_category(social_category)
        if normalized_social:
            result["social_category"] = normalized_social

        # 6. Incorporation Date
        incorporation_value = self._find_label_value(
            text,
            (
                "date of incorporation",
                "date of incorporation / registration of enterprise",
                "date of registration of enterprise",
            ),
        )

        incorporation_date = self._normalize_date(incorporation_value)
        if incorporation_date:
            result["date_of_incorporation"] = incorporation_date

        # 7. Udyam Registration Date
        udyam_registration_value = self._find_label_value(
            text,
            (
                "udyam registration date",
                "date of udyam registration",
            ),
        )

        udyam_registration_date = self._normalize_date(udyam_registration_value)
        if udyam_registration_date:
            result["udyam_registration_date"] = udyam_registration_date

        # 8. Enterprise Address with sub-label cleaning & candidate scoring
        address_candidates: list[tuple[float, str]] = []
        for src_text, src_score in all_ocr_sources:
            extracted_addr = self._extract_udyam_official_address(src_text)
            if not extracted_addr:
                # Fallback to _find_label_value extraction
                raw_addr_val = self._find_label_value(
                    src_text,
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
                        "government e-market",
                        "gem",
                        "treds",
                        "national career service",
                        "ncs",
                        "district industries centre",
                        "msme-dfo",
                        "date of printing",
                        "date of udyam registration",
                        "mobile",
                        "mobile no",
                        "email",
                        "email id",
                    ),
                )
                if raw_addr_val:
                    extracted_addr = self._clean_udyam_official_address(raw_addr_val)

            if extracted_addr and len(extracted_addr) >= 10:
                sc = self._score_udyam_address_candidate(extracted_addr, src_score)
                address_candidates.append((sc, extracted_addr))

        if address_candidates:
            address_candidates.sort(key=lambda x: x[0], reverse=True)
            best_addr_sc, best_addr = address_candidates[0]
            if best_addr_sc > 0:
                result["enterprise_address"] = best_addr

        return result