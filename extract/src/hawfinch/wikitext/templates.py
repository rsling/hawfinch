"""Scanner for templates and links in wikitext, without expansion.

It follows the MediaWiki preprocessor where it matters for reading arguments:

- a pipe splits template arguments only at the template's own level, not inside nested
  templates, links (``[[a|b]]``), comments or extension tags (``<ref>``, ``<nowiki>``, …);
- an argument is named if it contains ``=`` at its own level; named values are stripped
  of surrounding whitespace, positional values are not;
- positional arguments are numbered from 1, and a later explicit ``2=`` overrides.

Template names are not case-folded: Wiktionary titles are case-sensitive, so ``{{m}}``
and ``{{M}}`` are different templates. Comments are removed from names and values.

Templates inside ``<ref>`` content are found as well. Unbalanced markup does not raise;
it is reported as an :class:`Anomaly` so that it can be counted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.S)
OPAQUE_TAGS = "nowiki|pre|math|chem|ce|syntaxhighlight|source|score|gallery|ref|templatedata"
TOKEN = re.compile(
    r"(?P<comment><!--.*?(?:-->|\Z))"
    rf"|(?P<tag><(?P<tagname>{OPAQUE_TAGS})\b(?:[^>]*?/>|[^>]*>(?P<content>.*?)(?:</(?P=tagname)\s*>|\Z)))"
    r"|\{\{|\}\}|\[\[|\]\]|\|",
    re.S | re.I,
)


@dataclass(frozen=True, slots=True)
class Template:
    name: str
    args: tuple[tuple[str | None, str], ...]
    start: int
    end: int
    depth: int

    def params(self) -> dict[str, str]:
        """Arguments by key as MediaWiki sees them; positional ones under ``"1"``, ``"2"``, …"""
        result, position = {}, 0
        for key, value in self.args:
            if key is None:
                position += 1
                result[str(position)] = value
            else:
                result[key] = value
        return result

    def positional(self) -> list[str]:
        return [value for key, value in self.args if key is None]

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.params().get(key, default)


@dataclass(frozen=True, slots=True)
class Link:
    target: str
    label: str | None
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Anomaly:
    kind: str
    position: int


@dataclass
class Scan:
    templates: list[Template] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)


@dataclass
class _Frame:
    kind: str  # "tpl" or "link"
    start: int
    pipes: list[int] = field(default_factory=list)
    children: list[tuple[int, int]] = field(default_factory=list)


def normalize_name(raw: str) -> str:
    name = " ".join(COMMENT.sub("", raw).replace("_", " ").split())
    if name.startswith("#") and ":" in name:
        return name[: name.index(":")]
    for prefix in ("Vorlage:", "Template:"):
        if name.startswith(prefix):
            return name[len(prefix) :].strip()
    return name


def _first_equals(text: str, start: int, end: int, children: list[tuple[int, int]]) -> int:
    position = text.find("=", start, end)
    while position != -1:
        if not any(a <= position < b for a, b in children):
            return position
        position = text.find("=", position + 1, end)
    return -1


def _template(text: str, frame: _Frame, end: int, depth: int) -> Template:
    bounds = [frame.start + 2, *(p + 1 for p in frame.pipes)]
    stops = [*frame.pipes, end - 2]
    name = normalize_name(text[bounds[0] : stops[0]])
    args = []
    for a, b in zip(bounds[1:], stops[1:], strict=True):
        equals = _first_equals(text, a, b, frame.children)
        if equals == -1:
            args.append((None, COMMENT.sub("", text[a:b])))
        else:
            key = COMMENT.sub("", text[a:equals]).strip()
            args.append((key, COMMENT.sub("", text[equals + 1 : b]).strip()))
    return Template(name, tuple(args), frame.start, end, depth)


def _link(text: str, frame: _Frame, end: int) -> Link:
    inner = text[frame.start + 2 : end - 2]
    if frame.pipes:
        cut = frame.pipes[0] - frame.start - 2
        return Link(inner[:cut].strip(), inner[cut + 1 :], frame.start, end)
    return Link(inner.strip(), None, frame.start, end)


def scan(text: str, offset: int = 0, base_depth: int = 0) -> Scan:
    """Find all templates (nested ones included) and links in ``text``."""
    result = Scan()
    stack: list[_Frame] = []

    def depth() -> int:
        return base_depth + sum(1 for f in stack if f.kind == "tpl")

    def close(frame: _Frame, end: int) -> None:
        if frame.kind == "tpl":
            result.templates.append(_template(text, frame, end, depth()))
        else:
            result.links.append(_link(text, frame, end))
        if stack:
            stack[-1].children.append((frame.start, end))

    for m in TOKEN.finditer(text):
        token, start, end = m.group(), m.start(), m.end()
        if m.group("comment") is not None or m.group("tag") is not None:
            if stack:
                stack[-1].children.append((start, end))
            if m.group("tagname") and m.group("tagname").lower() == "ref" and m.group("content"):
                inner = scan(m.group("content"), 0, depth())
                shift = m.start("content")
                result.templates += [_shift(t, shift) for t in inner.templates]
                result.links += [_shift(link, shift) for link in inner.links]
                result.anomalies += [Anomaly(a.kind, a.position + shift) for a in inner.anomalies]
        elif token == "{{":
            stack.append(_Frame("tpl", start))
        elif token == "[[":
            stack.append(_Frame("link", start))
        elif token == "|":
            if stack:
                stack[-1].pipes.append(start)
        elif token == "}}":
            if not any(f.kind == "tpl" for f in stack):
                result.anomalies.append(Anomaly("stray }}", start))
                continue
            while stack[-1].kind != "tpl":
                result.anomalies.append(Anomaly("unclosed [[", stack.pop().start))
            close(stack.pop(), end)
        elif token == "]]":
            if stack and stack[-1].kind == "link":
                close(stack.pop(), end)
            else:
                result.anomalies.append(Anomaly("stray ]]", start))
    for frame in stack:
        result.anomalies.append(
            Anomaly("unclosed {{" if frame.kind == "tpl" else "unclosed [[", frame.start)
        )
    result.templates.sort(key=lambda t: t.start)
    result.links.sort(key=lambda link: link.start)
    if offset:
        result.templates = [_shift(t, offset) for t in result.templates]
        result.links = [_shift(link, offset) for link in result.links]
        result.anomalies = [Anomaly(a.kind, a.position + offset) for a in result.anomalies]
    return result


def _shift(item, by: int):
    return type(item)(
        **{
            **{f: getattr(item, f) for f in item.__slots__},
            "start": item.start + by,
            "end": item.end + by,
        }
    )


def find_templates(text: str) -> list[Template]:
    return scan(text).templates
