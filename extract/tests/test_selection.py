from pathlib import Path

import pytest

from hawfinch.features.selection import (
    KEPT,
    LEFT_OUT,
    MIXED,
    UNDECIDED,
    flexion_selection,
    kept_sections,
    lemma_sections,
    verb_sections,
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
    ("name", "selection"),
    [
        ("snacken", MIXED),  # one verb section of two left out
        ("poldern", LEFT_OUT),
        ("aalfett", None),  # no verb section
    ],
)
def test_verb_selection(name, selection):
    assert verb_selection(sections(name)) == selection


def left_out(name: str) -> dict[int, bool]:
    return verb_sections(sections(name))


def test_a_section_that_points_to_another_spelling_is_not_a_lexeme():
    austrian, swiss = sections("verrussen")
    assert austrian.left_out and not austrian.spelling_variant
    assert swiss.labels == ["Verb"] and not swiss.senses
    assert swiss.spelling_variant and not swiss.left_out
    assert sections("verrussen", kept_sections) == []
    assert verb_sections(sections("verrussen")) == {1: True}
    assert verb_selection(sections("verrussen")) == LEFT_OUT
    assert not any(s.spelling_variant for s in sections("snacken"))


def test_flexion_selection_follows_the_sections_where_they_agree():
    assert flexion_selection(left_out("poldern"), [{1: True}]) == [LEFT_OUT]
    assert flexion_selection({1: False}, [{1: False}]) == [KEPT]  # also if it differs
    assert flexion_selection({}, [{}, {}]) == [KEPT, KEPT]  # no verb section, no lemma page


# The fits below are those of the pages named, in the dump of 2026-11-01.
@pytest.mark.parametrize(
    ("sections_left_out", "fits", "expected"),
    [
        # snacken: one conjugation serves both sections
        ({1: False, 2: True}, [{1: True, 2: True}], [KEPT]),
        # jucken: the conjugation with sein reproduces only the section left out
        (
            {1: False, 2: True},
            [{1: True, 2: False}, {1: False, 2: True}],
            [KEPT, LEFT_OUT],
        ),
        # tauen: the only conjugation reproduces the section left out, but the section
        # that stays would be left without one
        ({1: False, 2: True}, [{1: False, 2: True}], [UNDECIDED]),
        # the section that stays has no overview table
        ({1: True, 2: False}, [{1: True}, {1: False}], [UNDECIDED, UNDECIDED]),
        # a conjugation that reproduces no section
        (
            {1: False, 2: True},
            [{1: True, 2: False}, {1: False, 2: False}],
            [KEPT, UNDECIDED],
        ),
    ],
)
def test_flexion_selection_on_pages_with_sections_of_both_kinds(sections_left_out, fits, expected):
    assert flexion_selection(sections_left_out, fits) == expected


def test_flexion_selection_with_real_sections():
    assert left_out("snacken") == {1: False, 2: True}
    assert flexion_selection(left_out("snacken"), [{1: True, 2: True}]) == [KEPT]


def test_kept_verb_sections():
    assert verb_selection(sections("snacken")[:1]) == KEPT
