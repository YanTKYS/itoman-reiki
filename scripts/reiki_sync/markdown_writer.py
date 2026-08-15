from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import RegulationDoc

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]")


def safe_filename(source_id: str) -> str:
    """Turn a source identifier into a safe file basename.

    Reiki-Base identifiers (e.g. ``q910RG00000001``) are already filesystem
    safe; this only guards against unexpected characters if the site's ID
    scheme differs from what was observed during development.
    """
    name = _UNSAFE_FILENAME_CHARS.sub("_", source_id.strip())
    return f"{name}.md"


def build_front_matter(doc: RegulationDoc) -> str:
    data: dict = {
        "title": doc.title,
        "source_id": doc.source_id,
        "source_url": doc.source_url,
        "type": doc.type,
    }
    if doc.reiki_number:
        data["reiki_number"] = doc.reiki_number
    if doc.promulgation_date:
        data["promulgation_date"] = doc.promulgation_date
    if doc.enforcement_date:
        data["enforcement_date"] = doc.enforcement_date
    data.update(doc.extra_front_matter)
    dumped = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    return f"---\n{dumped}---\n"


def render_markdown(doc: RegulationDoc) -> str:
    front_matter = build_front_matter(doc)
    body = doc.body_markdown.rstrip("\n")
    return f"{front_matter}\n{body}\n"


def write_markdown(doc: RegulationDoc, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / safe_filename(doc.source_id)
    path.write_text(render_markdown(doc), encoding="utf-8")
    return path
