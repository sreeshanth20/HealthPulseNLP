"""API v1 router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (admin, alerts, analytics, auth, complaints, documents,
                        intelligence, reports, users)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(complaints.router)
api_router.include_router(reports.router)
api_router.include_router(documents.router)
api_router.include_router(alerts.router)
api_router.include_router(intelligence.router)
api_router.include_router(analytics.router)
api_router.include_router(admin.router)
