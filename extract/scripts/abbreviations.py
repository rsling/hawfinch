"""Feasibility survey of the sections labelled ``Abkürzung`` (decision 0005).

For every German section with an ``Abkürzung`` label, records the shape of the spelling
(abbreviation period, all capitals, mixed case, …), whether anything signals its part of
speech (another Wortart label, a gender in the heading), whether it has a noun table and
whether the Aussprache block has an IPA transcription. From these it derives the status of
the section under decision 0005: ``lexeme``, ``stub`` or ``code`` (a vehicle registration
code, which is a stub too).

Writes ``abbreviations.tsv`` (one row per section), ``summary.tsv`` (counts by shape, signal
and IPA) and ``status.tsv`` (counts by shape and status).
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

from hawfinch.features.partofspeech import NAME_LABELS
from hawfinch.wikitext.plain import to_plain
from hawfinch.wikitext.sections import blocks, german_sections
from hawfinch.wikitext.templates import scan

IPA_PLACEHOLDERS = {"", "…", "...", "-", "—"}
FIELDS = [
    "page_id",
    "title",
    "labels",
    "signal",
    "genders",
    "shape",
    "table",
    "ipa",
    "audio",
    "example",
    "senses",
    "code_senses",
    "status",
    "sense1",
]
# Only these spellings are tested for lexeme status; all others are stubs.
LEXEME_SHAPES = {"all caps", "mixed case"}
NOUN_TABLE = "Deutsch Substantiv Übersicht"
REGISTRATION_CODE = re.compile(r"[Kk]ennzeichen|Unterscheidungszeichen")
GENDERS = {
    "m",
    "f",
    "n",
    "mf",
    "nm",
    "mn.",
    "nf",
    "fn",
    "fm",
    "mfn",
    "nPl.",
    "kPl.",
    "fPl.",
    "mPl.",
}


def sense_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith(":")]


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


def has_audio(lines: list[str]) -> bool:
    return any(
        t.name == "Audio" and any(v.strip() for v in t.positional())
        for line in lines
        for t in scan(line).templates
    )


def has_example(lines: list[str]) -> bool:
    return any(line.strip(": ") and "fehlen" not in line for line in lines)


def status(record: dict) -> str:
    """Lexeme, stub or code. A lexeme has all capitals or mixed case and at least one of: an
    IPA transcription, a noun table, a gender in the heading, a second part-of-speech label.
    A section whose senses are all vehicle registration codes is a code."""
    if record["shape"] not in LEXEME_SHAPES:
        return "stub"
    if not (record["ipa"] or record["table"] or record["signal"] != "none"):
        return "stub"
    if record["senses"] and record["code_senses"] == record["senses"]:
        return "code"
    return "lexeme"


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
                body = pos.section.body(text)
                parts = blocks(body)
                senses = [to_plain(s) for s in sense_lines(parts.get("Bedeutungen", []))]
                genders = sorted({t.name for t in pos.heading_templates if t.name in GENDERS})
                record = {
                    "page_id": row["page_id"],
                    "title": row["title"],
                    "labels": " + ".join(labels),
                    "signal": signal(labels, genders),
                    "genders": ",".join(genders),
                    "shape": shape(row["title"]),
                    "table": any(t.name == NOUN_TABLE for t in scan(body).templates),
                    "ipa": has_ipa(parts.get("Aussprache", [])),
                    "audio": has_audio(parts.get("Aussprache", [])),
                    "example": has_example(parts.get("Beispiele", [])),
                    "senses": len(senses),
                    "code_senses": sum(bool(REGISTRATION_CODE.search(s)) for s in senses),
                    "sense1": senses[0][:200] if senses else "",
                }
                record["status"] = status(record)
                records.append(record)
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
    by_status = Counter((r["shape"], r["status"]) for r in records)
    with (out / "status.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["shape", "status", "n"])
        for (shape_, status_), n in sorted(by_status.items()):
            writer.writerow([shape_, status_, n])
    print(f"{len(records):,} sections labelled Abkürzung -> {out}")
