# App factory: builds the FastAPI app and mounts routers
from importlib.metadata import version

from fastapi import FastAPI

from sage.api.routes import health


def create_app() -> FastAPI:
    # The version comes from pyproject.toml, so it lives in one place
    app = FastAPI(title="SAGE", version=version("sage-backend"))
    app.include_router(health.router)
    return app


app = create_app()
