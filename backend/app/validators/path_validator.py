from pathlib import Path

from app.core.config import Settings


class PathValidationError(ValueError):
    """Raised when a user-provided path violates filesystem policy."""


class PathValidator:
    def __init__(self, settings: Settings):
        self._settings = settings

    def validate_directory(self, path: Path) -> Path:
        resolved_path = path.expanduser().resolve()

        if not resolved_path.exists():
            raise PathValidationError(f"Path does not exist: {resolved_path}")

        if not resolved_path.is_dir():
            raise PathValidationError(f"Path is not a directory: {resolved_path}")

        if not self._is_within_allowed_roots(resolved_path):
            raise PathValidationError(f"Path is outside allowed roots: {resolved_path}")

        return resolved_path

    def validate_regular_file(self, path: Path) -> Path:
        """Validate a file without following a user-supplied symlink."""
        expanded_path = path.expanduser()
        if expanded_path.is_symlink():
            raise PathValidationError(f"Symbolic links are not supported: {expanded_path}")

        resolved_path = expanded_path.resolve()
        if not resolved_path.exists():
            raise PathValidationError(f"Path does not exist: {resolved_path}")
        if not resolved_path.is_file():
            raise PathValidationError(f"Path is not a regular file: {resolved_path}")
        if not self._is_within_allowed_roots(resolved_path):
            raise PathValidationError(f"Path is outside allowed roots: {resolved_path}")
        return resolved_path

    def validate_new_path(self, path: Path) -> Path:
        """Validate a path that does not exist yet (e.g. target of rename/move or new project)."""
        expanded_path = path.expanduser()
        # Find closest existing ancestor to check for symlinks
        ancestor = expanded_path
        while not ancestor.exists() and ancestor != ancestor.parent:
            ancestor = ancestor.parent

        if ancestor.is_symlink():
            raise PathValidationError(f"Symbolic links are not supported: {ancestor}")

        resolved_path = expanded_path.resolve()
        if not self._is_within_allowed_roots(resolved_path):
            raise PathValidationError(f"Path is outside allowed roots: {resolved_path}")
        return resolved_path

    def _is_within_allowed_roots(self, path: Path) -> bool:
        allowed_roots = [root.expanduser().resolve() for root in self._settings.allowed_roots]
        return any(path == root or root in path.parents for root in allowed_roots)

