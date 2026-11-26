from pathlib import Path

import pytest

from hawfinch.features.declension import (
    ADJECTIVAL,
    DEFAULT,
    IRREGULAR,
    LOAN,
    MARKED_N,
    MARKED_R,
    NO_GENDER,
    NOTE_ATTRIBUTE,
    NOTE_CAPITALS,
    NOTE_LEUTE,
    NOTE_NS,
    NOTE_STEM,
    NOTE_WORDS,
    NOTE_ZERO,
    NOUN_TABLE,
    PRIMARY,
    SECONDARY,
    Singular,
    adjectival_types,
    name_types,
    noun_types,
    plural_only_type,
    plural_type,
    read_noun,
    umlauted,
)
from hawfinch.wikitext.templates import find_templates

FIXTURES = Path(__file__).parent / "fixtures" / "nouns"


def noun(name: str):
    text = (FIXTURES / f"{name}.wiki").read_text(encoding="utf-8")
    (table,) = [t for t in find_templates(text) if t.name == NOUN_TABLE]
    return read_noun(table)


def types(name: str) -> list[tuple]:
    """(gender, class, plural stem, segmented plural, note) of every singular and plural."""
    table = noun(name)
    result = []
    for singular in table.singulars:
        for plural in table.plurals:
            found = plural_type(singular, plural)
            result.append(
                (found.gender, found.plural_class, found.stem, found.segmented, found.note)
            )
    return result


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        # primary: -e for masculine and neuter nouns, -en for feminine nouns
        ("aschekreuz", [("n", PRIMARY, "Aschekreuz", "Aschekreuz-e", "")]),
        ("einzugschacht", [("m", PRIMARY, "Einzugschächt", "Einzugschächt-e", "")]),
        ("hauptsaal", [("m", PRIMARY, "Hauptsäl", "Hauptsäl-e", "")]),
        ("yachthafen", [("m", PRIMARY, "Yachthäfen", "Yachthäfen-", "")]),
        ("schispringerin", [("f", PRIMARY, "Schispringerinn", "Schispringerinn-en", "")]),
        # secondary: the opposite
        ("kunktator", [("m", SECONDARY, "Kunktator", "Kunktator-en", "")]),
        ("foton", [("n", SECONDARY, "Foton", "Foton-en", "")]),
        ("darmnaht", [("f", SECONDARY, "Darmnäht", "Darmnäht-e", "")]),
        ("grosstochter", [("f", SECONDARY, "Großtöchter", "Großtöchter-", "")]),
        ("mondenfinsternis", [("f", SECONDARY, "Mondenfinsterniss", "Mondenfinsterniss-e", "")]),
        # marked: -er plurals and weak masculine nouns
        ("zeigewort", [("n", MARKED_R, "Zeigewört", "Zeigewört-er", "")]),
        ("cocastrauch", [("m", MARKED_R, "Cocasträuch", "Cocasträuch-er", "")]),
        ("eunuche", [("m", MARKED_N, "Eunuche", "Eunuche-n", "")]),
        # a genitive in -ns belongs to a singular in -n
        ("landfriede", [("m", PRIMARY, "Landfrieden", "Landfrieden-", NOTE_NS)]),
        # default and loan
        ("ufo", [("n", DEFAULT, "Ufo", "Ufo-s", "")]),
        ("karpellum", [("n", LOAN, "Karpell", "Karpell-a", "")]),
        ("apokarpium", [("n", LOAN, "Apokarpi", "Apokarpi-en", "")]),
        ("casus", [("m", LOAN, "Casus", "Casus-", NOTE_ZERO)]),
        # parallel plurals and parallel genders
        (
            "kubbuz",
            [("n", LOAN, "Kubbuz", "Kubbuz-im", ""), ("n", PRIMARY, "Kubbuz", "Kubbuz-e", "")],
        ),
        (
            "rabenaas",
            [
                ("n", PRIMARY, "Rabenaas", "Rabenaas-e", ""),
                ("n", MARKED_R, "Rabenäs", "Rabenäs-er", ""),
            ],
        ),
        (
            "bretzel",
            [
                ("f", PRIMARY, "Bretzel", "Bretzel-n", ""),
                ("n", SECONDARY, "Bretzel", "Bretzel-n", ""),
            ],
        ),
        # a native suffix on a stem that the singular does not have
        ("profanbau", [("m", SECONDARY, "Profanbaut", "Profanbaut-en", NOTE_STEM)]),
        # a plural in -leute is substitutive, and irregular
        (
            "clubobmann",
            [
                ("m", MARKED_R, "Clubobmänn", "Clubobmänn-er", ""),
                ("m", IRREGULAR, "Clubobleut", "Clubobleut-e", NOTE_LEUTE),
            ],
        ),
        # several words, the first one inflected
        ("quaestio-juris", [("f", LOAN, "Quaestion Juris", "Quaestion-es Juris", NOTE_WORDS)]),
    ],
)
def test_plural_type(name, expected):
    assert types(name) == expected


def test_singular_of_a_genitive_in_ns():
    found = plural_type(noun("landfriede").singulars[0], "Landfrieden")
    assert found.singular == "Landfrieden"


def test_genitive_in_es_stands_for_the_one_in_s():
    # the page gives Zeigeworts and, starred, Zeigewortes
    assert noun("zeigewort").singulars[0].genitives == ("Zeigewortes",)
    assert noun("ufo").singulars[0].genitives == ("Ufos", "Ufo")


@pytest.mark.parametrize(
    ("genitives", "plural", "plural_class", "variants"),
    [
        (("Elbs", "Elben"), "Elben", MARKED_N, ("Elbs",)),  # weak by a variant
        (("Elbs", "Elben"), "Elbe", PRIMARY, ("Elben",)),
        (("Elbs",), "Elbe", PRIMARY, ()),
    ],
)
def test_genitive_variants(genitives, plural, plural_class, variants):
    found = plural_type(Singular("m", "Elb", genitives), plural)
    assert (found.plural_class, found.genitive_variants) == (plural_class, variants)


@pytest.mark.parametrize(
    ("plural", "plural_class", "segmented"),
    [
        ("Leute", PRIMARY, "Leut-e"),
        ("Ferien", PRIMARY, "Ferie-n"),
        ("Kosten", PRIMARY, "Kost-en"),
        ("Eltern", PRIMARY, "Elter-n"),
        ("Geschwister", PRIMARY, "Geschwister-"),
        ("Hot Pants", DEFAULT, "Hot Pant-s"),
        ("Mammalia", LOAN, "Mammali-a"),
        ("Plantae", LOAN, "Planta-e"),
        ("USA", None, "USA-"),
    ],
)
def test_plural_only(plural, plural_class, segmented):
    found = plural_only_type(plural)
    assert (found.gender, found.singular) == (NO_GENDER, None)
    assert found.note == (NOTE_CAPITALS if plural_class is None else "")
    assert (found.plural_class, found.segmented) == (plural_class, segmented)


def names(wikitext: str, name: str, gender: str = ""):
    (table,) = find_templates(wikitext)
    return [(f.gender, f.plural_class, f.segmented) for f in name_types(table, name, gender)]


def test_name_tables():
    # the surname table builds genitive and plural in -s, except after a sibilant
    assert names("{{Deutsch Nachname Übersicht}}", "Uhse") == [("mf", DEFAULT, "Uhse-s")]
    assert names("{{Deutsch Nachname Übersicht}}", "Schulz") == []
    given = (
        "{{Deutsch Vorname Übersicht f"
        "|Nominativ Plural 1=Egbertinen|Nominativ Plural 2=Egbertines}}"
    )
    assert names(given, "Egbertine") == [("f", None, "Egbertinen-"), ("f", DEFAULT, "Egbertine-s")]
    assert names("{{Deutsch Toponym Übersicht}}", "Polen", "n") == []


def adjectival(wikitext: str):
    (table,) = find_templates(wikitext)
    return [(f.gender, f.plural_class, f.segmented, f.note) for f in adjectival_types(table)]


def test_adjectival_noun():
    table = "{{Deutsch adjektivisch Übersicht|Genus=m|Stamm=Beigeordnete}}"
    assert adjectival(table) == [("m", ADJECTIVAL, "Beigeordnet-e", "")]
    assert adjectival(table.replace("}}", "|kein Plural=1}}")) == []


def test_noun_with_attributive_adjective():
    table = (
        "{{Deutsch adjektivisch Übersicht|Genus=m|Nominativ Singular stark=grauer Star"
        "|Genitiv Singular stark=grauen Stars|Nominativ Plural stark=graue Stare}}"
    )
    assert adjectival(table) == [("m", PRIMARY, "graue Star-e", NOTE_ATTRIBUTE)]


def kept(name: str, gender: str = "") -> list[tuple]:
    return [
        (found.gender, found.plural_class, found.segmented, found.note)
        for _, found in noun_types(noun(name), gender)
    ]


def test_plural_without_suffix_is_dropped_beside_another_plural():
    # Dattelkeks and Dattelkekse, for a masculine and a neuter singular
    assert kept("dattelkeks") == [
        ("m", PRIMARY, "Dattelkeks-e", ""),
        ("n", PRIMARY, "Dattelkeks-e", ""),
    ]
    assert kept("kkw") == [("n", DEFAULT, "KKW-s", "")]  # KKW and KKWs
    # without a suffix after a reduced syllable: an e-plural, kept beside the one in -s
    assert kept("bretzel") == [(f[0], f[1], f[3], f[4]) for f in types("bretzel")]


def test_plural_without_suffix_stays_if_it_is_the_only_one():
    assert kept("casus") == [("m", LOAN, "Casus-", NOTE_ZERO)]


def test_abbreviation_in_capitals_without_suffix_has_no_class():
    assert kept("vwl") == [("f", None, "VWL-", NOTE_CAPITALS)]


def test_gender_of_the_heading_is_used_where_the_table_has_none():
    table = read_noun(
        find_templates(
            "{{Deutsch Substantiv Übersicht|Nominativ Singular=Frau"
            "|Genitiv Singular=Frau|Nominativ Plural=Frauen}}"
        )[0]
    )
    (found,) = noun_types(table, "f")
    assert (found[1].gender, found[1].plural_class) == ("f", PRIMARY)
    (found,) = noun_types(table)
    assert found[1].plural_class is None


def test_noun_without_plural():
    table = noun("sufiismus")
    assert table.singulars[0].nominative == "Sufiismus"
    assert table.plurals == ()


def test_plural_only_noun():
    table = noun("hot-pants")
    assert table.singulars == ()
    assert table.plurals == ("Hot Pants",)


@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        ("Stuhl", ["Stühl"]),
        ("Baum", ["Bäum"]),
        ("Saal", ["Säl", "Saäl"]),
        ("Apfel", ["Äpfel"]),
        ("Kloster", ["Klöster"]),
        ("Fisch", []),
    ],
)
def test_umlauted(stem, expected):
    assert umlauted(stem) == expected


@pytest.mark.parametrize(
    ("gender", "singular", "genitive", "plural", "plural_class", "segmented"),
    [
        ("m", "Bus", "Busses", "Busse", PRIMARY, "Buss-e"),
        ("f", "Tante", "Tante", "Tanten", PRIMARY, "Tante-n"),
        ("n", "Mädchen", "Mädchens", "Mädchen", PRIMARY, "Mädchen-"),
        ("n", "Kindchen", "Kindchens", "Kinderchen", PRIMARY, "Kinderchen-"),
        ("m", "Staat", "Staates", "Staaten", SECONDARY, "Staat-en"),
        ("f", "Mutter", "Mutter", "Mütter", SECONDARY, "Mütter-"),
        ("m", "Mann", "Mannes", "Männer", MARKED_R, "Männ-er"),
        ("n", "Herz", "Herzens", "Herzen", IRREGULAR, "Herz-en"),
        ("m", "Name", "Namens", "Namen", PRIMARY, "Namen-"),
        ("f", "Subfamilia", "Subfamilia", "Subfamiliae", LOAN, "Subfamilia-e"),
        ("n", "Thema", "Themas", "Themata", LOAN, "Thema-ta"),
        ("n", "Museum", "Museums", "Museen", LOAN, "Muse-en"),
        ("n", "Fossil", "Fossils", "Fossilien", LOAN, "Fossil-ien"),
        ("n", "Tempus", "Tempus", "Tempora", LOAN, "Tempor-a"),
        ("m", "Atlas", "Atlas", "Atlanten", LOAN, "Atlant-en"),
        ("m", "Gentleman", "Gentlemans", "Gentlemen", LOAN, "Gentlemen-"),
        ("f", "Liquida", "Liquida", "Liquidä", LOAN, "Liquid-ä"),
        ("m", "Junge", "Jungen", "Jungs", DEFAULT, "Jung-s"),
        ("f", "Box", "Box", "Boxes", DEFAULT, "Box-es"),
        (
            "m",
            "Leutnant zur See",
            "Leutnants zur See",
            "Leutnante zur See",
            PRIMARY,
            "Leutnant-e zur See",
        ),
    ],
)
def test_plural_type_of_forms(gender, singular, genitive, plural, plural_class, segmented):
    found = plural_type(Singular(gender, singular, (genitive,)), plural)
    assert (found.plural_class, found.segmented) == (plural_class, segmented)
