# App factory: builds the FastAPI app, adds middleware and mounts routers
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from sage.api.routes import (
    chats,
    electives,
    health,
    history,
    me,
    onboarding,
    plans,
    questionnaire,
)
from sage.config import get_settings
from sage.engine.stubs import FixedAdvisor, InterimEligibility, SeededPlanGenerator
from sage.shared.api import problems
from sage.shared.errors import InternalError
from sage.shared.rulebook import Rulebook
from sage.shared.seed import SEED_FILE
from sage.shared.supabase.auth import SupabaseTokenVerifier
from sage.shared.supabase.client import connect
from sage.shared.supabase.rules import SupabaseRuleRepository
from sage.shared.supabase.students import SupabaseStudentRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Builds what every request shares, once. A missing setting stops the app here, loudly, rather
    # than failing every request. Unit tests run this only to check startup fails; the rest hand
    # the routes fakes instead.
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SECRET_KEY. make dev takes them from local Supabase, "
            "and the deploy sets them on Azure."
        )
    # Said at every start, so a test window's setting is never left on unnoticed
    if settings.accept_email_sign_in:
        logger.warning(
            "ACCEPT_EMAIL_SIGN_IN is on, so email-provider accounts can sign in. "
            "Switch it off when the test window ends."
        )
    # The plan stand-in reads its seed file now, so a wrong path in the image fails the deploy's
    # health check rather than the first onboarding
    app.state.plan_generator = SeededPlanGenerator(SEED_FILE)
    app.state.eligibility_checker = InterimEligibility()
    app.state.advisor = FixedAdvisor()
    client = connect(settings.supabase_url, settings.supabase_secret_key)
    app.state.verifier = SupabaseTokenVerifier(
        client, accept_email=settings.email_sign_in
    )
    app.state.rulebook = Rulebook(SupabaseRuleRepository(client))
    app.state.students = SupabaseStudentRepository(client)
    yield


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
        lifespan=lifespan,
        generate_unique_id_function=operation_id,
        responses=problems.errors(InternalError),  # any route can fail unexpectedly
    )
    problems.install(app)

    # A browser only lets a page from another address call this API if the API names that
    # address. The frontend sends its sign-in token in a header, not a cookie, so credentials
    # stay off.
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin for origin in origins if origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # /health stays at the root, where Azure checks it. Everything a student uses is versioned.
    app.include_router(health.router)
    for area in (me, onboarding, plans, questionnaire, electives, history, chats):
        app.include_router(area.router, prefix="/v1")
    return app


app = create_app()
