"""
Document classification service for BidSure AI.

Phase 1:
- Identify document type
- Calculate a transparent weighted confidence score
- Preserve weighted evidence for explainability
- Handle controlled OCR variations
- Detect ambiguous classifications
- Flag low-confidence classifications for review

This is intentionally rule-based for the initial prototype.
The classifier interface can later be backed by an ML/LLM model.
"""

import re
from typing import Dict, List, Tuple


class DocumentClassifier:
    """Classifies extracted document text into known document types."""

    # Each pattern has a weight representing how strongly
    # that pattern indicates the corresponding document type.
    DOCUMENT_PATTERNS: Dict[str, Dict[str, float]] = {
        "GST_CERTIFICATE": {
            "goods and services tax": 0.30,
            "gstin": 0.40,
            "gst registration": 0.20,
            "certificate of registration": 0.05,
            "taxpayer": 0.05,
        },
        "PAN_CARD": {
            "permanent account number": 0.50,
            "income tax department": 0.30,
            "pan": 0.20,
        },
        "COMPANY_REGISTRATION": {
            "certificate of incorporation": 0.30,
            "registrar of companies": 0.25,
            "company registration": 0.20,
            "corporate identity number": 0.20,
            "cin": 0.05,
        },
        "FINANCIAL_STATEMENT": {
            "balance sheet": 0.25,
            "profit and loss": 0.20,
            "profit & loss": 0.20,
            "assets and liabilities": 0.15,
            "audited financial statement": 0.10,
            "financial statements": 0.10,
        },
        "BANK_CERTIFICATE": {
            "bank certificate": 0.30,
            "bank account": 0.25,
            "account number": 0.20,
            "banker": 0.15,
            "branch manager": 0.10,
        },
        "EXPERIENCE_CERTIFICATE": {
            "experience certificate": 0.30,
            "work order": 0.20,
            "successfully completed": 0.20,
            "similar work": 0.15,
            "completion certificate": 0.15,
        },
        "TECHNICAL_CERTIFICATE": {
            "technical certificate": 0.30,
            "technical specification": 0.25,
            "compliance certificate": 0.25,
            "technical qualification": 0.20,
        },
        "AFFIDAVIT": {
            "affidavit": 0.40,
            "sworn before": 0.25,
            "deponent": 0.20,
            "notary": 0.15,
        },
        "UNDERTAKING": {
            "undertaking": 0.40,
            "hereby undertake": 0.25,
            "we undertake": 0.20,
            "declaration and undertaking": 0.15,
        },
        "TENDER_DOCUMENT": {
            "tender document": 0.25,
            "notice inviting tender": 0.20,
            "nit": 0.10,
            "bid submission": 0.20,
            "tender id": 0.10,
            "bid document": 0.15,
        },
    }

    # Controlled OCR aliases.
    OCR_ALIASES: Dict[str, List[str]] = {
        "gstin": [
            "gst1n",
            "gst in",
            "gstln",
        ],
        "pan": [
            "p an",
        ],
        "cin": [
            "c in",
        ],
    }

    # Confidence thresholds.
    CONFIDENCE_THRESHOLDS = {
        "HIGH": 0.90,
        "MEDIUM": 0.70,
    }

    # If the difference between the top two evidence scores
    # is smaller than this value, classification is considered
    # ambiguous.
    AMBIGUITY_THRESHOLD = 0.10

    def classify(self, text: str) -> dict:
        """
        Classify a document based on extracted text.

        Args:
            text: OCR/text-extracted document content.

        Returns:
            Dictionary containing:
            - document type
            - evidence score
            - confidence
            - confidence level
            - matched patterns
            - evidence
            - ambiguity information
            - review flag
        """

        # Empty input cannot be classified.
        if not text or not text.strip():
            return self._unknown_result()

        # Normalize OCR/extracted text.
        normalized_text = self._normalize(text)

        # Store:
        # document_type -> (score, matched_patterns, evidence)
        scores: Dict[
            str,
            Tuple[float, List[str], List[dict]]
        ] = {}

        # Calculate weighted evidence for every document type.
        for document_type, patterns in self.DOCUMENT_PATTERNS.items():

            matched_patterns = []
            evidence = []

            for pattern, weight in patterns.items():

                matched_variant = self._find_matching_variant(
                    pattern,
                    normalized_text,
                )

                if matched_variant is not None:

                    matched_patterns.append(pattern)

                    evidence.append(
                        {
                            "pattern": pattern,
                            "weight": weight,
                            "matched_as": matched_variant,
                        }
                    )

            # Only keep document types with at least
            # one matching piece of evidence.
            if matched_patterns:

                weighted_score = sum(
                    item["weight"]
                    for item in evidence
                )

                scores[document_type] = (
                    min(weighted_score, 1.0),
                    matched_patterns,
                    evidence,
                )

        # No evidence for any known document type.
        if not scores:
            return self._unknown_result()

        # ---------------------------------------------------------
        # Rank document types by evidence score.
        # ---------------------------------------------------------
        ranked_scores = sorted(
            scores.items(),
            key=lambda item: item[1][0],
            reverse=True,
        )

        # ---------------------------------------------------------
        # Best classification.
        # ---------------------------------------------------------
        document_type, (
            evidence_score,
            matched_patterns,
            evidence,
        ) = ranked_scores[0]

        # ---------------------------------------------------------
        # Second-best classification / ambiguity detection.
        # ---------------------------------------------------------

        ambiguity = False
        second_best_document_type = None
        second_best_score = None
        score_difference = None

        if len(ranked_scores) > 1:

            second_best_document_type, (
                raw_second_best_score,
                _,
                _,
            ) = ranked_scores[1]

            second_best_score = raw_second_best_score

            # Difference between the strongest and
            # second-strongest classification.
            score_difference = round(
                evidence_score - second_best_score,
                2,
            )

            # A small difference means the classifier
            # cannot confidently distinguish between
            # the two document types.
            ambiguity = (
                score_difference < self.AMBIGUITY_THRESHOLD
            )

        # ---------------------------------------------------------
        # Confidence calibration.
        # ---------------------------------------------------------

        confidence = self._calibrate_confidence(
            evidence_score
        )

        confidence_level = self._confidence_level(
            confidence
        )

        # ---------------------------------------------------------
        # Human review decision.
        # ---------------------------------------------------------

        # Review is required when:
        # 1. confidence is below MEDIUM, OR
        # 2. classification is ambiguous.
        needs_review = (
            confidence < self.CONFIDENCE_THRESHOLDS["MEDIUM"]
            or ambiguity
        )

        # ---------------------------------------------------------
        # Final classification result.
        # ---------------------------------------------------------

        return {
            "document_type": document_type,
            "evidence_score": round(evidence_score, 2),
            "confidence": confidence,
            "confidence_level": confidence_level,
            "classification_method": "weighted_keyword_rule",
            "matched_patterns": matched_patterns,
            "evidence": evidence,

            # Ambiguity information.
            "ambiguity": ambiguity,
            "second_best_document_type": second_best_document_type,
            "second_best_score": (
                round(second_best_score, 2)
                if second_best_score is not None
                else None
            ),
            "score_difference": score_difference,

            # Human review flag.
            "needs_review": needs_review,
        }

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize extracted/OCR text for matching."""

        return " ".join(
            text.lower().split()
        )

    def _find_matching_variant(
        self,
        pattern: str,
        text: str,
    ) -> str | None:
        """
        Find the canonical pattern or one of its approved OCR
        aliases in the normalized text.

        Returns:
            The text variant that matched, or None.
        """

        # First try the canonical pattern.
        if self._pattern_matches(pattern, text):
            return pattern

        # Then try explicitly approved OCR variants.
        for alias in self.OCR_ALIASES.get(pattern, []):

            if self._pattern_matches(alias, text):
                return alias

        return None

    @staticmethod
    def _pattern_matches(
        pattern: str,
        text: str,
    ) -> bool:
        """
        Check whether a classification pattern appears as a
        complete word or phrase.

        Single-word patterns use word boundaries.
        Multi-word patterns allow flexible whitespace.
        """

        pattern = pattern.strip().lower()

        escaped_pattern = re.escape(pattern)

        # Multi-word pattern.
        if " " in pattern:

            escaped_pattern = escaped_pattern.replace(
                r"\ ",
                r"\s+",
            )

            regex = rf"\b{escaped_pattern}\b"

            return re.search(
                regex,
                text,
            ) is not None

        # Single-word pattern.
        regex = rf"\b{escaped_pattern}\b"

        return re.search(
            regex,
            text,
        ) is not None

    @staticmethod
    def _calibrate_confidence(
        weighted_score: float,
    ) -> float:
        """
        Convert weighted evidence into a calibrated confidence score.

        Weighted evidence represents the strength of matched indicators.
        Calibration converts that evidence into the confidence presented
        to downstream components and users.
        """

        if weighted_score >= 0.90:
            return 0.90

        if weighted_score >= 0.60:
            return 0.70

        return round(
            weighted_score,
            2,
        )

    def _confidence_level(
        self,
        confidence: float,
    ) -> str:
        """Convert numeric confidence into a human-readable level."""

        if confidence >= self.CONFIDENCE_THRESHOLDS["HIGH"]:
            return "HIGH"

        if confidence >= self.CONFIDENCE_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def _unknown_result() -> dict:
        """Return a standard result when classification is unsuccessful."""

        return {
            "document_type": "UNKNOWN",
            "evidence_score": 0.0,
            "confidence": 0.0,
            "confidence_level": "LOW",
            "classification_method": "weighted_keyword_rule",
            "matched_patterns": [],
            "evidence": [],

            # No ambiguity when there is no classification.
            "ambiguity": False,
            "second_best_document_type": None,
            "second_best_score": None,
            "score_difference": None,

            # Unknown documents always require review.
            "needs_review": True,
        }


# ================================================================
# TESTS
# ================================================================

def test_ambiguous_classification():
    """
    Verify that a small difference between the top two scores
    is correctly classified as ambiguous.

    Production document patterns are temporarily replaced with
    controlled test weights. This prevents us from changing
    production rules just to manufacture an ambiguous example.
    """

    classifier = DocumentClassifier()

    # Controlled test evidence:
    #
    # GST_CERTIFICATE       = 0.60
    # COMPANY_REGISTRATION  = 0.55
    # Difference             = 0.05
    #
    # Since 0.05 < 0.10, the result must be ambiguous.
    classifier.DOCUMENT_PATTERNS = {
        "GST_CERTIFICATE": {
            "gstin": 0.60,
        },
        "COMPANY_REGISTRATION": {
            "certificate of incorporation": 0.55,
        },
    }

    text = """
    GSTIN
    certificate of incorporation
    """

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"

    assert result["evidence_score"] == 0.60

    assert (
        result["second_best_document_type"]
        == "COMPANY_REGISTRATION"
    )

    assert result["second_best_score"] == 0.55

    assert result["score_difference"] == 0.05

    assert result["ambiguity"] is True

    assert result["needs_review"] is True


def test_clear_classification_is_not_ambiguous():
    """
    Verify that a normal GST document with strong GST evidence
    is not incorrectly marked as ambiguous.
    """

    text = """
    GST REGISTRATION CERTIFICATE
    GSTIN
    GST registration
    GOODS AND SERVICES TAX
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"

    assert result["ambiguity"] is False

    assert result["needs_review"] is False


def test_ambiguity_threshold_boundary():
    """
    Verify the exact threshold.

    Difference == 0.10 should NOT be ambiguous because the
    classifier uses:

        difference < AMBIGUITY_THRESHOLD
    """

    classifier = DocumentClassifier()

    # Controlled evidence:
    #
    # GST_CERTIFICATE       = 0.60
    # COMPANY_REGISTRATION  = 0.50
    # Difference             = 0.10
    classifier.DOCUMENT_PATTERNS = {
        "GST_CERTIFICATE": {
            "gstin": 0.60,
        },
        "COMPANY_REGISTRATION": {
            "certificate of incorporation": 0.50,
        },
    }

    text = """
    GSTIN
    certificate of incorporation
    """

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"

    assert result["evidence_score"] == 0.60

    assert (
        result["second_best_document_type"]
        == "COMPANY_REGISTRATION"
    )

    assert result["second_best_score"] == 0.50

    assert result["score_difference"] == 0.10

    assert result["ambiguity"] is False


def test_single_classification_is_not_ambiguous():
    """
    Verify that when only one document type has evidence,
    there is no ambiguity.
    """

    classifier = DocumentClassifier()

    text = """
    GSTIN
    GST registration
    """

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"

    assert result["second_best_document_type"] is None

    assert result["second_best_score"] is None

    assert result["score_difference"] is None

    assert result["ambiguity"] is False


def test_unknown_document_requires_review():
    """
    Verify that an unrecognized document is returned as UNKNOWN
    and requires human review.
    """

    classifier = DocumentClassifier()

    text = """
    This document contains completely unrelated information.
    """

    result = classifier.classify(text)

    assert result["document_type"] == "UNKNOWN"

    assert result["confidence"] == 0.0

    assert result["ambiguity"] is False

    assert result["second_best_document_type"] is None

    assert result["second_best_score"] is None

    assert result["score_difference"] is None

    assert result["needs_review"] is True