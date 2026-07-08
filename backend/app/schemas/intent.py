from pathlib import Path

from pydantic import BaseModel, Field


class SearchFilesIntent(BaseModel):
    """Structured intent for searching files under an allowed directory."""

    root_path: Path = Field(description="Directory to search within.")
    query: str = Field(min_length=1, max_length=255, description="Case-insensitive filename query.")
    include_hidden: bool = Field(default=False, description="Whether hidden files should be searched.")
    max_results: int | None = Field(default=None, ge=1, le=500)
