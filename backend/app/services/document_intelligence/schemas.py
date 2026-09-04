from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentType(str, Enum):
    """
    Supported bidder document types for the initial
    Document Intelligence implementation.
    """

    GST_CERTIFICATE = "GST_CERTIFICATE"
    UDYAM_CERTIFICATE = "UDYAM_CERTIFICATE"
    PAN = "PAN"
    INCOME_TAX = "INCOME_TAX"
    UNKNOWN = "UNKNOWN"


class DocumentClassificationResponse(BaseModel):
    """
    Structured response produced by the document
    classification layer.
    """

    document_type: DocumentType

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class GSTDocumentFields(BaseModel):
    """
    Fields extracted from a GST registration certificate.

    These fields represent document facts only.
    Compliance is evaluated separately.
    """

    model_config = ConfigDict(extra="forbid")

    gstin: str | None = None
    legal_name: str | None = None
    trade_name: str | None = None
    registration_date: str | None = None
    status: str | None = None


class UdyamDocumentFields(BaseModel):
    """
    Fields extracted from an Udyam/MSME certificate.

    These fields represent document facts only.
    Compliance is evaluated separately.
    """

    model_config = ConfigDict(extra="forbid")

    udyam_number: str | None = None
    enterprise_name: str | None = None
    organisation_type: str | None = None
    major_activity: str | None = None
    registration_date: str | None = None


class PANDocumentFields(BaseModel):
    """
    Fields extracted from a PAN document.

    These fields represent document facts only.
    Compliance is evaluated separately.
    """

    model_config = ConfigDict(extra="forbid")

    pan_number: str | None = None
    name: str | None = None
    date_of_birth_or_incorporation: str | None = None


class IncomeTaxDocumentFields(BaseModel):
    """
    Fields extracted from an Income Tax document/ITR acknowledgement.

    These fields represent document facts only.
    Compliance is evaluated separately.
    """

    model_config = ConfigDict(extra="forbid")

    pan_number: str | None = None
    assessment_year: str | None = None
    acknowledgement_number: str | None = None
    filing_date: str | None = None
    gross_total_income: str | None = None
    total_income: str | None = None


class DocumentFieldExtractionResponse(BaseModel):
    """
    Common response returned by the structured field extraction layer.

    The extractor identifies the document type and returns the appropriate
    typed field object. It does not perform compliance verification.
    """

    document_type: DocumentType

    fields: (
        GSTDocumentFields
        | UdyamDocumentFields
        | PANDocumentFields
        | IncomeTaxDocumentFields
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_document_type_matches_fields(self):
        expected_fields = {
            DocumentType.GST_CERTIFICATE: GSTDocumentFields,
            DocumentType.UDYAM_CERTIFICATE: UdyamDocumentFields,
            DocumentType.PAN: PANDocumentFields,
            DocumentType.INCOME_TAX: IncomeTaxDocumentFields,
        }

        expected_type = expected_fields.get(self.document_type)

        if expected_type is None:
            raise ValueError(
                "Structured field extraction is not supported for "
                f"document type: {self.document_type}"
            )

        if not isinstance(self.fields, expected_type):
            raise ValueError(
                f"Fields type {type(self.fields).__name__} does not match "
                f"document type {self.document_type.value}"
            )

        return self


class ExtractedPage(BaseModel):
    """
    Text extracted from a single document page.
    """

    page_number: int = Field(ge=1)
    text: str


class PDFTextExtractionResult(BaseModel):
    """
    Common result returned by PDF text extraction and OCR extraction.
    """

    pages: list[ExtractedPage]
    total_pages: int = Field(ge=0)
    total_characters: int = Field(ge=0)

class TextExtractionMethod(str, Enum):
    """
    Method used to obtain document text.
    """

    NATIVE_PDF = "NATIVE_PDF"
    OCR = "OCR"


class DocumentIntelligenceResult(BaseModel):
    """
    Complete result produced by the Document Intelligence pipeline.

    This model combines:
    - text extraction
    - document classification
    - structured field extraction

    It does not contain a compliance decision.
    """

    document_type: DocumentType

    classification_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    extraction_method: TextExtractionMethod

    extracted_text: str

    total_pages: int = Field(
        ge=0,
    )

    total_characters: int = Field(
        ge=0,
    )

    fields: (
        GSTDocumentFields
        | UdyamDocumentFields
        | PANDocumentFields
        | IncomeTaxDocumentFields
    )

    extraction_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_document_type_matches_fields(self):
        expected_fields = {
            DocumentType.GST_CERTIFICATE: GSTDocumentFields,
            DocumentType.UDYAM_CERTIFICATE: UdyamDocumentFields,
            DocumentType.PAN: PANDocumentFields,
            DocumentType.INCOME_TAX: IncomeTaxDocumentFields,
        }

        expected_type = expected_fields.get(self.document_type)

        if expected_type is None:
            raise ValueError(
                "Document intelligence does not support structured "
                f"extraction for document type: {self.document_type}"
            )

        if not isinstance(self.fields, expected_type):
            raise ValueError(
                f"Fields type {type(self.fields).__name__} does not match "
                f"document type {self.document_type.value}"
            )

        return self