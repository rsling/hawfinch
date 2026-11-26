"""Which part-of-speech sections of a lemma page go into the database.

A part-of-speech section is left out if all its senses are marked as archaic, regional,
Austrian or Swiss (``docs/features/usage-labels.md``). A section that only points to another
spelling is not a lexeme either (``docs/features/part-of-speech.md``). The rules hold for
every part of speech, so they are applied here and not in the readers of the single
features: :func:`lemma_sections` gives every German part-of-speech section of a page with
the labels of its senses, and :func:`kept_sections` only those that stay.

``Flexion:`` pages are not sections of a lemma page, and a conjugation does not say which
verb section of the lemma page it belongs to. :func:`verb_selection` sums up the verb
sections of a lemma page that are not spelling variants (:func:`verb_sections`). Where only
some of them are left out, :func:`flexion_selection` assigns the conjugations of the
``Flexion:`` page of the same name to the sections whose overview table they reproduce.
What it cannot assign is ``undecided`` and needs a row in the patch :data:`FLEXION_PATCH`
(``extract/patches/flexion-sections.tsv``, ``docs/decisions/0007-patches.md``), whose rows are
keyed by :func:`conjugation_key`.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property

from hawfinch.features.inflection import PARTICIPLE, PRETERITE, Verb, principal_forms
from hawfinch.features.usage import sense_labels, sense_lines
from hawfinch.patches import PatchSpec
from hawfinch.wikitext.sections import PosSection, german_sections
from hawfinch.wikitext.templates import scan

KEPT = "kept"
MIXED = "mixed"
LEFT_OUT = "left out"
UNDECIDED = "undecided"

# Which verb section a conjugation goes with, where the rule leaves it undecided.
FLEXION_PATCH = PatchSpec(
    name="flexion-sections",
    key=("title", "preterite", "participle", "auxiliary", "reflexive"),
    values={"decision": frozenset({KEPT, LEFT_OUT})},
)

# Templates that point to the entry of another spelling.
SPELLING_VARIANTS = frozenset({"Schweizer und Liechtensteiner Schreibweise", "Alte Schreibweise"})


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

    @cached_property
    def spelling_variant(self) -> bool:
        """Whether the section only points to the entry of another spelling: it has no
        senses and holds a spelling-variant template (``verrussen``, the Swiss spelling of
        ``verrußen``). Such a section is not a lexeme."""
        return not self.senses and any(
            template.name in SPELLING_VARIANTS for template in scan(self.body).templates
        )


def lemma_sections(title: str, text: str) -> Iterator[LemmaSection]:
    """Every German part-of-speech section of a page, kept or not."""
    for entry in german_sections(text):
        for number, pos in enumerate(entry.pos_sections, 1):
            body = pos.section.body(text)
            senses = [sense_labels(line) for line in sense_lines(body)]
            yield LemmaSection(title, number, pos, body, senses)


def kept_sections(title: str, text: str) -> Iterator[LemmaSection]:
    """The German part-of-speech sections of a page that go into the database."""
    return (
        section
        for section in lemma_sections(title, text)
        if not section.left_out and not section.spelling_variant
    )


def verb_sections(sections: Iterable[LemmaSection]) -> dict[int, bool]:
    """The verb sections among ``sections`` (those of one lemma page) that are not spelling
    variants, by number, with whether they are left out."""
    return {
        section.number: section.left_out
        for section in sections
        if "Verb" in section.labels and not section.spelling_variant
    }


def verb_selection(sections: Iterable[LemmaSection]) -> str | None:
    """Whether the verb sections among ``sections`` (those of one lemma page) are all kept,
    all left out or mixed; ``None`` if there is no verb section."""
    flags = set(verb_sections(sections).values())
    if not flags:
        return None
    if len(flags) == 2:
        return MIXED
    return LEFT_OUT if flags.pop() else KEPT


def flexion_selection(
    left_out: Mapping[int, bool], fits: Sequence[Mapping[int, bool]]
) -> list[str]:
    """For each conjugation of a ``Flexion:`` page, whether it is kept, left out or undecided.

    ``left_out`` says for each verb section of the lemma page (by number) whether it is left
    out. ``fits`` says for each conjugation which verb sections it reproduces; a section
    without an overview table is missing from that mapping.

    If all verb sections are left out, so are all conjugations; if none is, or there is no
    verb section, all are kept. Otherwise a conjugation is kept if it reproduces a section
    that stays. It is left out if it reproduces only sections that are left out, provided
    that every section that stays has a table and a conjugation that reproduces it: a
    conjugation can serve two sections of which it reproduces only one (``tauen``, where the
    sections differ in the auxiliary). Everything else is undecided.
    """
    if not any(left_out.values()):
        return [KEPT] * len(fits)
    if all(left_out.values()):
        return [LEFT_OUT] * len(fits)
    staying = [number for number, out in left_out.items() if not out]
    served = all(any(fit.get(number) for fit in fits) for number in staying)
    result = []
    for fit in fits:
        if any(fit.get(number) for number in staying):
            result.append(KEPT)
        elif served and any(fit.values()):
            result.append(LEFT_OUT)
        else:
            result.append(UNDECIDED)
    return result


def conjugation_key(title: str, verb: Verb) -> tuple[str, ...]:
    """The key of a conjugation in :data:`FLEXION_PATCH`: the page title, the preterite and
    the participle as the conjugation generates them (variants joined by `` / ``), the
    auxiliary, and ``yes`` if it is reflexive. It names the conjugation by its content, so a
    row stops matching when Wiktionary changes the conjugation."""
    forms = principal_forms(verb)
    return (
        title,
        " / ".join(forms[PRETERITE]),
        " / ".join(forms[PARTICIPLE]),
        verb.auxiliary,
        "yes" if verb.reflexive else "",
    )
