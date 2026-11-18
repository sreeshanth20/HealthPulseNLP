"""HealthPulse AI FastAPI application entrypoint.

Run from backend/:  uvicorn app.main:app --reload --port 8000
Interactive docs:   http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # noqa: F401 - ensures all models register on Base
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.dependencies import get_current_user  # noqa: F401
from app.services.document_service import storage_root
from app.services.nlp_service import DISCLAIMER

logging.basicConfig(
    level=logging.INFO if not settings.is_production else logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("healthpulse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # dev convenience: create tables automatically outside production
    # (production uses `alembic upgrade head` via the Docker entrypoint)
    if not settings.is_production:
        Base.metadata.create_all(bind=engine)
        logger.info("Dev mode: Base.metadata.create_all executed")
    storage_root()
    logger.info("%s v%s starting (env=%s)", settings.app_name, settings.app_version,
                settings.environment)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Integrated Healthcare & Civic Intelligence Platform API.\n\n"
        "**Disclaimer:** association scores are statistical co-occurrence "
        "indicators — not diagnoses, not causal proof, not clinical risk "
        "probabilities."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()[0]["msg"] if exc.errors() else "Validation error",
                 "errors": exc.errors()[:5]},
    )


@app.get("/api/v1/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/api/v1/disclaimer", tags=["system"])
def disclaimer():
    return {"disclaimer": DISCLAIMER}
