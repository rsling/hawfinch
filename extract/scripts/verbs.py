"""Feasibility test of verb stems (step 2).

Reads every German verb conjugation from the ``Flexion:`` pages, derives its stems, generates
the principal forms from them and compares these with ``Deutsch Verb Übersicht`` on the lemma
page. A lemma page can hold several verb sections and a ``Flexion:`` page several
conjugations (trennbar and untrennbar, weak and strong, reflexive); each overview table is
paired with the conjugation on the page of the same name that reproduces most of its forms.

A form agrees if the main form of the overview table is among the generated variants
(``main``), and agrees fully if the two sets of variants are the same (``full``).

Writes to ``data/interim/feasibility/verbs/``:

- ``stems.tsv``: one row per conjugation, with the stems and the generated forms;
- ``comparison.tsv``: one row per overview table, with the paired conjugation and the
  agreement of each form;
- ``mismatches.tsv``: one row per form whose main form is not generated;
- ``summary.tsv``: agreement by template class and form;
- ``sample.tsv``: a stratified sample of conjugations for checking by hand. If
  ``sample.annotated.tsv`` exists, its rows are kept with their annotation and shown with
  their current values instead of drawing a new sample.
"""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

from hawfinch.features.inflection import (
    PRINCIPAL_FORMS,
    REGULAR,
    STEM_FIELDS,
    VERB_TEMPLATES,
    Verb,
    conjugation_class,
    is_copula_group,
    lexeme_stem,
    overview_forms,
    principal_forms,
    read_verb,
    split_prefix,
    stem_variants,
    stems,
)
from hawfinch.features.usage import restricted
from hawfinch.wikitext.sections import german_sections
from hawfinch.wikitext.templates import scan

FLEXION_NS = 108
FLEXION_PREFIX = "Flexion:"
OVERVIEW = "Deutsch Verb Übersicht"
SEED = 20261125
PER_STRATUM = 9
ANNOTATED = "sample.annotated.tsv"
STEM_KEYS = STEM_FIELDS


def stratum(verb: Verb) -> str:
    """Class of a conjugation, for the summary and the sample."""
    if verb.weak:
        if verb.template != REGULAR:
            return "weak, reflexive template"
        if verb.word_group:
            return "weak, several words"
        if verb.infinitive.endswith(("eln", "ern")):
            return "weak, -eln/-ern"
        if verb.present.endswith(("s", "ß", "x", "z")):
            return "weak, stem in sibilant"
        if verb.present.endswith(("d", "t", "m", "n")):
            return "weak, stem in d/t/m/n"
        return "weak, separable" if verb.separable else "weak, other"
    if verb.special:
        return "irregular, modal/tun/wissen"
    if verb.mixed:
        return "mixed"
    if verb.overrides:
        return "sein" if verb.infinitive == "sein" else "strong, single forms given"
    if verb.present_2sg != verb.present:
        return "strong, vowel change in present"
    return "strong, separable" if verb.separable else "strong, other"


def process_row_group(args) -> tuple[list[dict], list[dict], Counter, dict[str, list[bool]]]:
    """Conjugations, overview tables, unread templates, and for every lemma page with verb
    sections whether each of them is left out as archaic or regional."""
    path, index = args
    table = pq.ParquetFile(path).read_row_group(index, columns=["ns", "title", "text", "redirect"])
    conjugations, overviews, unread, left_out = [], [], Counter(), {}
    for row in table.to_pylist():
        if row["redirect"] is not None:
            continue
        text = row["text"]
        if row["ns"] == FLEXION_NS and "Deutsch Verb" in text:
            title = row["title"].removeprefix(FLEXION_PREFIX)
            for template in scan(text).templates:
                if template.name not in VERB_TEMPLATES:
                    continue
                verb = read_verb(template)
                if verb is None:
                    unread[template.name] += 1
                    continue
                conjugations.append({"title": title, "verb": verb, "start": template.start})
        elif row["ns"] == 0 and OVERVIEW in text:
            for entry in german_sections(text):
                for number, pos in enumerate(entry.pos_sections, 1):
                    body = pos.section.body(text)
                    if any(label == "Verb" for label, _ in pos.wortarten):
                        left_out.setdefault(row["title"], []).append(restricted(body))
                    if restricted(body):
                        continue
                    for template in scan(body).templates:
                        if template.name == OVERVIEW:
                            overviews.append(
                                {
                                    "title": row["title"],
                                    "section": number,
                                    "labels": "+".join(label for label, _ in pos.wortarten),
                                    "forms": overview_forms(template),
                                }
                            )
    return conjugations, overviews, unread, left_out


def agreement(generated: dict[str, list[str]], listed: dict[str, list[str]]) -> dict[str, str]:
    """Per principal form: ``full``, ``main`` (main form generated, variants differ) or ``no``."""
    result = {}
    for key in PRINCIPAL_FORMS:
        ours, theirs = generated[key], listed[key]
        if set(ours) == set(theirs):
            result[key] = "full"
        elif theirs and theirs[0] in ours:
            result[key] = "main"
        else:
            result[key] = "no"
    return result


def pair(overview: dict, candidates: list[dict]) -> tuple[dict, dict[str, str]] | None:
    best = None
    for candidate in candidates:
        result = agreement(candidate["forms"], overview["forms"])
        score = (
            sum(v != "no" for v in result.values()),
            sum(v == "full" for v in result.values()),
            candidate["verb"].auxiliary in overview["forms"]["Hilfsverb"],
        )
        if best is None or score > best[0]:
            best = (score, candidate, result)
    return None if best is None else (best[1], best[2])


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _join(values: list[str]) -> str:
    return " / ".join(values) if values else "—"


def _variants(conjugations: list[dict], simplex: set[str]) -> list[dict]:
    """One row per variant stem: those a conjugation gives itself, and those of a parallel
    conjugation (``frug`` besides ``fragte``), that is, of a later conjugation on the same
    page with the same particles and reflexivity whose stems differ from the first one's."""
    rows = []
    first: dict[tuple, dict] = {}
    for conjugation in conjugations:
        verb = conjugation["verb"]
        if is_copula_group(verb):
            continue
        key = (conjugation["title"], verb.particles, verb.reflexive)
        lexeme = lexeme_stem(verb, simplex)
        found = [(*v, "same conjugation") for v in stem_variants(verb, simplex)]
        base = first.setdefault(key, conjugation)
        if base is not conjugation:
            found += [
                (name, stem, "parallel conjugation")
                for name, stem in conjugation["stems"].items()
                if stem != base["stems"][name]
            ]
            found += [
                (name, stem, "parallel conjugation")
                for name, stem in stem_variants(verb, simplex)
                if (name, stem) not in stem_variants(base["verb"], simplex)
            ]
            found = [f for f in found if f[2] == "parallel conjugation"]
        for name, stem, source in dict.fromkeys(found):
            rows.append(
                {
                    "title": conjugation["title"],
                    "lexeme": lexeme,
                    "reflexive": "yes" if verb.reflexive else "",
                    "field": name,
                    "stem": stem,
                    "class": conjugation_class(verb),
                    "source": source,
                }
            )
    return rows


def _sample_key(row: dict) -> tuple:
    return row["title"], row["participles"], row["auxiliary"], row["reflexive"]


def _annotated_sample(path: Path, stem_rows: list[dict]) -> list[dict] | None:
    """The rows of an already annotated sample with their current values, so that a rerun
    does not draw a new sample and lose the annotation."""
    if not path.exists():
        return None
    current = {}
    for row in stem_rows:
        current.setdefault(_sample_key(row), row)
    with path.open(encoding="utf-8", newline="") as fh:
        annotated = list(csv.DictReader(fh, delimiter="\t"))
    return [
        {**current[_sample_key(old)], "correct": old["correct"], "comment": old["comment"]}
        for old in annotated
        if _sample_key(old) in current
    ]


def run(cache: Path, out: Path, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    groups = pq.ParquetFile(cache).num_row_groups
    conjugations, overviews, unread, left_out = [], [], Counter(), {}
    with ProcessPoolExecutor(workers) as pool:
        for c, o, u, x in pool.map(process_row_group, [(cache, i) for i in range(groups)]):
            conjugations += c
            overviews += o
            unread += u
            left_out.update(x)
    # A Flexion page does not say which verb section of the lemma page a conjugation belongs
    # to. Its conjugations are left out if all verb sections of the lemma page are.
    read = len(conjugations)
    conjugations = [c for c in conjugations if not all(left_out.get(c["title"], [False]))]
    dropped = read - len(conjugations)
    mixed = sum(any(flags) and not all(flags) for flags in left_out.values())
    conjugations.sort(key=lambda c: (c["title"], c["start"]))
    overviews.sort(key=lambda o: (o["title"], o["section"]))

    simplex = {
        c["verb"].present
        for c in conjugations
        if not c["verb"].particles and split_prefix(c["verb"])[0] == ""
    }
    by_title = defaultdict(list)
    for number, conjugation in enumerate(conjugations):
        verb = conjugation["verb"]
        conjugation.update(
            id=number,
            forms=principal_forms(verb),
            stems=stems(verb, simplex),
            stratum=stratum(verb),
        )
        conjugation["matched"] = "no overview table"
        by_title[conjugation["title"]].append(conjugation)

    comparison, mismatches = [], []
    for overview in overviews:
        row = {"title": overview["title"], "section": overview["section"]}
        paired = pair(overview, by_title.get(overview["title"], []))
        if paired is None:
            comparison.append({**row, "status": "no Flexion page"})
            continue
        conjugation, result = paired
        verb = conjugation["verb"]
        auxiliary = verb.auxiliary in overview["forms"]["Hilfsverb"]
        if all(v == "full" for v in result.values()):
            status = "full"
        elif all(v != "no" for v in result.values()):
            status = "main"
        else:
            status = "differs"
        rank = ["differs", "main", "full"]
        if conjugation["matched"] not in rank or rank.index(status) > rank.index(
            conjugation["matched"]
        ):
            conjugation["matched"] = status
        comparison.append(
            {
                **row,
                "conjugation": conjugation["id"],
                "template": verb.template,
                "stratum": conjugation["stratum"],
                "status": status,
                "auxiliary": "yes" if auxiliary else "no",
                **result,
            }
        )
        for key, value in result.items():
            if value == "no":
                mismatches.append(
                    {
                        **row,
                        "stratum": conjugation["stratum"],
                        "form": key,
                        "generated": _join(conjugation["forms"][key]),
                        "overview": _join(overview["forms"][key]),
                    }
                )

    stem_rows = []
    for conjugation in conjugations:
        verb = conjugation["verb"]
        if is_copula_group(verb):  # ab sein: compared above, but not a lexeme
            continue
        stem_rows.append(
            {
                "id": conjugation["id"],
                "title": conjugation["title"],
                "template": verb.template.removeprefix("Deutsch Verb "),
                "stratum": conjugation["stratum"],
                "lexeme": lexeme_stem(verb, simplex),
                "class": conjugation_class(verb),
                **conjugation["stems"],
                "participles": _join(list(verb.participles)),
                "auxiliary": verb.auxiliary,
                "reflexive": "yes" if verb.reflexive else "",
                "matched": conjugation["matched"],
                **{key: _join(conjugation["forms"][key]) for key in PRINCIPAL_FORMS[:-1]},
            }
        )
    variant_rows = _variants(conjugations, simplex)
    _write(out / "variants.tsv", list(variant_rows[0]), variant_rows)
    stem_fields = list(stem_rows[0])
    _write(out / "stems.tsv", stem_fields, stem_rows)
    comparison_fields = [
        "title",
        "section",
        "conjugation",
        "template",
        "stratum",
        "status",
        "auxiliary",
        *PRINCIPAL_FORMS,
    ]
    _write(out / "comparison.tsv", comparison_fields, comparison)
    _write(
        out / "mismatches.tsv",
        ["title", "section", "stratum", "form", "generated", "overview"],
        mismatches,
    )

    summary = []
    paired_rows = [r for r in comparison if r["status"] != "no Flexion page"]
    strata = sorted({r["stratum"] for r in paired_rows})
    for name in [*strata, "all"]:
        rows = [r for r in paired_rows if name in ("all", r["stratum"])]
        entry = {"stratum": name, "tables": len(rows)}
        for status in ("full", "main", "differs"):
            entry[status] = sum(r["status"] == status for r in rows)
        entry["auxiliary differs"] = sum(r["auxiliary"] == "no" for r in rows)
        for key in PRINCIPAL_FORMS:
            entry[key] = sum(r[key] == "no" for r in rows)
        summary.append(entry)
    _write(out / "summary.tsv", list(summary[0]), summary)

    sample = _annotated_sample(out / ANNOTATED, stem_rows)
    if sample is None:
        rng = random.Random(SEED)
        sample = []
        by_stratum = defaultdict(list)
        for row in stem_rows:
            by_stratum[row["stratum"]].append(row)
        for name in sorted(by_stratum):
            rows = by_stratum[name]
            sample += rng.sample(rows, min(PER_STRATUM, len(rows)))
    sample_fields = [
        "stratum",
        "title",
        "lexeme",
        "class",
        *STEM_KEYS,
        "participles",
        "auxiliary",
        "reflexive",
        "matched",
        "correct",
        "comment",
    ]
    _write(
        out / "sample.tsv",
        sample_fields,
        [{k: row.get(k, "") for k in sample_fields} for row in sample],
    )

    status = Counter(r["status"] for r in comparison)
    matched = Counter(c["matched"] for c in conjugations)
    print(f"{dropped:,} of {read:,} conjugations left out as archaic or regional")
    print(f"{mixed} lemma pages with some verb sections left out, conjugations kept")
    print(f"{len(variant_rows):,} variant stems")
    print(f"{len(conjugations) - len(stem_rows)} combinations with sein left out of stems.tsv")
    print(f"{len(conjugations):,} conjugations read, {sum(unread.values())} not readable")
    print(f"{len(overviews):,} overview tables: {dict(status)}")
    print(f"conjugations by best pairing: {dict(matched)}")
    print(f"{len(mismatches):,} forms differ -> {out}")
