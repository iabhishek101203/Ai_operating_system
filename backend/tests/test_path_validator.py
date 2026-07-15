from pathlib import Path

import pytest

from app.core.config import Settings
from app.validators.path_validator import PathValidationError, PathValidator


def test_validate_directory_allows_path_inside_allowed_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    child = allowed / "child"
    child.mkdir()

    validator = PathValidator(Settings(allowed_roots=[allowed]))

    assert validator.validate_directory(child) == child.resolve()


def test_validate_directory_rejects_path_outside_allowed_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()

    validator = PathValidator(Settings(allowed_roots=[allowed]))

    with pytest.raises(PathValidationError):
        validator.validate_directory(outside)


def test_validate_directory_rejects_file(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello", encoding="utf-8")

    validator = PathValidator(Settings(allowed_roots=[tmp_path]))

    with pytest.raises(PathValidationError):
        validator.validate_directory(file_path)
