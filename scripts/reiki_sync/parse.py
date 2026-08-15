"""Parse an individual regulation detail page into a RegulationDoc.

Implemented against the actual observed HTML of
https://www1.g-reiki.net/itoman/reiki_honbun/*.html -- see scripts/probe.py
for how the reference pages used during development were captured.
"""

from __future__ import annotations

from .html_to_markdown import convert_fragment
from .models import RegulationDoc, RegulationRef


def parse_detail_page(ref: RegulationRef, html: str) -> RegulationDoc:
    raise NotImplementedError(
        "parse.parse_detail_page must be implemented against the real "
        "www1.g-reiki.net/itoman/ detail page structure"
    )
