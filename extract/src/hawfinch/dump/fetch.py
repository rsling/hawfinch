"""Download a German Wiktionary dump and the Kaikki baseline into ``data/raw/<date>/``.

Dumps are pinned by date (``YYYYMMDD``); there is no "latest". Every file is checked
against the SHA-1 list Wikimedia publishes with the dump. The Kaikki file has no published
checksum; its size, ``Last-Modified`` header, our own hashes and the dump date and
wiktextract commits stated on its download page are recorded instead.

Each date directory gets a ``fetch.json`` that records what was downloaded, from where,
when, and with which checksums. Release manifests are later built from it.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import TextIO

DUMP_BASE = "https://dumps.wikimedia.org/dewiktionary"
KAIKKI_PAGE = "https://kaikki.org/dewiktionary/rawdata.html"
KAIKKI_FILE = "https://kaikki.org/dewiktionary/raw-wiktextract-data.jsonl.gz"

# Generic on purpose: which contact to send to Wikimedia is not decided yet.
DEFAULT_USER_AGENT = "dump-fetch/0.1 (Python urllib)"

ARTICLES = "pages-articles.xml.bz2"
CATEGORY_TABLES = ("categorylinks.sql.gz", "linktarget.sql.gz")
CHECKSUMS = "sha1sums.txt"
MANIFEST = "fetch.json"

CHUNK = 1 << 20


class FetchError(RuntimeError):
    """A download failed or did not match its published checksum."""


@dataclass
class FetchedFile:
    name: str
    url: str
    size: int
    sha1: str
    sha256: str
    checked_against: str | None
    last_modified: str | None
    fetched_at: str


def dump_filename(date: str, suffix: str) -> str:
    return f"dewiktionary-{date}-{suffix}"


def dump_url(date: str, suffix: str) -> str:
    return f"{DUMP_BASE}/{date}/{dump_filename(date, suffix)}"


def check_date(date: str) -> str:
    if not re.fullmatch(r"\d{8}", date):
        raise ValueError(f"dump date must be YYYYMMDD, got {date!r}")
    return date


def parse_checksums(text: str) -> dict[str, str]:
    """Parse a ``sha1sums.txt`` file: one ``<hex digest>  <file name>`` per line."""
    sums = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            digest, name = parts
            sums[name] = digest.lower()
    return sums


def parse_kaikki_page(html: str) -> dict[str, str | None]:
    """Read the source dump date and the wiktextract commits from Kaikki's download page."""
    text = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]*>", " ", html)))
    date = re.search(r"dewiktionary dump dated (\d{4})-(\d{2})-(\d{2})", text)
    commits = re.search(r"using wiktextract \( ?([0-9a-f]{6,40}) and ([0-9a-f]{6,40}) ?\)", text)
    return {
        "dump_date": "".join(date.groups()) if date else None,
        "wiktextract_commit": commits.group(1) if commits else None,
        "wikitextprocessor_commit": commits.group(2) if commits else None,
    }


def _hashes(path: Path) -> tuple[hashlib._Hash, hashlib._Hash]:
    sha1, sha256 = hashlib.sha1(), hashlib.sha256()
    if path.exists():
        with path.open("rb") as f:
            while chunk := f.read(CHUNK):
                sha1.update(chunk)
                sha256.update(chunk)
    return sha1, sha256


def _request(url: str, user_agent: str, offset: int = 0) -> urllib.request.Request:
    headers = {"User-Agent": user_agent}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    return urllib.request.Request(url, headers=headers)


def get_text(url: str, user_agent: str = DEFAULT_USER_AGENT) -> str:
    with urllib.request.urlopen(_request(url, user_agent), timeout=60) as response:
        return response.read().decode("utf-8")


def download(
    url: str,
    dest: Path,
    *,
    expected_sha1: str | None = None,
    user_agent: str = DEFAULT_USER_AGENT,
    log: TextIO = sys.stderr,
) -> FetchedFile:
    """Download ``url`` to ``dest``, resuming a ``.part`` file if one is left over.

    An existing ``dest`` whose SHA-1 matches ``expected_sha1`` is kept without downloading.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and expected_sha1:
        sha1, sha256 = _hashes(dest)
        if sha1.hexdigest() == expected_sha1:
            print(f"{dest.name}: present, checksum ok", file=log)
            return _record(dest, url, sha1, sha256, expected_sha1, None)

    part = dest.with_name(dest.name + ".part")
    offset = part.stat().st_size if part.exists() else 0
    with urllib.request.urlopen(_request(url, user_agent, offset), timeout=60) as response:
        if offset and response.status != 206:
            offset = 0  # server ignored the range request; start again
        sha1, sha256 = _hashes(part) if offset else (hashlib.sha1(), hashlib.sha256())
        length = response.headers.get("Content-Length")
        total = offset + int(length) if length else None
        last_modified = response.headers.get("Last-Modified")
        done, started, next_report = offset, time.monotonic(), 0.0
        with part.open("ab" if offset else "wb") as out:
            while chunk := response.read(CHUNK):
                out.write(chunk)
                sha1.update(chunk)
                sha256.update(chunk)
                done += len(chunk)
                if total and done / total >= next_report:
                    rate = (done - offset) / max(time.monotonic() - started, 1e-6) / 1e6
                    print(
                        f"{dest.name}: {done / total:4.0%} of {total / 1e6:.0f} MB, "
                        f"{rate:.1f} MB/s",
                        file=log,
                    )
                    next_report += 0.1
    if total is not None and done != total:
        raise FetchError(f"{dest.name}: got {done} bytes, expected {total}")
    if expected_sha1 and sha1.hexdigest() != expected_sha1:
        part.unlink()
        raise FetchError(f"{dest.name}: SHA-1 {sha1.hexdigest()} does not match {expected_sha1}")
    part.replace(dest)
    return _record(dest, url, sha1, sha256, expected_sha1, last_modified)


def _record(dest, url, sha1, sha256, checked_against, last_modified) -> FetchedFile:
    if last_modified:
        last_modified = parsedate_to_datetime(last_modified).astimezone(UTC).isoformat()
    return FetchedFile(
        name=dest.name,
        url=url,
        size=dest.stat().st_size,
        sha1=sha1.hexdigest(),
        sha256=sha256.hexdigest(),
        checked_against=checked_against,
        last_modified=last_modified,
        fetched_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def update_manifest(directory: Path, files: list[FetchedFile], **fields) -> Path:
    """Merge ``files`` and ``fields`` into ``fetch.json`` in ``directory``."""
    path = directory / MANIFEST
    manifest = json.loads(path.read_text()) if path.exists() else {"files": {}}
    manifest.update(fields)
    for f in files:
        manifest["files"][f.name] = asdict(f)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return path


def fetch_dump(
    date: str,
    raw_dir: Path,
    *,
    categories: bool = False,
    user_agent: str = DEFAULT_USER_AGENT,
    log: TextIO = sys.stderr,
) -> list[FetchedFile]:
    """Download the articles dump of ``date`` (and optionally the category tables)."""
    date = check_date(date)
    directory = raw_dir / date
    sums_name = dump_filename(date, CHECKSUMS)
    sums_text = get_text(dump_url(date, CHECKSUMS), user_agent)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / sums_name).write_text(sums_text)
    sums = parse_checksums(sums_text)

    wanted = [ARTICLES, *(CATEGORY_TABLES if categories else ())]
    fetched = []
    for suffix in wanted:
        name = dump_filename(date, suffix)
        if name not in sums:
            raise FetchError(f"{name} is not listed in {sums_name}")
        fetched.append(
            download(
                dump_url(date, suffix),
                directory / name,
                expected_sha1=sums[name],
                user_agent=user_agent,
                log=log,
            )
        )
    update_manifest(directory, fetched, wiki="dewiktionary", dump_date=date)
    return fetched


def fetch_kaikki(
    raw_dir: Path,
    *,
    expected_date: str | None = None,
    user_agent: str = DEFAULT_USER_AGENT,
    log: TextIO = sys.stderr,
) -> FetchedFile:
    """Download Kaikki's German-edition file into the directory of the dump it was built from.

    Fails if ``expected_date`` is given and Kaikki's current file comes from another dump.
    """
    info = parse_kaikki_page(get_text(KAIKKI_PAGE, user_agent))
    date = info["dump_date"]
    if date is None:
        raise FetchError(f"no dump date found on {KAIKKI_PAGE}")
    if expected_date and date != check_date(expected_date):
        raise FetchError(f"Kaikki's file is built from the {date} dump, not {expected_date}")
    directory = raw_dir / date / "kaikki"
    fetched = download(
        KAIKKI_FILE, directory / Path(KAIKKI_FILE).name, user_agent=user_agent, log=log
    )
    update_manifest(directory, [fetched], source_page=KAIKKI_PAGE, **info)
    return fetched
