#!/usr/bin/env python3
"""Developer helper: fetch a page and save the raw HTML for manual inspection.

Not part of the PoC's public CLI surface -- used only while building the
parser against the real site structure.

Usage:
    python scripts/probe.py <url> <output-file>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reiki_sync.http_client import PoliteClient  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)
    url, out_path = sys.argv[1], sys.argv[2]
    client = PoliteClient(delay_seconds=2.0)
    html = client.get(url)
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"saved {len(html)} bytes -> {out_path}")


if __name__ == "__main__":
    main()
