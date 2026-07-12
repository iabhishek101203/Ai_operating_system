# Architecture

## Goal

The AI Operating System Assistant lets users interact with their computer through natural language while keeping execution constrained, inspectable, and recoverable.

This project intentionally separates AI reasoning from system execution. The LLM may classify intent and produce structured JSON, but it must not directly produce shell commands or execute operating system actions.

## Core Pipeline

```text
Natural Language
-> Intent Understanding
-> Function Calling
-> Structured Intent
-> Validation
-> Dry-Run Preview
-> User Confirmation
-> Safe Tool Execution
-> Operation Logging
-> Undo Metadata
```

## Backend Layers

```text
api/
  FastAPI route handlers. Routes should be thin and delegate business logic.

core/
  Configuration, security policies, and shared application constants.

schemas/
  Pydantic request and response models for intents, previews, execution, and logs.

validators/
  Path validation, operation validation, and policy enforcement.

tools/
  Safe Python implementations of supported OS operations.

services/
  Application workflows that coordinate validation, preview, execution, and logging.

storage/
  Persistence layer for operation history and undo metadata.
```

## Design Rules

- API routes must not contain filesystem business logic.
- Tools must accept structured inputs, not raw natural language.
- Every mutating operation must support preview before execution.
- Every supported operation must have explicit validation.
- Dangerous locations and unsupported operations must fail closed.
- Operation logs should be detailed enough to support audit and undo.

## Initial Operation

The first supported operation is `search_files` because it is read-only and low-risk. It is useful for proving path validation, structured responses, preview flow, and test strategy.

The first mutating operation is `rename_file`. It adds a short-lived preview authorization that is bound to the exact structured intent and consumed once on execution. The resulting before/after effect summary and undo metadata are stored in SQLite. Undo is conflict-aware: it will not restore a previous name if that name is now occupied or the renamed file was modified after the original operation.
