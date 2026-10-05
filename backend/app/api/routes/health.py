from fastapi import APIRouter

from app.api.deps import DatabaseDep, ProviderDep, SettingsDep
from app.schemas.analysis import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def health(settings: SettingsDep, db: DatabaseDep, provider: ProviderDep) -> HealthResponse:
    db_ok = db.ping()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=settings.app_version,
        environment=settings.app_env,
        database="ok" if db_ok else "error",
        llm_provider=provider.name,
        llm_model=provider.model,
        max_upload_size_mb=settings.max_upload_size_mb,
    )
