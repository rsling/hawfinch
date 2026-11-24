"""Part of speech of a lexeme, from the ``{{Wortart|…}}`` labels of its Wiktionary section.

Proper nouns are a part of speech of their own (decision 0003). German Wiktionary has no
single label for them: a proper noun's section is usually headed ``Substantiv`` plus a
second label naming the kind of name (``Toponym``, ``Nachname``, ``Vorname``, ``Eigenname``,
…). This module is the label rule, the detection mode used when no language model is
configured: a section is a proper noun if any of its labels is a name label, or if it is a
``Substantiv`` whose first meaning line defines it as a language. Otherwise a ``Substantiv``
is a common noun. Sense-level classification by an optional language model is the other mode
(decision 0006). Definitions are in docs/features/part-of-speech.md.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

NAME_LABELS = frozenset(
    {"Toponym", "Nachname", "Vorname", "Eigenname", "Göttername", "Bauwerksname", "Straßenname"}
)

PROPER_NOUN = "proper noun"
COMMON_NOUN = "common noun"

# The first meaning line is headed by "Sprache", "-sprache" or "Varietät": only an optional
# subject label, an article and up to five lower-case words (adjectives, participles) come
# before it. A register label such as "Seemannssprache:" or "(Jägersprache)" does not count.
LANGUAGE_NAME = re.compile(
    r"^:?\[1\]\s+"
    r"(?:[A-ZÄÖÜ][a-zäöü]+wissenschaft:\s+)?"
    r"(?:(?:die|eine|der|ein)\s+)?"
    r"(?:[a-zäöüß][\w-]*\s+){0,5}"
    r"(?:\w*[Ss]prache|Varietät)\b(?!\s*[:)])"
)
NAMES_A_LANGUAGE_KIND = re.compile(r"[Ss]prache$")  # Fachsprache, Zeichensprache


def is_language_name(title: str, first_sense: str) -> bool:
    """Whether the first meaning line, as plain text (``:[1] …``), defines a language."""
    return bool(LANGUAGE_NAME.search(first_sense)) and not NAMES_A_LANGUAGE_KIND.search(title)


def noun_class(
    labels: Iterable[str], *, title: str | None = None, first_sense: str | None = None
) -> str | None:
    """``PROPER_NOUN``, ``COMMON_NOUN``, or ``None`` for sections that are not nouns.

    Without ``title`` and ``first_sense`` only the labels are used.
    """
    labels = set(labels)
    if labels & NAME_LABELS:
        return PROPER_NOUN
    if "Substantiv" in labels:
        if title and first_sense and is_language_name(title, first_sense):
            return PROPER_NOUN
        return COMMON_NOUN
    return None
