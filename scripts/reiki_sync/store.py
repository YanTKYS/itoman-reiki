from __future__ import annotations

import json
from pathlib import Path

from .models import RegulationDoc


def entry_for(doc: RegulationDoc, markdown_file: str) -> dict:
    return {
        "id": doc.source_id,
        "title": doc.title,
        "type": doc.type,
        "source_url": doc.source_url,
        "markdown_file": markdown_file,
    }


def write_regulations_json(entries: list[dict], path: Path) -> None:
    entries_sorted = sorted(entries, key=lambda e: e["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(entries_sorted, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
