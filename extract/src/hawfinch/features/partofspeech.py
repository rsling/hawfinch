"""Part of speech of a lexeme, from the ``{{Wortart|…}}`` labels of its Wiktionary section.

Lexemes keep Wiktionary's labels, with exceptions (docs/features/part-of-speech.md): the
form-entry labels (decision 0004), ``Abkürzung`` (decision 0005), and the name labels below.
A name label says that the section names something (``{{Wortart|Toponym|Deutsch}}`` next to
``Substantiv``). It is not a part of speech: it marks the senses for the ``named_entity`` field
of their lexical units (decision 0003). A section whose only labels are name labels is a
``Substantiv``.
"""

from __future__ import annotations

NAME_LABELS = frozenset(
    {"Toponym", "Nachname", "Vorname", "Eigenname", "Göttername", "Bauwerksname", "Straßenname"}
)
