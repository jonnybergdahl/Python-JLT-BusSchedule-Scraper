"""Constants for the JLT client."""

from zoneinfo import ZoneInfo

__version__ = "1.1.0"

API_URL = "https://www.jlt.se/api/StopAreaApi/GetClosestDepartures"
STOP_SEARCH_URL = "https://www.etiscloud.net/jonkopingRP/v6/ajaxList.aspx"

# A small pool of realistic, current desktop browser User-Agent strings. One
# is picked at random per request so the scraper does not present a single
# static fingerprint on every call.
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:158.0) Gecko/20100101 Firefox/158.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/27.0.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 "
    "Edg/156.0.0.0",
)

# Departure times on jlt.se are always Swedish local time
JLT_TIMEZONE = ZoneInfo("Europe/Stockholm")
