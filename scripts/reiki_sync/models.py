from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RegulationRef:
    """A single row discovered from an index/listing page."""

    source_id: str
    title: str
    source_url: str
    type: str | None = None


@dataclass
class RegulationDoc:
    """A fully parsed individual regulation, ready to be rendered as Markdown."""

    source_id: str
    title: str
    source_url: str
    type: str | None
    reiki_number: str | None = None
    promulgation_date: str | None = None
    enforcement_date: str | None = None
    body_markdown: str = ""
    extra_front_matter: dict = field(default_factory=dict)
