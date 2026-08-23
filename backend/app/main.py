from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.modules.webhooks.router import webhook_router
from app.modules.payments.router import payment_router
from app.modules.recovery.router import recovery_router
from app.intelligence.router import intelligence_router

setup_logging()

app = FastAPI(
    title="RecoverX API",
    description="Autonomous AI Revenue Recovery Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(payment_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(recovery_router, prefix="/api/v1/recovery", tags=["recovery"])
app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
