from pathlib import Path
import shutil


class MoveFileTool:
    """Allowlisted move implementation; it never invokes a shell."""

    def move(self, source_path: Path, target_dir: Path) -> Path:
        if not source_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {source_path}")
        if not target_dir.is_dir():
            raise NotADirectoryError(f"Target is not a directory: {target_dir}")

        target_path = target_dir / source_path.name
        if target_path.exists() or target_path.is_symlink():
            raise FileExistsError(f"Destination file already exists: {target_path}")

        # Perform moving
        shutil.move(str(source_path), str(target_path))
        return target_path
