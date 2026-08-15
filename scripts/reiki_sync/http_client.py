"""Polite HTTP client for fetching pages from the Reiki-Base site.

Design goals:
- Always send an identifying User-Agent (site operators should be able to see
  who is requesting pages and why).
- Enforce a minimum delay between requests so the site is never hammered.
- Do not retry aggressively; a failure is surfaced to the caller instead of
  being silently worked around.
"""

from __future__ import annotations

import time
import urllib.robotparser
from dataclasses import dataclass

import requests

DEFAULT_USER_AGENT = (
    "itoman-reiki-sync/0.1 "
    "(+https://github.com/yantkys/itoman-reiki; PoC for archiving public "
    "municipal regulations as Markdown)"
)


class FetchError(RuntimeError):
    """Raised when a page cannot be fetched (network error or non-2xx status)."""


class RobotsDisallowed(RuntimeError):
    """Raised when robots.txt disallows fetching the requested URL."""


@dataclass
class PoliteClient:
    user_agent: str = DEFAULT_USER_AGENT
    delay_seconds: float = 2.0
    timeout_seconds: float = 20.0
    respect_robots: bool = True

    def __post_init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent})
        self._last_request_at: float | None = None
        self._robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    def _check_robots(self, url: str) -> None:
        if not self.respect_robots:
            return
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(url)
        origin = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
        rp = self._robots_cache.get(origin)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = origin + "/robots.txt"
            try:
                resp = self._session.get(robots_url, timeout=self.timeout_seconds)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    # No robots.txt (or inaccessible) -> treat as "allow all".
                    rp.parse([])
            except requests.RequestException:
                rp.parse([])
            self._robots_cache[origin] = rp
        if not rp.can_fetch(self.user_agent, url):
            raise RobotsDisallowed(f"robots.txt disallows fetching: {url}")

    def _throttle(self) -> None:
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            remaining = self.delay_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def get(self, url: str) -> str:
        self._check_robots(url)
        self._throttle()
        try:
            resp = self._session.get(url, timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise FetchError(f"request failed for {url}: {exc}") from exc
        if resp.status_code != 200:
            raise FetchError(f"unexpected status {resp.status_code} for {url}")
        resp.encoding = resp.apparent_encoding or resp.encoding
        return resp.text
