"""FinAlly backend — FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.market.seed_prices import SEED_PRICES
from app.routers.chat import create_chat_router
from app.routers.portfolio import create_portfolio_router
from app.routers.watchlist import create_watchlist_router
from app.snapshots import snapshot_loop

# Load .env from project root (one level above backend/)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

# Shared state
price_cache = PriceCache()
market_source = create_market_data_source(price_cache)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Initialize database
    await init_db()

    # Start market data
    default_tickers = list(SEED_PRICES.keys())
    await market_source.start(default_tickers)

    # Start portfolio snapshot background task (every 30s)
    snapshot_task = asyncio.create_task(snapshot_loop(price_cache))

    yield

    # Shutdown
    snapshot_task.cancel()
    try:
        await snapshot_task
    except asyncio.CancelledError:
        pass
    await market_source.stop()


app = FastAPI(title="FinAlly", version="0.1.0", lifespan=lifespan)

# --- Routers ---
stream_router = create_stream_router(price_cache)
app.include_router(stream_router)

chat_router = create_chat_router(price_cache)
app.include_router(chat_router)

portfolio_router = create_portfolio_router(price_cache)
app.include_router(portfolio_router)

watchlist_router = create_watchlist_router(price_cache)
app.include_router(watchlist_router)


# --- Health check ---
@app.get("/api/health")
async def health():
    return {"status": "ok"}


# --- Static file serving (Next.js export) ---
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
