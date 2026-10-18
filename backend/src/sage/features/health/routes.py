# Liveness check for Azure Container Apps and quick smoke tests.
# Also reports the running commit, so a deploy can confirm its new version is the one answering.
from typing import Annotated

from fastapi import APIRouter, Depends

from sage.config import Settings, get_settings
from sage.features.health.models import Health

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check the backend is up, and which commit it runs")
async def get_health(settings: Annotated[Settings, Depends(get_settings)]) -> Health:
    return Health(status="ok", commit=settings.git_sha)
