"""Data models for the JLT client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Departure:
    """A single upcoming departure."""

    line: str
    destination: str
    direction: str
    departure: datetime
    time_to_departure: str

    @property
    def departure_time(self) -> str:
        """Return the departure time formatted as HH:MM."""
        return self.departure.strftime("%H:%M")


@dataclass(frozen=True, slots=True)
class Stop:
    """A bus stop."""

    id: int
    name: str
