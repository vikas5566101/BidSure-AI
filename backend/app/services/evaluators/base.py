from abc import ABC, abstractmethod

from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)


class RequirementEvaluator(ABC):
    """
    Base contract for all tender requirement evaluators.
    """

    @property
    @abstractmethod
    def requirement_type(self) -> str:
        """
        Return the requirement type handled by this evaluator.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:
        """
        Evaluate the supplied evidence against the requirement.
        """
        raise NotImplementedError