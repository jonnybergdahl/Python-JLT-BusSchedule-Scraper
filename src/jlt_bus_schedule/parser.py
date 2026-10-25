"""Parsers for the HTML fragments returned by JLT."""

from __future__ import annotations

from datetime import datetime, timedelta
import re

from bs4 import BeautifulSoup

from .models import Departure, Stop

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")
_DEPARTED_TEXT = "Har avgått"


def _clean(text: str) -> str:
    """Collapse all whitespace runs into single spaces."""
    return " ".join(text.split())


def parse_departures(html: str, now: datetime) -> list[Departure]:
    """Parse the departure board HTML fragment.

    The fragment only contains clock times, so ``now`` is used to place each
    departure on the right date. It should be a timezone aware datetime in
    JLT_TIMEZONE.
    """
    soup = BeautifulSoup(html, "html.parser")
    departures: list[Departure] = []

    for suggestion in soup.select("div.travel-suggestion"):
        direction_el = suggestion.select_one("div.direction")
        line_el = suggestion.select_one("div.line-info span")
        time_el = suggestion.select_one("p")
        if not direction_el or not line_el or not time_el:
            continue

        # Direction is shown as "mot <destination>"
        direction = _clean(direction_el.get_text(" ", strip=True))
        destination = (
            direction[4:] if direction.lower().startswith("mot ") else direction
        )

        # Time is shown as "12:34 (Avgår om 5 min)" or "Har avgått"
        raw = _clean(time_el.get_text(" ", strip=True))
        if _DEPARTED_TEXT in raw:
            continue
        match = _TIME_RE.match(raw)
        if not match:
            continue

        departure = now.replace(
            hour=int(match.group(1)),
            minute=int(match.group(2)),
            second=0,
            microsecond=0,
        )
        # Departures after midnight belong to the next day
        if departure < now - timedelta(hours=1):
            departure += timedelta(days=1)

        departures.append(
            Departure(
                line=line_el.get_text(strip=True),
                destination=destination,
                direction=direction,
                departure=departure,
                time_to_departure=raw[match.end() :].strip(" ()"),
            )
        )

    return departures


def parse_stops(html: str) -> list[Stop]:
    """Parse the stop search result HTML fragment."""
    soup = BeautifulSoup(html, "html.parser")
    stops: list[Stop] = []

    for option in soup.select("li.travel-option[data-id]"):
        # The data-id attribute is "<name>|<stop id>|<type>"
        name, _, rest = str(option["data-id"]).partition("|")
        stop_id = rest.partition("|")[0]
        if not stop_id.isdigit():
            continue
        stop = Stop(id=int(stop_id), name=_clean(name))
        if stop not in stops:
            stops.append(stop)

    return stops
