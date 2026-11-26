from pathlib import Path

import pytest

from hawfinch.features.selection import (
    KEPT,
    LEFT_OUT,
    MIXED,
    keeps_flexion,
    kept_sections,
    lemma_sections,
    verb_selection,
)

FIXTURES = Path(__file__).parent / "fixtures" / "usage"


def sections(name: str, select=lemma_sections):
    text = (FIXTURES / f"{name}.wiki").read_text(encoding="utf-8")
    return list(select(name, text))


def test_sections_carry_number_labels_and_senses():
    first, second = sections("snacken")
    assert (first.title, first.number, first.labels) == ("snacken", 1, ["Verb"])
    assert (second.number, second.labels) == (2, ["Verb"])
    assert first.senses == [({}, False)]  # Jugendsprache is not one of the four kinds
    assert second.senses == [({"regional": "Norddeutschland"}, False)]
    assert second.body.lstrip().startswith("{{Deutsch Verb Übersicht")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("aalfett", [True]),
        ("aaser", [True]),  # every sense marked, with different labels
        ("bazi", [False]),  # one sense of two
        ("tuetlein", [False]),  # qualified label
        ("snacken", [False, True]),
    ],
)
def test_left_out(name, expected):
    assert [section.left_out for section in sections(name)] == expected


def test_kept_sections_skips_sections_left_out():
    assert [section.number for section in sections("snacken", kept_sections)] == [1]
    assert sections("poldern", kept_sections) == []
    assert len(sections("bazi", kept_sections)) == 1


@pytest.mark.parametrize(
    ("name", "selection", "kept"),
    [
        ("snacken", MIXED, True),  # one verb section of two left out: conjugations stay
        ("poldern", LEFT_OUT, False),
        ("aalfett", None, True),  # no verb section
    ],
)
def test_verb_selection_decides_for_the_flexion_page(name, selection, kept):
    assert verb_selection(sections(name)) == selection
    assert keeps_flexion(selection) is kept


def test_kept_verb_sections():
    assert verb_selection(sections("snacken")[:1]) == KEPT
