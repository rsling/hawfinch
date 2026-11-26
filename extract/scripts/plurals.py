"""Feasibility test of the plural class (step 2).

Reads every ``Deutsch Substantiv Übersicht`` and ``Deutsch adjektivisch Übersicht`` in a
German section, and classifies each nominative plural against each singular of the table
(see ``docs/features/plural-classes.md``). Sections whose senses are all marked as archaic,
regional, Austrian or Swiss are left out (``docs/features/usage-labels.md``). There is no
second source to compare with; the
test shows how the plurals are distributed over the classes.

Writes to ``data/interim/feasibility/plurals/``:

- ``plurals.tsv``: one row per singular and plural of a table, with class, plural stem and
  segmented plural;
- ``variants.tsv``: one row per genitive singular that does not fit the class of its noun;
- ``summary.tsv``: rows by gender, class, suffix type, umlaut and note;
- ``sections.tsv``: tables by what they hold;
- ``unclassified.tsv``: all rows without a class;
- ``sample.tsv``: a stratified sample for checking by hand. If ``sample.annotated.tsv``
  exists, its rows are kept with their annotation and shown with their current values.
"""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

from hawfinch.features.declension import (
    ADJECTIVAL_TABLE,
    GENDERS,
    LOAN,
    NAME_TABLES,
    NO_GENDER,
    NOTE_WORDS,
    NOTE_ZERO,
    NOUN_TABLE,
    PRIMARY,
    PluralType,
    adjectival_types,
    name_types,
    noun_types,
    read_noun,
)
from hawfinch.features.selection import lemma_sections
from hawfinch.wikitext.templates import scan

TABLES = frozenset({NOUN_TABLE, ADJECTIVAL_TABLE}) | NAME_TABLES
SEED = 20261126
PER_STRATUM = 6
ANNOTATED = "sample.annotated.tsv"
FIELDS = [
    "title",
    "section",
    "labels",
    "table",
    "gender",
    "singular",
    "genitive",
    "plural",
    "class",
    "stem",
    "segmented",
    "suffix",
    "umlaut",
    "genitive_variants",
    "note",
    "genders",
    "plurals",
]


def _row(found: PluralType, genitives: tuple[str, ...] = ()) -> dict:
    return {
        "gender": found.gender,
        "singular": found.singular or "",
        "genitive": " / ".join(genitives) if found.singular else "",
        "plural": "",
        "class": found.plural_class or "",
        "stem": found.stem,
        "segmented": found.segmented,
        "suffix": found.suffix or "",
        "umlaut": "yes" if found.umlaut else "no",
        "genitive_variants": " / ".join(found.genitive_variants),
        "note": found.note,
    }


def _table_rows(template, title: str, heading: str) -> tuple[str, list[dict], int, int]:
    """Kind of table, its rows, and its numbers of singulars and plurals. ``heading`` is the
    gender given in the heading of the section, used where the table gives none."""
    if template.name in NAME_TABLES:
        found = name_types(template, title, heading)
        rows = [{**_row(f), "plural": f.segmented.replace("-", "")} for f in found]
        for row, f in zip(rows, found, strict=True):
            head, _, tail = f.segmented.rpartition("-")
            row["plural"] = head + tail
        return ("name table" if found else "name table, no plural"), rows, 1, len(found)
    if template.name == ADJECTIVAL_TABLE:
        found = adjectival_types(template)
        rows = [_row(f) for f in found]
        for row, f in zip(rows, found, strict=True):
            head, _, tail = f.segmented.rpartition("-")
            row["plural"] = head + tail
        return ("adjectival table" if found else "adjectival table, no plural"), rows, 1, len(found)
    noun = read_noun(template)
    if not noun.plurals:
        return "no plural", [], len(noun.singulars), 0
    rows = []
    for singular, found in noun_types(noun, heading):
        head, _, tail = found.segmented.rpartition("-")
        rows.append({**_row(found, singular.genitives if singular else ()), "plural": head + tail})
    if not noun.singulars:
        return "plural only", rows, 0, len(noun.plurals)
    if len(noun.singulars) > 1:
        kind = "several genders"
    elif len(noun.plurals) > 1:
        kind = "several plurals"
    else:
        kind = "one plural"
    return kind, rows, len(noun.singulars), len(noun.plurals)


def process_row_group(args) -> tuple[list[dict], Counter]:
    path, index = args
    table = pq.ParquetFile(path).read_row_group(index, columns=["ns", "title", "text", "redirect"])
    rows, sections = [], Counter()
    for page in table.to_pylist():
        if page["redirect"] is not None or page["ns"] != 0 or "Übersicht" not in page["text"]:
            continue
        for section in lemma_sections(page["title"], page["text"]):
            tables = [t for t in scan(section.body).templates if t.name in TABLES]
            if section.left_out:
                sections["left out: all senses archaic or regional"] += len(tables)
                continue
            if section.spelling_variant:
                sections["left out: spelling variant"] += len(tables)
                continue
            genders_given = [t.name for t in section.pos.heading_templates if t.name in GENDERS]
            heading = genders_given[0] if len(genders_given) == 1 else ""
            for template in tables:
                kind, found, genders, plurals = _table_rows(template, page["title"], heading)
                sections[kind] += 1
                for row in found:
                    rows.append(
                        {
                            "title": page["title"],
                            "section": section.number,
                            "labels": "+".join(section.labels),
                            "table": template.name.removeprefix("Deutsch ").removesuffix(
                                " Übersicht"
                            ),
                            **row,
                            "genders": genders,
                            "plurals": plurals,
                        }
                    )
    return rows, sections


def stratum(row: dict) -> str:
    """Class of a row for the sample: the plural class, divided where it is large."""
    gender, plural_class = row["gender"], row["class"]
    if not plural_class:
        return "no class"
    if row["note"] == NOTE_WORDS:
        return "several words, inflected inside"
    if plural_class == LOAN:
        return "loan, no suffix" if row["note"] == NOTE_ZERO else "loan"
    if plural_class == PRIMARY:
        if gender == NO_GENDER:
            return "primary, no singular"
        if gender == "f":
            return "primary, f"
        if row["segmented"].endswith("-"):
            return "primary, m/n, no suffix"
        if gender == "m":
            return "primary, m, -e, umlaut" if row["umlaut"] == "yes" else "primary, m, -e"
        return "primary, n, -e"
    if plural_class in ("secondary", "marked-r"):
        return f"{plural_class}, {gender}"
    return plural_class


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def _plural_of(row: dict) -> str:
    head, _, tail = row["segmented"].rpartition("-")
    return row.get("plural") or head + tail


def _annotated_sample(path: Path, rows: list[dict]) -> list[dict] | None:
    """The rows of an already annotated sample with their current values, so that a rerun
    does not draw a new sample and lose the annotation. A row is found again by its page and
    its plural, and by its gender where that is still the same."""
    if not path.exists():
        return None
    exact, loose = {}, {}
    for row in rows:
        exact.setdefault((row["title"], row["plural"], row["gender"]), row)
        loose.setdefault((row["title"], row["plural"]), row)
    with path.open(encoding="utf-8", newline="") as fh:
        annotated = list(csv.DictReader(fh, delimiter="\t"))
    result = []
    for old in annotated:
        key = (old["title"], _plural_of(old))
        current = exact.get((*key, old["gender"])) or loose.get(key)
        if current is None:
            current = {**old, "stratum": "no longer in the data"}
        result.append(
            {
                **current,
                "checked_as": old.get("checked_as") or f"{old['class']}: {old['segmented']}",
                "correct": old["correct"],
                "comment": old["comment"],
            }
        )
    return result


def run(cache: Path, out: Path, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    groups = pq.ParquetFile(cache).num_row_groups
    rows, sections = [], Counter()
    with ProcessPoolExecutor(workers) as pool:
        for found, counted in pool.map(process_row_group, [(cache, i) for i in range(groups)]):
            rows += found
            sections += counted
    rows.sort(key=lambda r: (r["title"], r["section"], r["gender"], r["plural"]))
    for row in rows:
        row["stratum"] = stratum(row)
    _write(out / "plurals.tsv", FIELDS, rows)
    _write(out / "unclassified.tsv", FIELDS, [r for r in rows if not r["class"]])
    variants = [
        {**row, "field": "genitive singular", "form": form}
        for row in rows
        for form in row["genitive_variants"].split(" / ")
        if form
    ]
    _write(
        out / "variants.tsv",
        ["title", "section", "gender", "singular", "plural", "class", "field", "form"],
        variants,
    )

    keys = ("table", "gender", "class", "suffix", "umlaut", "note")
    counts = Counter(tuple(r[k] for k in keys) for r in rows)
    summary = [
        dict(zip((*keys, "rows"), (*key, n), strict=True))
        for key, n in sorted(counts.items(), key=lambda kv: (kv[0][:3], -kv[1]))
    ]
    _write(out / "summary.tsv", [*keys, "rows"], summary)
    _write(
        out / "sections.tsv",
        ["tables", "count"],
        [{"tables": name, "count": n} for name, n in sections.most_common()],
    )

    sample = _annotated_sample(out / ANNOTATED, rows)
    if sample is None:
        rng = random.Random(SEED)
        by_stratum = defaultdict(list)
        for row in rows:
            by_stratum[row["stratum"]].append(row)
        sample = []
        for name in sorted(by_stratum):
            sample += rng.sample(by_stratum[name], min(PER_STRATUM, len(by_stratum[name])))
    sample_fields = [
        "stratum",
        "title",
        "gender",
        "singular",
        "genitive",
        "class",
        "stem",
        "segmented",
        "genitive_variants",
        "note",
        "checked_as",
        "correct",
        "comment",
    ]
    _write(
        out / "sample.tsv",
        sample_fields,
        [{k: row.get(k, "") for k in sample_fields} for row in sample],
    )
    strata = Counter(r["stratum"] for r in rows)
    _write(
        out / "strata.tsv",
        ["stratum", "rows"],
        [{"stratum": name, "rows": n} for name, n in sorted(strata.items())],
    )

    classes = Counter(r["class"] or "(none)" for r in rows)
    print(f"{sum(sections.values()):,} tables: {dict(sections.most_common())}")
    print(f"{len(rows):,} rows: {dict(classes.most_common())}")
    print(f"{len(variants):,} genitive variants; {len(sample)} rows in the sample -> {out}")
