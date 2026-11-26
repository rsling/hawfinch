"""Which part-of-speech sections of a lemma page go into the database.

A part-of-speech section is left out if all its senses are marked as archaic, regional,
Austrian or Swiss (``docs/features/usage-labels.md``). The rule holds for every part of
speech, so it is applied here and not in the readers of the single features:
:func:`lemma_sections` gives every German part-of-speech section of a page with the labels
of its senses, and :func:`kept_sections` only those that stay.

``Flexion:`` pages are not sections of a lemma page, and a conjugation does not say which
verb section of the lemma page it belongs to. :func:`verb_selection` therefore sums up the
verb sections of a lemma page, and :func:`keeps_flexion` decides from that for the whole
``Flexion:`` page of the same name.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from hawfinch.features.usage import sense_labels, sense_lines
from hawfinch.wikitext.sections import PosSection, german_sections

KEPT = "kept"
MIXED = "mixed"
LEFT_OUT = "left out"


@dataclass
class LemmaSection:
    """A German part-of-speech section of a lemma page."""

    title: str  # of the page
    number: int  # position among the part-of-speech sections of its entry, from 1
    pos: PosSection
    body: str  # own text, up to the first subsection
    senses: list[tuple[dict[str, str], bool]]  # per sense: see ``usage.sense_labels``

    @property
    def labels(self) -> list[str]:
        """The part-of-speech labels of the heading."""
        return [label for label, _ in self.pos.wortarten]

    @property
    def left_out(self) -> bool:
        """Whether every sense is marked. A section without senses stays."""
        return bool(self.senses) and all(found for found, _ in self.senses)


def lemma_sections(title: str, text: str) -> Iterator[LemmaSection]:
    """Every German part-of-speech section of a page, kept or not."""
    for entry in german_sections(text):
        for number, pos in enumerate(entry.pos_sections, 1):
            body = pos.section.body(text)
            senses = [sense_labels(line) for line in sense_lines(body)]
            yield LemmaSection(title, number, pos, body, senses)


def kept_sections(title: str, text: str) -> Iterator[LemmaSection]:
    """The German part-of-speech sections of a page that go into the database."""
    return (section for section in lemma_sections(title, text) if not section.left_out)


def verb_selection(sections: Iterable[LemmaSection]) -> str | None:
    """Whether the verb sections among ``sections`` (those of one lemma page) are all kept,
    all left out or mixed; ``None`` if there is no verb section."""
    flags = {section.left_out for section in sections if "Verb" in section.labels}
    if not flags:
        return None
    if len(flags) == 2:
        return MIXED
    return LEFT_OUT if flags.pop() else KEPT


def keeps_flexion(selection: str | None) -> bool:
    """Whether the conjugations of a ``Flexion:`` page are kept, given the
    :func:`verb_selection` of its lemma page. They are left out only if all verb sections of
    the lemma page are; where only some are, all conjugations stay."""
    return selection != LEFT_OUT
