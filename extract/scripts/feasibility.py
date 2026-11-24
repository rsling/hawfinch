"""Driver for the feasibility test (the gate before M1). Throwaway glue; the logic it uses
lives in the ``hawfinch`` package.

    uv run python extract/scripts/feasibility.py cache --date 20261101
    uv run python extract/scripts/feasibility.py inventory --date 20261101
    uv run python extract/scripts/feasibility.py proper-nouns --date 20261101
    uv run python extract/scripts/feasibility.py abbreviations --date 20261101
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from hawfinch.dump.fetch import ARTICLES, dump_filename
from hawfinch.dump.pages import build_page_cache

DATA = Path("data")


def cache_path(date: str) -> Path:
    return DATA / "interim" / date / "pages.parquet"


def cmd_cache(args: argparse.Namespace) -> None:
    dump = DATA / "raw" / args.date / dump_filename(args.date, ARTICLES)
    started = time.monotonic()
    count = build_page_cache(dump, cache_path(args.date))
    print(f"{count:,} pages in {time.monotonic() - started:.0f} s -> {cache_path(args.date)}")


def cmd_inventory(args: argparse.Namespace) -> None:
    from inventory import run_inventory

    out = DATA / "interim" / "feasibility" / "inventory"
    run_inventory(cache_path(args.date), out, workers=args.workers)


def cmd_proper_nouns(args: argparse.Namespace) -> None:
    from proper_nouns import run

    out = DATA / "interim" / "feasibility" / "proper_nouns"
    if args.evaluate:
        from proper_nouns import evaluate

        evaluate(out)
    else:
        run(cache_path(args.date), out, args.workers)


def cmd_abbreviations(args: argparse.Namespace) -> None:
    from abbreviations import run

    run(cache_path(args.date), DATA / "interim" / "feasibility" / "abbreviations", args.workers)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    cache = sub.add_parser("cache", help="copy the XML dump into the Parquet page cache")
    cache.add_argument("--date", required=True)
    inventory = sub.add_parser("inventory", help="step 1: inventory of markup in German entries")
    inventory.add_argument("--date", required=True)
    inventory.add_argument("--workers", type=int, default=8)
    proper = sub.add_parser("proper-nouns", help="test proper-noun detection from Wortart labels")
    proper.add_argument("--date", required=True)
    proper.add_argument("--workers", type=int, default=8)
    proper.add_argument(
        "--evaluate", action="store_true", help="compare annotation.tsv with the rule's classes"
    )
    abbreviations = sub.add_parser("abbreviations", help="survey sections labelled Abkürzung")
    abbreviations.add_argument("--date", required=True)
    abbreviations.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    commands = {
        "cache": cmd_cache,
        "inventory": cmd_inventory,
        "proper-nouns": cmd_proper_nouns,
        "abbreviations": cmd_abbreviations,
    }
    commands[args.command](args)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
