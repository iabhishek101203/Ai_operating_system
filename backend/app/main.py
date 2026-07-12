from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router


app = FastAPI(
    title="AI Operating System Assistant",
    description="Safety-first backend for natural language operating system workflows.",
    version="0.1.0",
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


frontend_directory = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
