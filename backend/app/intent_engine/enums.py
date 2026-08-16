"""
AI Operating System - Intent Engine Enums

These enums define the vocabulary understood by the Intent Engine.
Every module (parser, classifier, planner, policy engine, etc.)
uses these shared enums instead of raw strings.
"""

from enum import Enum


class IntentType(str, Enum):
    """High-level user intentions."""

    SEARCH = "search"
    RENAME = "rename"
    MOVE = "move"
    COPY = "copy"
    DELETE = "delete"
    CREATE = "create"
    READ = "read"
    WRITE = "write"
    ORGANIZE = "organize"
    GIT = "git"
    PROJECT = "project"
    INSTALL = "install"
    EXECUTE = "execute"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


class IntentStatus(str, Enum):
    """Lifecycle of an interpreted intent."""

    RECEIVED = "received"
    PARSED = "parsed"
    VALIDATED = "validated"
    RESOLVED = "resolved"
    READY = "ready"
    FAILED = "failed"


class EntityType(str, Enum):
    """Types of entities extracted from a user's request."""

    FILE = "file"
    DIRECTORY = "directory"
    PATH = "path"
    FILE_EXTENSION = "file_extension"
    PROJECT = "project"
    TEMPLATE = "template"
    GIT_REPOSITORY = "git_repository"
    COMMAND = "command"
    PATTERN = "pattern"
    TEXT = "text"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """
    Human-readable confidence levels.

    The numeric confidence score will still be stored separately
    (for example: 0.93), but this enum allows the UI and planner
    to make quick decisions.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ClarificationReason(str, Enum):
    """Reasons why the assistant needs more information."""

    MISSING_PATH = "missing_path"
    MULTIPLE_MATCHES = "multiple_matches"
    MISSING_FILENAME = "missing_filename"
    MISSING_DESTINATION = "missing_destination"
    AMBIGUOUS_COMMAND = "ambiguous_command"
    LOW_CONFIDENCE = "low_confidence"
    PERMISSION_REQUIRED = "permission_required"
    UNKNOWN = "unknown"