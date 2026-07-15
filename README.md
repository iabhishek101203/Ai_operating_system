# AI Operating System Assistant

A secure, safe AI-powered natural language interface for Operating System tasks using constrained tool calling. 

Rather than allowing the LLM to generate and execute arbitrary shell commands (which introduces prompt injection, hallucination, and destructive risks), this system translates user requests into structured, validated execution plans (predefined tool calls). Every workflow passes through path validation, dry-run preview, explicit user confirmation, safe Python tool execution, operations logging, and reversible rollback (undo).

## System Pipeline

```text
Natural Language Instruction
-> Gemini AI Planner (Structured JSON)
-> Pydantic Parameter Validation
-> Path Validation (Within Allowed Roots)
-> Dry-Run Preview
-> Explicit User Confirmation
-> Safe Python Tool Execution (No raw shell)
-> Durable SQLite Logging
-> Reversible Undo (Rollback)
```

## Supported OS Tools

- **File Search (`search_files`)**: Safe read-only file search.
- **Rename File (`rename_file`)**: Renames files inside allowed directories [Undoable].
- **Move File (`move_file`)**: Moves files safely to another directory [Undoable].
- **Delete File (`delete_file`)**: Sends files/directories to the system recycle bin via `send2trash` [Safety guardrail].
- **Organize Folder (`organize_folder`)**: Categorizes immediate files into subfolders based on extensions (Documents, Code, Images, Audio, Video, Archives) [Undoable].
- **Find Duplicates (`find_duplicates`)**: Finds duplicate files recursively by matching SHA256 content hashes.
- **Scaffold Project (`create_project`)**: Prepares React, Django, or Node.js project skeletons securely. Sanitizes names and runs hardcoded command templates with safe offline scaffolds.
- **Initialize Git (`initialize_git`)**: Sets up local git workspace.
- **Install Dependencies (`install_dependencies`)**: Securely executes `npm install` or pip environment installs.
- **Create README (`create_readme`)**: Scaffolds markdown index files [Undoable].

---

## Getting Started

### 1. Backend Setup & Run
Configure Python and start the API server:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Frontend Development & Build
The frontend is built with React + Vite + TypeScript + Tailwind CSS.

- **Start Dev Server**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  *(Vite is preconfigured to proxy `/api` requests to the FastAPI server on port 8000).*

- **Build Production Assets**:
  ```bash
  cd frontend
  npm run build
  ```
  *(Vite compiles and saves the production asset bundles directly to `backend/frontend/` so that FastAPI serves the UI automatically at `http://127.0.0.1:8000/`).*

### 3. Settings Configuration
Open `http://127.0.0.1:8000/` and click the **Settings icon** in the top right to configure:
- **Allowed Roots**: Absolute directory paths where the assistant is authorized to perform actions.
- **Gemini API Key**: Your Gemini API Key (stored locally in browser localStorage and sent securely in headers, or read from `GEMINI_API_KEY` env var).
- **Gemini Model**: Choose between fast planning (`gemini-2.5-flash`) or advanced reasoning (`gemini-2.5-pro`).

---

## Verifying & Testing

A complete test suite covers path traversal guardrails, symlink checks, tool execution, scaffolds, mock AI plans, and transaction rollbacks.

Run the test suite from the `backend/` folder:
```bash
cd backend
.venv/bin/pytest
```
