import json
import subprocess
from pathlib import Path


class ProjectTemplatesTool:
    def create_project(self, project_type: str, project_name: str, location: Path) -> Path:
        project_dir = location / project_name
        if project_dir.exists():
            raise FileExistsError(f"Directory already exists: {project_dir}")

        project_dir.mkdir(parents=True, exist_ok=True)

        if project_type == "react":
            try:
                subprocess.run(
                    ["npx", "-y", "create-vite@latest", project_name, "--template", "react-ts"],
                    cwd=str(location),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except Exception:
                # Fallback: create files manually if npx/vite is not available
                self._scaffold_react_fallback(project_dir, project_name)
        elif project_type == "django":
            try:
                subprocess.run(
                    ["django-admin", "startproject", project_name, "."],
                    cwd=str(project_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except Exception:
                # Fallback: scaffold minimal Django structure
                self._scaffold_django_fallback(project_dir, project_name)
        elif project_type == "node":
            self._scaffold_node(project_dir, project_name)

        return project_dir

    def initialize_git(self, project_path: Path) -> None:
        if not project_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {project_path}")
        subprocess.run(
            ["git", "init"],
            cwd=str(project_path),
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def install_dependencies(self, project_path: Path, package_manager: str) -> None:
        if not project_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {project_path}")

        if package_manager == "npm":
            subprocess.run(
                ["npm", "install"],
                cwd=str(project_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        elif package_manager == "pip":
            # Check if venv exists, if not create it
            venv_dir = project_path / "venv"
            if not venv_dir.exists():
                subprocess.run(
                    ["python3", "-m", "venv", "venv"],
                    cwd=str(project_path),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            # Find pip
            pip_executable = venv_dir / "bin" / "pip"
            if not pip_executable.exists():
                pip_executable = venv_dir / "Scripts" / "pip.exe"

            req_file = project_path / "requirements.txt"
            if req_file.exists():
                subprocess.run(
                    [str(pip_executable), "install", "-r", "requirements.txt"],
                    cwd=str(project_path),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            else:
                subprocess.run(
                    [str(pip_executable), "install", "django"],
                    cwd=str(project_path),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

    def create_readme(self, project_path: Path, content: str) -> Path:
        if not project_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {project_path}")
        readme_path = project_path / "README.md"
        readme_path.write_text(content, encoding="utf-8")
        return readme_path

    def _scaffold_react_fallback(self, project_dir: Path, name: str) -> None:
        (project_dir / "src").mkdir(exist_ok=True)
        (project_dir / "public").mkdir(exist_ok=True)

        pkg_json = {
            "name": name,
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
            },
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
            },
            "devDependencies": {
                "vite": "^5.3.1",
            },
        }
        with open(project_dir / "package.json", "w") as f:
            json.dump(pkg_json, f, indent=2)

        (project_dir / "index.html").write_text(
            f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
            encoding="utf-8",
        )

        (project_dir / "src" / "main.tsx").write_text(
            """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
            encoding="utf-8",
        )

        (project_dir / "src" / "App.tsx").write_text(
            """import React from 'react'
function App() {
  return (
    <div>
      <h1>Welcome to React TS Fallback</h1>
    </div>
  )
}
export default App
""",
            encoding="utf-8",
        )

    def _scaffold_django_fallback(self, project_dir: Path, name: str) -> None:
        inner_dir = project_dir / name
        inner_dir.mkdir(exist_ok=True)

        (project_dir / "manage.py").write_text(
            f"""#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{name}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
""",
            encoding="utf-8",
        )

        (inner_dir / "__init__.py").write_text("", encoding="utf-8")
        (inner_dir / "wsgi.py").write_text(
            f"""import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{name}.settings')
application = get_wsgi_application()
""",
            encoding="utf-8",
        )

        (inner_dir / "settings.py").write_text(
            f"""
DEBUG = True
ALLOWED_HOSTS = []
SECRET_KEY = 'fallback-secret-key'
ROOT_URLCONF = '{name}.urls'
""",
            encoding="utf-8",
        )

        (inner_dir / "urls.py").write_text(
            """from django.urls import path
urlpatterns = []
""",
            encoding="utf-8",
        )

    def _scaffold_node(self, project_dir: Path, name: str) -> None:
        pkg_json = {"name": name, "version": "1.0.0", "main": "index.js", "dependencies": {"express": "^4.19.2"}}
        with open(project_dir / "package.json", "w") as f:
            json.dump(pkg_json, f, indent=2)

        (project_dir / "index.js").write_text(
            """const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.send('Hello World from Node/Express!');
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
""",
            encoding="utf-8",
        )
