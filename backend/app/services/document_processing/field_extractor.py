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

    # =========================================================
    # IDENTIFIER PATTERNS
    # =========================================================

    GSTIN_PATTERN = re.compile(
        r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b",
        re.IGNORECASE,
    )

    PAN_PATTERN = re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b",
        re.IGNORECASE,
    )

    UDYAM_PATTERN = re.compile(
        r"\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b",
        re.IGNORECASE,
    )

    # =========================================================
    # HELPER
    # =========================================================

    @staticmethod
    def _extract_labeled_value(
        text: str,
        label_pattern: str,
    ) -> str | None:
        """
        Extract the value appearing after a labelled field.

        Example:

            Legal Name: ABC Industries Pvt Ltd

        returns:

            ABC Industries Pvt Ltd
        """

        match = re.search(
            rf"{label_pattern}\s*:\s*(.+)",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        value = match.group(1).strip()

        return value if value else None

    # =========================================================
    # GST
    # =========================================================

    def extract_gst_fields(self, text: str) -> dict:
        """
        Extract structured GST certificate fields.

        Supported fields:
        - gstin
        - legal_name
        - registration_date
        - registration_status
        - business_type
        - principal_address
        """

        if not text or not text.strip():
            return {}

        normalized_text = text.strip()

        fields = {}

        # -----------------------------------------------------
        # GSTIN
        # -----------------------------------------------------

        gstin_match = self.GSTIN_PATTERN.search(
            normalized_text
        )

        if gstin_match:
            fields["gstin"] = gstin_match.group(0).upper()

        # -----------------------------------------------------
        # Legal Name
        # -----------------------------------------------------

        legal_name = self._extract_labeled_value(
            normalized_text,
            r"Legal\s+Name",
        )

        if legal_name:
            fields["legal_name"] = legal_name

        # -----------------------------------------------------
        # Registration Date
        # -----------------------------------------------------

        registration_date = self._extract_labeled_value(
            normalized_text,
            r"Registration\s+Date",
        )

        if registration_date:
            fields["registration_date"] = registration_date

        # -----------------------------------------------------
        # Registration Status
        # -----------------------------------------------------

        registration_status = self._extract_labeled_value(
            normalized_text,
            r"Registration\s+Status",
        )

        if registration_status:
            fields["registration_status"] = (
                registration_status.upper()
            )

        # -----------------------------------------------------
        # Business Type
        # -----------------------------------------------------

        business_type = self._extract_labeled_value(
            normalized_text,
            r"Business\s+Type",
        )

        if business_type:
            fields["business_type"] = (
                business_type.upper()
            )

        # -----------------------------------------------------
        # Principal Address
        # -----------------------------------------------------

        principal_address = self._extract_labeled_value(
            normalized_text,
            r"Principal\s+Address",
        )

        if principal_address:
            fields["principal_address"] = principal_address

        return fields

    # =========================================================
    # PAN
    # =========================================================

    def extract_pan_fields(self, text: str) -> dict:
        """
        Extract structured PAN card fields.

        Supported fields:
        - pan
        - name
        - father_name
        - date_of_birth
        """

        if not text or not text.strip():
            return {}

        normalized_text = text.strip()

        fields = {}

        # -----------------------------------------------------
        # PAN
        # -----------------------------------------------------

        pan_match = self.PAN_PATTERN.search(
            normalized_text
        )

        if pan_match:
            fields["pan"] = pan_match.group(0).upper()

        # -----------------------------------------------------
        # Name
        # -----------------------------------------------------

        name = self._extract_labeled_value(
            normalized_text,
            r"Name",
        )

        if name:
            fields["name"] = name

        # -----------------------------------------------------
        # Father's Name
        # -----------------------------------------------------

        father_name = self._extract_labeled_value(
            normalized_text,
            r"Father(?:'s)?\s+Name",
        )

        if father_name:
            fields["father_name"] = father_name

        # -----------------------------------------------------
        # Date of Birth
        # -----------------------------------------------------

        date_of_birth = self._extract_labeled_value(
            normalized_text,
            r"Date\s+of\s+Birth",
        )

        if date_of_birth:
            fields["date_of_birth"] = date_of_birth

        return fields

    # =========================================================
    # UDYAM
    # =========================================================

    def extract_udyam_fields(self, text: str) -> dict:
        """
        Extract structured fields from a Udyam Registration Certificate.

        Supported fields:
        - udyam_number
        - enterprise_name
        - enterprise_type
        - major_activity
        - social_category
        - date_of_incorporation
        - udyam_registration_date
        - enterprise_address

        Handles OCR/native PDF text where the enterprise address
        may continue onto one or more following lines.
        """

        if not text or not text.strip():
            return {}

        normalized_text = text.strip()

        fields = {}

        # -----------------------------------------------------
        # Udyam Registration Number
        # -----------------------------------------------------

        udyam_match = self.UDYAM_PATTERN.search(
            normalized_text
        )

        if udyam_match:
            udyam_number = udyam_match.group(0).upper()
            fields["udyam_number"] = udyam_number

        # -----------------------------------------------------
        # Enterprise Name
        # -----------------------------------------------------

        enterprise_name = self._extract_labeled_value(
            normalized_text,
            r"Name\s+of\s+Enterprise",
        )

        if enterprise_name:
            fields["enterprise_name"] = enterprise_name

        # -----------------------------------------------------
        # Enterprise Type
        # -----------------------------------------------------

        enterprise_type = self._extract_labeled_value(
            normalized_text,
            r"Type\s+of\s+Enterprise",
        )

        if enterprise_type:
            fields["enterprise_type"] = (
                enterprise_type.upper()
            )

        # -----------------------------------------------------
        # Major Activity
        # -----------------------------------------------------

        major_activity = self._extract_labeled_value(
            normalized_text,
            r"Major\s+Activity",
        )

        if major_activity:
            fields["major_activity"] = (
                major_activity.upper()
            )

        # -----------------------------------------------------
        # Social Category
        # -----------------------------------------------------

        social_category = self._extract_labeled_value(
            normalized_text,
            r"Social\s+Category",
        )

        if social_category:
            fields["social_category"] = (
                social_category.upper()
            )

        # -----------------------------------------------------
        # Date of Incorporation
        # -----------------------------------------------------

        incorporation_date_match = re.search(
            r"Date\s+of\s+Incorporation\s*:\s*"
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            normalized_text,
            re.IGNORECASE,
        )

        if incorporation_date_match:
            fields["date_of_incorporation"] = (
                incorporation_date_match.group(1)
            )

        # -----------------------------------------------------
        # Udyam Registration Date
        # -----------------------------------------------------

        registration_date_match = re.search(
            r"Udyam\s+Registration\s+Date\s*:\s*"
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            normalized_text,
            re.IGNORECASE,
        )

        if registration_date_match:
            fields["udyam_registration_date"] = (
                registration_date_match.group(1)
            )

        # -----------------------------------------------------
        # Enterprise Address
        # -----------------------------------------------------
        #
        # Address may span multiple lines.
        #
        # Example:
        #
        # Enterprise Address: 123 Industrial Area,
        # Mumbai, Maharashtra
        #
        # We capture the first line plus all continuation
        # lines until another known field begins.
        # -----------------------------------------------------

        address_match = re.search(
            r"Enterprise\s+Address\s*:\s*"
            r"(.+?)(?="
            r"\n\s*(?:"
            r"UDYAM\s+REGISTRATION\s+NUMBER"
            r"|Name\s+of\s+Enterprise"
            r"|Type\s+of\s+Enterprise"
            r"|Major\s+Activity"
            r"|Social\s+Category"
            r"|Date\s+of\s+Incorporation"
            r"|Udyam\s+Registration\s+Date"
            r"|Enterprise\s+Address"
            r")"
            r"|\Z)",
            normalized_text,
            re.IGNORECASE | re.DOTALL,
        )

        if address_match:
            enterprise_address = address_match.group(1)

            # Convert newlines and repeated whitespace
            # into a single space.
            enterprise_address = re.sub(
                r"\s+",
                " ",
                enterprise_address,
            ).strip()

            if enterprise_address:
                fields["enterprise_address"] = (
                    enterprise_address
                )

        return fields