# AI OS Assistant - Backend

FastAPI backend for the AI Operating System Assistant. It enforces a strict safety pipeline:
```text
natural language -> Gemini plan -> structured intent -> validation -> preview -> confirmation -> execution -> log -> undo
```

## Setup & Running

1. **Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Server**:
   ```bash
   .venv/bin/uvicorn app.main:app --reload
   ```
   Open `http://127.0.0.1:8000` to see the served UI.
   Open `http://127.0.0.1:8000/docs` to view the API Swagger docs.

3. **Running Tests**:
   ```bash
   .venv/bin/pytest
   ```

## Design Principles
- **No Raw Shell Invocations**: All tools are implemented safely in native Python code.
- **Allowed Roots**: Operations are restricted to directories specified in settings (e.g. `AIOS_ALLOWED_ROOTS`).
- **Conflict-aware Undo**: Reversible operations (rename, move, organize, template scaffolds) store metadata in SQLite for safe, conflict-aware rollback.
