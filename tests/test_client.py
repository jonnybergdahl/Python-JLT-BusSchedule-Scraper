"""Tests for the JLT client."""

from __future__ import annotations

from datetime import datetime, timedelta
import re

import aiohttp
import pytest

from jlt_bus_schedule import (
    API_URL,
    JLT_TIMEZONE,
    USER_AGENTS,
    JltApiClient,
    JltConnectionError,
    Stop,
    client,
)

from .conftest import STOP_ID, MockJlt, load_fixture


async def test_client_fetches_departures(mock_jlt: MockJlt) -> None:
    """Test fetching departures."""
    mock_jlt.body = load_fixture("departures_6001350.html")

    async with aiohttp.ClientSession() as session:
        departures = await JltApiClient(session).async_get_departures(STOP_ID, 20)

    assert len(departures) == 20
    assert len(mock_jlt.requests) == 1
    request = mock_jlt.requests[0]
    assert request.query == {"fromId": str(STOP_ID), "take": "20"}
    assert request.headers["User-Agent"] in USER_AGENTS


async def test_client_rotates_user_agent(
    mock_jlt: MockJlt, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that each request picks a new User-Agent from the pool."""
    picks = iter(USER_AGENTS[:2])
    monkeypatch.setattr(client.random, "choice", lambda _: next(picks))

    async with aiohttp.ClientSession() as session:
        jlt = JltApiClient(session)
        await jlt.async_get_departures(STOP_ID)
        await jlt.async_get_departures(STOP_ID)

    seen = [request.headers["User-Agent"] for request in mock_jlt.requests]
    assert seen == list(USER_AGENTS[:2])


async def test_client_custom_user_agent(mock_jlt: MockJlt) -> None:
    """Test that a custom User-Agent is sent."""
    async with aiohttp.ClientSession() as session:
        jlt = JltApiClient(session, user_agent="Test/1.0")
        assert await jlt.async_get_departures(STOP_ID) == []

    assert mock_jlt.requests[0].headers["User-Agent"] == "Test/1.0"


@pytest.mark.usefixtures("mock_jlt")
async def test_client_owns_session() -> None:
    """Test that a client without a session creates and closes its own."""
    async with JltApiClient() as jlt:
        await jlt.async_get_departures(STOP_ID)
        session = jlt._session  # noqa: SLF001
        assert session is not None

    assert session.closed
    assert jlt._session is None  # noqa: SLF001


@pytest.mark.usefixtures("mock_jlt")
async def test_client_keeps_external_session() -> None:
    """Test that a session passed to the client is not closed by it."""
    async with aiohttp.ClientSession() as session:
        async with JltApiClient(session) as jlt:
            await jlt.async_get_departures(STOP_ID)
        assert not session.closed


async def test_client_http_error(mock_jlt: MockJlt) -> None:
    """Test that an HTTP error status raises JltConnectionError."""
    mock_jlt.status = 500

    async with aiohttp.ClientSession() as session:
        with pytest.raises(JltConnectionError):
            await JltApiClient(session).async_get_departures(STOP_ID)


async def test_client_timeout(mock_jlt: MockJlt) -> None:
    """Test that a timeout raises JltConnectionError."""
    mock_jlt.delay = 1

    async with aiohttp.ClientSession() as session:
        with pytest.raises(JltConnectionError):
            await JltApiClient(session).async_get_departures(STOP_ID, timeout=0.1)


async def test_client_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a connection error raises JltConnectionError."""
    # Nothing listens on port 1
    monkeypatch.setattr(client, "API_URL", "http://127.0.0.1:1/departures")

    async with aiohttp.ClientSession() as session:
        with pytest.raises(JltConnectionError):
            await JltApiClient(session).async_get_departures(STOP_ID)


async def test_client_searches_stops(mock_jlt: MockJlt) -> None:
    """Test searching for stops."""
    mock_jlt.body = load_fixture("stop_search_jonkoping.html")

    async with aiohttp.ClientSession() as session:
        stops = await JltApiClient(session).async_search_stops("Jönköping")

    assert len(stops) == 12
    query = mock_jlt.requests[0].query
    assert query["letters"] == "Jönköping"
    assert query["optType"] == "0"


async def test_client_search_errors(mock_jlt: MockJlt) -> None:
    """Test that errors when searching raise JltConnectionError."""
    mock_jlt.status = 503

    async with aiohttp.ClientSession() as session:
        with pytest.raises(JltConnectionError):
            await JltApiClient(session).async_search_stops("Jönköping")


@pytest.mark.live
async def test_live_departures() -> None:
    """Test fetching and parsing departures from the live jlt.se site."""
    async with aiohttp.ClientSession() as session:
        # Check the raw response, so a markup change on jlt.se is detected even
        # if it makes the parser silently return nothing
        async with session.get(
            API_URL, params={"fromId": STOP_ID, "take": 20}
        ) as response:
            assert response.status == 200
            html = await response.text()

        departures = await JltApiClient(session).async_get_departures(STOP_ID, 20)

    assert html.count('class="travel-suggestion"') >= len(departures)
    if "travel-suggestion" in html and "Har avgått" not in html:
        assert departures, "jlt.se returned departures that could not be parsed"

    now = datetime.now(JLT_TIMEZONE)
    for departure in departures:
        assert departure.line
        assert departure.destination
        assert re.fullmatch(r"\d{2}:\d{2}", departure.departure_time)
        assert departure.time_to_departure.startswith("Avgår")
        assert now - timedelta(hours=1) <= departure.departure
        assert departure.departure <= now + timedelta(days=1)


@pytest.mark.live
async def test_live_stop_search() -> None:
    """Test searching for stops against the live JLT travel planner."""
    async with JltApiClient() as client:
        stops = await client.async_search_stops("Rådhusparken")
        # The stop IDs from the search must work with the departure board
        await client.async_get_departures(stops[0].id, 5)

    assert Stop(id=6001320, name="Jönköping Rådhusparken") in stops
