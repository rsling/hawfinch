"""Usage labels on senses: archaic, regional, Austrian and Swiss.

First version, written for the feasibility test. The definition is in
``docs/features/usage-labels.md``.

The labels are on the lines of the block ``Bedeutungen``, one line per sense, in three forms:
arguments of ``{{K|…}}`` (``{{K|Schweiz|ugs.}}``), label templates without arguments
(``{{österr.}}``), and italic text at the start of the line (``''koblenzisch:''``). A label
counts for a sense unless it is qualified in the same place (``besonders``, ``auch``,
``sonst``): a qualified label says that the sense is also in use elsewhere.

:func:`sense_labels` reads one sense line, and :func:`restricted` says whether every sense
of a section carries a label; such a section is not taken into the database. The rule is
applied to the pages in ``hawfinch.features.selection``.
"""

from __future__ import annotations

import re

from hawfinch.wikitext.sections import blocks
from hawfinch.wikitext.templates import scan

KINDS = ("archaic", "regional", "Austrian", "Swiss")
PATTERNS = {
    "archaic": re.compile(
        r"^(veraltet|veraltend|va\.|vatd\.|Bedva\.|tlwva\.|verschwunden|archaisch|altertümlich"
        r"|altertümelnd)$"
    ),
    "Austrian": re.compile(
        r"österr|Österr|^Wien$|wienerisch|Kärnten|Vorarlberg|^Tirol|^tirol|Steiermark|steirisch"
    ),
    "Swiss": re.compile(r"[Ss]chweiz|^CH&LI$|Liechtenstein"),
    "regional": re.compile(
        r"^(regional|reg\.|landsch\.|landschaftlich|mundartlich|mundartnah|mdal\.|dialektal"
        r"|nordd\.|südd\.|süddt\.|md\.|bar\.|bair\.|schwäb\.)$"
        r"|^(nord|süd|ost|west|mittel|ober|nieder|platt|ruhr)\w*deutsch(land)?$"
        r"|^(Nord|Süd|Ost|West|Mittel)\w*deutsch(land)?$"
        r"|bairisch|bay(e)?risch|^Bayern$|schwäbisch|alemannisch|berlin(er)?isch|^Berlin$"
        r"|pfälzisch|rheinisch|rheinländisch|^Rheinland$|fränkisch|sächsisch|^Sachsen$|hessisch"
        r"|erzgebirgisch|meißnisch|osterländisch|vogtländisch|schlesisch|saarländisch"
        r"|westfälisch|thüringisch|^Thüringen$|kölsch|[Kk]oblenzisch|luxemburgisch|^Luxemburg$"
        r"|^Belgien$|^Südtirol$|^Brandenburg$|^Mecklenburg$|^Baden$|badisch|^Preußen$"
    ),
}
QUALIFIERS = frozenset(
    {"besonders", "bes.", "auch", "meist", "meistens", "sonst", "oft", "häufig", "vor allem",
     "überwiegend", "vorwiegend", "teilweise", "teils", "außer", "allgemein"}
)  # fmt: skip
SENSE = re.compile(r"^:+\[")
_ITALIC = re.compile(r"^:+\[[^\]]*\]\s*''([^']+)''")
_WORD = re.compile(r"[\wäöüÄÖÜß.&]+")


def kinds_of(value: str) -> set[str]:
    return {kind for kind, pattern in PATTERNS.items() if pattern.search(value)}


def sense_labels(line: str) -> tuple[dict[str, str], bool]:
    """Kinds of label on one sense line, each with the value that gave it, and whether a
    label was left out because it is qualified."""
    found, qualified = {}, False
    for template in scan(line).templates:
        if template.name == "K":
            values = [v.strip() for key, v in template.args if key is None]
            labels = {kind: v for v in values for kind in kinds_of(v)}
            if labels and QUALIFIERS.intersection(values):
                qualified = True
            else:
                found.update(labels)
        elif not template.args or all(key is None for key, _ in template.args):
            for kind in kinds_of(template.name):
                found[kind] = template.name
    m = _ITALIC.match(line)
    if m:
        words = _WORD.findall(m.group(1))
        labels = {kind: w for w in words for kind in kinds_of(w)}
        if labels and QUALIFIERS.intersection(words):
            qualified = True
        else:
            found.update(labels)
    return found, qualified


def sense_lines(body: str) -> list[str]:
    """The lines of ``Bedeutungen`` that give a sense."""
    return [line for line in blocks(body).get("Bedeutungen", []) if SENSE.match(line)]


def restricted(body: str) -> bool:
    """Whether every sense of a part-of-speech section is marked as archaic, regional,
    Austrian or Swiss. A section without senses is not restricted."""
    senses = sense_lines(body)
    return bool(senses) and all(sense_labels(line)[0] for line in senses)
