"""Discover regulation entries (id, title, URL) from the site's index pages.

This module is intentionally implemented against the *actual* observed HTML
of https://www1.g-reiki.net/itoman/ rather than assumptions about the
Reiki-Base template in general, since class names and markup vary slightly
between municipalities running the same vendor platform.
"""

from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .http_client import PoliteClient
from .models import RegulationRef

MENU_URL = "https://www1.g-reiki.net/itoman/reiki_menu.html"


def fetch_all_refs(client: PoliteClient) -> list[RegulationRef]:
    """Return every (id, title, url, type) row reachable from the menu page.

    Raises NotImplementedError until the real site structure has been
    inspected -- see scripts/probe.py.
    """
    raise NotImplementedError(
        "listing.fetch_all_refs must be implemented against the real "
        "www1.g-reiki.net/itoman/ HTML structure"
    )


def _abs_url(base: str, href: str) -> str:
    return urljoin(base, href)
