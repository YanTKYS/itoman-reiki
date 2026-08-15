#!/usr/bin/env python3
"""Fetch regulations from the Itoman City Reiki-Base site and convert them to
one Markdown file each.

    python scripts/sync.py --limit 10
    python scripts/sync.py --ids q910RG00000001,q910RG00000002

This is a proof of concept: it intentionally does not paginate through the
entire regulation catalogue. See README.md for scope and constraints.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reiki_sync import listing, parse  # noqa: E402
from reiki_sync.http_client import FetchError, PoliteClient, RobotsDisallowed  # noqa: E402
from reiki_sync.markdown_writer import write_markdown  # noqa: E402
from reiki_sync.store import entry_for, write_regulations_json  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--limit", type=int, default=10, help="max number of regulations to fetch (default: 10)")
    p.add_argument("--ids", type=str, default=None, help="comma-separated source_ids to fetch instead of the first --limit entries")
    p.add_argument("--delay", type=float, default=2.0, help="minimum seconds between HTTP requests (default: 2.0)")
    p.add_argument("--out", type=Path, default=REPO_ROOT / "reiki", help="output directory for Markdown files")
    p.add_argument("--metadata", type=Path, default=REPO_ROOT / "metadata" / "regulations.json", help="path to write regulations.json")
    p.add_argument("--no-robots", action="store_true", help="skip robots.txt check (not recommended)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    client = PoliteClient(delay_seconds=args.delay, respect_robots=not args.no_robots)

    print("Fetching regulation index...", file=sys.stderr)
    try:
        refs = listing.fetch_all_refs(client)
    except RobotsDisallowed as exc:
        print(f"Blocked by robots.txt: {exc}", file=sys.stderr)
        return 2
    except FetchError as exc:
        print(f"Failed to fetch index: {exc}", file=sys.stderr)
        return 2

    if args.ids:
        wanted = set(args.ids.split(","))
        selected = [r for r in refs if r.source_id in wanted]
        missing = wanted - {r.source_id for r in selected}
        if missing:
            print(f"Warning: ids not found in index: {sorted(missing)}", file=sys.stderr)
    else:
        selected = refs[: args.limit]

    print(f"Selected {len(selected)} regulation(s) out of {len(refs)} discovered", file=sys.stderr)

    entries = []
    failures = []
    for i, ref in enumerate(selected, start=1):
        print(f"[{i}/{len(selected)}] {ref.source_id} {ref.title}", file=sys.stderr)
        try:
            html = client.get(ref.source_url)
            doc = parse.parse_detail_page(ref, html)
            path = write_markdown(doc, args.out)
        except (FetchError, RobotsDisallowed) as exc:
            print(f"  failed: {exc}", file=sys.stderr)
            failures.append((ref, str(exc)))
            continue
        entries.append(entry_for(doc, str(path.relative_to(REPO_ROOT))))

    write_regulations_json(entries, args.metadata)
    print(f"Wrote {len(entries)} Markdown file(s) and {args.metadata}", file=sys.stderr)
    if failures:
        print(f"{len(failures)} regulation(s) failed to fetch/convert:", file=sys.stderr)
        for ref, err in failures:
            print(f"  - {ref.source_id}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
