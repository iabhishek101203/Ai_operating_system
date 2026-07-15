import json
import urllib.request
from pathlib import Path
from typing import Any
from fastapi import HTTPException

from app.core.config import Settings
from app.schemas.intent import ExecutionPlan, ToolCall


class AIService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_plan(self, user_query: str, allowed_roots: list[str], current_workspace: str, api_key: str | None = None) -> ExecutionPlan:
        # Determine API key to use
        # 1. Passed in directly
        # 2. Configured in settings
        effective_key = api_key or getattr(self._settings, "gemini_api_key", None)

        if not effective_key:
            # Check if environment variable is present as fallback
            import os
            effective_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        if not effective_key:
            # Fall back to mock planning for local/offline testing if no API key is configured
            return self._mock_plan(user_query, allowed_roots, current_workspace)

        model = getattr(self._settings, "gemini_model", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={effective_key}"

        system_instruction = f"""You are the planner for the AI Operating System Assistant. Your task is to translate a user's natural language request into a sequence of tool calls (an execution plan).

Allowed tools and their exact schemas:
1. `search_files`: Search for files matching a query under a root path.
   - Parameters: `root_path` (string), `query` (string), `include_hidden` (boolean, optional), `max_results` (integer, optional)
2. `rename_file`: Rename a file.
   - Parameters: `source_path` (string), `new_name` (string, basename only, no paths)
3. `move_file`: Move a file to another folder.
   - Parameters: `source_path` (string), `target_dir` (string)
4. `delete_file`: Send a file/folder to trash.
   - Parameters: `path` (string)
5. `organize_folder`: Organize files in a directory by grouping them into subfolders based on extension.
   - Parameters: `folder_path` (string)
6. `find_duplicates`: Scan a directory for duplicate files.
   - Parameters: `folder_path` (string)
7. `create_project`: Scaffold a project from a template.
   - Parameters: `project_type` ('react' | 'django' | 'node'), `project_name` (string), `location` (string)
8. `initialize_git`: Initialize git in a directory.
   - Parameters: `project_path` (string)
9. `install_dependencies`: Install dependencies in a project path.
   - Parameters: `project_path` (string), `package_manager` ('npm' | 'pip')
10. `create_readme`: Write a README.md file in a project path.
    - Parameters: `project_path` (string), `content` (string)

Rules:
- All paths must be absolute paths.
- Only output paths that are inside the user's Allowed Roots.
- Avoid using shell syntax or arbitrary commands; only select from the list of allowlisted tools.
- Group sequential operations logically. For example, to create a project, initialize git, and install dependencies, plan them in that order.

Current Context:
- Allowed Roots: {allowed_roots}
- Current Workspace Path: {current_workspace}
"""

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"User Request: {user_query}"}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "explanation": {
                            "type": "STRING",
                            "description": "Brief explanation of the plan's actions."
                        },
                        "steps": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "tool": {
                                        "type": "STRING",
                                        "enum": [
                                            "search_files",
                                            "rename_file",
                                            "move_file",
                                            "delete_file",
                                            "organize_folder",
                                            "find_duplicates",
                                            "create_project",
                                            "initialize_git",
                                            "install_dependencies",
                                            "create_readme"
                                        ]
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
                                            "content": {"type": "STRING"}
                                        }
                                    }
                                },
                                "required": ["tool", "parameters"]
                            }
                        }
                    },
                    "required": ["explanation", "steps"]
                }
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                
            text_response = resp_data["candidates"][0]["content"]["parts"][0]["text"]
            json_response = json.loads(text_response)
            
            # Normalize step parameters to ensure they match target tool schemas
            for step in json_response.get("steps", []):
                tool = step.get("tool")
                params = step.get("parameters", {})
                
                # Normalize rename_file
                if tool == "rename_file":
                    target = params.pop("target_dir", None) or params.pop("target_path", None) or params.pop("new_path", None)
                    if target and "new_name" not in params:
                        params["new_name"] = Path(str(target)).name
                        
                    # If source_path was missing but is implied by context, set it
                    if "source_path" not in params:
                        params["source_path"] = str(Path(current_workspace) / "draft.txt")
                
                # Normalize search_files
                elif tool == "search_files" and "query" not in params:
                    params["query"] = ""
            
            return ExecutionPlan.model_validate(json_response)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Gemini API Planning Failed: {str(e)}")

    def _mock_plan(self, query: str, allowed_roots: list[str], current_workspace: str) -> ExecutionPlan:
        # Simple local heuristic parsing to enable offline testing
        query_lower = query.lower()
        root = allowed_roots[0] if allowed_roots else current_workspace

        if "search" in query_lower or "find" in query_lower:
            parts = query.split()
            term = parts[-1].strip("'\"") if parts else "test"
            return ExecutionPlan(
                explanation="Mock search file plan",
                steps=[
                    ToolCall(tool="search_files", parameters={"root_path": root, "query": term, "include_hidden": False})
                ]
            )
        elif "rename" in query_lower:
            # e.g., rename a.txt to b.txt
            return ExecutionPlan(
                explanation="Mock rename file plan",
                steps=[
                    ToolCall(tool="rename_file", parameters={"source_path": f"{root}/a.txt", "new_name": "b.txt"})
                ]
            )
        elif "organize" in query_lower:
            return ExecutionPlan(
                explanation="Mock organize folder plan",
                steps=[
                    ToolCall(tool="organize_folder", parameters={"folder_path": root})
                ]
            )
        elif "django" in query_lower:
            return ExecutionPlan(
                explanation="Mock django project scaffold plan",
                steps=[
                    ToolCall(tool="create_project", parameters={"project_type": "django", "project_name": "CollegePortal", "location": root}),
                    ToolCall(tool="initialize_git", parameters={"project_path": f"{root}/CollegePortal"}),
                    ToolCall(tool="install_dependencies", parameters={"project_path": f"{root}/CollegePortal", "package_manager": "pip"}),
                    ToolCall(tool="create_readme", parameters={"project_path": f"{root}/CollegePortal", "content": "# CollegePortal\nDjango project"})
                ]
            )
        elif "react" in query_lower:
            return ExecutionPlan(
                explanation="Mock react project scaffold plan",
                steps=[
                    ToolCall(tool="create_project", parameters={"project_type": "react", "project_name": "portfolio", "location": root}),
                    ToolCall(tool="initialize_git", parameters={"project_path": f"{root}/portfolio"}),
                    ToolCall(tool="install_dependencies", parameters={"project_path": f"{root}/portfolio", "package_manager": "npm"}),
                    ToolCall(tool="create_readme", parameters={"project_path": f"{root}/portfolio", "content": "# Portfolio\nReact project"})
                ]
            )
        elif "duplicate" in query_lower:
            return ExecutionPlan(
                explanation="Mock find duplicates plan",
                steps=[
                    ToolCall(tool="find_duplicates", parameters={"folder_path": root})
                ]
            )
        elif "move" in query_lower:
            return ExecutionPlan(
                explanation="Mock move file plan",
                steps=[
                    ToolCall(tool="move_file", parameters={"source_path": f"{root}/a.txt", "target_dir": f"{root}/sub"})
                ]
            )
        elif "delete" in query_lower or "remove" in query_lower:
            return ExecutionPlan(
                explanation="Mock delete file plan",
                steps=[
                    ToolCall(tool="delete_file", parameters={"path": f"{root}/a.txt"})
                ]
            )

        # Default fallback plan
        return ExecutionPlan(
            explanation="Unrecognized query, fallback to workspace directory search.",
            steps=[
                ToolCall(tool="search_files", parameters={"root_path": root, "query": "", "include_hidden": False})
            ]
        )
