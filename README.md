# Python-JLT-BusSchedule-Scraper
Python library that scrapes the JLT site for bus schedules. 

[JLT (Jönköpings Länstrafik)](https://www.jlt.se) has no public API for departures, so this
library scrapes the HTML fragment used by the departure board on jlt.se, and the stop search
of the travel planner that jlt.se embeds from etiscloud.net.

It is used by the [JLT Bus Schedule](https://github.com/jonnybergdahl/HomeAssistant_JltBusSchedule_Integration)
Home Assistant integration.

## Installation

```bash
pip install jlt-bus-schedule
```

Requires Python 3.11 or later.

## Usage

```python
import asyncio

from jlt_bus_schedule import JltApiClient


async def main() -> None:
    async with JltApiClient() as client:
        stops = await client.async_search_stops("Rådhusparken")
        stop = stops[0]
        print(f"{stop.name} ({stop.id})")

        for departure in await client.async_get_departures(stop.id, take=10):
            print(
                f"{departure.departure_time} {departure.line:>3} "
                f"{departure.destination} ({departure.time_to_departure})"
            )


asyncio.run(main())
```

```
Jönköping Rådhusparken (6001320)
13:20   3 Råslätt via Asecs-Ryhov (Avgår nu)
13:21 141 Sävsjö via Vrigstad (Avgår nu)
13:22   4 Huskvarna via Solåsen-Ryhov (Avgår om 1 min)
...
```

### Sharing an aiohttp session

Pass an existing `aiohttp.ClientSession` to share it with the rest of your application, as
Home Assistant integrations should. The client never closes a session it did not create.

```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession

client = JltApiClient(async_get_clientsession(hass))
```

Without a session the client creates its own, which is closed by `await client.close()` or when
leaving an `async with` block.

Each request uses a `User-Agent` picked at random from a pool of common desktop browsers
(`USER_AGENTS`). A fixed `User-Agent` header can be set with
`JltApiClient(session, user_agent="MyApp/1.0")`.

## API

### `JltApiClient`

| Method | Description |
|--------|-------------|
| `async_get_departures(stop_id, take=20, timeout=10)` | Upcoming departures for all lines at a stop, as a list of `Departure`. Departures that have already left are skipped, but JLT counts them in `take`, so fewer than `take` departures may be returned. |
| `async_search_stops(query, timeout=10)` | Stops matching a name, best match first, as a list of `Stop`. |
| `close()` | Close the session, if it was created by the client. |

Both methods raise `JltConnectionError` on HTTP errors, connection errors and timeouts. All
exceptions raised by the library inherit from `JltError`.

### `Departure`

| Attribute | Type | Example |
|-----------|------|---------|
| `line` | `str` | `"1"` |
| `destination` | `str` | `"Huskvarna via Centrum-Elmia"` |
| `direction` | `str` | `"mot Huskvarna via Centrum-Elmia"` |
| `departure` | `datetime` | Timezone aware, in `JLT_TIMEZONE` (Europe/Stockholm) |
| `departure_time` | `str` | `"11:41"` |
| `time_to_departure` | `str` | `"Avgår om 5 min"` |

### `Stop`

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | `int` | `6001320` |
| `name` | `str` | `"Jönköping Rådhusparken"` |

### Parsers

`parse_departures(html, now)` and `parse_stops(html)` parse the HTML fragments without doing
any network requests. `parse_departures` uses `now` to place the clock times on the right date,
so departures after midnight end up on the next day.

## Development

```bash
pip install -e ".[test]"
pytest
```

Tests marked `live` call the real jlt.se site to detect markup changes. Skip them with
`pytest -m "not live"`.

## Releasing

Releases are published to PyPI by the `Publish to PyPI` workflow when a GitHub release is
published, using [trusted publishing](https://docs.pypi.org/trusted-publishers/). Bump
`__version__` in `src/jlt_bus_schedule/const.py` before creating the release.
