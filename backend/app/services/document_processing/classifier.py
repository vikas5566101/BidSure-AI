"""
Document classification service for BidSure AI.

Phase 1:
- Identify document type
- Calculate transparent weighted confidence
- Preserve weighted evidence
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

    # =========================================================
    # DOCUMENT PATTERNS
    # =========================================================

    DOCUMENT_PATTERNS: Dict[str, Dict[str, float]] = {

        # -----------------------------------------------------
        # GST CERTIFICATE
        # -----------------------------------------------------
        #
        # IMPORTANT:
        # The original five weights are preserved because the
        # existing tests depend on them summing to 1.0.
        #
        # Additional real-world GST indicators are added with
        # small weights.
        # -----------------------------------------------------

        "GST_CERTIFICATE": {

            # Original production/test patterns
            "goods and services tax": 0.30,
            "gstin": 0.40,
            "gst registration": 0.20,
            "certificate of registration": 0.05,
            "taxpayer": 0.05,

            # Real GST certificate indicators
            "form gst reg-06": 0.10,
            "registration certificate": 0.10,
            "registration number": 0.05,
            "constitution of business": 0.05,
            "date of liability": 0.05,
            "date of validity": 0.05,
            "type of registration": 0.05,

            # Indian GST authority wording
            "goods and services tax act": 0.05,
        },

        # -----------------------------------------------------
        # PAN CARD
        # -----------------------------------------------------

        "PAN_CARD": {
            "permanent account number": 0.50,
            "income tax department": 0.30,
            "pan": 0.20,
        },

        # -----------------------------------------------------
        # UDYAM CERTIFICATE
        # -----------------------------------------------------

        "UDYAM_CERTIFICATE": {
            "udyam registration": 0.35,
            "udyam registration number": 0.40,
            "udyam": 0.15,
            "ministry of micro": 0.10,
        },

        # -----------------------------------------------------
        # COMPANY REGISTRATION
        # -----------------------------------------------------

        "COMPANY_REGISTRATION": {
            "certificate of incorporation": 0.30,
            "registrar of companies": 0.25,
            "company registration": 0.20,
            "corporate identity number": 0.20,
            "cin": 0.05,
        },

        # -----------------------------------------------------
        # FINANCIAL STATEMENT
        # -----------------------------------------------------

        "FINANCIAL_STATEMENT": {
            "balance sheet": 0.25,
            "profit and loss": 0.20,
            "profit & loss": 0.20,
            "assets and liabilities": 0.15,
            "audited financial statement": 0.10,
            "financial statements": 0.10,
        },

        # -----------------------------------------------------
        # BANK CERTIFICATE
        # -----------------------------------------------------

        "BANK_CERTIFICATE": {
            "bank certificate": 0.30,
            "bank account": 0.25,
            "account number": 0.20,
            "banker": 0.15,
            "branch manager": 0.10,
        },

        # -----------------------------------------------------
        # EXPERIENCE CERTIFICATE
        # -----------------------------------------------------

        "EXPERIENCE_CERTIFICATE": {
            "experience certificate": 0.30,
            "work order": 0.20,
            "successfully completed": 0.20,
            "similar work": 0.15,
            "completion certificate": 0.15,
        },

        # -----------------------------------------------------
        # TECHNICAL CERTIFICATE
        # -----------------------------------------------------

        "TECHNICAL_CERTIFICATE": {
            "technical certificate": 0.30,
            "technical specification": 0.25,
            "compliance certificate": 0.25,
            "technical qualification": 0.20,
        },

        # -----------------------------------------------------
        # AFFIDAVIT
        # -----------------------------------------------------

        "AFFIDAVIT": {
            "affidavit": 0.40,
            "sworn before": 0.25,
            "deponent": 0.20,
            "notary": 0.15,
        },

        # -----------------------------------------------------
        # UNDERTAKING
        # -----------------------------------------------------

        "UNDERTAKING": {
            "undertaking": 0.40,
            "hereby undertake": 0.25,
            "we undertake": 0.20,
            "declaration and undertaking": 0.15,
        },

        # -----------------------------------------------------
        # TENDER DOCUMENT
        # -----------------------------------------------------

        "TENDER_DOCUMENT": {
            "tender document": 0.25,
            "notice inviting tender": 0.20,
            "nit": 0.10,
            "bid submission": 0.20,
            "tender id": 0.10,
            "bid document": 0.15,
        },
    }

    # =========================================================
    # CONTROLLED OCR ALIASES
    # =========================================================

    OCR_ALIASES: Dict[str, List[str]] = {

        # -----------------------------------------------------
        # GSTIN
        # -----------------------------------------------------

        "gstin": [
            "gst1n",
            "gst in",
            "gstln",
        ],

        # -----------------------------------------------------
        # PAN
        # -----------------------------------------------------

        "pan": [
            "p an",
        ],

        # -----------------------------------------------------
        # CIN
        # -----------------------------------------------------

        "cin": [
            "c in",
        ],

        # -----------------------------------------------------
        # UDYAM
        # -----------------------------------------------------

        "udyam": [
            "udyarn",
        ],

        "udyam registration": [
            "udyarn registration",
        ],

        "udyam registration number": [
            "udyarn registration number",
        ],

        # -----------------------------------------------------
        # GST REAL-WORLD OCR VARIANTS
        # -----------------------------------------------------

        "form gst reg-06": [
            "form gst reg 06",
            "form gst reg—06",
            "form gst reg 06",
        ],

        "registration certificate": [
            "reglstration certificate",
            "registratlon certificate",
        ],

        "registration number": [
            "reglstration number",
            "registratlon number",
        ],

        "constitution of business": [
            "constitutlon of business",
            "constitution of buslness",
        ],

        "date of liability": [
            "date of liabillty",
            "date of liabllity",
        ],

        "date of validity": [
            "date of validlty",
            "date of valldity",
        ],

        "type of registration": [
            "type of reglstration",
            "type of registratlon",
        ],

        "goods and services tax act": [
            "goods and services tax act",
        ],
    }

    # =========================================================
    # CONFIDENCE THRESHOLDS
    # =========================================================

    CONFIDENCE_THRESHOLDS = {
        "HIGH": 0.90,
        "MEDIUM": 0.70,
    }

    # =========================================================
    # AMBIGUITY THRESHOLD
    # =========================================================

    AMBIGUITY_THRESHOLD = 0.10

    # =========================================================
    # CLASSIFY
    # =========================================================

    def classify(
        self,
        text: str,
    ) -> dict:
        """
        Classify a document based on extracted text.

        Returns:
            Dictionary containing:

            - document_type
            - evidence_score
            - confidence
            - confidence_level
            - classification_method
            - matched_patterns
            - evidence
            - ambiguity
            - second_best_document_type
            - second_best_score
            - score_difference
            - needs_review
        """

        # -----------------------------------------------------
        # Empty input
        # -----------------------------------------------------

        if not text or not text.strip():
            return self._unknown_result()

        # -----------------------------------------------------
        # Normalize extracted/OCR text
        # -----------------------------------------------------

        normalized_text = self._normalize(
            text
        )

        # -----------------------------------------------------
        # Store classification scores
        #
        # document_type ->
        # (
        #     score,
        #     matched_patterns,
        #     evidence
        # )
        # -----------------------------------------------------

        scores: Dict[
            str,
            Tuple[
                float,
                List[str],
                List[dict],
            ],
        ] = {}

        # -----------------------------------------------------
        # Calculate weighted evidence
        # -----------------------------------------------------

        for (
            document_type,
            patterns,
        ) in self.DOCUMENT_PATTERNS.items():

            matched_patterns = []

            evidence = []

            for (
                pattern,
                weight,
            ) in patterns.items():

                matched_variant = (
                    self._find_matching_variant(
                        pattern,
                        normalized_text,
                    )
                )

                if matched_variant is not None:

                    matched_patterns.append(
                        pattern
                    )

                    evidence.append(
                        {
                            "pattern": pattern,
                            "weight": weight,
                            "matched_as": matched_variant,
                        }
                    )

            # -------------------------------------------------
            # Keep document types that have evidence
            # -------------------------------------------------

            if matched_patterns:

                weighted_score = sum(
                    item["weight"]
                    for item in evidence
                )

                scores[
                    document_type
                ] = (
                    min(
                        weighted_score,
                        1.0,
                    ),
                    matched_patterns,
                    evidence,
                )

        # -----------------------------------------------------
        # No known evidence
        # -----------------------------------------------------

        if not scores:
            return self._unknown_result()

        # -----------------------------------------------------
        # Rank classifications
        # -----------------------------------------------------

        ranked_scores = sorted(
            scores.items(),
            key=lambda item: item[1][0],
            reverse=True,
        )

        # -----------------------------------------------------
        # Best classification
        # -----------------------------------------------------

        document_type, (
            evidence_score,
            matched_patterns,
            evidence,
        ) = ranked_scores[0]

        # -----------------------------------------------------
        # Second-best classification
        # -----------------------------------------------------

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

            second_best_score = (
                raw_second_best_score
            )

            score_difference = round(
                evidence_score
                - second_best_score,
                2,
            )

            ambiguity = (
                score_difference
                < self.AMBIGUITY_THRESHOLD
            )

        # -----------------------------------------------------
        # Confidence calibration
        # -----------------------------------------------------

        confidence = (
            self._calibrate_confidence(
                evidence_score
            )
        )

        confidence_level = (
            self._confidence_level(
                confidence
            )
        )

        # -----------------------------------------------------
        # Human review decision
        # -----------------------------------------------------

        needs_review = (
            confidence
            < self.CONFIDENCE_THRESHOLDS[
                "MEDIUM"
            ]
            or ambiguity
        )

        # -----------------------------------------------------
        # Final classification result
        # -----------------------------------------------------

        return {
            "document_type": document_type,

            "evidence_score": round(
                evidence_score,
                2,
            ),

            "confidence": confidence,

            "confidence_level": (
                confidence_level
            ),

            "classification_method": (
                "weighted_keyword_rule"
            ),

            "matched_patterns": (
                matched_patterns
            ),

            "evidence": evidence,

            "ambiguity": ambiguity,

            "second_best_document_type": (
                second_best_document_type
            ),

            "second_best_score": (
                round(
                    second_best_score,
                    2,
                )
                if second_best_score is not None
                else None
            ),

            "score_difference": (
                score_difference
            ),

            "needs_review": needs_review,
        }

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        """
        Normalize extracted/OCR text for matching.

        Converts:
            multiple spaces/newlines
        into:
            single spaces
        """

        return " ".join(
            text.lower().split()
        )

    # =========================================================
    # FIND MATCHING VARIANT
    # =========================================================

    def _find_matching_variant(
        self,
        pattern: str,
        text: str,
    ) -> str | None:
        """
        Find the canonical pattern or one of its approved
        OCR aliases.

        Returns:
            The text variant that matched, or None.
        """

        # -----------------------------------------------------
        # Try canonical pattern first
        # -----------------------------------------------------

        if self._pattern_matches(
            pattern,
            text,
        ):
            return pattern

        # -----------------------------------------------------
        # Try OCR aliases
        # -----------------------------------------------------

        for alias in self.OCR_ALIASES.get(
            pattern,
            [],
        ):

            if self._pattern_matches(
                alias,
                text,
            ):
                return alias

        return None

    # =========================================================
    # PATTERN MATCHING
    # =========================================================

    @staticmethod
    def _pattern_matches(
        pattern: str,
        text: str,
    ) -> bool:
        """
        Check whether a pattern appears as a complete
        word or phrase.

        Multi-word patterns allow flexible whitespace.
        """

        pattern = pattern.strip().lower()

        escaped_pattern = re.escape(
            pattern
        )

        # -----------------------------------------------------
        # Multi-word pattern
        # -----------------------------------------------------

        if " " in pattern:

            escaped_pattern = (
                escaped_pattern.replace(
                    r"\ ",
                    r"\s+",
                )
            )

            regex = (
                rf"\b{escaped_pattern}\b"
            )

            return (
                re.search(
                    regex,
                    text,
                )
                is not None
            )

        # -----------------------------------------------------
        # Single-word pattern
        # -----------------------------------------------------

        regex = (
            rf"\b{escaped_pattern}\b"
        )

        return (
            re.search(
                regex,
                text,
            )
            is not None
        )

    # =========================================================
    # CONFIDENCE CALIBRATION
    # =========================================================

    @staticmethod
    def _calibrate_confidence(
        weighted_score: float,
    ) -> float:
        """
        Convert weighted evidence into a confidence score.

        Rules:

        >= 0.90 -> 0.90
        >= 0.60 -> 0.70
        otherwise -> evidence score
        """

        if weighted_score >= 0.90:
            return 0.90

        if weighted_score >= 0.60:
            return 0.70

        return round(
            weighted_score,
            2,
        )

    # =========================================================
    # CONFIDENCE LEVEL
    # =========================================================

    def _confidence_level(
        self,
        confidence: float,
    ) -> str:
        """
        Convert numeric confidence to a human-readable level.
        """

        if (
            confidence
            >= self.CONFIDENCE_THRESHOLDS[
                "HIGH"
            ]
        ):
            return "HIGH"

        if (
            confidence
            >= self.CONFIDENCE_THRESHOLDS[
                "MEDIUM"
            ]
        ):
            return "MEDIUM"

        return "LOW"

    # =========================================================
    # UNKNOWN RESULT
    # =========================================================

    @staticmethod
    def _unknown_result() -> dict:
        """
        Return a standard result when classification
        is unsuccessful.
        """

        return {
            "document_type": "UNKNOWN",

            "evidence_score": 0.0,

            "confidence": 0.0,

            "confidence_level": "LOW",

            "classification_method": (
                "weighted_keyword_rule"
            ),

            "matched_patterns": [],

            "evidence": [],

            "ambiguity": False,

            "second_best_document_type": None,

            "second_best_score": None,

            "score_difference": None,

            "needs_review": True,
        }