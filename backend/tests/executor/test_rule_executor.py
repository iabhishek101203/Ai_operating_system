from app.executor.rule_executor import RuleExecutor
from app.intent_engine.enums import IntentStatus
from app.planner.models import ExecutionPlan


def test_unsafe_plan():

    executor = RuleExecutor()

    plan = ExecutionPlan(
        intent="rename",
        safe_to_execute=False,
        reasoning="Unsafe",
    )

    result = executor.execute(plan)

    assert result.success is False
    assert result.message == "Unsafe"