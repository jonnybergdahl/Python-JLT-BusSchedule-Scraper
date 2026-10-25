"""Exceptions raised by the JLT client."""


class JltError(Exception):
    """Base error for the JLT client."""


class JltConnectionError(JltError):
    """Error communicating with jlt.se."""
