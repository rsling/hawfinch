import bz2
import hashlib
import io
from pathlib import Path

import pytest

from hawfinch.dump.fetch import (
    FetchError,
    check_date,
    download,
    dump_url,
    parse_checksums,
    parse_kaikki_page,
)
from hawfinch.dump.pages import cached_siteinfo, read_pages, write_pages
from hawfinch.dump.reader import iter_pages, read_siteinfo

FIXTURE = Path(__file__).parent / "fixtures" / "mini-dump.xml"


def test_siteinfo():
    info = read_siteinfo(FIXTURE)
    assert info.dbname == "dewiktionary"
    assert info.namespaces[108] == "Flexion" and info.namespaces[0] == ""


def test_pages_in_file_order_with_revision_not_contributor_id():
    pages = list(iter_pages(FIXTURE))
    assert [p.title for p in pages] == ["µm", "Fluß", "Häuser", "Flexion:kaufen"]
    redirect, fluss = pages[0], pages[1]
    assert redirect.redirect == "μm" and redirect.rev_id == 6386436
    assert fluss.redirect is None and fluss.page_id == 9873 and fluss.rev_id == 9193078
    assert fluss.text.startswith("== Fluß ({{Sprache|Deutsch}}) ==")
    assert fluss.timestamp.isoformat() == "2022-05-31T08:02:19+00:00"
    assert [p.title for p in iter_pages(FIXTURE, namespaces={108})] == ["Flexion:kaufen"]


def test_bz2_input(tmp_path):
    compressed = tmp_path / "dump.xml.bz2"
    compressed.write_bytes(bz2.compress(FIXTURE.read_bytes()))
    assert [p.title for p in iter_pages(compressed)] == [p.title for p in iter_pages(FIXTURE)]


def test_page_cache_round_trip(tmp_path):
    out = tmp_path / "pages.parquet"
    assert write_pages(iter_pages(FIXTURE), out, read_siteinfo(FIXTURE), log=None) == 4
    assert list(read_pages(out)) == list(iter_pages(FIXTURE))
    assert [p.title for p in read_pages(out, namespaces=[0])] == ["µm", "Fluß", "Häuser"]
    assert cached_siteinfo(out) == read_siteinfo(FIXTURE)


def test_checksums_and_urls():
    sums = parse_checksums("abc123  dewiktionary-20261101-pages-articles.xml.bz2\n\n")
    assert sums == {"dewiktionary-20261101-pages-articles.xml.bz2": "abc123"}
    assert dump_url("20261101", "sha1sums.txt") == (
        "https://dumps.wikimedia.org/dewiktionary/20261101/dewiktionary-20261101-sha1sums.txt"
    )
    with pytest.raises(ValueError):
        check_date("latest")


def test_kaikki_page():
    html = (
        "<p>The current version was extracted from the <a href='x'>dewiktionary dump</a>"
        " dated 2026-11-01.</p> ... using <a>wiktextract</a> (<a>19f9a30</a> and"
        " <a>6f96ddf</a>)."
    )
    assert parse_kaikki_page(html) == {
        "dump_date": "20261101",
        "wiktextract_commit": "19f9a30",
        "wikitextprocessor_commit": "6f96ddf",
    }


def test_download_verifies_checksum(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"x" * 3000)
    good = hashlib.sha1(source.read_bytes()).hexdigest()
    record = download(source.as_uri(), tmp_path / "a.bin", expected_sha1=good, log=io.StringIO())
    assert record.size == 3000 and record.sha1 == good
    with pytest.raises(FetchError):
        download(source.as_uri(), tmp_path / "b.bin", expected_sha1="0" * 40, log=io.StringIO())
    assert not (tmp_path / "b.bin").exists() and not (tmp_path / "b.bin.part").exists()
