# App factory: builds the FastAPI app, adds middleware and mounts routers
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sage.api.routes import health
from sage.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    # The version comes from pyproject.toml, so it lives in one place
    app = FastAPI(title="SAGE", version=version("sage-backend"))

    # A browser only lets a page from another address call this API if the API names that
    # address. The frontend will send its sign-in token in a header, not a cookie, so
    # credentials stay off.
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin for origin in origins if origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    return app


app = create_app()
