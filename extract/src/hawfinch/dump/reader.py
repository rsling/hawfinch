"""Streaming reader for MediaWiki XML dumps (``pages-articles.xml.bz2``).

Pages are yielded one at a time and the parsed tree is cleared behind them, so memory use
stays flat over the whole dump. Only the latest revision is read; ``pages-articles`` dumps
contain no other.
"""

from __future__ import annotations

import bz2
import xml.etree.ElementTree as ET
from collections.abc import Container, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import IO


@dataclass(frozen=True, slots=True)
class Page:
    ns: int
    page_id: int
    title: str
    rev_id: int
    timestamp: datetime
    text: str
    redirect: str | None = None
    model: str | None = None


@dataclass
class SiteInfo:
    sitename: str
    dbname: str
    base: str
    generator: str
    case: str
    namespaces: dict[int, str] = field(default_factory=dict)


def open_dump(path: Path) -> IO[bytes]:
    path = Path(path)
    return bz2.open(path, "rb") if path.suffix == ".bz2" else path.open("rb")


def _qname(root_tag: str) -> str:
    return root_tag[: root_tag.index("}") + 1] if root_tag.startswith("{") else ""


def _siteinfo(elem: ET.Element, q: str) -> SiteInfo:
    def text(name: str) -> str:
        return elem.findtext(q + name) or ""

    namespaces = {
        int(ns.get("key")): ns.text or "" for ns in elem.iterfind(f"{q}namespaces/{q}namespace")
    }
    return SiteInfo(
        sitename=text("sitename"),
        dbname=text("dbname"),
        base=text("base"),
        generator=text("generator"),
        case=text("case"),
        namespaces=namespaces,
    )


def _page(elem: ET.Element, q: str) -> Page:
    revision = elem.find(q + "revision")
    redirect = elem.find(q + "redirect")
    return Page(
        ns=int(elem.findtext(q + "ns")),
        page_id=int(elem.findtext(q + "id")),
        title=elem.findtext(q + "title"),
        rev_id=int(revision.findtext(q + "id")),
        timestamp=datetime.fromisoformat(revision.findtext(q + "timestamp")),
        text=revision.findtext(q + "text") or "",
        redirect=redirect.get("title") if redirect is not None else None,
        model=revision.findtext(q + "model"),
    )


def read_siteinfo(path: Path) -> SiteInfo:
    """Read the ``<siteinfo>`` header of a dump without touching the pages."""
    with open_dump(path) as f:
        context = ET.iterparse(f, events=("start", "end"))
        _, root = next(context)
        q = _qname(root.tag)
        for event, elem in context:
            if event == "end" and elem.tag == q + "siteinfo":
                return _siteinfo(elem, q)
    raise ValueError(f"{path}: no <siteinfo> element")


def iter_pages(path: Path, namespaces: Container[int] | None = None) -> Iterator[Page]:
    """Yield the pages of a dump in file order, optionally only those in ``namespaces``."""
    with open_dump(path) as f:
        context = ET.iterparse(f, events=("start", "end"))
        _, root = next(context)
        q = _qname(root.tag)
        page_tag = q + "page"
        for event, elem in context:
            if event != "end" or elem.tag != page_tag:
                continue
            if namespaces is None or int(elem.findtext(q + "ns")) in namespaces:
                yield _page(elem, q)
            root.clear()
