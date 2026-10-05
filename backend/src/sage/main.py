# App factory: builds the FastAPI app and mounts routers
from fastapi import FastAPI

from sage.api.routes import health


def create_app() -> FastAPI:
    app = FastAPI(title="SAGE", version="0.1.0")
    app.include_router(health.router)
    return app


app = create_app()
