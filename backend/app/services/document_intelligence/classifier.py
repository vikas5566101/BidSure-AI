from google import genai

from app.core.config import settings
from app.services.document_intelligence.schemas import (
    DocumentClassificationResponse,
)


class DocumentClassifier:
    """
    Uses Gemini to classify bidder documents into one of
    the supported document types.

    This component performs classification only.
    It does not extract document fields or verify
    information against external government sources.
    """

    SYSTEM_INSTRUCTION = """
You are the document classification component
of BidSure AI.

Your task is to classify a bidder document into exactly
one of the supported document types.

Supported document types:

1. GST_CERTIFICATE
2. UDYAM_CERTIFICATE
3. PAN
4. INCOME_TAX
5. UNKNOWN

Rules:

1. Classify the document only from the supplied document
   content.

2. Do not extract or invent document field values.

3. GST_CERTIFICATE refers to a Goods and Services Tax
   registration certificate or equivalent GST registration
   document.

4. UDYAM_CERTIFICATE refers to an Udyam Registration /
   MSME registration certificate.

5. PAN refers to a Permanent Account Number document/card
   issued by the Income Tax Department.

6. INCOME_TAX refers to an Income Tax Return, ITR
   acknowledgement, or similar income-tax filing document.

7. If the document does not clearly belong to one of the
   supported types, classify it as UNKNOWN.

8. Confidence must be a value between 0.0 and 1.0.

9. Do not classify a document based only on its filename.

10. This component performs classification only.
    It does not make any compliance or qualification
    decision.
""".strip()

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

        # Gemini client is created lazily.
        # This allows tests to inject/mock the client
        # without making real API calls.
        self.client = None

    def classify(
        self,
        document_text: str,
    ) -> DocumentClassificationResponse:
        """
        Classify the supplied document text.

        Args:
            document_text: Text extracted from the bidder document.

        Returns:
            DocumentClassificationResponse containing:
            - document_type
            - confidence

        Raises:
            ValueError: If document text is empty.
            RuntimeError: If Gemini API key is not configured.
            RuntimeError: If Gemini returns an empty response.
            pydantic.ValidationError: If Gemini returns invalid
                structured output.
        """

        # Validate document content first.
        if not document_text or not document_text.strip():
            raise ValueError(
                "Document text cannot be empty."
            )

        # Validate API configuration before creating the client.
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        # Create the Gemini client only when needed.
        #
        # IMPORTANT:
        # Do not recreate the client if one has already been
        # injected by tests or created during an earlier call.
        if self.client is None:
            self.client = genai.Client(
                api_key=self.api_key,
            )

        response = self.client.interactions.create(
            model=self.model,
            system_instruction=self.SYSTEM_INSTRUCTION,
            input=(
                "Classify the following document.\n\n"
                "Document text:\n"
                f"{document_text}"
            ),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": (
                    DocumentClassificationResponse
                    .model_json_schema()
                ),
            },
        )

        # Current Gemini Interactions API response format.
        output_text = response.output_text

        if not output_text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # Validate Gemini's structured JSON response using
        # the Pydantic response schema.
        return DocumentClassificationResponse.model_validate_json(
            output_text
        )


# Shared classifier instance used by the application.
document_classifier = DocumentClassifier()