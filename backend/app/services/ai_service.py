import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.config import Settings
from app.schemas.intent import ExecutionPlan, ToolCall


class AIService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_plan(
        self,
        user_query: str,
        allowed_roots: list[str],
        current_workspace: str,
        api_key: str | None = None,
        planner: str = "auto",
    ) -> ExecutionPlan:

        effective_key = api_key or getattr(self._settings, "gemini_api_key", None)
        if not effective_key:
            effective_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        if planner == "rule":
            return self._mock_plan(user_query, allowed_roots, current_workspace)

        if planner == "auto" and not effective_key:
            return self._mock_plan(user_query, allowed_roots, current_workspace)

        if planner == "gemini" and not effective_key:
            raise HTTPException(
                status_code=400,
                detail="Gemini planner selected but no API key is configured.",
            )

        model = getattr(self._settings, "gemini_model", "gemini-2.5-flash")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={effective_key}"
        )

        system_instruction = (
            "You are the planner for the AI Operating System Assistant. "
            "Translate the user's natural language request into a sequence "
            "of tool calls (an execution plan). Return ONLY JSON matching "
            "the provided schema."
        )

        payload: dict[str, Any] = {
            "contents": [
                {"role": "user", "parts": [{"text": f"User Request: {user_query}"}]}
            ],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "explanation": {"type": "STRING"},
                        "steps": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "tool": {
                                        "type": "STRING",
                                        "enum": [
                                            "search_files", "rename_file", "move_file",
                                            "delete_file", "organize_folder", "find_duplicates",
                                            "create_project", "initialize_git",
                                            "install_dependencies", "create_readme",
                                        ],
                                    },
                                    "parameters": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "root_path": {"type": "STRING"},
                                            "query": {"type": "STRING"},
                                            "include_hidden": {"type": "BOOLEAN"},
                                            "max_results": {"type": "INTEGER"},
                                            "source_path": {"type": "STRING"},
                                            "new_name": {"type": "STRING"},
                                            "target_dir": {"type": "STRING"},
                                            "path": {"type": "STRING"},
                                            "folder_path": {"type": "STRING"},
                                            "project_type": {"type": "STRING"},
                                            "project_name": {"type": "STRING"},
                                            "location": {"type": "STRING"},
                                            "project_path": {"type": "STRING"},
                                            "package_manager": {"type": "STRING"},
                                            "content": {"type": "STRING"},
                                        },
                                    },
                                },
                                "required": ["tool", "parameters"],
                            },
                        },
                    },
                    "required": ["explanation", "steps"],
                },
            },
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                resp_data = json.loads(response.read().decode("utf-8"))

            text_response = resp_data["candidates"][0]["content"]["parts"][0]["text"]
            json_response = json.loads(text_response)

            for step in json_response.get("steps", []):
                tool = step.get("tool")
                params = step.get("parameters", {})

                if tool == "rename_file":
                    target = (
                        params.pop("target_dir", None)
                        or params.pop("target_path", None)
                        or params.pop("new_path", None)
                    )
                    if target and "new_name" not in params:
                        params["new_name"] = Path(str(target)).name
                    if "source_path" not in params:
                        params["source_path"] = str(Path(current_workspace) / "draft.txt")

                elif tool == "search_files" and "query" not in params:
                    params["query"] = ""

            return ExecutionPlan.model_validate(json_response)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API Planning Failed: {str(e)}",
            )

    def _mock_plan(
        self,
        query: str,
        allowed_roots: list[str],
        current_workspace: str,
    ) -> ExecutionPlan:
        """Local rule-based planner used when Gemini is unavailable."""

        query_lower = query.lower()
        root = allowed_roots[0] if allowed_roots else current_workspace

        # Search
        if "search" in query_lower or "find" in query_lower:
            parts = query.split()
            term = parts[-1].strip("'\"") if parts else ""
            return ExecutionPlan(
                explanation="Search for matching files.",
                steps=[ToolCall(
                    tool="search_files",
                    parameters={"root_path": root, "query": term, "include_hidden": False},
                )],
            )

        # Rename
        if "rename" in query_lower:
            match = re.search(r"rename\s+(.+?)\s+to\s+(.+)", query, re.IGNORECASE)
            if not match:
                raise HTTPException(status_code=400, detail="Couldn't understand rename command.")
            source, destination = match.group(1).strip(), match.group(2).strip()
            return ExecutionPlan(
                explanation=f"Rename {source} to {destination}",
                steps=[ToolCall(
                    tool="rename_file",
                    parameters={"source_path": str(Path(root) / source), "new_name": destination},
                )],
            )

        # Organize
        if "organize" in query_lower:
            return ExecutionPlan(
                explanation="Organize folder.",
                steps=[ToolCall(tool="organize_folder", parameters={"folder_path": root})],
            )

        # Django
        if "django" in query_lower:
            proj = f"{root}/CollegePortal"
            return ExecutionPlan(
                explanation="Create Django project.",
                steps=[
                    ToolCall(tool="create_project", parameters={"project_type": "django", "project_name": "CollegePortal", "location": root}),
                    ToolCall(tool="initialize_git", parameters={"project_path": proj}),
                    ToolCall(tool="install_dependencies", parameters={"project_path": proj, "package_manager": "pip"}),
                    ToolCall(tool="create_readme", parameters={"project_path": proj, "content": "# CollegePortal\nDjango project"}),
                ],
            )

        # React
        if "react" in query_lower:
            proj = f"{root}/portfolio"
            return ExecutionPlan(
                explanation="Create React project.",
                steps=[
                    ToolCall(tool="create_project", parameters={"project_type": "react", "project_name": "portfolio", "location": root}),
                    ToolCall(tool="initialize_git", parameters={"project_path": proj}),
                    ToolCall(tool="install_dependencies", parameters={"project_path": proj, "package_manager": "npm"}),
                    ToolCall(tool="create_readme", parameters={"project_path": proj, "content": "# Portfolio\nReact project"}),
                ],
            )

        # Duplicates
        if "duplicate" in query_lower:
            return ExecutionPlan(
                explanation="Find duplicate files.",
                steps=[ToolCall(tool="find_duplicates", parameters={"folder_path": root})],
            )

        # Move
        if "move" in query_lower:
            match = re.search(r"move\s+(.+?)\s+to\s+(.+)", query, re.IGNORECASE)
            if not match:
                raise HTTPException(status_code=400, detail="Couldn't understand move command.")
            source, destination = match.group(1).strip(), match.group(2).strip()
            return ExecutionPlan(
                explanation=f"Move {source} to {destination}",
                steps=[ToolCall(
                    tool="move_file",
                    parameters={"source_path": str(Path(root) / source), "target_dir": str(Path(root) / destination)},
                )],
            )

        # Delete
        if "delete" in query_lower or "remove" in query_lower:
            match = re.search(r"(?:delete|remove)\s+(.+)", query, re.IGNORECASE)
            target = match.group(1).strip() if match else "a.txt"
            return ExecutionPlan(
                explanation="Delete file.",
                steps=[ToolCall(tool="delete_file", parameters={"path": str(Path(root) / target)})],
            )

        # Default
        return ExecutionPlan(
            explanation="Search the workspace.",
            steps=[ToolCall(
                tool="search_files",
                parameters={"root_path": root, "query": "", "include_hidden": False},
            )],
        )
