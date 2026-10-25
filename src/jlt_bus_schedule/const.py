"""Constants for the JLT client."""

from zoneinfo import ZoneInfo

__version__ = "1.0.0"

API_URL = "https://www.jlt.se/api/StopAreaApi/GetClosestDepartures"
STOP_SEARCH_URL = "https://www.etiscloud.net/jonkopingRP/v6/ajaxList.aspx"
USER_AGENT = (
    f"jlt-bus-schedule/{__version__} "
    "(+https://github.com/jonnybergdahl/Python-JLT-BusSchedule-Scraper)"
)

# Departure times on jlt.se are always Swedish local time
JLT_TIMEZONE = ZoneInfo("Europe/Stockholm")
