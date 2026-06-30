from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai import router as ai_router
from app.api.routes.ai_stream import router as ai_stream_router
from app.api.routes.auth import router as auth_router
from app.api.routes.billing import router as billing_router
from app.api.routes.chat_history import router as chat_history_router
from app.api.routes.health import router as health_router
from app.api.routes.observability import router as observability_router
from app.api.routes.providers import router as providers_router
from app.api.routes.users import router as users_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.metrics import metrics_middleware


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        description="SaaS AI Backend with API Key Authentication, usage logging, and dashboard support.",
        version=settings.APP_VERSION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(metrics_middleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(billing_router, prefix="/billing", tags=["Billing"])
    app.include_router(observability_router, prefix="/observability", tags=["Observability"])
    app.include_router(ai_router, prefix="/v1", tags=["AI"])
    app.include_router(ai_stream_router, prefix="/v1", tags=["AI"])
    app.include_router(providers_router, prefix="/v1", tags=["AI Gateway"])
    app.include_router(users_router, prefix="/users", tags=["Users"])
    app.include_router(chat_history_router, prefix="/chat", tags=["Chat History"])

    @app.get("/", tags=["Health"])
    def root():
        return {
            "status": "running",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


app = create_app()
