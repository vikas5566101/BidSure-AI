from app.services.evaluators.gst_evaluator import (
    GSTEvaluator,
)
from app.services.evaluators.udyam_evaluator import (
    UdyamEvaluator,
)
from app.services.evaluators.income_tax_evaluator import (
    IncomeTaxEvaluator,
)
from app.services.evaluators.registry import (
    evaluator_registry,
)


def register_evaluators() -> None:
    """
    Register all available requirement evaluators.

    Evaluator registration is kept in one controlled
    location so the application can initialize all
    compliance rules during startup.
    """

    if evaluator_registry.get("GST") is None:
        evaluator_registry.register(
            GSTEvaluator()
        )

    if evaluator_registry.get("UDYAM") is None:
        evaluator_registry.register(
            UdyamEvaluator()
        )

    if evaluator_registry.get("INCOME_TAX") is None:
        evaluator_registry.register(
            IncomeTaxEvaluator()
        )