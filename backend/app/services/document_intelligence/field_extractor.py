import json
from typing import Type

from google import genai
from pydantic import BaseModel

from app.core.config import settings

from .schemas import (
    DocumentFieldExtractionResponse,
    DocumentType,
    GSTDocumentFields,
    IncomeTaxDocumentFields,
    PANDocumentFields,
    UdyamDocumentFields,
)


class DocumentFieldExtractor:
    """
    Extract structured fields from supported procurement documents
    using Gemini.

    This component performs extraction only.
    It does NOT perform compliance verification.
    """

    _SCHEMA_MAP: dict[DocumentType, Type[BaseModel]] = {
        DocumentType.GST_CERTIFICATE: GSTDocumentFields,
        DocumentType.UDYAM_CERTIFICATE: UdyamDocumentFields,
        DocumentType.PAN: PANDocumentFields,
        DocumentType.INCOME_TAX: IncomeTaxDocumentFields,
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = (
            api_key
            if api_key is not None
            else settings.GEMINI_API_KEY
        )

        self.model = (
            model
            if model is not None
            else settings.GEMINI_MODEL
        )

        # Client is intentionally created lazily inside extract().
        # This makes the class easier to test and avoids creating
        # a real Gemini client during object construction.
        self.client = None

    def extract(
        self,
        document_text: str,
        document_type: DocumentType,
    ) -> DocumentFieldExtractionResponse:

        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty.")

        field_schema = self._SCHEMA_MAP.get(document_type)

        if field_schema is None:
            raise ValueError(
                "Structured field extraction is not supported for "
                f"document type: {document_type.value}"
            )

        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        # Create the client here so tests can mock genai.Client
        # correctly and so no external client is created during
        # application startup.
        self.client = genai.Client(api_key=self.api_key)

        response_schema = self._build_response_schema(field_schema)

        response = self.client.interactions.create(
            model=self.model,
            system_instruction=self._build_system_instruction(
                document_type,
                field_schema,
            ),
            input=(
                "Extract structured fields from this document.\n\n"
                f"Document type: {document_type.value}\n\n"
                "Document text:\n"
                f"{document_text}"
            ),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": response_schema,
            },
        )

        # Current Gemini Interactions API
        # returns the generated text through output_text.
        output_text = response.output_text

        if not output_text:
            raise RuntimeError("Gemini returned an empty response.")

        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError("Gemini returned invalid JSON.") from exc

        fields = field_schema.model_validate(
            payload.get("fields", {})
        )

        confidence = payload.get("confidence")

        if confidence is None:
            raise ValueError(
                "Gemini response does not contain extraction confidence."
            )

        return DocumentFieldExtractionResponse(
            document_type=document_type,
            fields=fields,
            confidence=confidence,
        )

    @staticmethod
    def _build_response_schema(
        field_schema: Type[BaseModel],
    ) -> dict:
        return {
            "type": "object",
            "properties": {
                "fields": field_schema.model_json_schema(),
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
            "required": [
                "fields",
                "confidence",
            ],
        }

    @staticmethod
    def _build_system_instruction(
        document_type: DocumentType,
        field_schema: Type[BaseModel],
    ) -> str:
        return f"""
You are a structured document field extraction engine.

Document type:
{document_type.value}

Extract factual information ONLY from the supplied document text.

Rules:
- Do not invent or guess values.
- If a field is missing or unreadable, return null.
- Preserve document values as faithfully as possible.
- Extract only fields defined by the schema.
- Do not perform compliance verification.
- Do not determine eligibility or qualification.
- Do not compare against tender requirements.
- Do not verify against external portals.
- Return valid JSON only.
- Include an overall extraction confidence from 0 to 1.

Expected fields:
{field_schema.model_json_schema()}
""".strip()


document_field_extractor = DocumentFieldExtractor()