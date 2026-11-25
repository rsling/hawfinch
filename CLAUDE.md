# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Hawfinch builds a lexical database of German grammar from German Wiktionary dumps (a modern successor to CELEX), plus tools and analyses on top of it. It has three parts, developed in this order:

1. `extract/`: Python package `hawfinch` that extracts grammatical features of words (phonology, inflection, word formation, morphosyntax) from the dumps.
2. `analysis/`: R and Python analyses for a publication on the "core" of German grammar; `paper/` holds the manuscript.
3. `app/`: web interface with Shiny visualisations. Built last.

`docs/roadmap.md` holds the milestones of release 1, which is the extractor only (M1 inflection, M2 word formation and phonology, M3 senses and freeze). The extractor is feature-frozen after release 1; the app is release 2, and the analyses run on a pinned release without a roadmap.

A later phase will link the lexical data with usage data from web corpora. It will get its own top-level `corpus/` directory and join onto releases by lexeme ID.

Most of the tree is scaffolding: the feature, model, validate and export modules are docstring-only stubs, and every CLI subcommand except `fetch` exits with "not implemented yet". Implemented so far: `dump/` (fetch, XML reader, Parquet page cache, SQL table reader), first versions of `wikitext/` (templates, sections and blocks, plain text), and the list of Wiktionary's name labels in `features/partofspeech.py`. The feasibility test is driven by `extract/scripts/feasibility.py`; its results are in `docs/feasibility.md`.

## Commands

Python is managed with `uv`. The repository root is a uv workspace with `extract/` as its only member; dev tools are in the root `dev` dependency group, and `uv.lock` is committed.

```sh
make setup    # uv sync
make test     # uv run pytest (configured in the root pyproject.toml, tests in extract/tests)
make lint     # ruff check + ruff format --check
make format   # ruff autofix + format
```

Single test: `uv run pytest extract/tests/test_cli.py::test_help_lists_subcommands`

CLI: `uv run hawfinch {fetch,extract,validate,export}`

## Architecture

**The data release is the only interface between the parts.** The extractor writes a versioned release to `data/release/<version>/` (Parquet tables, a DuckDB file, and a `MANIFEST.json` with dump date, extractor commit and checksums). `analysis/` and `app/` read a release and must never import from `extract/`. `analysis/release.txt` pins the release the analyses run against.

Extractor pipeline, in `extract/src/hawfinch/`: `dump/` (fetch and stream the XML, select German entries) → `wikitext/` (parse pages, sections, de.wiktionary templates) → `features/` (one module per linguistic domain) → `model/` (record types; the release schema) → `validate/` (consistency and coverage checks) → `export/` (release writers). `cli.py` exposes these stages as subcommands.

Workspace and tool configuration (uv, pytest, ruff) lives in the root `pyproject.toml`; packaging metadata lives in `extract/pyproject.toml`.

## Data model essentials

Read `docs/schema/profile.md` (what the database must contain), `docs/decisions/0001-extraction-strategy.md` (where each item sits in Wiktionary markup, and why we do not build on wiktextract) and `docs/open-questions.md` before working on the extractor.

- The extractor reads template arguments straight from the dump, without template or Lua expansion. Kaikki/wiktextract output is a validation baseline only.
- Three levels (`docs/decisions/0002-lexeme-model.md`): a lexeme is a stem with all its form-side properties; a sense is a meaning (word-specific for now); a lexical unit pairs one lexeme with one sense. Any difference in a lexeme-level field means two lexemes; restrictions and syntactic properties that hold in one sense only go on the lexical unit. Never merge across Wiktionary part-of-speech sections.
- Stems are stored, not citation forms: verbs lack the infinitive suffix (`kauf`).
- Periphrastic forms are never stored; only single-word inflected forms go into the word-form table. zu-infinitives and gerundives are not stored either. Partizip I (`-end`) is derivation: an `-end` word is a lexeme only if Wiktionary lists it with its own meaning. Partizip II is a verb word form, but its declined forms are stored only for adjective lexemes (`docs/decisions/0004-participles-and-zu-forms.md`).
- There is no proper-noun part of speech (`docs/decisions/0003-named-entities.md`). Lexemes keep Wiktionary's; name labels (`Toponym`, `Nachname`, …) are not parts of speech, and a section with only name labels is a `Substantiv`.
  - Lexical units have a field `named_entity`. It is `default` where Wiktionary does not mark the entry as a name ("not that we know of", not "no"). Otherwise it is the head noun of the sense's definition as a lemma (`Stadt`, `Nachname`), or `unspecified` if there is none (`docs/features/named-entities.md`).
  - Marked means a name label, a name table or a `{{K|…}}` name label, and nothing else. Release 1 takes Wiktionary's marking without heuristics and stores heads, not types; grouping heads into types is left to the analyses.
  - The extractor uses no language model (0006 is withdrawn).
- `Abkürzung` is not a part of speech (`docs/decisions/0005-abbreviations.md`).
  - Short words and abbreviated names are ordinary lexemes with a `coding` field: `regular` or `short`. There is no `abbreviation` value.
  - A section labelled `Abkürzung` is a lexeme (and `short`) only if it is in all capitals or mixed case and has IPA, a noun table, a gender in the heading or a second part-of-speech label. Without a part-of-speech signal it is a `Substantiv`. Never apply these rules to other lexemes.
  - All other `Abkürzung` sections go into the stub table: entries without a signal (`BBodSchG`, `BT`), orthographic abbreviations (`Einw.`), unit symbols, E numbers, vehicle registration codes, and every other spelling (lower case, single letters) whatever its markup.
  - Clippings (`Uni`, `Kita`) are `short`, recognised from the Herkunft in M2.
- Boundary symbols (`docs/features/segmentation.md`): `·` syllable (`An·zah·lung`), `-` inflection (`läuf-t`, `ge-koch-t`), `.` compound (`Haus.tür`), `+` linking element (`Kind+er.garten`), `:` derivation (`Gesund:heit`), `=` verb particle (`ab=kauf`).
- Do not implement syllable boundaries in IPA without discussing it with the user first, and never derive them from the orthographic "Worttrennung".
- Stable identifiers for senses and lexemes across extraction runs are required and unsolved; do not settle on a scheme without discussion.

## Conventions

- Test fixtures in `extract/tests/fixtures/` are small real wikitext pages, one per parsing edge case.
- A new or changed feature needs its linguistic definition in `docs/features/`, and schema changes need `docs/schema/` updated. Design decisions go in `docs/decisions/`.
- Nothing under `data/` is tracked except READMEs, `.gitkeep` files and release manifests. Do not commit dumps or release tables.

## Licensing

Code is BSD 2-Clause. Data derived from Wiktionary is CC BY-SA and must be released under that licence with attribution, not under BSD. Dependencies must be compatible with BSD 2-Clause.
