from collections import defaultdict
from hashlib import sha256
from pathlib import Path


class FindDuplicatesTool:
    def find_duplicates(self, folder_path: Path) -> dict[str, list[str]]:
        """Scans folder_path recursively for duplicate files by SHA256 content hash.

        Returns a dict of {sha256_hash: [list of duplicate file paths]}
        """
        if not folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")

        hashes = defaultdict(list)
        for path in folder_path.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            # Skip hidden paths
            if any(part.startswith(".") for part in path.parts):
                continue

            try:
                file_hash = self._compute_hash(path)
                hashes[file_hash].append(str(path))
            except IOError:
                # If file cannot be read, skip it
                continue

        # Filter to only return groups with duplicates
        return {h: paths for h, paths in hashes.items() if len(paths) > 1}

    @staticmethod
    def _compute_hash(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
