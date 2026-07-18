from pathlib import Path


class RenameFileTool:
    """Allowlisted rename implementation; it never invokes a shell."""

    def rename(self, source_path: Path, target_path: Path) -> Path:
        if target_path.exists() or target_path.is_symlink():
            raise FileExistsError(f"Destination already exists: {target_path}")
        return source_path.rename(target_path)
