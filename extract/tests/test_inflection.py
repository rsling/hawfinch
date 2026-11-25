from pathlib import Path

import pytest

from hawfinch.features.inflection import (
    IMPERATIVE_PL,
    IMPERATIVE_SG,
    PARTICIPLE,
    PRESENT_1SG,
    PRESENT_2SG,
    PRESENT_3SG,
    PRETERITE,
    SUBJUNCTIVE,
    VERB_TEMPLATES,
    conjugation_class,
    is_copula_group,
    lexeme_stem,
    overview_forms,
    principal_forms,
    read_verb,
    split_prefix,
    stem_variants,
    stems,
)
from hawfinch.wikitext.templates import find_templates

FIXTURES = Path(__file__).parent / "fixtures" / "flexion"


def verbs(name: str):
    text = (FIXTURES / f"{name}.wiki").read_text(encoding="utf-8")
    return [read_verb(t) for t in find_templates(text) if t.name in VERB_TEMPLATES]


def forms(verb) -> list[list[str]]:
    result = principal_forms(verb)
    keys = (PRESENT_1SG, PRESENT_2SG, PRESENT_3SG, PRETERITE, SUBJUNCTIVE, IMPERATIVE_SG)
    return [result[key] for key in (*keys, IMPERATIVE_PL, PARTICIPLE)]


def test_weak_verb_has_one_stem():
    (verb,) = verbs("reisen")
    assert verb.weak and verb.infinitive == "reisen" and verb.auxiliary == "sein"
    assert set(stems(verb).values()) == {"reis"}
    assert forms(verb) == [
        ["reise"],
        ["reist"],  # the s of -st merges with the stem's
        ["reist"],
        ["reiste"],
        ["reiste"],
        ["reise", "reis"],
        ["reist"],
        ["gereist"],
    ]


@pytest.mark.parametrize(
    ("name", "second", "third", "preterite", "imperative"),
    [
        ("reden", "redest", "redet", "redete", ["rede", "red"]),
        ("atmen", "atmest", "atmet", "atmete", ["atme"]),
    ],
)
def test_e_before_endings(name, second, third, preterite, imperative):
    (verb,) = verbs(name)
    result = principal_forms(verb)
    assert result[PRESENT_2SG] == [second] and result[PRESENT_3SG] == [third]
    assert result[PRETERITE] == [preterite] and result[IMPERATIVE_SG] == imperative
    assert verb.auxiliary == "haben"  # haben= without a value


def test_stem_in_el():
    (verb,) = verbs("sammeln")
    assert verb.present == "sammel"
    assert principal_forms(verb)[PRESENT_1SG] == ["sammle", "sammele", "sammel"]
    assert principal_forms(verb)[PRESENT_2SG] == ["sammelst"]


def test_knien_keeps_its_e():
    haben, sein = verbs("knien")
    assert haben.present == "knie" and (haben.auxiliary, sein.auxiliary) == ("haben", "sein")
    assert principal_forms(haben)[PRESENT_1SG] == ["knie"]
    assert principal_forms(haben)[PRESENT_2SG] == ["kniest"]


def test_particle_overrides_and_auxiliary_of_weak_verb():
    (verb,) = verbs("abrutschen")
    assert verb.particles == ("ab",) and lexeme_stem(verb) == "ab=rutsch"
    assert verb.auxiliary == "sein"  # haben=sein
    result = principal_forms(verb)
    assert result[PRESENT_1SG] == ["rutsche ab"]
    assert result[PRESENT_2SG] == ["rutschst ab", "rutscht ab"]  # given on the page
    assert result[PARTICIPLE] == ["abgerutscht"]


def test_three_conjugations_on_one_page():
    plain, separable, reflexive = verbs("umstellen")
    assert lexeme_stem(plain) == "um:stell" and plain.participles == ("umstellt",)
    assert lexeme_stem(separable) == "um=stell" and separable.participles == ("umgestellt",)
    assert reflexive.reflexive and lexeme_stem(reflexive) == "um=stell"
    assert principal_forms(separable)[PRETERITE] == ["stellte um"]


def test_no_main_clause_forms():
    (verb,) = verbs("bausparen")
    result = principal_forms(verb)
    assert result[PRESENT_1SG] == [] and result[PRETERITE] == []
    assert result[IMPERATIVE_SG] == ["bauspar", "bauspare"]
    assert result[PARTICIPLE] == ["baugespart"]


def test_strong_verb_with_vowel_change():
    plain, reflexive, separable = verbs("uebergeben")
    assert stems(plain) == {
        "present": "geb",
        "present_2sg": "gib",
        "preterite": "gab",
        "participle": "geb",
    }
    assert forms(plain) == [
        ["übergebe"],
        ["übergibst"],
        ["übergibt"],
        ["übergab"],
        ["übergäbe"],
        ["übergib"],
        ["übergebt"],
        ["übergeben"],
    ]
    assert reflexive.reflexive and stems(reflexive) == stems(plain)
    assert stems(separable) == stems(plain)
    assert lexeme_stem(separable) == "über=geb"
    assert stems(separable)["participle"] == "geb"  # über-ge-geb-en
    assert principal_forms(separable)[IMPERATIVE_SG] == ["gib über"]


def test_strong_stem_in_t():
    (finden,) = verbs("finden")
    assert principal_forms(finden)[PRESENT_2SG] == ["findest"]
    assert stems(finden)["participle"] == "fund"
    assert conjugation_class(finden) == "strong"
    (halten,) = verbs("halten")
    result = principal_forms(halten)
    assert (result[PRESENT_2SG], result[PRESENT_3SG]) == (["hältst"], ["hält"])
    assert result[IMPERATIVE_SG] == ["halt", "halte"] and result[IMPERATIVE_PL] == ["haltet"]


def test_mixed_verb():
    (verb,) = verbs("denken")
    assert verb.mixed
    assert stems(verb) == {
        "present": "denk",
        "present_2sg": "denk",
        "preterite": "dach",
        "participle": "dach",
    }
    assert conjugation_class(verb) == "mixed"
    result = principal_forms(verb)
    assert result[PRETERITE] == ["dachte"] and result[SUBJUNCTIVE] == ["dächte"]


def test_modal_and_tun():
    (muessen,) = verbs("muessen")
    assert forms(muessen) == [
        ["muss"],
        ["musst"],
        ["muss"],
        ["musste"],
        ["müsste"],
        [],
        [],
        ["gemusst"],
    ]
    assert stems(muessen)["preterite"] == "muss"
    (tun,) = verbs("tun")
    result = principal_forms(tun)
    assert result[PRESENT_1SG] == ["tue", "tu"]  # given on the page, with a <ref>
    assert result[PRESENT_3SG] == ["tut"] and result[IMPERATIVE_SG] == ["tu", "tue"]


def test_word_group():
    (verb,) = verbs("rad-fahren")
    assert verb.word_group and verb.lemma == "Rad fahren" and lexeme_stem(verb) == "Rad fahr"
    result = principal_forms(verb)
    assert result[PRESENT_2SG] == ["fährst Rad"] and result[PARTICIPLE] == ["Rad gefahren"]
    assert stems(verb)["participle"] == "fahr"


def test_particle_written_differently_when_separated():
    sein, haben = verbs("brustschwimmen")
    assert (sein.auxiliary, haben.auxiliary) == ("sein", "haben")
    result = principal_forms(sein)
    assert result[PRETERITE] == ["schwamm Brust", "schwomm Brust"]
    assert result[SUBJUNCTIVE] == ["schwämme Brust", "schwömme Brust"]
    assert result[PARTICIPLE] == ["brustgeschwommen"]


def test_overview_table():
    # The table of the first verb section of "backen", without its picture.
    (template,) = find_templates(
        "{{Deutsch Verb Übersicht\n|Präsens_ich=backe\n|Präsens_du=bäckst\n"
        "|Präsens_du*=backst\n|Präsens_er, sie, es=bäckt\n|Präsens_er, sie, es*=backt\n"
        "|Präteritum_ich=buk\n|Präteritum_ich*=backte\n|Partizip II=gebacken\n"
        "|Konjunktiv II_ich=büke\n|Konjunktiv II_ich*=backte\n|Imperativ Singular=backe\n"
        "|Imperativ Singular*=back\n|Imperativ Plural=backt\n|Hilfsverb=haben\n"
        "|Bild=Konevets - bakery.jpg|mini|1|Im Kloster wird selbst ''gebacken''.\n}}"
    )
    result = overview_forms(template)
    assert result[PRESENT_2SG] == ["bäckst", "backst"]
    assert result[PRETERITE] == ["buk", "backte"]
    assert result[IMPERATIVE_PL] == ["backt"] and result["Hilfsverb"] == ["haben"]


def test_absent_forms_in_overview_table():
    (template,) = find_templates(
        "{{Deutsch Verb Übersicht|Präsens_ich=—|Präsens_er, sie, es=regnet|Hilfsverb=haben}}"
    )
    result = overview_forms(template)
    assert result[PRESENT_1SG] == [] and result[PRESENT_3SG] == ["regnet"]


def test_subjunctive_stems_that_do_not_follow_from_the_preterite():
    werfen, stehen, rennen = verbs("werfen")[0], verbs("stehen")[0], verbs("rennen")[0]
    assert stems(werfen)["preterite"] == "warf"
    assert stem_variants(werfen) == [("subjunctive", "würf")]  # the only stem
    assert stem_variants(stehen) == [("subjunctive", "stünd")]  # a variant besides ständ
    assert stems(rennen)["preterite"] == "rann" and conjugation_class(rennen) == "mixed"
    assert stem_variants(rennen) == [("subjunctive", "renn")]
    assert stem_variants(verbs("reisen")[0]) == []


def test_inseparable_prefix():
    plain, _, separable = verbs("uebergeben")
    assert lexeme_stem(plain) == "über:geb" and lexeme_stem(separable) == "über=geb"
    assert lexeme_stem(verbs("gehoeren")[0]) == "gehör"  # ge- needs a known base
    assert lexeme_stem(verbs("gehoeren")[0], {"hör"}) == "ge:hör"
    assert lexeme_stem(verbs("denken")[0]) == "denk"
    assert lexeme_stem(verbs("reden")[0]) == "red"  # geredet
    verifizieren = verbs("verifizieren")[0]
    assert lexeme_stem(verifizieren, {"barrikadier"}) == "verifizier"
    assert split_prefix(verifizieren, {"ifizier"}) == ("ver", "ifizier")


def test_sein_has_three_stems():
    verb = verbs("sein")[0]
    assert stems(verb) == {
        "present": "s",
        "present_2sg": "b",
        "preterite": "w",
        "participle": "wes",
    }
    assert conjugation_class(verb) == "irregular" and lexeme_stem(verb) == "s"
    assert not is_copula_group(verb)


def test_variant_stems():
    assert stem_variants(verbs("heben")[0]) == [("preterite", "hub")]  # hüb follows from hub
    gebaeren = verbs("gebaeren")[0]
    assert lexeme_stem(gebaeren) == "gebär" and stems(gebaeren)["present_2sg"] == "gebier"
    assert stem_variants(gebaeren) == [("present_2sg", "gebär")]  # gebärst besides gebierst
    assert stem_variants(verbs("bieten")[0]) == []  # beutst is a single form, not a stem
