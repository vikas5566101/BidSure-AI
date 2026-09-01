"""
Local extraction-quality validation for BidSure AI.

IMPORTANT:

This verifier belongs to Team 1.

It validates whether extracted OCR fields are structurally
and semantically reasonable.

It does NOT:
- contact government portals
- verify GST registration with the government
- verify PAN with the Income Tax Department
- verify Udyam with the MSME portal
- prove document authenticity

Team 2 is responsible for external/government verification.

This module answers:

    "Does this extracted value look reliable?"

not:

    "Is this registration officially valid?"
"""

import re


class DocumentVerifier:
    """
    Validate extracted document fields locally.

    The verifier deliberately does NOT modify extracted values.

    It only reports:
        - verified_fields
        - fields_requiring_review
        - errors
        - verification_status

    The existing 'verification' naming is retained for backward
    compatibility with the current Team 1 contract.
    """

    # =========================================================
    # FIELD PATTERNS
    # =========================================================

    GSTIN_PATTERN = re.compile(
        r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]$",
        re.IGNORECASE,
    )

    PAN_PATTERN = re.compile(
        r"^[A-Z]{5}\d{4}[A-Z]$",
        re.IGNORECASE,
    )

    UDYAM_PATTERN = re.compile(
        r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$",
        re.IGNORECASE,
    )

    DATE_PATTERN = re.compile(
        r"^\d{2}/\d{2}/\d{4}$"
    )

    PIN_PATTERN = re.compile(
        r"^\d{6}$"
    )

    # =========================================================
    # EXPECTED GST VALUES
    # =========================================================

    GST_REGISTRATION_TYPES = {
        "REGULAR",
        "COMPOSITION",
        "CASUAL TAXABLE PERSON",
        "NON-RESIDENT TAXABLE PERSON",
        "SEZ UNIT",
        "SEZ DEVELOPER",
        "TDS DEDUCTOR",
        "TCS COLLECTOR",
        "OIDAR",
        "UNREGISTERED",
        "INPUT SERVICE DISTRIBUTOR",
    }

    GST_REGISTRATION_STATUSES = {
        "ACTIVE",
        "REGULAR",
        "CANCELLED",
        "SUSPENDED",
        "INACTIVE",
    }

    # =========================================================
    # EXPECTED UDYAM VALUES
    # =========================================================

    UDYAM_ENTERPRISE_TYPES = {
        "MICRO",
        "SMALL",
        "MEDIUM",
    }

    UDYAM_SOCIAL_CATEGORIES = {
        "GENERAL",
        "SC",
        "ST",
        "OBC",
    }

    UDYAM_MAJOR_ACTIVITIES = {
        "MANUFACTURING",
        "SERVICES",
        "TRADING",
    }

    # =========================================================
    # GENERIC HELPERS
    # =========================================================

    @staticmethod
    def _clean(
        value: object,
    ) -> str:
        """
        Convert a value to a normalized string.
        """

        if value is None:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value),
        ).strip()

    @classmethod
    def _is_meaningful_text(
        cls,
        value: object,
        minimum_length: int = 2,
    ) -> bool:
        """
        Determine whether a text field contains meaningful
        human-readable content.
        """

        text = cls._clean(
            value
        )

        if len(text) < minimum_length:
            return False

        # -----------------------------------------------------
        # Reject strings consisting mostly of symbols.
        # -----------------------------------------------------

        alphanumeric_count = sum(
            character.isalnum()
            for character in text
        )

        if alphanumeric_count < minimum_length:
            return False

        # -----------------------------------------------------
        # Reject obvious OCR garbage.
        # -----------------------------------------------------

        garbage_patterns = [
            r"^\*+$",
            r"^[\[\]\|\-_:=/\\]+$",
            r"^\*?\s*\[[^\]]*\]\s*$",
            r"^[A-Z]{1,2}$",
        ]

        for pattern in garbage_patterns:

            if re.fullmatch(
                pattern,
                text,
                re.IGNORECASE,
            ):
                return False

        return True

    @classmethod
    def _looks_like_ocr_garbage(
        cls,
        value: object,
    ) -> bool:
        """
        Detect common OCR garbage patterns.

        This does not attempt to correct OCR.

        It only identifies suspicious output.
        """

        text = cls._clean(
            value
        )

        if not text:
            return True

        # -----------------------------------------------------
        # Excessive punctuation.
        # -----------------------------------------------------

        punctuation_count = sum(
            not character.isalnum()
            and not character.isspace()
            for character in text
        )

        if (
            len(text) > 0
            and punctuation_count / len(text) > 0.35
        ):
            return True

        # -----------------------------------------------------
        # Repeated unusual symbols.
        # -----------------------------------------------------

        if re.search(
            r"[\[\]\|]{2,}",
            text,
        ):
            return True

        # -----------------------------------------------------
        # OCR-like corruption.
        # -----------------------------------------------------

        suspicious_patterns = [
            r"\b[A-Z]\d[A-Z]\d[A-Z]\b",
            r"\*\s*\[",
            r"\|\s*[A-Z]{1,2}\b",
        ]

        for pattern in suspicious_patterns:

            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                return True

        return False

    @classmethod
    def _validate_date(
        cls,
        value: object,
    ) -> bool:
        """
        Validate DD/MM/YYYY format.
        """

        text = cls._clean(
            value
        )

        if not cls.DATE_PATTERN.fullmatch(
            text
        ):
            return False

        day, month, year = (
            text.split("/")
        )

        day = int(day)
        month = int(month)
        year = int(year)

        if not 1 <= month <= 12:
            return False

        if not 1 <= day <= 31:
            return False

        if not 1900 <= year <= 2100:
            return False

        return True

    # =========================================================
    # GSTIN CHECKSUM
    # =========================================================

    @staticmethod
    def _gstin_checksum(
        gstin: str,
    ) -> str:
        """
        Calculate the GSTIN checksum using the standard
        base-36 algorithm.

        GSTIN contains 15 characters.
        The checksum is calculated from the first 14.

        Multipliers alternate:
            2, 1, 2, 1, ...

        The checksum is the base-36 complement of the
        accumulated value.
        """

        characters = (
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        )

        gstin = str(gstin).upper()

        if len(gstin) != 15:
            raise ValueError(
                "GSTIN must contain exactly 15 characters"
            )

        total = 0

        for index, character in enumerate(gstin[:14]):

            if character not in characters:
                raise ValueError(
                    f"Invalid GSTIN character: {character}"
                )

            code = characters.index(
                character
            )

            # GSTIN checksum uses alternating
            # multipliers 2, 1, 2, 1, ...
            factor = (
                2
                if index % 2 == 0
                else 1
            )

            product = code * factor

            total += (
                product // 36
                + product % 36
            )

        check_value = (
            36 - (total % 36)
        ) % 36

        return characters[
            check_value
        ]

    @classmethod
    def _validate_gstin(
        cls,
        value: object,
    ) -> bool:
        """
        Validate GSTIN structure and checksum.
        """

        gstin = cls._clean(
            value
        ).upper()

        if not cls.GSTIN_PATTERN.fullmatch(
            gstin
        ):
            return False

        try:

            expected = (
                cls._gstin_checksum(
                    gstin
                )
            )

        except (
            ValueError,
            IndexError,
        ):

            return False

        return (
            gstin[-1]
            == expected
        )

    # =========================================================
    # GST VALIDATION
    # =========================================================

    @classmethod
    def _verify_gst(
        cls,
        data: dict,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Validate GST fields locally.

        Returns:

            verified_fields
            fields_requiring_review
            errors
        """

        verified_fields = []
        review_fields = []
        errors = []

        # -----------------------------------------------------
        # GSTIN
        # -----------------------------------------------------

        if "gstin" in data:

            if cls._validate_gstin(
                data["gstin"]
            ):

                verified_fields.append(
                    "gstin"
                )

            else:

                review_fields.append(
                    "gstin"
                )

        # -----------------------------------------------------
        # Legal name
        # -----------------------------------------------------

        if "legal_name" in data:

            value = data[
                "legal_name"
            ]

            if (
                cls._is_meaningful_text(
                    value
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "legal_name"
                )

            else:

                review_fields.append(
                    "legal_name"
                )

        # -----------------------------------------------------
        # Trade name
        # -----------------------------------------------------

        if "trade_name" in data:

            value = data[
                "trade_name"
            ]

            if (
                cls._is_meaningful_text(
                    value
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "trade_name"
                )

            else:

                review_fields.append(
                    "trade_name"
                )

        # -----------------------------------------------------
        # Constitution
        # -----------------------------------------------------

        if "constitution" in data:

            value = data[
                "constitution"
            ]

            if (
                cls._is_meaningful_text(
                    value
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "constitution"
                )

            else:

                review_fields.append(
                    "constitution"
                )

        # -----------------------------------------------------
        # Business type
        # -----------------------------------------------------

        if "business_type" in data:

            value = data[
                "business_type"
            ]

            if (
                cls._is_meaningful_text(
                    value
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "business_type"
                )

            else:

                review_fields.append(
                    "business_type"
                )

        # -----------------------------------------------------
        # Registration date
        # -----------------------------------------------------

        if "registration_date" in data:

            if cls._validate_date(
                data["registration_date"]
            ):

                verified_fields.append(
                    "registration_date"
                )

            else:

                review_fields.append(
                    "registration_date"
                )

        # -----------------------------------------------------
        # Registration type
        # -----------------------------------------------------

        if "registration_type" in data:

            value = cls._clean(
                data["registration_type"]
            ).upper()

            if value in (
                cls.GST_REGISTRATION_TYPES
            ):

                verified_fields.append(
                    "registration_type"
                )

            else:

                review_fields.append(
                    "registration_type"
                )

        # -----------------------------------------------------
        # Registration status
        # -----------------------------------------------------

        if "registration_status" in data:

            value = cls._clean(
                data["registration_status"]
            ).upper()

            if value in (
                cls.GST_REGISTRATION_STATUSES
            ):

                verified_fields.append(
                    "registration_status"
                )

            else:

                review_fields.append(
                    "registration_status"
                )

        # -----------------------------------------------------
        # Principal address
        # -----------------------------------------------------

        if "principal_address" in data:

            value = data[
                "principal_address"
            ]

            if (
                cls._is_meaningful_text(
                    value,
                    minimum_length=10,
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "principal_address"
                )

            else:

                review_fields.append(
                    "principal_address"
                )

        # -----------------------------------------------------
        # GST address details
        # -----------------------------------------------------

        address_details = data.get(
            "address_details"
        )

        if isinstance(
            address_details,
            dict,
        ):

            for field_name, value in (
                address_details.items()
            ):

                field_path = (
                    "address_details."
                    + field_name
                )

                if field_name == "pin_code":

                    if cls.PIN_PATTERN.fullmatch(
                        cls._clean(value)
                    ):

                        verified_fields.append(
                            field_path
                        )

                    else:

                        review_fields.append(
                            field_path
                        )

                    continue

                if (
                    cls._is_meaningful_text(
                        value,
                        minimum_length=2,
                    )
                    and not cls._looks_like_ocr_garbage(
                        value
                    )
                ):

                    verified_fields.append(
                        field_path
                    )

                else:

                    review_fields.append(
                        field_path
                    )

        return (
            verified_fields,
            review_fields,
            errors,
        )

    # =========================================================
    # PAN VALIDATION
    # =========================================================

    @classmethod
    def _verify_pan(
        cls,
        data: dict,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Validate PAN fields locally.
        """

        verified_fields = []
        review_fields = []
        errors = []

        # -----------------------------------------------------
        # PAN
        # -----------------------------------------------------

        if "pan" in data:

            pan = cls._clean(
                data["pan"]
            ).upper()

            if cls.PAN_PATTERN.fullmatch(
                pan
            ):

                verified_fields.append(
                    "pan"
                )

            else:

                review_fields.append(
                    "pan"
                )

        # -----------------------------------------------------
        # Name
        # -----------------------------------------------------

        if "name" in data:

            value = data[
                "name"
            ]

            if (
                cls._is_meaningful_text(
                    value
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "name"
                )

            else:

                review_fields.append(
                    "name"
                )

        # -----------------------------------------------------
        # Father's name
        # -----------------------------------------------------

        if "father_name" in data:

            value = data[
                "father_name"
            ]

            if (
                cls._is_meaningful_text(
                    value
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "father_name"
                )

            else:

                review_fields.append(
                    "father_name"
                )

        # -----------------------------------------------------
        # Date of birth
        # -----------------------------------------------------

        if "date_of_birth" in data:

            if cls._validate_date(
                data["date_of_birth"]
            ):

                verified_fields.append(
                    "date_of_birth"
                )

            else:

                review_fields.append(
                    "date_of_birth"
                )

        return (
            verified_fields,
            review_fields,
            errors,
        )

    # =========================================================
    # UDYAM VALIDATION
    # =========================================================

    @classmethod
    def _verify_udyam(
        cls,
        data: dict,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Validate Udyam fields locally.
        """

        verified_fields = []
        review_fields = []
        errors = []

        # -----------------------------------------------------
        # Udyam number
        # -----------------------------------------------------

        if "udyam_number" in data:

            value = cls._clean(
                data["udyam_number"]
            ).upper()

            if cls.UDYAM_PATTERN.fullmatch(
                value
            ):

                verified_fields.append(
                    "udyam_number"
                )

            else:

                review_fields.append(
                    "udyam_number"
                )

        # -----------------------------------------------------
        # Enterprise name
        # -----------------------------------------------------

        if "enterprise_name" in data:

            value = data[
                "enterprise_name"
            ]

            if (
                cls._is_meaningful_text(
                    value
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "enterprise_name"
                )

            else:

                review_fields.append(
                    "enterprise_name"
                )

        # -----------------------------------------------------
        # Enterprise type
        # -----------------------------------------------------

        if "enterprise_type" in data:

            value = cls._clean(
                data["enterprise_type"]
            ).upper()

            if value in (
                cls.UDYAM_ENTERPRISE_TYPES
            ):

                verified_fields.append(
                    "enterprise_type"
                )

            else:

                review_fields.append(
                    "enterprise_type"
                )

        # -----------------------------------------------------
        # Major activity
        # -----------------------------------------------------

        if "major_activity" in data:

            value = cls._clean(
                data["major_activity"]
            ).upper()

            if value in (
                cls.UDYAM_MAJOR_ACTIVITIES
            ):

                verified_fields.append(
                    "major_activity"
                )

            else:

                review_fields.append(
                    "major_activity"
                )

        # -----------------------------------------------------
        # Social category
        # -----------------------------------------------------

        if "social_category" in data:

            value = cls._clean(
                data["social_category"]
            ).upper()

            if value in (
                cls.UDYAM_SOCIAL_CATEGORIES
            ):

                verified_fields.append(
                    "social_category"
                )

            else:

                review_fields.append(
                    "social_category"
                )

        # -----------------------------------------------------
        # Incorporation date
        # -----------------------------------------------------

        if "date_of_incorporation" in data:

            if cls._validate_date(
                data["date_of_incorporation"]
            ):

                verified_fields.append(
                    "date_of_incorporation"
                )

            else:

                review_fields.append(
                    "date_of_incorporation"
                )

        # -----------------------------------------------------
        # Udyam registration date
        # -----------------------------------------------------

        if "udyam_registration_date" in data:

            if cls._validate_date(
                data["udyam_registration_date"]
            ):

                verified_fields.append(
                    "udyam_registration_date"
                )

            else:

                review_fields.append(
                    "udyam_registration_date"
                )

        # -----------------------------------------------------
        # Enterprise address
        # -----------------------------------------------------

        if "enterprise_address" in data:

            value = data[
                "enterprise_address"
            ]

            if (
                cls._is_meaningful_text(
                    value,
                    minimum_length=10,
                )
                and not cls._looks_like_ocr_garbage(
                    value
                )
            ):

                verified_fields.append(
                    "enterprise_address"
                )

            else:

                review_fields.append(
                    "enterprise_address"
                )

        return (
            verified_fields,
            review_fields,
            errors,
        )

    # =========================================================
    # PUBLIC API
    # =========================================================

    def verify(
        self,
        document_type: str,
        extracted_data: dict,
    ) -> dict:
        """
        Validate extracted fields locally.

        IMPORTANT:

        The returned 'verification_status' describes LOCAL
        extraction validation only.

        It does NOT mean that the government registration
        has been externally verified.
        """

        if not isinstance(
            extracted_data,
            dict,
        ):

            extracted_data = {}

        document_type = (
            document_type
            or "UNKNOWN"
        ).upper()

        # -----------------------------------------------------
        # Empty extraction
        # -----------------------------------------------------

        if not extracted_data:

            return {
                "verification_status": (
                    "REVIEW_REQUIRED"
                ),
                "verified_fields": [],
                "fields_requiring_review": [],
                "errors": [
                    "No fields were extracted"
                ],
                "external_verification": False,
            }

        # -----------------------------------------------------
        # Select document-specific validator.
        # -----------------------------------------------------

        if document_type == "GST_CERTIFICATE":

            (
                verified_fields,
                review_fields,
                errors,
            ) = self._verify_gst(
                extracted_data
            )

        elif document_type == "PAN_CARD":

            (
                verified_fields,
                review_fields,
                errors,
            ) = self._verify_pan(
                extracted_data
            )

        elif document_type == "UDYAM_CERTIFICATE":

            (
                verified_fields,
                review_fields,
                errors,
            ) = self._verify_udyam(
                extracted_data
            )

        else:

            verified_fields = []
            review_fields = list(
                extracted_data.keys()
            )
            errors = [
                "Unsupported document type for local validation"
            ]

        # -----------------------------------------------------
        # Remove duplicate fields.
        # -----------------------------------------------------

        verified_fields = list(
            dict.fromkeys(
                verified_fields
            )
        )

        review_fields = list(
            dict.fromkeys(
                review_fields
            )
        )

        # -----------------------------------------------------
        # Determine local validation status.
        # -----------------------------------------------------

        if errors:

            status = "REVIEW_REQUIRED"

        elif review_fields:

            status = "REVIEW_REQUIRED"

        elif verified_fields:

            status = "VERIFIED"

        else:

            status = "REVIEW_REQUIRED"

        # -----------------------------------------------------
        # Return result.
        # -----------------------------------------------------

        return {
            "verification_status": status,
            "verified_fields": verified_fields,
            "fields_requiring_review": review_fields,
            "errors": errors,
            "external_verification": False,
        }