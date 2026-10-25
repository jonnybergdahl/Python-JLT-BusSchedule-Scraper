"""Fixtures for the JLT client tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestServer
import pytest

from jlt_bus_schedule import JLT_TIMEZONE, client

FIXTURES = Path(__file__).parent / "fixtures"

STOP_ID = 6001350
DESTINATION = "Huskvarna via Centrum-Elmia"

# Time used for tests with a frozen clock
NOW = datetime(2026, 10, 25, 11, 40, tzinfo=JLT_TIMEZONE)

DEPARTURES_PATH = "/departures"
STOP_SEARCH_PATH = "/stops"


@dataclass
class MockJlt:
    """Responses and recorded requests of the mock JLT server."""

    body: str = ""
    status: int = 200
    delay: float = 0
    requests: list[web.Request] = field(default_factory=list)


@pytest.fixture
async def mock_jlt(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[MockJlt]:
    """Run a local server and point the client to it instead of jlt.se."""
    mock = MockJlt()

    async def handler(request: web.Request) -> web.Response:
        mock.requests.append(request)
        await asyncio.sleep(mock.delay)
        return web.Response(text=mock.body, status=mock.status)

    app = web.Application()
    app.router.add_get(DEPARTURES_PATH, handler)
    app.router.add_get(STOP_SEARCH_PATH, handler)

    async with TestServer(app) as server:
        monkeypatch.setattr(client, "API_URL", str(server.make_url(DEPARTURES_PATH)))
        monkeypatch.setattr(
            client, "STOP_SEARCH_URL", str(server.make_url(STOP_SEARCH_PATH))
        )
        yield mock


def load_fixture(name: str) -> str:
    """Load a fixture file."""
    return (FIXTURES / name).read_text(encoding="utf-8")


def make_html(*suggestions: tuple[str, str, str]) -> str:
    """Build a departure board fragment from (line, time text, direction)."""
    return "\n".join(
        f"""
    <div class="travel-suggestion">
        <a class="info" href="/res-med-oss/linjer-hallplatser/linje/?id={line}">
            <p>
                {time_text}
            </p>
            <div class="destination">
                <div class="line-info-area">
                    <div class="icon-shape number"><div><span class="text">S</span></div></div>
                    <div class="icon-shape line-info"><span class="text">{line}</span></div>
                </div>
                <div class="direction">
                    {direction}
                </div>
            </div>
        </a>
    </div>"""
        for line, time_text, direction in suggestions
    )
