# hawfinch

A lexical database of German grammar, extracted from German Wiktionary, with tools to access it and analyses built on it.

The project has three parts:

| Directory   | Part                                                                                   | Status      |
|-------------|----------------------------------------------------------------------------------------|-------------|
| `extract/`  | Python package that extracts grammatical features of words from German Wiktionary dumps | scaffolded  |
| `analysis/` | R and Python analyses of the extracted data, for a publication on the core of German grammar | not started |
| `app/`      | Web interface with Shiny visualisations for browsing the data                          | not started |

The first release covers the extractor only; see [the roadmap](docs/roadmap.md).

Supporting directories: `data/` (dumps and releases, not in git), `docs/` (schema, feature definitions, design decisions) and `paper/` (manuscript).

The parts communicate only through versioned data releases written by the extractor. The app and the analyses read a release; they do not import extractor code.

## Getting started

Python is managed with [uv](https://docs.astral.sh/uv/).

```sh
make setup   # uv sync: create .venv and install the extractor with dev tools
make test    # run the test suite
make lint    # ruff check and format check
```

After `make setup`, run the command-line tool with `uv run hawfinch`.

## Licence

The code is released under the BSD 2-Clause licence (see `LICENSE`). Data derived from Wiktionary is covered by Wiktionary's own licence terms, not by BSD; see `data/README.md`.
