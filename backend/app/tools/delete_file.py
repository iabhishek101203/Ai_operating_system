from pathlib import Path
from send2trash import send2trash


class DeleteFileTool:
    """Safe deletion using send2trash."""

    def delete(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        send2trash(str(path))
