"""Streaming reader for the MySQL table dumps Wikimedia publishes (``*.sql.gz``).

Only the ``INSERT INTO `<table>` VALUES (…),(…);`` lines are read. Strings are returned
with MySQL escapes undone; binary columns (sort keys) are decoded as UTF-8 with
``surrogateescape``, so no byte is lost. Integers come back as ``int``, ``NULL`` as ``None``.

``categorylinks`` names its category only by ``cl_target_id``; the name is in
``linktarget`` (``lt_id``, ``lt_namespace``, ``lt_title``).
"""

from __future__ import annotations

import gzip
import re
from collections.abc import Iterator
from pathlib import Path

ROW = re.compile(r"\(((?:'(?:[^'\\]|\\.)*'|[^'()])*)\)", re.S)
VALUE = re.compile(r"'((?:[^'\\]|\\.)*)'|(NULL)|([^,]+)", re.S)
ESCAPE = re.compile(r"\\(.)", re.S)
ESCAPES = {"0": "\0", "n": "\n", "r": "\r", "t": "\t", "Z": "\x1a", "b": "\b"}


def _unescape(raw: str) -> str:
    return ESCAPE.sub(lambda m: ESCAPES.get(m.group(1), m.group(1)), raw)


def _value(m: re.Match) -> str | int | float | None:
    if m.group(1) is not None:
        return _unescape(m.group(1))
    if m.group(2):
        return None
    raw = m.group(3).strip()
    try:
        return int(raw)
    except ValueError:
        return float(raw)


def iter_rows(path: Path, table: str) -> Iterator[tuple]:
    """Yield the rows of ``table``. Rows may follow ``VALUES`` on the same line or one per
    line until the closing ``;`` (newer dumps); a row never spans lines, because line breaks
    inside strings are escaped."""
    prefix = f"INSERT INTO `{table}` VALUES"
    inside = False
    with gzip.open(path, "rt", encoding="utf-8", errors="surrogateescape") as f:
        for line in f:
            start = 0
            if line.startswith(prefix):
                inside, start = True, len(prefix)
            elif not inside:
                continue
            for row in ROW.finditer(line, start):
                yield tuple(_value(v) for v in VALUE.finditer(row.group(1)))
            if line.rstrip().endswith(";"):
                inside = False
