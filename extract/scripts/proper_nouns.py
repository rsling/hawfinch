"""Feasibility test: can proper nouns be told from common nouns by their Wortart labels?

Collects every German section labelled Substantiv or with a name label, applies the rule in
``hawfinch.features.partofspeech``, and checks it against independent signals:

- the inflection table (name tables such as ``Deutsch Toponym Übersicht`` versus
  ``Deutsch Substantiv Übersicht``),
- ``{{K|…}}`` labels on single senses (``{{K|Toponym}}``, ``{{K|Eigenname}}``),
- definitions shaped like a name's (``Familienname``, ``Stadt in …``).

Writes ``nouns.parquet`` (one row per section) and a blind sample for manual checking:
500 sections of each class, shuffled, showing only title and senses (``sample.tsv``), with
the key in ``sample_key.tsv``.
"""

from __future__ import annotations

import csv
import random
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from hawfinch.features.partofspeech import COMMON_NOUN, NAME_LABELS, PROPER_NOUN, noun_class
from hawfinch.wikitext.plain import to_plain
from hawfinch.wikitext.sections import blocks, german_sections
from hawfinch.wikitext.templates import scan

SEED = 20261124
SAMPLE_SIZE = 500
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
NAME_TABLES = (
    "Deutsch Toponym Übersicht",
    "Deutsch Nachname Übersicht",
    "Deutsch Vorname Übersicht",
    "Deutsch Eigenname Übersicht",
    "Deutsch Name Übersicht",
)
PERSON_NAME = re.compile(r"^(?:Familienname|Nachname|(?:männlicher|weiblicher)\s+Vorname|Vorname)")
PLACE_NAME = re.compile(
    r"^(?:\S+\s+){0,2}?(?:Stadt|Großstadt|Kleinstadt|Hauptstadt|Gemeinde|Ortsteil|Ortschaft|Ort|"
    r"Dorf|Stadtteil|Fluss|Insel|Staat|Land|Bundesland|Kanton|Region|Provinz|Landkreis|Berg|"
    r"Gebirge|See)\s+(?:in|im|an|am|auf|der|des|von|bei)\b"
)
SCHEMA = pa.schema(
    [
        ("page_id", pa.int64()),
        ("title", pa.string()),
        ("section", pa.int32()),
        ("labels", pa.list_(pa.string())),
        ("noun_class", pa.string()),
        ("genders", pa.list_(pa.string())),
        ("tables", pa.list_(pa.string())),
        ("senses", pa.list_(pa.string())),
        ("k_labels", pa.list_(pa.string())),
        ("name_shaped", pa.bool_()),
    ]
)


def sense_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith(":")]


def section_record(page_id: int, title: str, index: int, text: str, pos) -> dict | None:
    labels = [label for label, _ in pos.wortarten]
    cls = noun_class(labels)
    if cls is None:
        return None
    body = pos.section.body(text)
    raw_senses = sense_lines(blocks(body).get("Bedeutungen", []))
    k_labels = set()
    for line in raw_senses:
        for t in scan(line).templates:
            if t.name == "K":
                k_labels.update(v.strip() for v in t.positional() if v.strip())
    senses = [to_plain(line) for line in raw_senses]
    stripped = [re.sub(r"^:+\s*(?:\[[^\]]*\]\s*)?(?:\([^)]*\)\s*)?", "", s) for s in senses]
    tables = sorted(
        {t.name for t in scan(body).templates if t.depth == 0 and "Übersicht" in t.name}
    )
    return {
        "page_id": page_id,
        "title": title,
        "section": index,
        "labels": labels,
        "noun_class": cls,
        "genders": sorted({t.name for t in pos.heading_templates if t.name in GENDERS}),
        "tables": tables,
        "senses": senses,
        "k_labels": sorted(k_labels),
        "name_shaped": any(PERSON_NAME.match(s) or PLACE_NAME.match(s) for s in stripped),
    }


def process_row_group(args) -> list[dict]:
    path, index = args
    table = pq.ParquetFile(path).read_row_group(
        index, columns=["ns", "page_id", "title", "text", "redirect"]
    )
    records = []
    for row in table.to_pylist():
        if row["ns"] != 0 or row["redirect"] is not None:
            continue
        n = 0
        for entry in german_sections(row["text"]):
            for pos in entry.pos_sections:
                record = section_record(row["page_id"], row["title"], n, row["text"], pos)
                if record:
                    records.append(record)
                n += 1
    return records


def collect(cache: Path, out: Path, workers: int) -> pa.Table:
    groups = pq.ParquetFile(cache).num_row_groups
    with ProcessPoolExecutor(workers) as pool:
        parts = pool.map(process_row_group, [(cache, i) for i in range(groups)])
        records = [r for part in parts for r in part]
    table = pa.Table.from_pylist(records, schema=SCHEMA)
    pq.write_table(table, out, compression="zstd")
    return table


def table_kind(tables: list[str]) -> str:
    if not tables:
        return "no table"
    if any(t.startswith(NAME_TABLES) for t in tables):
        return "name table"
    if any(t.startswith("Deutsch Substantiv Übersicht") for t in tables):
        return "Substantiv table"
    return "other: " + "+".join(tables)


def write_tsv(path: Path, header: list[str], rows) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def sense_text(senses: list[str], limit: int = 8, width: int = 200) -> str:
    shown = [s if len(s) <= width else s[: width - 1] + "…" for s in senses[:limit]]
    more = f" … (+{len(senses) - limit} more)" if len(senses) > limit else ""
    return " ‖ ".join(shown) + more if shown else "(no Bedeutungen)"


def run(cache: Path, out: Path, workers: int = 8) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rows = collect(cache, out / "nouns.parquet", workers).to_pylist()
    proper_k = {"Toponym", "Eigenname", "Nachname", "Vorname", "Familienname", "Göttername"}

    counts = Counter(r["noun_class"] for r in rows)
    by_table = Counter((r["noun_class"], table_kind(r["tables"])) for r in rows)
    signals = Counter()
    strata: dict[str, list[dict]] = {
        "common_with_name_k_label": [],
        "common_name_shaped": [],
        "common_abbreviation": [],
        "proper_with_substantiv_table": [],
    }
    for r in rows:
        k_proper = bool(set(r["k_labels"]) & proper_k)
        signals[(r["noun_class"], "K name label on a sense", k_proper)] += 1
        signals[(r["noun_class"], "name-shaped definition", r["name_shaped"])] += 1
        if r["noun_class"] == COMMON_NOUN:
            if k_proper:
                strata["common_with_name_k_label"].append(r)
            if r["name_shaped"]:
                strata["common_name_shaped"].append(r)
            if "Abkürzung" in r["labels"]:
                strata["common_abbreviation"].append(r)
        elif table_kind(r["tables"]) == "Substantiv table":
            strata["proper_with_substantiv_table"].append(r)

    with (out / "signals.txt").open("w") as f:
        print("sections:", dict(counts), file=f)
        print("\nclass x table:", file=f)
        for (cls, kind), n in sorted(by_table.items(), key=lambda x: (x[0][0], -x[1])):
            print(f"  {cls:12} {kind:45} {n}", file=f)
        print("\nclass x signal:", file=f)
        for key, n in sorted(signals.items()):
            print(f"  {key} {n}", file=f)
        print("\nstrata:", {k: len(v) for k, v in strata.items()}, file=f)
        print("name labels:", sorted(NAME_LABELS), file=f)

    for name, items in strata.items():
        write_tsv(
            out / f"stratum_{name}.tsv",
            ["page_id", "section", "title", "labels", "tables", "k_labels", "senses"],
            [
                (
                    r["page_id"],
                    r["section"],
                    r["title"],
                    " + ".join(r["labels"]),
                    "+".join(r["tables"]),
                    ", ".join(r["k_labels"]),
                    sense_text(r["senses"]),
                )
                for r in items
            ],
        )

    rng = random.Random(SEED)
    sample = []
    for cls in (PROPER_NOUN, COMMON_NOUN):
        pool = [r for r in rows if r["noun_class"] == cls]
        sample += rng.sample(pool, SAMPLE_SIZE)
    rng.shuffle(sample)
    write_tsv(
        out / "sample.tsv",
        ["item", "title", "senses"],
        [(i + 1, r["title"], sense_text(r["senses"])) for i, r in enumerate(sample)],
    )
    write_tsv(
        out / "sample_key.tsv",
        ["item", "page_id", "section", "title", "noun_class", "labels", "tables"],
        [
            (
                i + 1,
                r["page_id"],
                r["section"],
                r["title"],
                r["noun_class"],
                " + ".join(r["labels"]),
                "+".join(r["tables"]),
            )
            for i, r in enumerate(sample)
        ],
    )


def read_tsv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def evaluate(out: Path) -> None:
    """Compare the blind judgments in ``annotation.tsv`` with the rule's classes."""
    key = {r["item"]: r for r in read_tsv(out / "sample_key.tsv")}
    sample = {r["item"]: r for r in read_tsv(out / "sample.tsv")}
    judged = read_tsv(out / "annotation.tsv")
    assert sorted(r["item"] for r in judged) == sorted(key), "annotation must cover every item"
    expected = {PROPER_NOUN: "P", COMMON_NOUN: "C"}
    matrix = Counter()
    borderline = Counter()
    disagreements = []
    for r in judged:
        k = key[r["item"]]
        matrix[(k["noun_class"], r["judgment"])] += 1
        if r["borderline"]:
            borderline[(k["noun_class"], r["borderline"], r["judgment"])] += 1
        if r["judgment"] != expected[k["noun_class"]] or r["borderline"]:
            disagreements.append(
                (
                    r["item"],
                    k["title"],
                    k["noun_class"],
                    r["judgment"],
                    r["borderline"],
                    r["note"],
                    k["labels"],
                    sample[r["item"]]["senses"],
                )
            )
    with (out / "evaluation.txt").open("w") as f:
        for cls in (PROPER_NOUN, COMMON_NOUN):
            row = {j: matrix[(cls, j)] for j in "PCMU"}
            print(f"{cls:12} {row}  total {sum(row.values())}", file=f)
        print("\nborderline (rule class, class, judgment):", file=f)
        for k, n in sorted(borderline.items(), key=lambda x: -x[1]):
            print(f"  {k} {n}", file=f)
    write_tsv(
        out / "disagreements.tsv",
        ["item", "title", "rule", "judgment", "borderline", "note", "labels", "senses"],
        sorted(disagreements, key=lambda d: (d[2], d[3], d[4])),
    )
