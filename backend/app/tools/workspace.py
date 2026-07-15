import os
from pathlib import Path
from typing import Any, Union
from app.validators.path_validator import PathValidator


class WorkspaceExplorerTool:
    """Lists files and directories under authorized workspace roots in a hierarchical structure."""

    def __init__(self, path_validator: PathValidator) -> None:
        self._path_validator = path_validator
        # Common system and build directories to ignore
        self.IGNORE_DIRS = {
            "node_modules",
            ".venv",
            "venv",
            "env",
            ".git",
            "__pycache__",
            ".pytest_cache",
            ".aios",
            ".oxlintrc.json",
            "package-lock.json",
            "operations.sqlite3",
            ".DS_Store",
            "Thumbs.db",
        }

    def list_workspace(self, allowed_roots: list[Path]) -> list[dict[str, Any]]:
        tree = []
        for root in allowed_roots:
            if not root.exists() or not root.is_dir():
                continue
            
            # Ensure path is valid and authorized
            try:
                validated_root = self._path_validator.validate_existing_path(root, is_dir=True)
                tree.append({
                    "name": validated_root.name or str(validated_root),
                    "path": str(validated_root),
                    "is_dir": True,
                    "children": self._scan_dir(validated_root, depth=0)
                })
            except Exception:
                # If root cannot be validated, skip it
                continue
        return tree

    def _scan_dir(self, directory: Path, depth: int) -> list[dict[str, Any]]:
        # Hard limit depth to prevent resource exhaustion
        if depth > 4:
            return []

        nodes = []
        try:
            for entry in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                # Skip hidden entries and ignored directories
                if entry.name.startswith(".") or entry.name in self.IGNORE_DIRS:
                    continue

                if entry.is_dir() and not entry.is_symlink():
                    nodes.append({
                        "name": entry.name,
                        "path": str(entry),
                        "is_dir": True,
                        "children": self._scan_dir(entry, depth + 1)
                    })
                elif entry.is_file():
                    nodes.append({
                        "name": entry.name,
                        "path": str(entry),
                        "is_dir": False
                    })
        except PermissionError:
            pass # Ignore directory scans that we don't have access to
        return nodes
