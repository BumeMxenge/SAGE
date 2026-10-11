# App factory: builds the FastAPI app, adds middleware and mounts routers
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from sage.api import problems
from sage.api.routes import health
from sage.config import get_settings
from sage.domain.errors import InternalError


def operation_id(route: APIRoute) -> str:
    # The route function's name in camelCase (get_plan becomes getPlan), for /docs and the
    # generated TypeScript
    first, *rest = route.name.split("_")
    return first + "".join(word.capitalize() for word in rest)


def create_app() -> FastAPI:
    settings = get_settings()
    # The version comes from pyproject.toml, so it lives in one place
    app = FastAPI(
        title="SAGE",
        version=version("sage-backend"),
        generate_unique_id_function=operation_id,
        responses=problems.errors(InternalError),  # any route can fail unexpectedly
    )
    problems.install(app)

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
