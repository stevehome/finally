"""Health check endpoint."""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    """Return service health status."""
    return {"status": "ok", "db": "ok", "market_data": "running"}
