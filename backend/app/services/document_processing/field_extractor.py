"""
Field extraction for BidSure AI Document Intelligence.

This module extracts structured fields from text that has already
been extracted by DocumentLoader.

It does not perform:
- PDF extraction
- OCR
- document classification
- external verification
"""

import re


class FieldExtractor:
    """
    Extract structured fields from classified document text.
    """

    GSTIN_PATTERN = re.compile(
        r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b",
        re.IGNORECASE,
    )

    def extract_gst_fields(self, text: str) -> dict:
        """
        Extract GST certificate fields.

        Currently supported:
        - gstin
        - legal_name
        - registration_status
        """

        if not text or not text.strip():
            return {}

        normalized_text = text.strip()

        fields = {}

        # ---------------------------------------------------------
        # GSTIN
        # ---------------------------------------------------------

        gstin_match = self.GSTIN_PATTERN.search(
            normalized_text
        )

        if gstin_match:
            fields["gstin"] = gstin_match.group(0).upper()

        # ---------------------------------------------------------
        # Legal Name
        # ---------------------------------------------------------

        legal_name_match = re.search(
            r"Legal\s+Name\s*:\s*(.+)",
            normalized_text,
            re.IGNORECASE,
        )

        if legal_name_match:
            legal_name = legal_name_match.group(1).strip()

            if legal_name:
                fields["legal_name"] = legal_name

        # ---------------------------------------------------------
        # Registration Status
        # ---------------------------------------------------------

        status_match = re.search(
            r"Registration\s+Status\s*:\s*([A-Za-z]+)",
            normalized_text,
            re.IGNORECASE,
        )

        if status_match:
            fields["registration_status"] = (
                status_match.group(1).strip().upper()
            )

        return fields
