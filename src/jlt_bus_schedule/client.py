"""Client for the JLT (Jönköpings Länstrafik) departure board.

JLT has no public JSON API for departures, so this scrapes the HTML fragment
used by the departure board on jlt.se, and the stop search of the travel
planner that jlt.se embeds from etiscloud.net.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime
import random
from types import TracebackType
from typing import Self

import aiohttp

from .const import API_URL, JLT_TIMEZONE, STOP_SEARCH_URL, USER_AGENTS
from .exceptions import JltConnectionError
from .models import Departure, Stop
from .parser import parse_departures, parse_stops


class JltApiClient:
    """Fetch departures and stops from JLT.

    Pass an existing aiohttp session to share it with the rest of the
    application. Without one, the client creates its own session, which is
    closed by close() or when leaving an ``async with`` block.

    Each request uses a User-Agent picked at random from USER_AGENTS, unless
    a fixed ``user_agent`` is given.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._close_session = False
        self._user_agent = user_agent

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the session if it was created by the client."""
        await self.close()

    async def close(self) -> None:
        """Close the session if it was created by the client."""
        if self._session and self._close_session:
            await self._session.close()
            self._session = None
            self._close_session = False

    async def _async_get(
        self, url: str, params: dict[str, str | int], timeout: float
    ) -> str:
        """Fetch a URL and return the response body."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(timeout):
                async with self._session.get(
                    url,
                    params=params,
                    headers={
                        "User-Agent": self._user_agent or random.choice(USER_AGENTS)
                    },
                ) as response:
                    response.raise_for_status()
                    return await response.text()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise JltConnectionError(f"Error fetching {url}: {err}") from err

    async def async_get_departures(
        self, stop_id: int, take: int = 20, timeout: float = 10
    ) -> list[Departure]:
        """Return upcoming departures for all lines at a stop."""
        html = await self._async_get(
            API_URL, {"fromId": stop_id, "take": take}, timeout
        )
        return parse_departures(html, datetime.now(JLT_TIMEZONE))

    async def async_search_stops(self, query: str, timeout: float = 10) -> list[Stop]:
        """Return stops matching a name, best match first."""
        html = await self._async_get(
            STOP_SEARCH_URL,
            {"fld": "input-from_ajax", "letters": query, "optType": 0},
            timeout,
        )
        return parse_stops(html)
