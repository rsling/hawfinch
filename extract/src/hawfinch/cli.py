"""Command-line entry point: ``hawfinch fetch | extract | validate | export``."""

import argparse
import sys
from collections.abc import Sequence

from hawfinch import __version__

SUBCOMMANDS = {
    "fetch": "download a German Wiktionary dump into data/raw",
    "extract": "parse a dump and derive the grammatical features",
    "validate": "run consistency checks and coverage reports on extracted data",
    "export": "write a versioned data release",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hawfinch", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, summary in SUBCOMMANDS.items():
        subparsers.add_parser(name, help=summary, description=summary)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"hawfinch {args.command}: not implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
