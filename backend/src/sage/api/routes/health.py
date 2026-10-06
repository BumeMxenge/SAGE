# Liveness check for Azure Container Apps and quick smoke tests.
# Also reports the running commit, so a deploy can confirm its new version is the one answering.
from typing import Annotated

from fastapi import APIRouter, Depends

from sage.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    return {"status": "ok", "commit": settings.git_sha}
