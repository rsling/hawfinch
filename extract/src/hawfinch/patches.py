"""Patches: tables that we create to filter, amend or make unambiguous data from Wiktionary
where extraction by rule is not feasible (``docs/decisions/0007-patches.md``).

A patch pins data to what we have decided, regardless of what Wiktionary says. Each patch is
a TSV file in ``extract/patches/``. Its columns are the key, which identifies a case by its
content in the dump, the value columns, ``comment`` (why) and ``dump`` (the snapshot the row
was checked against). The feature that needs a patch defines it with a :class:`PatchSpec`
and finds the cases that need a row; :func:`check` compares the two.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

PATCHES = Path(__file__).resolve().parents[2] / "patches"
NOTES = ("comment", "dump")


class PatchError(ValueError):
    """A patch table that cannot be read as its spec says."""


@dataclass(frozen=True)
class PatchSpec:
    name: str  # the file is ``<name>.tsv``
    key: tuple[str, ...]
    values: Mapping[str, frozenset[str]] = field(default_factory=dict)  # allowed values

    @property
    def columns(self) -> tuple[str, ...]:
        return (*self.key, *self.values, *NOTES)


Key = tuple[str, ...]


def read_patch(spec: PatchSpec, directory: Path = PATCHES) -> dict[Key, dict[str, str]]:
    """The rows of a patch by key. Raises :class:`PatchError` if the columns are not those
    of the spec, a value is not allowed, or a key occurs twice."""
    path = directory / f"{spec.name}.tsv"
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if tuple(reader.fieldnames or ()) != spec.columns:
            raise PatchError(f"{path.name}: columns {reader.fieldnames}, expected {spec.columns}")
        rows: dict[Key, dict[str, str]] = {}
        for line, row in enumerate(reader, 2):
            for column, allowed in spec.values.items():
                if row[column] not in allowed:
                    raise PatchError(f"{path.name}:{line}: {column}={row[column]!r} not allowed")
            key = tuple(row[column] for column in spec.key)
            if key in rows:
                raise PatchError(f"{path.name}:{line}: key {key} occurs twice")
            rows[key] = row
    return rows


@dataclass(frozen=True)
class Coverage:
    """How a patch fits a snapshot."""

    missing: list[Key]  # cases that need a row and have none: they block a release
    unmatched: list[Key]  # rows that match no case in the snapshot
    pinned: list[Key]  # rows that match a case the rule decides now

    @property
    def complete(self) -> bool:
        return not self.missing


def check(rows: Mapping[Key, object], present: Iterable[Key], relevant: Iterable[Key]) -> Coverage:
    """Compare the rows of a patch with the cases of a snapshot: ``present`` are all cases the
    patch could apply to, ``relevant`` those that the rule leaves open and need a row."""
    present, relevant = set(present), set(relevant)
    keys = set(rows)
    return Coverage(
        missing=sorted(relevant - keys),
        unmatched=sorted(keys - present),
        pinned=sorted((keys & present) - relevant),
    )
