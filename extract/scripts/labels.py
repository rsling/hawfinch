"""Feasibility survey of usage labels (step 2): how many German lemma sections does
Wiktionary mark as archaic, regional, Austrian or Swiss?

The labels are read by ``hawfinch.features.usage`` (see ``docs/features/usage-labels.md``).

Writes to ``data/interim/feasibility/labels/``:

- ``sections.tsv``: one row per section with at least one labelled sense;
- ``summary.tsv``: sections by part of speech, kind of label and whether all senses or only
  some carry it;
- ``values.tsv``: the label values that were counted, by kind.
"""

from __future__ import annotations

import csv
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

from hawfinch.features.selection import lemma_sections
from hawfinch.features.usage import KINDS


def pos_group(labels: list[str]) -> str:
    for name in ("Substantiv", "Verb", "Adjektiv"):
        if name in labels:
            return name
    return "other"


def process_row_group(args) -> tuple[list[dict], Counter, Counter]:
    path, index = args
    table = pq.ParquetFile(path).read_row_group(index, columns=["ns", "title", "text", "redirect"])
    rows, totals, values = [], Counter(), Counter()
    for page in table.to_pylist():
        if page["redirect"] is not None or page["ns"] != 0:
            continue
        for section in lemma_sections(page["title"], page["text"]):
            if not section.senses:
                continue
            group = pos_group(section.labels)
            totals[group] += 1
            counts, qualified, marked = Counter(), 0, 0
            for found, was_qualified in section.senses:
                qualified += was_qualified
                marked += bool(found)
                for kind, value in found.items():
                    counts[kind] += 1
                    values[(kind, value)] += 1
            if not counts and not qualified:
                continue
            rows.append(
                {
                    "title": page["title"],
                    "section": section.number,
                    "pos": group,
                    "senses": len(section.senses),
                    **{kind: counts[kind] for kind in KINDS},
                    "any": marked,
                    "qualified": qualified,
                }
            )
    return rows, totals, values


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(cache: Path, out: Path, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    groups = pq.ParquetFile(cache).num_row_groups
    rows, totals, values = [], Counter(), Counter()
    with ProcessPoolExecutor(workers) as pool:
        for found, counted, seen in pool.map(
            process_row_group, [(cache, i) for i in range(groups)]
        ):
            rows += found
            totals += counted
            values += seen
    rows.sort(key=lambda r: (r["title"], r["section"]))
    _write(out / "sections.tsv", list(rows[0]), rows)
    _write(
        out / "values.tsv",
        ["kind", "value", "senses"],
        [
            {"kind": kind, "value": value, "senses": n}
            for (kind, value), n in sorted(values.items(), key=lambda kv: (kv[0][0], -kv[1]))
        ],
    )
    summary = []
    for group in ("Substantiv", "Verb", "Adjektiv", "other", "all"):
        chosen = [r for r in rows if group in ("all", r["pos"])]
        total = sum(totals.values()) if group == "all" else totals[group]
        for kind in (*KINDS, "any"):
            every = sum(r[kind] == r["senses"] for r in chosen)
            some = sum(0 < r[kind] < r["senses"] for r in chosen)
            summary.append(
                {
                    "pos": group,
                    "sections": total,
                    "label": kind,
                    "all senses": every,
                    "some senses": some,
                    "share all": f"{every / total:.1%}",
                }
            )
        only = sum(r["qualified"] > 0 and r["any"] == 0 for r in chosen)
        summary.append(
            {"pos": group, "sections": total, "label": "qualified only", "some senses": only}
        )
    _write(out / "summary.tsv", list(summary[0]), summary)
    for row in summary:
        if row["pos"] in ("Substantiv", "all"):
            print(row)
