from pathlib import Path

from app.executor.executor import Executor
from app.executor.models import ExecutionResult
from app.planner.models import ExecutionPlan

from app.tools.rename_file import RenameFileTool
from app.tools.move_file import MoveFileTool
from app.tools.delete_file import DeleteFileTool
from app.tools.search_files import SearchFilesTool


class RuleExecutor(Executor):

    def __init__(self):
        self.rename_tool = RenameFileTool()
        self.move_tool = MoveFileTool()
        self.delete_tool = DeleteFileTool()
        self.search_tool = SearchFilesTool()

    def execute(self, plan: ExecutionPlan) -> ExecutionResult:

        if not plan.safe_to_execute:
            return ExecutionResult(
                success=False,
                action=plan.intent,
                message=plan.reasoning,
            )

        if not plan.steps:
            return ExecutionResult(
                success=False,
                action=plan.intent,
                message="Execution plan contains no steps.",
            )

        step = plan.steps[0]

        try:

            if step.action == "rename":

                self.rename_tool.rename(
                    Path(step.parameters["source"]),
                    Path(step.parameters["destination"]),
                )

            elif step.action == "move":

                self.move_tool.move(
                    Path(step.parameters["source"]),
                    Path(step.parameters["destination"]),
                )

            elif step.action == "delete":

                self.delete_tool.delete(
                    Path(step.parameters["target"])
                )

            elif step.action == "search":

                self.search_tool.search(
                    root_path=Path(step.parameters["root"]),
                    query=step.parameters["query"],
                    include_hidden=False,
                    max_results=20,
                )

            else:

                return ExecutionResult(
                    success=False,
                    action=step.action,
                    message=f"Unsupported action '{step.action}'.",
                )

            return ExecutionResult(
                success=True,
                action=step.action,
                message="Execution completed successfully.",
            )

        except Exception as e:

            return ExecutionResult(
                success=False,
                action=step.action,
                message=str(e),
            )