from app.planner.models import (
    ExecutionPlan,
    ExecutionStep,
)


def test_execution_step():
    step = ExecutionStep(
        action="rename",
        parameters={
            "source": "report.txt",
            "destination": "final.txt",
        },
    )

    assert step.action == "rename"
    assert step.parameters["source"] == "report.txt"


def test_execution_plan():
    plan = ExecutionPlan(
        intent="rename",
        steps=[
            ExecutionStep(
                action="rename",
                parameters={
                    "source": "report.txt",
                    "destination": "final.txt",
                },
            )
        ],
    )

    assert plan.intent == "rename"
    assert len(plan.steps) == 1