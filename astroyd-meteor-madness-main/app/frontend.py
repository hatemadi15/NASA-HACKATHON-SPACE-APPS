"""Standalone FastAPI app for serving the static simulator frontend."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def _resolve_frontend_root() -> Path:
    """Return the directory containing the bundled frontend assets."""
    project_root = Path(__file__).resolve().parent.parent
    return project_root


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

# Expose the entire frontend directory so supporting JS/CSS assets resolve.
app.mount(
    "/assets",
    StaticFiles(directory=str(FRONTEND_ROOT)),
    name="assets",
)


@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the main simulator HTML page."""
    return FileResponse(INDEX_FILE)


@app.get("/{asset_path:path}")
async def serve_static_asset(asset_path: str) -> FileResponse:
    """Serve additional JS/CSS assets bundled with the simulator."""
    candidate = (FRONTEND_ROOT / asset_path).resolve()

    # Prevent directory traversal and ensure the file lives under the frontend root.
    try:
        candidate.relative_to(FRONTEND_ROOT)
    except ValueError as exc:  # pragma: no cover - safety guard
        raise HTTPException(status_code=404, detail="Asset not found") from exc

    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(candidate)


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    import uvicorn

    uvicorn.run("app.frontend:app", host="0.0.0.0", port=4173, reload=False)
