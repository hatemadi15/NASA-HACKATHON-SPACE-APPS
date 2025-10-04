"""Standalone FastAPI app for serving the static simulator frontend."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def _resolve_frontend_root() -> Path:
    """Return the directory containing the bundled frontend assets."""
    return Path(__file__).resolve().parent.parent


FRONTEND_ROOT = _resolve_frontend_root()
INDEX_FILE = FRONTEND_ROOT / "index.html"

if not INDEX_FILE.exists():
    raise RuntimeError(
        f"Frontend index.html not found. Expected it at {INDEX_FILE}"
    )

app = FastAPI(
    title="Meteor Simulator Frontend",
    description="Static asset server for the Meteor Madness simulator UI.",
    version="1.0.0",
)

app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_ROOT), html=True),
    name="frontend",
)


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    import uvicorn

    uvicorn.run("app.frontend:app", host="0.0.0.0", port=4173, reload=False)
