"""Feasibility survey of the sections labelled ``Abkürzung`` (decision 0005).

For every German section with an ``Abkürzung`` label, records the shape of the spelling
(abbreviation period, all capitals, mixed case, …), whether anything signals its part of
speech (another Wortart label, a gender in the heading), and whether the Aussprache block has
an IPA transcription. Writes ``abbreviations.tsv`` (one row per section) and
``summary.tsv`` (counts by shape, signal and IPA).
"""

from __future__ import annotations

import csv
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq
from proper_nouns import GENDERS, sense_lines

from hawfinch.features.partofspeech import NAME_LABELS
from hawfinch.wikitext.plain import to_plain
from hawfinch.wikitext.sections import blocks, german_sections
from hawfinch.wikitext.templates import scan

IPA_PLACEHOLDERS = {"", "…", "...", "-", "—"}
FIELDS = ["page_id", "title", "labels", "signal", "genders", "shape", "ipa", "sense1"]


def shape(title: str) -> str:
    if "." in title:
        return "period"
    if " " in title:
        return "space"
    letters = [c for c in title if c.isalpha()]
    if len(letters) == 1:
        return "single letter"
    if letters and all(c.isupper() for c in letters):
        return "all caps"
    if any(c.isupper() for c in letters):
        return "mixed case"
    return "lower case"


def has_ipa(lines: list[str]) -> bool:
    for line in lines:
        if "{{IPA}}" not in line:
            continue
        for t in scan(line).templates:
            if t.name == "Lautschrift" and any(
                v.strip() not in IPA_PLACEHOLDERS for v in t.positional()
            ):
                return True
    return False


def signal(labels: list[str], genders: list[str]) -> str:
    if set(labels) & NAME_LABELS:
        return "name label"
    if "Substantiv" in labels:
        return "Substantiv"
    if genders:
        return "gender only"
    if len(set(labels)) > 1:
        return "other label"
    return "none"


def process_row_group(args) -> list[dict]:
    path, index = args
    table = pq.ParquetFile(path).read_row_group(
        index, columns=["ns", "page_id", "title", "text", "redirect"]
    )
    records = []
    for row in table.to_pylist():
        if row["ns"] != 0 or row["redirect"] is not None:
            continue
        text = row["text"]
        for entry in german_sections(text):
            for pos in entry.pos_sections:
                labels = [label for label, _ in pos.wortarten]
                if "Abkürzung" not in labels:
                    continue
                parts = blocks(pos.section.body(text))
                senses = [to_plain(s) for s in sense_lines(parts.get("Bedeutungen", []))]
                genders = sorted({t.name for t in pos.heading_templates if t.name in GENDERS})
                records.append(
                    {
                        "page_id": row["page_id"],
                        "title": row["title"],
                        "labels": " + ".join(labels),
                        "signal": signal(labels, genders),
                        "genders": ",".join(genders),
                        "shape": shape(row["title"]),
                        "ipa": has_ipa(parts.get("Aussprache", [])),
                        "sense1": senses[0][:200] if senses else "",
                    }
                )
    return records


def run(cache: Path, out: Path, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    groups = pq.ParquetFile(cache).num_row_groups
    with ProcessPoolExecutor(workers) as pool:
        parts = pool.map(process_row_group, [(cache, i) for i in range(groups)])
        records = [r for part in parts for r in part]
    with (out / "abbreviations.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    counts = Counter((r["shape"], r["signal"], r["ipa"]) for r in records)
    with (out / "summary.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["shape", "signal", "ipa", "n"])
        for (shape_, signal_, ipa), n in sorted(counts.items()):
            writer.writerow([shape_, signal_, ipa, n])
    print(f"{len(records):,} sections labelled Abkürzung -> {out}")
