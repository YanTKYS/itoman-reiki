"""Generic, structure-preserving HTML -> Markdown conversion.

This module intentionally does not try to be a general-purpose HTML-to-Markdown
library. It implements exactly the rules this project needs:

- Headings (``<h1>``-``<h6>``, or elements whose class is listed in
  ``heading_classes``) become Markdown ``#`` headings.
- Simple tables (no rowspan/colspan, no nested tables) become GFM Markdown
  tables.
- Complex tables are left as raw HTML (with purely presentational attributes
  such as ``style``/``class``/``bgcolor``/``width`` stripped, since those are
  page decoration, not regulation content) so rowspan/colspan structure is
  never silently destroyed.
- All other elements are flattened to their text content. No wording,
  spacing-for-readability, or character-width normalization is applied beyond
  collapsing the incidental ASCII whitespace that HTML source formatting
  introduces (the same collapsing a browser would do when rendering).
"""

from __future__ import annotations

import copy
import re

from bs4 import BeautifulSoup, NavigableString, Tag

_WS_RUN = re.compile(r"[ \t\r\n\f]+")
_BLOCK_TAGS = {
    "p",
    "div",
    "li",
    "tr",
    "table",
    "ul",
    "ol",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "br",
}
_TABLE_ATTR_ALLOWLIST = {"rowspan", "colspan"}


def _collapse_ws(text: str) -> str:
    """Collapse runs of ASCII whitespace to a single half-width space.

    This mirrors normal HTML rendering (consecutive source whitespace is
    insignificant outside <pre>). Full-width characters (including U+3000
    ideographic space) are left untouched.
    """
    return _WS_RUN.sub(" ", text)


def _inline_text(tag: Tag) -> str:
    parts: list[str] = []
    for child in tag.children:
        if isinstance(child, NavigableString):
            parts.append(_collapse_ws(str(child)))
        elif isinstance(child, Tag):
            if child.name == "br":
                parts.append("\n")
            else:
                parts.append(_inline_text(child))
    return "".join(parts)


def _clean_table_html(table: Tag) -> str:
    clone = copy.copy(table)
    for node in clone.find_all(True):
        allowed = {k: v for k, v in node.attrs.items() if k in _TABLE_ATTR_ALLOWLIST}
        node.attrs = allowed
    clone.attrs = {}
    return str(clone)


def _table_is_simple(table: Tag) -> bool:
    if table.find("table") is not None:
        return False
    for cell in table.find_all(["td", "th"]):
        try:
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
        except ValueError:
            return False
        if rowspan > 1 or colspan > 1:
            return False
    return True


def _table_to_markdown(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr", recursive=False) or table.find_all("tr"):
        cells = tr.find_all(["td", "th"], recursive=False)
        rows.append([_inline_text(c).strip() for c in cells])
    rows = [r for r in rows if r]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    header, *body = rows
    header = header + [""] * (width - len(header))

    def fmt(row: list[str]) -> str:
        row = row + [""] * (width - len(row))
        escaped = [c.replace("|", "\\|").replace("\n", "<br>") for c in row]
        return "| " + " | ".join(escaped) + " |"

    lines = [fmt(header), "| " + " | ".join(["---"] * width) + " |"]
    lines.extend(fmt(r) for r in body)
    return "\n".join(lines)


def convert_fragment(root: Tag, heading_classes: dict[str, int] | None = None) -> str:
    """Convert a BeautifulSoup fragment to Markdown text.

    ``heading_classes`` maps a CSS class name to a Markdown heading level
    (1-6), for sites where section headings are marked with a class rather
    than a semantic ``<hN>`` tag.
    """
    heading_classes = heading_classes or {}
    blocks: list[str] = []

    def heading_level(tag: Tag) -> int | None:
        if tag.name and re.fullmatch(r"h[1-6]", tag.name):
            return int(tag.name[1])
        for cls in tag.get("class") or []:
            if cls in heading_classes:
                return heading_classes[cls]
        return None

    def walk(node: Tag) -> None:
        for child in node.children:
            if isinstance(child, NavigableString):
                text = _collapse_ws(str(child)).strip()
                if text:
                    blocks.append(text)
                continue
            if not isinstance(child, Tag):
                continue

            if child.name == "table":
                if _table_is_simple(child):
                    md = _table_to_markdown(child)
                else:
                    md = _clean_table_html(child)
                if md:
                    blocks.append(md)
                continue

            level = heading_level(child)
            if level is not None:
                text = _inline_text(child).strip()
                if text:
                    blocks.append(f"{'#' * min(max(level, 1), 6)} {text}")
                continue

            if child.name in ("ul", "ol"):
                blocks.append(_list_to_markdown(child))
                continue

            if child.name in ("script", "style"):
                continue

            if child.name in _BLOCK_TAGS:
                text = _inline_text(child).strip()
                if text:
                    blocks.append(text)
                else:
                    walk(child)
                continue

            # Inline or unknown container: recurse transparently.
            walk(child)

    walk(root)
    return "\n\n".join(blocks)


def _list_to_markdown(list_tag: Tag, depth: int = 0) -> str:
    lines: list[str] = []
    marker = "1." if list_tag.name == "ol" else "-"
    index = 1
    for li in list_tag.find_all("li", recursive=False):
        prefix = "  " * depth + (f"{index}." if list_tag.name == "ol" else marker)
        index += 1
        nested_lists = li.find_all(["ul", "ol"], recursive=False)
        for nested in nested_lists:
            nested.extract()
        text = _inline_text(li).strip()
        lines.append(f"{prefix} {text}")
        for nested in nested_lists:
            lines.append(_list_to_markdown(nested, depth + 1))
    return "\n".join(lines)


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")
