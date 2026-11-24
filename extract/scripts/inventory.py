"""Step 1 of the feasibility test: inventory of the markup in German entries.

Counts, over the page cache, what the extractor will have to handle: languages, part-of-speech
labels and their combinations, heading templates, subsection headings, single-template lines
(the block markers), all templates per part of speech, the arguments of the table templates,
the `Flexion:` namespace, and markup anomalies. German Wortart counts are compared page by page
with the category tables of the same dump.

Output: CSV files and summary.json in the output directory.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

from hawfinch.dump.pages import cached_siteinfo
from hawfinch.dump.sqldump import iter_rows
from hawfinch.wikitext.sections import blank_comments, language_sections, split_sections
from hawfinch.wikitext.templates import scan

SAMPLES = 12
FLEXION_NS = 108
# Figures from the API on 2026-11-24, recorded in docs/decisions/0001-extraction-strategy.md.
API_FIGURES = {
    "Substantiv": 143_011,
    "Verb": 14_602,
    "Adjektiv": 18_327,
    "Deklinierte Form": 524_660,
    "Konjugierte Form": 226_719,
    "Suffix": 173,
    "Präfix": 147,
}


def shape(title: str) -> str:
    """A heading with every top-level template reduced to its name."""
    result = scan(title)
    out, last = [], 0
    for t in result.templates:
        if t.depth == 0:
            out += [title[last : t.start], "{{" + t.name + "}}"]
            last = t.end
    out.append(title[last:])
    return " ".join("".join(out).split())


def standalone_templates(body: str):
    """Templates that make up a whole line on their own (block markers and the like)."""
    for line in body.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("{{") and stripped.endswith("}}")):
            continue
        result = scan(stripped)
        top = [t for t in result.templates if t.depth == 0]
        if len(top) == 1 and top[0].start == 0 and top[0].end == len(stripped):
            yield top[0]


class Tally:
    def __init__(self):
        self.counts: dict[str, Counter] = defaultdict(Counter)
        self.samples: dict[str, dict] = defaultdict(lambda: defaultdict(list))

    def add(self, table, key, n=1, sample=None):
        self.counts[table][key] += n
        if sample is not None and len(self.samples[table][key]) < SAMPLES:
            self.samples[table][key].append(sample)

    def merge(self, other: Tally):
        for table, counter in other.counts.items():
            self.counts[table].update(counter)
        for table, keys in other.samples.items():
            for key, titles in keys.items():
                room = SAMPLES - len(self.samples[table][key])
                self.samples[table][key] += titles[:room]

    def plain(self):
        return (dict(self.counts), {t: dict(k) for t, k in self.samples.items()})


def german_page(tally: Tally, title: str, text: str, labels_out: set):
    entries = language_sections(text)
    languages = set()
    german = 0
    for entry in entries:
        language = entry.language or "<none>"
        languages.add(language)
        tally.add("language_sections", language)
        if language != "Deutsch":
            continue
        german += 1
        if entry.word != title:
            tally.add("entry_word_differs_from_title", "all", sample=title)
        stray = [c for c in entry.section.children if c.level != 3]
        if stray:
            tally.add("entry_children_not_level3", "all", sample=title)
        if not entry.pos_sections:
            tally.add("entry_without_pos_section", "all", sample=title)
        for pos in entry.pos_sections:
            german_pos_section(tally, title, text, pos, labels_out)
    for language in languages:
        tally.add("language_pages", language)
    tally.add("german_entries_per_page", german)


def german_pos_section(tally: Tally, title: str, text: str, pos, labels_out: set):
    section = pos.section
    labels = [label for label, _ in pos.wortarten]
    primary = labels[0] if labels else "<none>"
    tally.add("pos_sections", primary)
    if not labels:
        tally.add("pos_heading_without_wortart", shape(section.title), sample=title)
    tally.add("wortart_combination", " + ".join(labels) or "<none>", sample=title)
    for label, language in pos.wortarten:
        labels_out.add(label)
        tally.add("wortart_any_position", label)
        if language != "Deutsch":
            tally.add("wortart_language_not_deutsch", (label, language), sample=title)
    for t in pos.heading_templates:
        if t.name != "Wortart" and t.depth == 0:
            tally.add("heading_templates", (primary, t.name), sample=title)
    for sub in section.walk():
        if sub is not section:
            tally.add("subsection_headings", (primary, sub.level, shape(sub.title)), sample=title)

    seen_blocks = set()
    for t in standalone_templates(section.body(text)):
        seen_blocks.add((primary, t.name, bool(t.args)))
    for key in seen_blocks:
        tally.add("standalone_template_lines", key, sample=title)

    full = section.full(text)
    result = scan(full)
    seen = set()
    tables = 0
    for t in result.templates:
        tally.add("template_occurrences", (primary, t.name))
        seen.add(t.name)
        if t.depth == 0 and "Übersicht" in t.name:
            tables += 1
            tally.add("table_template_uses", (primary, t.name), sample=title)
            for key in t.params():
                tally.add("table_template_args", (t.name, key))
    for name in seen:
        tally.add("template_sections", (primary, name))
    tally.add("table_templates_per_section", (primary, tables), sample=title)
    for kind in {a.kind for a in result.anomalies}:
        tally.add("anomalies", (primary, kind), sample=title)


def flexion_page(tally: Tally, title: str, text: str, flexion_out: list):
    roots = split_sections(blank_comments(text))
    headings = [s for r in roots for s in r.walk() if s.level == 2]
    tally.add("flexion_level2_per_page", len(headings))
    kinds = []
    for h in headings:
        m = re.search(r"\(([^(){}]+)\)\s*\(\{\{", h.title)
        kind = m.group(1).strip() if m else "<none>"
        heading_templates = [t for t in scan(h.title).templates if t.depth == 0]
        language = next(((t.get("1") or "").strip() for t in heading_templates), "<none>")
        names = "+".join(t.name for t in heading_templates) or "<none>"
        tally.add("flexion_headings", (kind, names, language), sample=title)
        kinds.append((kind, language))
    result = scan(text)
    top = [t for t in result.templates if t.depth == 0]
    for t in top:
        tally.add("flexion_templates", t.name, sample=title)
        for key in t.params():
            tally.add("flexion_template_args", (t.name, key))
    for kind in {a.kind for a in result.anomalies}:
        tally.add("flexion_anomalies", kind, sample=title)
    base = title.split(":", 1)[1]
    flexion_out.append((base, tuple(kinds), tuple(t.name for t in top)))


def process_row_group(args):
    path, index = args
    table = pq.ParquetFile(path).read_row_group(
        index, columns=["ns", "page_id", "title", "text", "redirect"]
    )
    tally = Tally()
    german_labels: dict[str, tuple[int, tuple[str, ...]]] = {}
    flexion: list = []
    for row in table.to_pylist():
        if row["redirect"] is not None:
            continue
        if row["ns"] == 0:
            labels: set = set()
            german_page(tally, row["title"], row["text"], labels)
            if labels:
                german_labels[row["title"]] = (row["page_id"], tuple(sorted(labels)))
                for label in labels:
                    tally.add("wortart_pages", label)
        elif row["ns"] == FLEXION_NS:
            flexion_page(tally, row["title"], row["text"], flexion)
    return tally.plain(), german_labels, flexion


def category_members(raw_dir: Path, date: str, names: set[str]) -> dict[str, set[int]]:
    """Page IDs in each of the categories ``names`` (titles with spaces), from the SQL dumps."""
    wanted = {n.replace(" ", "_") for n in names}
    targets = {}
    for lt_id, namespace, lt_title in iter_rows(
        raw_dir / f"dewiktionary-{date}-linktarget.sql.gz", "linktarget"
    ):
        if namespace == 14 and lt_title in wanted:
            targets[lt_id] = lt_title.replace("_", " ")
    members: dict[str, set[int]] = {name: set() for name in targets.values()}
    for row in iter_rows(raw_dir / f"dewiktionary-{date}-categorylinks.sql.gz", "categorylinks"):
        cl_from, cl_type, target = row[0], row[4], row[6]
        if target in targets and cl_type == "page":
            members[targets[target]].add(cl_from)
    return members


def write_csv(path: Path, header: list[str], rows) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def run_inventory(cache: Path, out: Path, workers: int = 8) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    date = cache.parent.name
    raw_dir = cache.parent.parent.parent / "raw" / date
    siteinfo = cached_siteinfo(cache)
    assert siteinfo.namespaces.get(FLEXION_NS) == "Flexion"

    tally = Tally()
    german: dict[str, tuple[int, tuple[str, ...]]] = {}
    flexion: list = []
    groups = pq.ParquetFile(cache).num_row_groups
    with ProcessPoolExecutor(workers) as pool:
        for (counts, samples), labels, flex in pool.map(
            process_row_group, [(cache, i) for i in range(groups)]
        ):
            part = Tally()
            for table, counter in counts.items():
                part.counts[table].update(counter)
            for table, keys in samples.items():
                for key, titles in keys.items():
                    part.samples[table][key] = titles
            tally.merge(part)
            german.update(labels)
            flexion.extend(flex)

    # Flexion pages against the German lemma sections of their base title.
    for base, _kinds, names in flexion:
        labels = german.get(base, (None, ()))[1]
        relevant = [
            label for label in ("Verb", "Adjektiv", "Partizip I", "Partizip II") if label in labels
        ]
        status = "+".join(relevant) or ("other German section" if labels else "no German entry")
        tally.add("flexion_base", ("+".join(names) or "<none>", status), sample=base)
    flexion_bases = {base for base, _, _ in flexion}
    for label in ("Verb", "Adjektiv"):
        pages = [t for t, (_, labels) in german.items() if label in labels]
        has = sum(1 for t in pages if t in flexion_bases)
        tally.add("lemma_has_flexion_page", (label, "yes"), has)
        tally.add("lemma_has_flexion_page", (label, "no"), len(pages) - has, sample=None)
        for t in pages:
            if t not in flexion_bases:
                tally.add("lemma_without_flexion_page_sample", label, 0, sample=t)

    # Wortart pages against the categories of the same dump.
    top_labels = [label for label, _ in tally.counts["wortart_pages"].most_common(40)]
    members = category_members(raw_dir, date, {f"{label} (Deutsch)" for label in top_labels})
    ids = pq.read_table(cache, columns=["page_id", "ns", "title"]).to_pydict()
    by_id = {
        pid: (title if ns == 0 else f"{ns}:{title}")
        for pid, ns, title in zip(ids["page_id"], ids["ns"], ids["title"], strict=True)
    }
    comparison = []
    for label in top_labels:
        ours = {pid for pid, labels in german.values() if label in labels}
        category = members.get(f"{label} (Deutsch)")
        if category is None:
            comparison.append((label, len(ours), None, None, None, API_FIGURES.get(label), "", ""))
            continue
        only_ours = sorted(by_id.get(p, str(p)) for p in ours - category)
        only_cat = sorted(by_id.get(p, f"#{p}") for p in category - ours)
        comparison.append(
            (
                label,
                len(ours),
                len(category),
                len(only_ours),
                len(only_cat),
                API_FIGURES.get(label),
                "; ".join(only_ours[:SAMPLES]),
                "; ".join(only_cat[:SAMPLES]),
            )
        )

    # Write everything.
    counts, samples = tally.plain()
    for table, counter in counts.items():
        rows = []
        for key, n in counter.most_common():
            key = key if isinstance(key, tuple) else (key,)
            example = "; ".join(
                map(str, samples.get(table, {}).get(key if len(key) > 1 else key[0], []))
            )
            rows.append([*key, n, example])
        width = max((len(r) for r in rows), default=2) - 2
        write_csv(
            out / f"{table}.csv", [f"key{i + 1}" for i in range(width)] + ["n", "examples"], rows
        )
    write_csv(
        out / "wortart_vs_category.csv",
        [
            "wortart",
            "pages_ours",
            "pages_category",
            "only_ours",
            "only_category",
            "api",
            "only_ours_examples",
            "only_category_examples",
        ],
        comparison,
    )
    summary = {
        "date": date,
        "generator": siteinfo.generator,
        "german_pages": len(german),
        "flexion_pages": len(flexion),
        "pos_sections": dict(tally.counts["pos_sections"].most_common()),
        "wortart_pages": dict(tally.counts["wortart_pages"].most_common()),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary
