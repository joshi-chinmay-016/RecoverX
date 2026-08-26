from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import SecurityHeadersMiddleware, LoginRateLimiterMiddleware
from app.db.session import SessionLocal
from app.auth.router import router as auth_router
from app.modules.webhooks.router import webhook_router
from app.modules.payments.router import payment_router
from app.modules.recovery.router import recovery_router
from app.intelligence.router import intelligence_router
from app.agent.router import agent_router
from app.execution.router import router as execution_router
from app.learning.router import router as learning_router

setup_logging()
logger = get_logger("recoverx.main")

app = FastAPI(
    title="RecoverX API",
    description="Multi-Tenant Adaptive AI Revenue Recovery Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 1. Production Security Middleware (Inner)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    LoginRateLimiterMiddleware,
    max_attempts=settings.login_rate_limit_attempts,
    window_seconds=settings.login_rate_limit_window_seconds,
)

# 2. CORS Middleware (Outermost - intercepts all requests & handles preflight OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure unhandled exceptions return valid JSON with CORS headers."""
    logger.error(f"unhandled_exception path={request.url.path} error={str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "error": "INTERNAL_SERVER_ERROR"},
    )


# 3. Router Inclusions
app.include_router(auth_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(payment_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(recovery_router, prefix="/api/v1/recovery", tags=["recovery"])
app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(execution_router, prefix="/api/v1")
app.include_router(learning_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    """Liveness probe."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "platform": "RecoverX Enterprise Multi-Tenant",
    }


@app.get("/api/v1/readiness")
async def readiness_check():
    """Readiness probe checking database connectivity."""
    db_status = "unknown"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"degraded: {str(e)[:50]}"

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "security": "active",
    }
