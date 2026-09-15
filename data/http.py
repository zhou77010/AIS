"""AIS HTTP transport.

The smallest HTTP client the Data layer needs. It wraps the standard library so
that no third party dependency is required, keeps the cookies a source hands out
between requests, and turns every transport failure into a project error.
"""

from __future__ import annotations

import http.cookiejar
import urllib.error
import urllib.request
from typing import Protocol
from urllib.parse import urlsplit

from utils.exceptions import DataError

_DEFAULT_TIMEOUT_SECONDS = 15.0
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_ACCEPT = "application/json, text/plain, */*"


class HttpTransport(Protocol):
    """Contract for the transport a market data provider talks through."""

    def get(self, url: str) -> str:
        """Return the response body of one GET request.

        Args:
            url: Absolute URL to request.

        Returns:
            Response body decoded as text.

        Raises:
            DataError: When the request cannot be completed.
        """


class UrllibTransport:
    """HTTP transport built on the standard library only."""

    def __init__(self, timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS) -> None:
        """Create the transport with its own cookie jar.

        Args:
            timeout_seconds: Timeout of a single request.
        """
        self._timeout_seconds = timeout_seconds
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def get(self, url: str) -> str:
        """Return the response body of one GET request.

        Cookies received earlier are sent with the request and cookies received
        now are kept, which is what sources that hand out a session require.

        Args:
            url: Absolute URL to request.

        Returns:
            Response body decoded as text.

        Raises:
            DataError: When the status is an error or the host is unreachable.
        """
        request = urllib.request.Request(
            url,
            headers={"User-Agent": _USER_AGENT, "Accept": _ACCEPT},
        )
        try:
            with self._opener.open(request, timeout=self._timeout_seconds) as reply:
                return reply.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            raise DataError(
                f"request to {_without_query(url)} answered "
                f"HTTP {error.code} {error.reason}"
            ) from error
        except urllib.error.URLError as error:
            raise DataError(
                f"request to {_without_query(url)} failed: {error.reason}"
            ) from error


def _without_query(url: str) -> str:
    """Return a URL without its query string.

    Error messages are logged, and the query string may carry a session token
    that has no place in a log line, so it is dropped from every report.
    """
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"
