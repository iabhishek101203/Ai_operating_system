from pathlib import Path
import pytest

from app.core.config import Settings
from app.validators.path_validator import PathValidationError, PathValidator


def test_validate_new_path_resolves_nested_non_existent_paths(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    
    # Path doesn't exist, but is inside allowed root
    non_existent = allowed / "nested" / "deep" / "file.txt"
    
    validator = PathValidator(Settings(allowed_roots=[allowed]))
    resolved = validator.validate_new_path(non_existent)
    
    assert resolved == non_existent.resolve()


def test_validate_new_path_rejects_non_existent_outside_allowed(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    
    non_existent = outside / "folder" / "file.txt"
    
    validator = PathValidator(Settings(allowed_roots=[allowed]))
    with pytest.raises(PathValidationError):
        validator.validate_new_path(non_existent)


def test_validate_new_path_detects_symlinks_in_existing_ancestors(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    
    # Create a symlink to outside directory
    outside = tmp_path / "outside"
    outside.mkdir()
    
    symlink_dir = allowed / "symlink_folder"
    symlink_dir.symlink_to(outside, target_is_directory=True)
    
    non_existent = symlink_dir / "new_file.txt"
    
    validator = PathValidator(Settings(allowed_roots=[allowed]))
    with pytest.raises(PathValidationError):
        validator.validate_new_path(non_existent)
