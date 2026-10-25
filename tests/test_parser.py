"""Tests for the departure board and stop search parsers."""

from __future__ import annotations

from datetime import datetime

from jlt_bus_schedule import JLT_TIMEZONE, Stop, parse_departures, parse_stops

from .conftest import DESTINATION, NOW, load_fixture, make_html


def test_parse_recorded_response() -> None:
    """Test parsing a response recorded from jlt.se."""
    departures = parse_departures(load_fixture("departures_6001350.html"), NOW)

    assert len(departures) == 20
    first = departures[0]
    assert first.line == "1"
    assert first.destination == DESTINATION
    assert first.direction == f"mot {DESTINATION}"
    assert first.departure == datetime(2026, 10, 25, 11, 41, tzinfo=JLT_TIMEZONE)
    assert first.departure_time == "11:41"
    assert first.time_to_departure == "Avgår nu"
    assert departures[1].destination == "Råslätt"
    assert departures[1].time_to_departure == "Avgår om 1 min"
    assert {(d.line, d.destination) for d in departures} == {
        ("1", DESTINATION),
        ("1", "Råslätt"),
    }


def test_parse_collapses_whitespace() -> None:
    """Test that whitespace runs in the time to departure are collapsed."""
    departures = parse_departures(
        make_html(("1", "13:41 <span>(Avgår om 2h  0 min)</span>", "mot  Råslätt")),
        NOW,
    )

    assert departures[0].time_to_departure == "Avgår om 2h 0 min"
    assert departures[0].direction == "mot Råslätt"
    assert departures[0].destination == "Råslätt"


def test_parse_skips_departed_and_invalid() -> None:
    """Test that departed and malformed suggestions are skipped."""
    html = make_html(
        ("1", "Har avgått", "mot Råslätt"),
        ("1", "<span>(Inställd)</span>", "mot Råslätt"),
        ("1", "11:50 <span>(Avgår om 10 min)</span>", "mot Råslätt"),
    )
    html += '<div class="travel-suggestion"><p>11:55</p></div>'

    departures = parse_departures(html, NOW)

    assert [d.departure_time for d in departures] == ["11:50"]


def test_parse_without_mot_prefix() -> None:
    """Test a direction without the "mot" prefix."""
    departures = parse_departures(
        make_html(("28", "11:50 <span>(Avgår om 10 min)</span>", "Centrum")), NOW
    )

    assert departures[0].destination == "Centrum"
    assert departures[0].line == "28"


def test_parse_after_midnight() -> None:
    """Test that departures after midnight are placed on the next day."""
    now = datetime(2026, 10, 25, 23, 55, tzinfo=JLT_TIMEZONE)
    departures = parse_departures(
        make_html(
            ("1", "23:54 <span>(Avgår nu)</span>", "mot Råslätt"),
            ("1", "00:10 <span>(Avgår om 15 min)</span>", "mot Råslätt"),
        ),
        now,
    )

    assert departures[0].departure == datetime(
        2026, 10, 25, 23, 54, tzinfo=JLT_TIMEZONE
    )
    assert departures[1].departure == datetime(2026, 10, 26, 0, 10, tzinfo=JLT_TIMEZONE)


def test_parse_empty_response() -> None:
    """Test a stop without any upcoming departures."""
    assert parse_departures("", NOW) == []


def test_parse_recorded_stop_search() -> None:
    """Test parsing a stop search response recorded from the travel planner."""
    stops = parse_stops(load_fixture("stop_search_jonkoping.html"))

    assert len(stops) == 12
    assert stops[0] == Stop(id=6001242, name="Jönköping Juneporten")
    assert Stop(id=6001320, name="Jönköping Rådhusparken") in stops


def test_parse_stop_search_skips_invalid_and_duplicates() -> None:
    """Test that options without a numeric ID and duplicates are skipped."""
    html = """
        <li class="travel-option" data-id="Jönköping  Elmia|6001241|0">Elmia</li>
        <li class="travel-option" data-id="Storgatan 1, Jönköping|addr|1">x</li>
        <li class="travel-option" data-id="Utan id">x</li>
        <li class="travel-option">x</li>
        <li class="travel-option" data-id="Jönköping Elmia|6001241|0">Elmia</li>
    """

    assert parse_stops(html) == [Stop(id=6001241, name="Jönköping Elmia")]
