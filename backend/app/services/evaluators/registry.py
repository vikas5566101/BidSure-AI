from app.services.evaluators.base import RequirementEvaluator


class EvaluatorRegistry:
    """
    Registry of requirement evaluators.

    Maps a requirement_type to its evaluator.
    """

    def __init__(self):
        self._evaluators: dict[str, RequirementEvaluator] = {}

    def register(
        self,
        evaluator: RequirementEvaluator,
    ) -> None:

        requirement_type = evaluator.requirement_type.upper()

        if requirement_type in self._evaluators:
            raise ValueError(
                f"Evaluator already registered for "
                f"requirement type: {requirement_type}"
            )

        self._evaluators[requirement_type] = evaluator

    def get(
        self,
        requirement_type: str,
    ) -> RequirementEvaluator | None:

        return self._evaluators.get(
            requirement_type.upper()
        )


evaluator_registry = EvaluatorRegistry()