from app.services.evaluators.gst_evaluator import GSTEvaluator
from app.services.evaluators.registry import evaluator_registry


def register_evaluators() -> None:
    """
    Register all available requirement evaluators.

    This function is intentionally explicit so that evaluator
    registration happens in one controlled place.
    """

    if evaluator_registry.get("GST") is None:
        evaluator_registry.register(
            GSTEvaluator()
        )