from pathlib import Path


class SearchFilesTool:
    """Read-only file search implemented without shell commands."""

    def search(
        self,
        root_path: Path,
        query: str,
        *,
        include_hidden: bool,
        max_results: int,
    ) -> list[Path]:
        normalized_query = query.casefold()
        matches: list[Path] = []

        for path in root_path.rglob("*"):
            if not include_hidden and self._is_hidden(path):
                continue

            if normalized_query in path.name.casefold():
                matches.append(path)

            if len(matches) >= max_results:
                break

        return matches

    @staticmethod
    def _is_hidden(path: Path) -> bool:
        return any(part.startswith(".") for part in path.parts)
