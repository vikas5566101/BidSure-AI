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

    # Strict valid GSTIN format.
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
            r"^[\s:;,\-|]+",
            "",
            value,
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

    @staticmethod
    def _find_label_value(
        text: str,
        labels: tuple[str, ...],
        stop_labels: tuple[str, ...] | None = None,
    ) -> str | None:

        if not text:
            return None

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
        """
        Correct and validate a GSTIN candidate.

        GSTIN format:

        Positions 1-2:
            State code -> digits

        Positions 3-7:
            PAN letters -> letters

        Positions 8-11:
            PAN digits -> digits

        Position 12:
            PAN letter -> letter

        Position 13:
            Entity number -> alphanumeric

        Position 14:
            Z

        Position 15:
            Checksum -> alphanumeric

        Example:

            27ABCDE1234FIZ5

        becomes:

            27ABCDE1234F1Z5
        """

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

        # --------------------------------------------------------
        # Positions 1-2: digits
        # --------------------------------------------------------

        chars[0] = FieldExtractor._ocr_digit(chars[0])
        chars[1] = FieldExtractor._ocr_digit(chars[1])

        # --------------------------------------------------------
        # Positions 3-7: letters
        # --------------------------------------------------------

        for index in range(2, 7):
            chars[index] = FieldExtractor._ocr_letter(
                chars[index]
            )

        # --------------------------------------------------------
        # Positions 8-11: digits
        # --------------------------------------------------------

        for index in range(7, 11):
            chars[index] = FieldExtractor._ocr_digit(
                chars[index]
            )

        # --------------------------------------------------------
        # Position 12: letter
        # --------------------------------------------------------

        chars[11] = FieldExtractor._ocr_letter(
            chars[11]
        )

        # --------------------------------------------------------
        # Position 13: entity number
        #
        # Alphanumeric position.
        #
        # Common OCR:
        #
        # I -> 1
        # O -> 0
        # --------------------------------------------------------

        if chars[12] == "I":
            chars[12] = "1"
        elif chars[12] == "O":
            chars[12] = "0"

        # --------------------------------------------------------
        # Position 14: fixed Z
        #
        # If OCR reads Z incorrectly as 2 or 7, correct it.
        # --------------------------------------------------------

        if chars[13] in ("2", "7"):
            chars[13] = "Z"

        # --------------------------------------------------------
        # Position 15: checksum
        # --------------------------------------------------------

        corrected = "".join(chars)

        # Final strict validation.
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
        """
        Extract and normalize a GSTIN from OCR/native text.

        Handles:
        - Normal GSTIN
        - GSTIN with spaces
        - GSTIN with OCR character substitutions
        - Labelled GSTIN / Registration Number
        - Unlabelled GSTIN

        GSTIN structure:

            Positions 0-1   : State code       -> digits
            Positions 2-6   : PAN letters       -> letters
            Positions 7-10  : PAN digits        -> digits
            Position 11     : PAN letter        -> letter
            Position 12     : Entity number     -> alphanumeric
            Position 13     : Z                 -> Z
            Position 14     : Checksum          -> alphanumeric

        Common OCR corrections are applied only where the
        character position makes the correction reasonable.
        """

        if not text:
            return None

        # --------------------------------------------------------
        # OCR normalization
        # --------------------------------------------------------

        normalized_text = text.upper()

        # Remove whitespace INSIDE GSTIN-like sequences.
        #
        # Example:
        #   27 ABCDE 1234 F1Z5
        #
        # becomes:
        #   27ABCDE1234F1Z5
        #
        normalized_text = re.sub(
            r"(?<=\w)\s+(?=\w)",
            "",
            normalized_text,
        )

        # --------------------------------------------------------
        # Candidate extraction
        # --------------------------------------------------------

        candidates: list[str] = []

        # 1. Labelled GSTIN
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

        for match in labelled_pattern.finditer(
            normalized_text
        ):
            candidates.append(
                match.group(1).upper()
            )

        # --------------------------------------------------------
        # 2. Generic 15-character candidates
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
        # 3. OCR tolerant candidates
        #
        # OCR may produce:
        #
        #   06AIXPI829LIIZC
        #
        # where:
        #
        #   L -> 1
        #   I -> 1
        #
        # We therefore also search for GSTIN-shaped strings
        # containing common OCR-confused characters.
        # --------------------------------------------------------

        ocr_pattern = re.compile(
            r"(?<![A-Z0-9])"
            r"[0-9A-Z]{15}"
            r"(?![A-Z0-9])",
            re.IGNORECASE,
        )

        for match in ocr_pattern.finditer(
            normalized_text
        ):
            candidate = match.group(0).upper()

            if candidate not in candidates:
                candidates.append(candidate)

        # --------------------------------------------------------
        # Normalize each candidate
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
        """
        Correct common OCR errors in a GSTIN candidate.

        Corrections are POSITION-AWARE.

        Numeric positions:
            0, 1, 7, 8, 9, 10

        Alphabetic positions:
            2, 3, 4, 5, 6, 11

        Fixed position:
            13 -> Z

        Alphanumeric:
            12, 14

        Common OCR substitutions:

            O -> 0
            I -> 1
            L -> 1
            S -> 5
            B -> 8

        We do NOT blindly replace characters everywhere.
        """

        if not candidate:
            return None

        candidate = candidate.upper().strip()

        if len(candidate) != 15:
            return None

        chars = list(candidate)

        # --------------------------------------------------------
        # Numeric positions
        # --------------------------------------------------------

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

            char = chars[index]

            if char in numeric_ocr_map:
                chars[index] = numeric_ocr_map[char]

        # --------------------------------------------------------
        # Alphabetic positions
        # --------------------------------------------------------

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

            char = chars[index]

            if char in alphabetic_ocr_map:
                chars[index] = alphabetic_ocr_map[char]

        # --------------------------------------------------------
        # Position 13 must be Z.
        #
        # OCR may occasionally read:
        #
        #   2 -> Z
        #   7 -> Z
        # --------------------------------------------------------

        if chars[13] != "Z":

            if chars[13] in {
                "2",
                "7",
                "I",
                "1",
            }:
                chars[13] = "Z"

        # --------------------------------------------------------
        # Entity number position.
        #
        # Position 12 is officially alphanumeric.
        #
        # However, OCR frequently reads:
        #
        #   1 as I
        #
        # For our extraction pipeline, when an I appears here,
        # prefer the numeric interpretation.
        #
        # This fixes:
        #
        #   27ABCDE1234FIZ5
        #
        # -> 27ABCDE1234F1Z5
        #
        # and the real OCR:
        #
        #   06AIXPI829LIIZC
        #
        # -> 06AIXPI8291I1ZC
        # --------------------------------------------------------

        if chars[12] == "I":
            chars[12] = "1"

        # --------------------------------------------------------
        # Position 14 is checksum/alphanumeric.
        #
        # Do not aggressively modify it because it may
        # legitimately be either a digit or a letter.
        # --------------------------------------------------------

        corrected = "".join(chars)

        # --------------------------------------------------------
        # Final structural validation
        # --------------------------------------------------------

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
            ),
        )

        if not value:
            return None

        value = re.sub(
            r"\s+\d{1,3}\s*[—–-]\s*$",
            "",
            value,
        )

        value = re.sub(
            r"\s+[—–-]\s*$",
            "",
            value,
        )

        value = re.sub(
            r"\s*[\[\]{}|]+\s*$",
            "",
            value,
        )

        return FieldExtractor._clean_value(
            value
        )

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

        value = FieldExtractor._clean_value(
            value
        )

        return value or None

    # ============================================================
    # GST CONSTITUTION
    # ============================================================

    @staticmethod
    def _extract_constitution(
        text: str,
    ) -> str | None:

        value = FieldExtractor._find_label_value(
            text,
            (
                "constitution of business",
                "constitution",
            ),
            (
                "constitution of business",
                "constitution",
                "address of principal place of business",
                "principal place of business",
                "principal address",
                "date of liability",
                "registration date",
                "type of registration",
            ),
        )

        if not value:
            return None

        return FieldExtractor._clean_value(
            value
        )

    # ============================================================
    # GST REGISTRATION TYPE
    # ============================================================

    @staticmethod
    def _extract_registration_type(
        text: str,
    ) -> str | None:

        value = FieldExtractor._find_label_value(
            text,
            (
                "type of registration",
                "registration type",
            ),
            (
                "type of registration",
                "registration type",
                "particulars of approving",
                "date of issue of certificate",
                "date of liability",
                "date of validity",
            ),
        )

        if not value:
            return None

        upper = value.upper()

        known_types = (
            "NON-RESIDENT TAXABLE PERSON",
            "CASUAL TAXABLE PERSON",
            "SEZ DEVELOPER",
            "COMPOSITION",
            "REGULAR",
            "SEZ UNIT",
            "TDS",
            "TCS",
        )

        for registration_type in known_types:
            if registration_type in upper:
                return registration_type

        return FieldExtractor._clean_value(
            value
        )

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
            (
                "registration status",
                "status of registration",
                "business type",
                "principal address",
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
        Extract the complete GST principal address block.

        Handles OCR/native text where the structured address spans
        multiple lines, for example:

            Address of Principal Place of Business
            Building No./Flat No.: 44
            Name Of Premises/Building: AMBALA CANTT
            Road/Street: LUXMI NAGAR
            Nearby Landmark; BD Flour Mill
            Locality/Sub Locality: Nishat Bagh
            City/Town/Village: Ambala
            District: Ambala
            State: Haryana
            PIN Code: 133001 6

        The address extraction stops at the next certificate-level
        field such as Date of Liability or Type of Registration.
        """

        if not text:
            return None

        # ------------------------------------------------------------
        # Address labels
        # ------------------------------------------------------------

        address_labels = (
            "address of principal place of business",
            "principal place of business",
            "principal address",
        )

        # ------------------------------------------------------------
        # Certificate-level fields that terminate the address block.
        #
        # IMPORTANT:
        # Do NOT include address sub-fields here.
        # ------------------------------------------------------------

        stop_labels = (
            "date of liability",
            "date of validity",
            "type of registration",
            "registration type",
            "registration status",
            "status of registration",
            "particulars of approving",
            "date of issue of certificate",
            "date of issue",
        )

        address_pattern = "|".join(
            re.escape(label)
            for label in address_labels
        )

        stop_pattern = "|".join(
            re.escape(label)
            for label in stop_labels
        )

        # ------------------------------------------------------------
        # Extract everything after the address heading.
        #
        # We deliberately allow newlines here because the real GST
        # certificate has the address spread across multiple lines.
        # ------------------------------------------------------------

        pattern = re.compile(
            rf"(?:{address_pattern})"
            rf"\s*[:\-]?\s*"
            rf"(.+?)"
            rf"(?="
            rf"\s+(?:{stop_pattern})"
            rf"(?:\s*[:\-]|\s|$)"
            rf"|$"
            rf")",
            flags=re.IGNORECASE | re.DOTALL,
        )

        match = pattern.search(text)

        if not match:
            return None

        value = match.group(1)

        # ------------------------------------------------------------
        # Normalize whitespace/newlines.
        #
        # This converts:
        #
        # Building No...: 44
        # Name Of Premises...: AMBALA CANTT
        #
        # into one continuous address string.
        # ------------------------------------------------------------

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        value = FieldExtractor._clean_value(
            value
        )

        if not value:
            return None

        # ------------------------------------------------------------
        # Remove OCR garbage after PIN.
        #
        # Example:
        #
        # PIN Code: 133001 6
        #
        # becomes:
        #
        # PIN Code: 133001
        #
        # Only do this when PIN Code is explicitly present.
        # ------------------------------------------------------------

        value = re.sub(
            r"(pin\s*code\s*[:\-]?\s*\d{6})"
            r"(?:\s+\d+)?"
            r"\s*$",
            r"\1",
            value,
            flags=re.IGNORECASE,
        )

        # ------------------------------------------------------------
        # Remove common OCR trailing junk after the PIN.
        #
        # This is intentionally conservative: we only clean content
        # after an explicitly detected six-digit PIN.
        # ------------------------------------------------------------

        pin_match = re.search(
            r"(pin\s*code\s*[:\-]?\s*\d{6})",
            value,
            flags=re.IGNORECASE,
        )

        if pin_match:
            value = value[:pin_match.end()]

        return FieldExtractor._clean_value(
            value
        )

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

        # Building number
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

        # Premises
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

        # Road
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

        # Landmark
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

        # Locality
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

        # City
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

        # District
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

        # State
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

        # PIN
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

        gstin = self._extract_gstin(text)

        if gstin:
            result["gstin"] = gstin

        legal_name = self._extract_gst_legal_name(
            text
        )

        if legal_name:
            result["legal_name"] = legal_name

        trade_name = self._extract_gst_trade_name(
            text
        )

        if trade_name:
            result["trade_name"] = trade_name

        constitution = self._extract_constitution(
            text
        )

        if constitution:
            result["constitution"] = constitution

        registration_date_value = (
            self._find_label_value(
                text,
                (
                    "registration date",
                    "date of registration",
                    "date of liability",
                ),
                (
                    "registration date",
                    "date of registration",
                    "date of liability",
                    "date of validity",
                    "type of registration",
                    "registration status",
                ),
            )
        )

        registration_date = self._normalize_date(
            registration_date_value
        )

        if registration_date:
            result["registration_date"] = (
                registration_date
            )

        registration_type = (
            self._extract_registration_type(text)
        )

        if registration_type:
            result["registration_type"] = (
                registration_type
            )

        registration_status = (
            self._extract_registration_status(text)
        )

        if registration_status:
            result["registration_status"] = (
                registration_status
            )

        business_type = self._find_label_value(
            text,
            (
                "business type",
            ),
            (
                "business type",
                "principal address",
                "principal place of business",
            ),
        )

        if business_type:
            result["business_type"] = (
                self._uppercase(
                    business_type
                )
            )

        principal_address = (
            self._extract_gst_address(text)
        )

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

            address_lower = (
                principal_address.lower()
            )

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
    def _clean_pan_person_name(value: str | None) -> str | None:
        """
        Clean a person name extracted from noisy PAN OCR.
    
        This is intentionally conservative. We remove obvious
        OCR/document noise but do not try to invent a name.
        """
    
        if not value:
            return None
    
        value = value.strip()
    
        # Remove common OCR symbols at the beginning.
        value = re.sub(
            r"^[^A-Za-z]+",
            "",
            value,
        )
    
        # Remove common PAN-card OCR noise.
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
        """
        Extract PAN name/father name/DOB from flattened OCR.
    
        Example OCR:
    
            INCOME TAX DEPARTMENT
            MUNNA PRASAD SHARAN
            GOVT. OF INDIA
            RAM NARAYAN SAHANI22/1/1975
            Permanent Account Number
            EWKPS7210G
    
        Returns only fields that can be extracted with
        reasonable structural evidence.
    
        This is a fallback only. Labelled extraction remains
        the primary mechanism.
        """
    
        if not text:
            return {}
    
        result: dict = {}
    
        # --------------------------------------------------------
        # Normalize whitespace without destroying text.
        # --------------------------------------------------------
    
        normalized = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()
    
        # --------------------------------------------------------
        # DATE OF BIRTH
        # --------------------------------------------------------
    
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
    
        # --------------------------------------------------------
        # Find the date position.
        # Everything immediately before DOB is useful for
        # identifying father's name.
        # --------------------------------------------------------
    
        before_dob = normalized
    
        if date_match:
            before_dob = normalized[:date_match.start()]
    
        # --------------------------------------------------------
        # FATHER NAME
        #
        # Real OCR pattern:
        #
        # GOVT. OF INDIA RAM NARAYAN SAHANI22/1/1975
        #
        # Therefore take text after GOVT. OF INDIA and before DOB.
        # --------------------------------------------------------
    
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
    
                # Prevent document words from becoming
                # part of the father's name.
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
    
        # --------------------------------------------------------
        # NAME
        #
        # In the flattened real OCR:
        #
        # INCOME TAX DEPARTMENT E = MUNNA PRASAD SHARAN
        # GOVT. OF INDIA
        #
        # We use the first GOVT. OF INDIA as the boundary.
        # --------------------------------------------------------
    
        if govt_match:
    
            before_govt = normalized[
                :govt_match.start()
            ]
    
            # Remove document header.
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
    
                # Remove common OCR leftovers.
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
    
                # A person's PAN-card name should not contain
                # document boilerplate.
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
    # PAN EXTRACTION
    # ============================================================

    def extract_pan_fields(
        self,
        text: str,
    ) -> dict:
        """
        Extract PAN card fields.
    
        Extraction strategy:
    
        1. PAN number extraction
        2. Normal labelled-field extraction
        3. OCR-layout fallback for flattened PAN cards
    
        Labelled extraction always has priority.
        """
    
        if not text or not text.strip():
            return {}
    
        text = self._clean_text(text)
    
        result: dict = {}
    
        # ========================================================
        # 1. PAN NUMBER
        # ========================================================
    
        pan = self._extract_pan_number(text)
    
        if pan:
            result["pan"] = pan
    
        # ========================================================
        # 2. NORMAL LABELLED NAME
        # ========================================================
    
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
    
        # ========================================================
        # 3. NORMAL LABELLED FATHER NAME
        # ========================================================
    
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
    
        # ========================================================
        # 4. NORMAL LABELLED DOB
        # ========================================================
    
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
    
        # ========================================================
        # 5. OCR FALLBACK
        #
        # Only fill fields that were NOT already extracted.
        # ========================================================
    
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

        return FieldExtractor._clean_value(
            value
        )

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

        udyam_number = (
            self._extract_udyam_number(text)
        )

        if udyam_number:
            result["udyam_number"] = (
                udyam_number
            )

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

        normalized_type = (
            self._normalize_udyam_type(
                enterprise_type
            )
        )

        if normalized_type:
            result["enterprise_type"] = (
                normalized_type
            )

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
            result["major_activity"] = (
                normalized_activity
            )

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
            result["social_category"] = (
                normalized_social
            )

        incorporation_value = (
            self._find_label_value(
                text,
                (
                    "date of incorporation",
                    "date of incorporation / registration of enterprise",
                    "date of registration of enterprise",
                ),
                (
                    "date of incorporation",
                    "date of incorporation / registration of enterprise",
                    "date of registration of enterprise",
                    "date of commencement",
                    "udyam registration date",
                    "enterprise address",
                    "official address of enterprise",
                ),
            )
        )

        incorporation_date = (
            self._normalize_date(
                incorporation_value
            )
        )

        if incorporation_date:
            result["date_of_incorporation"] = (
                incorporation_date
            )

        udyam_registration_value = (
            self._find_label_value(
                text,
                (
                    "udyam registration date",
                    "date of udyam registration",
                ),
                (
                    "udyam registration date",
                    "date of udyam registration",
                    "enterprise address",
                    "official address of enterprise",
                    "in case of graduation",
                ),
            )
        )

        udyam_registration_date = (
            self._normalize_date(
                udyam_registration_value
            )
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
                    self._clean_value(
                        combined
                    )
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