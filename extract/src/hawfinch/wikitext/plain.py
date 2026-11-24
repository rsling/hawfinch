"""Readable plain text from a line of wikitext, for definitions and samples.

Links become their label (``[[lieben|liebe]]`` → ``liebe``), bold and italic quotes and
``<ref>`` notes are dropped, and templates are reduced to a short marker: the labels of
``{{K|…}}`` in parentheses (``(Recht, transitiv)``), any other template as its name and
positional arguments in angle brackets (``⟨ugs.⟩``, ``⟨Ü: en, house⟩``). Not a renderer of
what MediaWiki shows; it keeps what a reader needs to judge a definition.
"""

from __future__ import annotations

import re

from hawfinch.wikitext.templates import COMMENT, scan

REF = re.compile(r"<ref\b[^>]*?(?:/>|>.*?</ref\s*>)", re.S | re.I)
TAG = re.compile(r"</?[a-zA-Z][^>]*>")
QUOTES = re.compile(r"'{2,}")


def to_plain(text: str) -> str:
    text = REF.sub("", COMMENT.sub("", text))
    result = scan(text)
    items = [(t.start, t.end, t) for t in result.templates if t.depth == 0]
    covered = [(a, b) for a, b, _ in items]
    items += [
        (link.start, link.end, link)
        for link in result.links
        if not any(a <= link.start < b for a, b in covered)
    ]
    items.sort(key=lambda item: item[0])
    out, last = [], 0
    for start, end, item in items:
        if start < last:
            continue
        out.append(text[last:start])
        out.append(_render(item))
        last = end
    out.append(text[last:])
    plain = TAG.sub("", QUOTES.sub("", "".join(out)))
    return " ".join(plain.split())


def _render(item) -> str:
    if hasattr(item, "target"):
        label = item.label if item.label is not None else item.target
        return to_plain(label) if "[[" in label or "{{" in label else label
    positional = [to_plain(v) for v in item.positional() if v.strip()]
    if item.name == "K":
        return f"({', '.join(positional)})"
    return f"⟨{': '.join([item.name, ', '.join(positional)]) if positional else item.name}⟩"
