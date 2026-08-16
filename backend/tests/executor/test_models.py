from app.executor.models import ExecutionResult


def test_execution_result():
    result = ExecutionResult(
        success=True,
        message="Rename completed.",
        action="rename",
    )

    assert result.success is True
    assert result.message == "Rename completed."
    assert result.action == "rename"