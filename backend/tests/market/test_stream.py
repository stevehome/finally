"""Tests for SSE streaming endpoint."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import APIRouter

from app.market.cache import PriceCache
from app.market.stream import _generate_events, create_stream_router


def _make_request(disconnect_side_effects: list[bool]) -> MagicMock:
    """Build a mock Request whose is_disconnected() follows the given sequence."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.is_disconnected = AsyncMock(side_effect=disconnect_side_effects)
    return request


@pytest.mark.asyncio
class TestGenerateEvents:
    """Unit tests for the _generate_events async generator."""

    async def test_first_yield_is_retry_directive(self):
        """First yielded value must be the SSE retry directive."""
        cache = PriceCache()
        request = _make_request([True])  # Disconnect immediately after retry

        gen = _generate_events(cache, request, interval=0.01)
        first = await gen.__anext__()
        assert first == "retry: 1000\n\n"
        await gen.aclose()

    async def test_stops_on_immediate_disconnect(self):
        """Generator stops after the retry directive when client is already disconnected."""
        cache = PriceCache()
        cache.update("AAPL", 190.50)
        request = _make_request([True])

        events = []
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)

        assert events == ["retry: 1000\n\n"]

    async def test_yields_price_data_event(self):
        """After the retry directive, yields a data event with current prices."""
        cache = PriceCache()
        cache.update("AAPL", 190.50)
        request = _make_request([False, True])  # One loop, then disconnect

        events = []
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)

        assert events[0] == "retry: 1000\n\n"
        data_events = [e for e in events if e.startswith("data: ")]
        assert len(data_events) == 1

    async def test_event_json_structure(self):
        """Data events contain all required PriceUpdate fields."""
        cache = PriceCache()
        cache.update("AAPL", 190.50)
        request = _make_request([False, True])

        events = []
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)

        data_event = next(e for e in events if e.startswith("data: "))
        payload = json.loads(data_event[len("data: "):].strip())
        assert "AAPL" in payload
        ticker_data = payload["AAPL"]
        for key in ("ticker", "price", "previous_price", "timestamp", "change", "change_percent", "direction"):
            assert key in ticker_data, f"Missing key: {key}"
        assert ticker_data["price"] == 190.50

    async def test_multiple_tickers_in_event(self):
        """Data event contains all tickers present in the cache."""
        cache = PriceCache()
        cache.update("AAPL", 190.50)
        cache.update("GOOGL", 175.00)
        cache.update("TSLA", 250.00)
        request = _make_request([False, True])

        events = []
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)

        data_event = next(e for e in events if e.startswith("data: "))
        payload = json.loads(data_event[len("data: "):].strip())
        assert set(payload.keys()) == {"AAPL", "GOOGL", "TSLA"}

    async def test_no_data_event_when_cache_empty(self):
        """No data event is yielded when the cache is empty."""
        cache = PriceCache()
        request = _make_request([False, True])

        events = []
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)

        data_events = [e for e in events if e.startswith("data: ")]
        assert len(data_events) == 0

    async def test_no_duplicate_event_when_version_unchanged(self):
        """A second loop iteration does not yield a new event if prices haven't changed."""
        cache = PriceCache()
        cache.update("AAPL", 190.50)
        # Three loops: first produces event, second/third do not (version unchanged)
        request = _make_request([False, False, False, True])

        events = []
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)

        data_events = [e for e in events if e.startswith("data: ")]
        assert len(data_events) == 1  # Only one event despite multiple loops

    async def test_new_event_on_version_change(self):
        """A new data event is yielded when prices update between loop iterations."""
        cache = PriceCache()
        cache.update("AAPL", 190.50)

        call_count = 0

        async def disconnect_after_second_data():
            nonlocal call_count
            call_count += 1
            # Stay connected for the first 3 is_disconnected calls, then disconnect
            return call_count > 3

        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.is_disconnected = AsyncMock(side_effect=disconnect_after_second_data)

        events = []
        event_count = 0
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)
            event_count += 1
            # After the first data event, update the price to bump the version
            if event_count == 2:
                cache.update("AAPL", 195.00)

        data_events = [e for e in events if e.startswith("data: ")]
        assert len(data_events) >= 2


class TestCreateStreamRouter:
    """Tests for the create_stream_router factory."""

    def test_returns_api_router(self):
        """Should return a FastAPI APIRouter instance."""
        cache = PriceCache()
        router = create_stream_router(cache)
        assert isinstance(router, APIRouter)

    def test_creates_fresh_router_each_call(self):
        """Each call returns a distinct router — no shared state."""
        cache = PriceCache()
        router1 = create_stream_router(cache)
        router2 = create_stream_router(cache)
        assert router1 is not router2

    def test_router_has_prices_route(self):
        """Router must have a /prices GET route registered."""
        cache = PriceCache()
        router = create_stream_router(cache)
        paths = [r.path for r in router.routes]
        # FastAPI includes the router prefix in the route path
        assert "/api/stream/prices" in paths

    def test_router_prefix(self):
        """Router prefix should be /api/stream."""
        cache = PriceCache()
        router = create_stream_router(cache)
        assert router.prefix == "/api/stream"
