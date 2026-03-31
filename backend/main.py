"""FinAlly backend entry point."""

import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import get_watchlist_tickers, init_db
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.routers import health, portfolio
from app.routers.portfolio import record_snapshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared objects — created at module level so routers can be registered before lifespan
price_cache = PriceCache()
stream_router = create_stream_router(price_cache)


async def _snapshot_loop(app: FastAPI) -> None:
    """Record portfolio value every 30 seconds."""
    while True:
        try:
            await asyncio.sleep(30)
            record_snapshot(app.state.price_cache)
        except asyncio.CancelledError:
            break


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: DB init, market data start/stop, snapshot task."""
    logger.info("Starting FinAlly backend")
    init_db()
    tickers = get_watchlist_tickers()
    source = create_market_data_source(price_cache)
    await source.start(tickers)
    app.state.price_cache = price_cache
    app.state.source = source
    snapshot_task = asyncio.create_task(_snapshot_loop(app))
    logger.info("Market data started with %d tickers", len(tickers))
    yield
    logger.info("Shutting down")
    snapshot_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await snapshot_task
    await source.stop()


app = FastAPI(title="FinAlly API", lifespan=lifespan)

# API routers — registered before static mount
app.include_router(health.router, prefix="/api")
app.include_router(stream_router)
app.include_router(portfolio.router, prefix="/api")

# Static files — mount last; conditional on directory existing
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
