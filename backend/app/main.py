from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.advisor import router as advisor_router
from app.api.routes.health import router as health_router
from app.api.ws.chat import router as chat_ws_router
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)

# Avoid TensorFlow import side-effects from sentence-transformers/transformers
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Warm embedding model so the first chat is not a multi-minute load
    try:
        from app.services.embeddings import embed_text

        embed_text("warmup")
        logger.info("Embedding model warmed up")
    except Exception:
        logger.exception("Embedding warmup failed (first chat may be slow)")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "FastAPI backend for the Shire of Plantagenet AI Planning Advisor. "
            "Exposes REST health checks and a chat WebSocket compatible with the Next.js client."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(advisor_router)
    app.include_router(chat_ws_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "health": "/health",
            "chat_ws": "/ws/chat",
        }

    return app


app = create_app()
