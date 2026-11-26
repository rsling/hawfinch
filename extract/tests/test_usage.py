from pathlib import Path

import pytest

from hawfinch.features.usage import restricted, sense_labels, sense_lines

FIXTURES = Path(__file__).parent / "fixtures" / "usage"


def page(name: str) -> str:
    return (FIXTURES / f"{name}.wiki").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("aalfett", [{"archaic"}]),  # italic text
        ("abbruchbescheid", [{"Austrian"}]),
        ("abdankungsgottesdienst", [{"Swiss"}]),  # argument of {{K}}
        ("aaser", [{"regional"}, {"Swiss"}]),  # every sense marked, with different labels
        ("bazi", [{"regional", "Austrian"}, set()]),  # one sense of two
        ("tuetlein", [set()]),  # qualified: sonst va.
    ],
)
def test_labels_of_senses(name, expected):
    assert [set(sense_labels(line)[0]) for line in sense_lines(page(name))] == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("aalfett", True),
        ("abbruchbescheid", True),
        ("abdankungsgottesdienst", True),
        ("aaser", True),
        ("bazi", False),
        ("tuetlein", False),
    ],
)
def test_restricted(name, expected):
    assert restricted(page(name)) is expected


def test_qualified_label_is_reported():
    (line,) = sense_lines(page("tuetlein"))
    assert sense_labels(line) == ({}, True)


def test_section_without_senses_is_not_restricted():
    assert restricted("{{Bedeutungen}}\n\n{{Herkunft}}\n:[[x]]\n") is False
