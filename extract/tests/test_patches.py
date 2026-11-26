from pathlib import Path

import pytest

from hawfinch.features.inflection import VERB_TEMPLATES, read_verb
from hawfinch.features.selection import FLEXION_PATCH, KEPT, conjugation_key
from hawfinch.patches import PatchError, PatchSpec, check, read_patch
from hawfinch.wikitext.templates import scan

SPEC = PatchSpec(name="test", key=("title", "form"), values={"decision": frozenset({"a", "b"})})
HEADER = "title\tform\tdecision\tcomment\tdump\n"


def write(tmp_path: Path, text: str) -> Path:
    (tmp_path / "test.tsv").write_text(text, encoding="utf-8")
    return tmp_path


def test_read_patch_keys_rows_by_content(tmp_path):
    rows = read_patch(SPEC, write(tmp_path, HEADER + "x\ty\ta\twhy\t20261101\n"))
    assert rows[("x", "y")]["decision"] == "a"
    assert rows[("x", "y")]["comment"] == "why"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("title\tform\tdecision\tcomment\n", "columns"),
        (HEADER + "x\ty\tc\t\t\n", "not allowed"),
        (HEADER + "x\ty\ta\t\t\nx\ty\tb\t\t\n", "twice"),
    ],
)
def test_read_patch_rejects_malformed_tables(tmp_path, text, message):
    with pytest.raises(PatchError, match=message):
        read_patch(SPEC, write(tmp_path, text))


def test_check_reports_missing_unmatched_and_pinned_rows():
    rows = {("a",): {}, ("b",): {}, ("gone",): {}}
    coverage = check(rows, present=[("a",), ("b",), ("c",)], relevant=[("a",), ("c",)])
    assert coverage.missing == [("c",)]
    assert coverage.unmatched == [("gone",)]
    assert coverage.pinned == [("b",)]
    assert not coverage.complete


def test_flexion_patch_decides_tauen():
    text = (Path(__file__).parent / "fixtures" / "flexion" / "tauen.wiki").read_text("utf-8")
    (verb,) = [read_verb(t) for t in scan(text).templates if t.name in VERB_TEMPLATES]
    key = conjugation_key("tauen", verb)
    assert key == ("tauen", "taute", "getaut", "haben", "")
    assert read_patch(FLEXION_PATCH)[key]["decision"] == KEPT
