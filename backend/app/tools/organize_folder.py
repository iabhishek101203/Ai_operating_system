from pathlib import Path
import shutil


class OrganizeFolderTool:
    CATEGORIES = {
        "Documents": {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".csv", ".md"},
        "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"},
        "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"},
        "Video": {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv"},
        "Archives": {".zip", ".tar", ".gz", ".rar", ".7z"},
        "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".java", ".cpp", ".c", ".sh"},
    }

    def organize(self, folder_path: Path) -> list[dict[str, str]]:
        """Organizes immediate files in folder_path into category folders.

        Returns a list of dicts describing the moves: [{"original": str, "new": str}]
        """
        if not folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")

        moves = []
        for path in folder_path.iterdir():
            if not path.is_file() or path.is_symlink():
                continue

            # Skip hidden files
            if path.name.startswith("."):
                continue

            # Skip database files to prevent moving operations.sqlite3
            if path.suffix.lower() in {".sqlite3", ".sqlite", ".db"}:
                continue


            ext = path.suffix.lower()
            category = "Others"
            for cat, extensions in self.CATEGORIES.items():
                if ext in extensions:
                    category = cat
                    break

            target_dir = folder_path / category
            target_dir.mkdir(exist_ok=True)

            target_path = target_dir / path.name
            if target_path.exists():
                # Avoid collision by appending a counter
                base = path.stem
                counter = 1
                while True:
                    candidate = target_dir / f"{base}_{counter}{ext}"
                    if not candidate.exists():
                        target_path = candidate
                        break
                    counter += 1

            shutil.move(str(path), str(target_path))
            moves.append({
                "original": str(path),
                "new": str(target_path),
            })

        return moves
