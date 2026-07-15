from pathlib import Path

from app.tools.search_files import SearchFilesTool


def test_search_finds_matching_file_names(tmp_path: Path) -> None:
    (tmp_path / "project_notes.txt").write_text("notes", encoding="utf-8")
    (tmp_path / "other.txt").write_text("other", encoding="utf-8")

    tool = SearchFilesTool()

    matches = tool.search(tmp_path, "notes", include_hidden=False, max_results=10)

    assert matches == [tmp_path / "project_notes.txt"]


def test_search_skips_hidden_paths_by_default(tmp_path: Path) -> None:
    hidden_dir = tmp_path / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "secret_notes.txt").write_text("secret", encoding="utf-8")

    tool = SearchFilesTool()

    matches = tool.search(tmp_path, "notes", include_hidden=False, max_results=10)

    assert matches == []


def test_search_can_include_hidden_paths(tmp_path: Path) -> None:
    hidden_dir = tmp_path / ".hidden"
    hidden_dir.mkdir()
    hidden_file = hidden_dir / "secret_notes.txt"
    hidden_file.write_text("secret", encoding="utf-8")

    tool = SearchFilesTool()

    matches = tool.search(tmp_path, "notes", include_hidden=True, max_results=10)

    assert matches == [hidden_file]
