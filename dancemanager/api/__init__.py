"""FastAPI application factory for Dance Manager web UI."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dancemanager import __version__
import dancemanager.web.main as web_module
from dancemanager.web.main import router as web_app
from pathlib import Path

# Import routers to register them
from dancemanager.api.routes import (
    dancers_router as dancers,
    teams_router as teams,
    classes_router as classes,
    instructors_router as instructors,
    dances_router as dances,
    recitals_router as recitals,
    import_export_router as import_export,
)

# Path to static files (created if missing)
_STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "templates" / "static"


def _ensure_static_dir():
    _STATIC_DIR.mkdir(parents=True, exist_ok=True)


def create_app():
    """Create and configure the FastAPI application."""
    _ensure_static_dir()

    app = FastAPI(
        title="Dance Manager",
        description="Web interface for Dance Manager",
        version=__version__,
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Mount web routes (HTML views)
    app.include_router(web_app)

    # Mount API routes — routes already have /api/ prefix in decorators
    app.include_router(dancers)
    app.include_router(teams)
    app.include_router(classes)
    app.include_router(instructors)
    app.include_router(dances)
    app.include_router(recitals)
    app.include_router(import_export)

    return app
