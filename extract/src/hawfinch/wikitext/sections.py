"""Section structure of a de.wiktionary page.

A page holds one level-2 section per entry, headed ``== Haus ({{Sprache|Deutsch}}) ==``.
Its level-3 children are part-of-speech sections, headed for instance
``=== {{Wortart|Substantiv|Deutsch}}, {{n}} ===``, and the translations sit below those at
level 4. Inside a part-of-speech section, the parts (Worttrennung, Bedeutungen, Herkunft, …)
are not headings but blocks, each opened by a line holding a single template without
arguments (``{{Bedeutungen}}``); see :func:`blocks`.

Sections store offsets into the page text, not copies of it. Headings inside comments are
ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from hawfinch.wikitext.templates import COMMENT, Template, find_templates

HEADING = re.compile(r"^(=+)(.*?)(=+)[ \t]*$", re.M)


@dataclass
class Section:
    level: int
    title: str
    start: int
    body_start: int
    body_end: int
    end: int = -1
    children: list[Section] = field(default_factory=list)

    def body(self, text: str) -> str:
        """Own text, up to the first subsection."""
        return text[self.body_start : self.body_end]

    def full(self, text: str) -> str:
        """Own text plus all subsections."""
        return text[self.body_start : self.end]

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass
class PosSection:
    section: Section
    heading_templates: list[Template]
    wortarten: list[tuple[str, str]]  # (label, language) of each {{Wortart|…}} in the heading


@dataclass
class LanguageSection:
    section: Section
    word: str  # heading text before the language template, e.g. "Haus"
    language: str | None
    pos_sections: list[PosSection]


def blank_comments(text: str) -> str:
    """Replace comments by spaces, keeping offsets and line breaks."""
    return COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def split_sections(text: str) -> list[Section]:
    """Return the top-level sections of ``text`` as a tree; text before the first heading is
    not part of any section."""
    scrubbed = blank_comments(text)
    flat = []
    for m in HEADING.finditer(scrubbed):
        opening, closing = len(m.group(1)), len(m.group(3))
        level = min(opening, closing, 6)
        title = ("=" * (opening - level) + m.group(2) + "=" * (closing - level)).strip()
        if not title:
            continue
        body_start = min(m.end() + 1, len(text))
        flat.append(Section(level, title, m.start(), body_start, len(text)))
    for current, following in zip(flat, flat[1:], strict=False):
        current.body_end = following.start

    roots: list[Section] = []
    stack: list[Section] = []
    for section in flat:
        while stack and stack[-1].level >= section.level:
            stack.pop().end = section.start
        (stack[-1].children if stack else roots).append(section)
        stack.append(section)
    for section in stack:
        section.end = len(text)
    return roots


def _pos_section(section: Section) -> PosSection:
    templates = find_templates(section.title)
    wortarten = [
        ((t.get("1") or "").strip(), (t.get("2") or "").strip())
        for t in templates
        if t.name == "Wortart"
    ]
    return PosSection(section, templates, wortarten)


def language_sections(text: str) -> list[LanguageSection]:
    """All entries on a page: level-2 sections with their language and part-of-speech parts."""
    result = []
    for root in split_sections(text):
        for section in root.walk():
            if section.level != 2:
                continue
            templates = find_templates(section.title)
            language = next(
                ((t.get("1") or "").strip() for t in templates if t.name == "Sprache"), None
            )
            word = section.title.split("(", 1)[0].strip()
            pos = [_pos_section(c) for c in section.children if c.level == 3]
            result.append(LanguageSection(section, word, language, pos))
    return result


def german_sections(text: str) -> list[LanguageSection]:
    return [s for s in language_sections(text) if s.language == "Deutsch"]


BLOCK_MARKER = re.compile(r"^[ \t]*\{\{[ \t]*([^{}|=]+?)[ \t]*\}\}[ \t]*$")


def blocks(body: str) -> dict[str, list[str]]:
    """Split the own text of a part-of-speech section into blocks.

    A block starts at a line consisting of one template without arguments
    (``{{Bedeutungen}}``) and runs to the next such line. Returns the non-empty lines of each
    block under the marker's name; text before the first marker is under ``""``. If a marker
    occurs twice, the lines are joined.
    """
    result: dict[str, list[str]] = {"": []}
    current = ""
    for line in blank_comments(body).splitlines():
        m = BLOCK_MARKER.match(line)
        if m:
            current = " ".join(m.group(1).split())
            result.setdefault(current, [])
        elif line.strip():
            result[current].append(line.rstrip())
    return result
