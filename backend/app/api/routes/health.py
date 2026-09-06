from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    """Liveness plus non-secret config flags (safe to expose publicly)."""
    settings = get_settings()
    supabase_configured = bool(
        settings.supabase_url.strip() and settings.supabase_service_role_key.strip()
    )
    llm_configured = bool(
        settings.gemini_api_key.strip()
        or settings.groq_api_key.strip()
        or settings.hf_token.strip()
    )
    return {
        "status": "ok",
        "service": settings.app_name,
        "supabase_configured": supabase_configured,
        "llm_configured": llm_configured,
        "llm_provider": settings.llm_provider,
        "hybrid_search": settings.hybrid_search,
        "multi_hop": settings.multi_hop,
    }
