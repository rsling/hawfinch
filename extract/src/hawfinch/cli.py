"""Command-line entry point: ``hawfinch fetch | extract | validate | export``."""

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from hawfinch import __version__

SUBCOMMANDS = {
    "fetch": "download a German Wiktionary dump into data/raw",
    "extract": "parse a dump and derive the grammatical features",
    "validate": "run consistency checks and coverage reports on extracted data",
    "export": "write a versioned data release",
}


def add_fetch_arguments(parser: argparse.ArgumentParser) -> None:
    from hawfinch.dump.fetch import DEFAULT_USER_AGENT

    parser.add_argument("--date", required=True, help="dump date, YYYYMMDD")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="default: data")
    parser.add_argument(
        "--categories", action="store_true", help="also download categorylinks and linktarget"
    )
    parser.add_argument(
        "--kaikki", action="store_true", help="also download Kaikki's file built from this dump"
    )
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)


def run_fetch(args: argparse.Namespace) -> int:
    from hawfinch.dump.fetch import FetchError, fetch_dump, fetch_kaikki

    raw = args.data_dir / "raw"
    try:
        fetch_dump(args.date, raw, categories=args.categories, user_agent=args.user_agent)
        if args.kaikki:
            fetch_kaikki(raw, expected_date=args.date, user_agent=args.user_agent)
    except (FetchError, ValueError) as error:
        print(f"hawfinch fetch: {error}", file=sys.stderr)
        return 1
    return 0


HANDLERS: dict[str, tuple[Callable[[argparse.ArgumentParser], None], Callable[..., int]]] = {
    "fetch": (add_fetch_arguments, run_fetch),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hawfinch", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, summary in SUBCOMMANDS.items():
        sub = subparsers.add_parser(name, help=summary, description=summary)
        if name in HANDLERS:
            HANDLERS[name][0](sub)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in HANDLERS:
        return HANDLERS[args.command][1](args)
    print(f"hawfinch {args.command}: not implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
