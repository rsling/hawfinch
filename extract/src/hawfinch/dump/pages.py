"""Page cache: one pass over the XML dump into a Parquet table in ``data/interim/<date>/``.

Decompressing and parsing the dump takes minutes; reading the cache takes seconds, and the
cache can be queried directly with DuckDB. The table is a faithful copy of the dump's
latest revisions, with no selection or parsing. The dump's ``<siteinfo>`` is kept as JSON
in the Parquet metadata under the key ``siteinfo``.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Iterator
from dataclasses import asdict, fields
from pathlib import Path
from typing import TextIO

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from hawfinch.dump.reader import Page, SiteInfo, iter_pages, read_siteinfo

SCHEMA = pa.schema(
    [
        ("ns", pa.int32()),
        ("page_id", pa.int64()),
        ("title", pa.string()),
        ("rev_id", pa.int64()),
        ("timestamp", pa.timestamp("s", tz="UTC")),
        ("text", pa.string()),
        ("redirect", pa.string()),
        ("model", pa.string()),
    ]
)
COLUMNS = [f.name for f in fields(Page)]
assert COLUMNS == SCHEMA.names


def _batch(pages: list[Page]) -> pa.RecordBatch:
    columns = {name: [getattr(p, name) for p in pages] for name in COLUMNS}
    return pa.RecordBatch.from_pydict(columns, schema=SCHEMA)


def write_pages(
    pages: Iterable[Page],
    out: Path,
    siteinfo: SiteInfo | None = None,
    *,
    batch_size: int = 20_000,
    log: TextIO | None = sys.stderr,
) -> int:
    """Write ``pages`` to a Parquet file; returns the number of pages written."""
    out.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"siteinfo": json.dumps(asdict(siteinfo), ensure_ascii=False)} if siteinfo else {}
    tmp = out.with_name(out.name + ".part")
    count, buffer = 0, []
    with pq.ParquetWriter(tmp, SCHEMA.with_metadata(metadata), compression="zstd") as writer:
        for page in pages:
            buffer.append(page)
            if len(buffer) == batch_size:
                writer.write_batch(_batch(buffer))
                count += len(buffer)
                buffer.clear()
                if log and count % (10 * batch_size) == 0:
                    print(f"{out.name}: {count:,} pages", file=log)
        if buffer:
            writer.write_batch(_batch(buffer))
            count += len(buffer)
    tmp.replace(out)
    return count


def build_page_cache(dump: Path, out: Path, *, log: TextIO | None = sys.stderr) -> int:
    """Copy every page of ``dump`` into the Parquet cache ``out``."""
    return write_pages(iter_pages(dump), out, read_siteinfo(dump), log=log)


def cached_siteinfo(path: Path) -> SiteInfo:
    raw = json.loads(pq.read_schema(path).metadata[b"siteinfo"])
    raw["namespaces"] = {int(k): v for k, v in raw["namespaces"].items()}
    return SiteInfo(**raw)


def read_pages(
    path: Path, namespaces: Iterable[int] | None = None, *, batch_size: int = 10_000
) -> Iterator[Page]:
    """Yield the cached pages as :class:`Page` objects, optionally only from ``namespaces``."""
    filter_ = None if namespaces is None else ds.field("ns").isin(list(namespaces))
    scanner = ds.dataset(path, format="parquet").scanner(filter=filter_, batch_size=batch_size)
    for batch in scanner.to_batches():
        for row in batch.to_pylist():
            yield Page(**row)
