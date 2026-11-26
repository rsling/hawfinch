"""Noun declension: the noun table of a lemma page and the plural class derived from it.

First version, written for the feasibility test. The linguistic definition of the classes is
in ``docs/features/plural-classes.md``.

``Deutsch Substantiv Übersicht`` gives the eight case and number forms as named arguments
and the gender as ``Genus``. Parallel genders are numbered (``Genus 1``, ``Nominativ
Singular 1``), parallel plurals as well (``Nominativ Plural 2``), and a star marks a variant
of a single form (``Genitiv Singular*``, ``Nominativ Plural*``). Positional arguments are
image options and are ignored.

``Deutsch adjektivisch Übersicht`` is used for two things: nouns declined like adjectives,
given as ``Stamm`` (``Beigeordnete``), and nouns with an attributive adjective, given as
forms for the strong, weak and mixed declension of the adjective (``grauer Star``).

:func:`read_noun` turns a noun table into a :class:`Noun`, and :func:`noun_types` gives the
plurals of a noun with their class, plural stem and segmented plural. It uses
:func:`plural_type`, which compares one singular with one plural, and
:func:`plural_only_type` for a plural without a singular. :func:`adjectival_types` reads
the second template and :func:`name_types` the tables of names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from hawfinch.wikitext.templates import Template

NOUN_TABLE = "Deutsch Substantiv Übersicht"
ADJECTIVAL_TABLE = "Deutsch adjektivisch Übersicht"
GENDERS = ("m", "f", "n")
NO_GENDER = "nd"  # a noun without a singular has no gender

PRIMARY = "primary"
SECONDARY = "secondary"
MARKED_N = "marked-n"
MARKED_R = "marked-r"
DEFAULT = "default"
LOAN = "loan"
IRREGULAR = "irregular"
ADJECTIVAL = "adjectival"

# Suffix types; the literal suffix is in the segmented plural (``Tante-n``, ``Fenster-``).
E, EN, ER, S = "e", "en", "er", "s"

_CLASSES = {
    ("m", E): PRIMARY,
    ("n", E): PRIMARY,
    ("f", EN): PRIMARY,
    ("m", EN): SECONDARY,
    ("n", EN): SECONDARY,
    ("f", E): SECONDARY,
}

_ABSENT = {"", "—", "–", "-", "?"}
_BREAK = re.compile(r"</?br\s*/?>")
_REF = re.compile(r"<ref[^>]*?/>|<ref[^>]*>.*?</ref>", re.S)
_SMALL = re.compile(r"<small>.*?</small>", re.S)
_TAG = re.compile(r"<[^>]*>|''+")
_ARTICLE = re.compile(r"^\(?(?:der|die|das|des|dem|den)\)?\s+")
_KEY = re.compile(r"^(Nominativ|Genitiv|Dativ|Akkusativ) (Singular|Plural)(?: ([1-9]))?(\*{0,2})$")


@dataclass(frozen=True, slots=True)
class Singular:
    gender: str  # as given in ``Genus``; ``m``, ``f`` or ``n`` for a noun with a singular
    nominative: str
    genitives: tuple[str, ...]  # the main form first, then the starred variants


@dataclass(frozen=True, slots=True)
class Noun:
    singulars: tuple[Singular, ...]  # empty for a plural-only noun
    plurals: tuple[str, ...]  # nominative plurals: parallel ones, then starred variants


@dataclass(frozen=True, slots=True)
class PluralType:
    plural_class: str | None  # None where no class can be given: see the notes
    gender: str  # m, f, n, or ``nd`` for a plural without a singular
    singular: str | None  # the nominative singular the plural is built on
    stem: str  # the stem as it appears in the plural: Stühl, Baut, Finit
    suffix: str | None  # suffix type (e, en, er, s); None where the class does not give one
    segmented: str  # ``Stühl-e``, ``Lehrer-``, ``Leutnant-e zur See``
    umlaut: bool = False
    genitive_variants: tuple[str, ...] = ()  # genitives singular that do not fit the class
    note: str = ""


def _forms(value: str | None) -> list[str]:
    if value is None:
        return []
    value = _SMALL.sub("", _REF.sub("", value))
    forms = []
    for part in _BREAK.split(value):
        part = _ARTICLE.sub("", " ".join(_TAG.sub("", part).split()))
        if part not in _ABSENT:
            forms.append(part)
    return forms


def _without_short_genitive(nominative: str, genitives: list[str]) -> tuple[str, ...]:
    """The genitives without the form in ``-s`` where the one in ``-es`` is given as well:
    the variation is not stored, and the long form stands for both."""
    forms = dict.fromkeys(genitives)
    if nominative + "es" in forms:
        forms.pop(nominative + "s", None)
    return tuple(forms)


def read_noun(template: Template) -> Noun:
    """Read the genders, the singulars and the nominative plurals of a noun table."""
    cells: dict[tuple[str, str, str], list[str]] = {}
    genders: dict[str, str] = {}
    for key, value in template.args:
        if key is None:
            continue
        if key == "Genus" or re.fullmatch(r"Genus [1-9]", key):
            genders[key.removeprefix("Genus").strip()] = value.strip()
            continue
        m = _KEY.match(key)
        if m:
            case, number, index, _star = m.groups()
            cells.setdefault((case, number, index or ""), []).extend(_forms(value))

    singulars = []
    for index in sorted({i for (_, number, i) in cells if number == "Singular"} | set(genders)):
        nominative = cells.get(("Nominativ", "Singular", index), [])
        if not nominative:
            continue
        gender = genders.get(index) or genders.get("") or genders.get("1") or ""
        genitives = _without_short_genitive(
            nominative[0], cells.get(("Genitiv", "Singular", index), [])
        )
        singulars.append(Singular(gender, nominative[0], genitives))
    plurals = []
    for index in sorted(
        i for (case, number, i) in cells if (case, number) == ("Nominativ", "Plural")
    ):
        plurals += cells[("Nominativ", "Plural", index)]
    return Noun(tuple(singulars), tuple(dict.fromkeys(plurals)))


def _clean(value: str) -> str:
    forms = _forms(value)
    return forms[0] if forms else ""


_UMLAUT = {"a": "ä", "o": "ö", "u": "ü", "A": "Ä", "O": "Ö", "U": "Ü"}
_VOWEL = re.compile(r"[aouAOU]")


def umlauted(stem: str) -> list[str]:
    """The stem with its last ``a``, ``o`` or ``u`` umlauted: ``Stühl`` from ``Stuhl``,
    ``Bäum`` from ``Baum``, ``Säl`` from ``Saal``. Empty if it has none."""
    positions = [m.start() for m in _VOWEL.finditer(stem)]
    if not positions:
        return []
    last = positions[-1]
    result = []
    if stem[last] == "u" and last > 0 and stem[last - 1] in "aA":  # au -> äu
        result.append(stem[: last - 1] + _UMLAUT[stem[last - 1]] + stem[last:])
    else:
        if last > 0 and stem[last - 1].lower() == stem[last]:  # Saal -> Säl-e
            result.append(stem[: last - 1] + _UMLAUT[stem[last - 1]] + stem[last + 1 :])
        result.append(stem[:last] + _UMLAUT[stem[last]] + stem[last + 1 :])
    return result


def _stem_change(singular: str, stem: str) -> bool | None:
    """Whether ``stem`` is the singular (False) or its umlauted form (True), also with the
    final consonant doubled (``Buss-e``, ``Lehrerinn-en``, ``Flüss-e`` from ``Fluß``); None
    if it is neither."""
    bases = [singular]
    if singular and singular[-1] not in "aeiouäöüy":
        bases.append(singular + singular[-1])
    if singular.endswith("ß"):
        bases.append(singular[:-1] + "ss")
    for base in bases:
        if stem == base:
            return False
        if stem in umlauted(base):
            return True
    return None


# Literal suffixes in the order they are tried, with their type.
_NATIVE = (("en", EN), ("er", ER), ("es", S), ("e", E), ("n", EN), ("s", S), ("", E))
# Endings of loan plurals, for the segmentation only.
_LOAN_ENDINGS = ("ien", "en", "er", "es", "im", "ot", "a", "ä", "i", "e", "s", "x")
# A plural without a suffix is an e-plural whose suffix is elided after a reduced syllable:
# Fenster, Gebäude, Hintern, Mädchen, Büchlein, and syllabic l or n (Sackerl, Dirndl).
_REDUCED = re.compile(r"(?:e|e[lrmn]|e[lr]n|lein|[^aeiouäöüy][ln])$")
_DIMINUTIVE = ("chen", "lein")

NOTE_ZERO = "no suffix, not after a reduced syllable"
NOTE_WORDS = "several words, inflected inside"
NOTE_LEUTE = "plural in -leute"
NOTE_STEM = "stem differs"
NOTE_NS = "genitive in -ns, singular taken with -n"
NOTE_NO_GENDER = "gender not given"
NOTE_ATTRIBUTE = "with an attributive adjective"
NOTE_CAPITALS = "abbreviation in capitals, no suffix"


def _class(gender: str, suffix: str) -> str | None:
    if suffix == ER:
        return MARKED_R
    if suffix == S:
        return DEFAULT
    return _CLASSES.get((gender, suffix))


def _common_prefix(a: str, b: str) -> int:
    length = 0
    while length < min(len(a), len(b)) and a[length] == b[length]:
        length += 1
    return length


def _loan_stem(singular: str, plural: str) -> tuple[str, str]:
    """Stem and ending of a loan plural. The cut is before the ending, but never inside the
    part shared with the singular: ``Muse-en`` and ``Mysteri-en``, but ``Fossil-ien``;
    ``Tempor-a``. Without a recognisable ending the whole plural is the stem."""
    if plural == singular + "ta":
        return singular, "ta"
    if singular.endswith("man") and plural.endswith("men"):
        return plural, ""
    shared = _common_prefix(singular, plural)
    for ending in _LOAN_ENDINGS:
        if plural.endswith(ending) and len(plural) - len(ending) >= max(shared, 2):
            return plural[: -len(ending)], ending
    return plural, ""


def _capitals(word: str) -> bool:
    """Whether a word is an abbreviation written in capitals: ``VWL``, ``KZ``."""
    return not any(letter.islower() for letter in word)


def _loan(gender: str, singular: str, plural: str, note: str = "") -> PluralType:
    if note == NOTE_ZERO and _capitals(singular):  # VWL: no class
        return PluralType(None, gender, singular, plural, None, f"{plural}-", note=NOTE_CAPITALS)
    stem, ending = (plural, "") if note == NOTE_ZERO else _loan_stem(singular, plural)
    return PluralType(LOAN, gender, singular, stem, None, f"{stem}-{ending}", note=note)


def _irregular(gender: str, singular: str, plural: str) -> PluralType | None:
    """Plurals with a native suffix on a stem that the singular does not have."""

    def result(stem: str, literal: str, suffix: str) -> PluralType:
        return PluralType(
            _class(gender, suffix),
            gender,
            singular,
            stem,
            suffix,
            f"{stem}-{literal}",
            note=NOTE_STEM,
        )

    if singular.endswith(_DIMINUTIVE) and plural.endswith(_DIMINUTIVE):  # Kinderchen
        return result(plural, "", E)
    if singular.lower().endswith("bau") and plural == singular + "ten":  # Bauten
        return result(singular + "t", "en", EN)
    if singular.endswith("e") and plural in (singular[:-1] + "s", singular + "ns"):  # Jungs
        return result(plural[:-1], "s", S)
    return None


def _inside(gender: str, singular: str, plural: str) -> PluralType | None:
    """A noun written as several words that does not inflect at its end: the class is that
    of the first word that changes (``Leutnant-e zur See``, ``Quaestion-es Juris``)."""
    words, plural_words = singular.split(" "), plural.split(" ")
    if len(words) < 2 or len(words) != len(plural_words):
        return None
    changed = [i for i, (a, b) in enumerate(zip(words, plural_words, strict=True)) if a != b]
    if not changed:
        return None
    first = changed[0]
    word = plural_type(Singular(gender, words[first], ()), plural_words[first])
    stem = " ".join([*plural_words[:first], word.stem, *plural_words[first + 1 :]])
    segmented = " ".join([*plural_words[:first], word.segmented, *plural_words[first + 1 :]])
    note = NOTE_WORDS if first < len(words) - 1 else word.note
    return replace(word, singular=singular, stem=stem, segmented=segmented, note=note)


def plural_only_type(plural: str) -> PluralType:
    """A plural without a singular; its gender is ``nd``. The class follows from the ending
    alone: ``-e`` and ``-en`` are ``primary`` by convention, as if the stem of an e-plural
    were masculine or neuter (``Leut-e``) and that of an en-plural feminine (``Ferie-n``).
    A reduced syllable without a suffix is an elided ``-e`` (``Geschwister-``), ``-s`` is
    ``default`` (``Hot Pant-s``), and everything else is a ``loan`` plural (``Mammali-a``).
    An abbreviation in capitals has no class (``USA``)."""

    def result(plural_class: str | None, cut: int, suffix: str | None) -> PluralType:
        stem, literal = (plural[:-cut], plural[-cut:]) if cut else (plural, "")
        return PluralType(plural_class, NO_GENDER, None, stem, suffix, f"{stem}-{literal}")

    if _capitals(plural):  # USA, ÖBB
        return replace(result(None, 0, None), note=NOTE_CAPITALS)
    if plural.endswith("ae"):
        return result(LOAN, 1, None)
    if plural.endswith(("ien", "eln", "ern")):
        return result(PRIMARY, 1, EN)
    if plural.endswith("en"):
        return result(PRIMARY, 2, EN)
    if plural.endswith("e"):
        return result(PRIMARY, 1, E)
    if plural.endswith(("er", "el")):
        return result(PRIMARY, 0, E)
    if plural.endswith("s"):
        return result(DEFAULT, 1, S)
    for ending in ("im", "ot", "a", "i", "x"):
        if plural.endswith(ending):
            return result(LOAN, len(ending), None)
    return result(LOAN, 0, None)


def _genitives(singular: Singular) -> tuple[str, str, tuple[str, ...], str]:
    """The singular a table really gives, its kind of genitive (``weak``, ``ns`` or ``""``)
    and the genitives that do not fit.

    A noun is weak if any of its genitives is the nominative plus ``-n`` or ``-en``. A main
    genitive in ``-ns`` belongs to a singular in ``-n`` (``Friedens`` to ``Frieden``, not to
    ``Friede``), which is what the plural is then compared with."""
    nominative, genitives = singular.nominative, singular.genitives
    weak_forms = {nominative + "n", nominative + "en"}
    for ending in ("ns", "ens"):
        if genitives[:1] == (nominative + ending,):
            misfits = tuple(g for g in genitives[1:] if g in weak_forms)
            return nominative + ending[:-1], "ns", misfits, NOTE_NS
    if any(g in weak_forms for g in genitives):
        return nominative, "weak", tuple(g for g in genitives if g not in weak_forms), ""
    return nominative, "", (), ""


def plural_type(singular: Singular, plural: str) -> PluralType:
    """Class, stem and segmentation of one nominative plural of one singular."""
    gender = singular.gender
    nominative, genitive, misfits, note = _genitives(singular)
    if genitive == "ns" and gender != "m":  # Herz, Herzens
        nominative, note = singular.nominative, ""
    if nominative.lower().endswith(("mann", "frau")) and plural.lower().endswith("leute"):
        stem = plural[:-1]  # a substitutive plural: Kaufleut-e
        return PluralType(IRREGULAR, gender, nominative, stem, None, f"{stem}-e", note=NOTE_LEUTE)

    found = None
    for literal, suffix in _NATIVE:
        if literal and not plural.endswith(literal):
            continue
        stem = plural[: len(plural) - len(literal)]
        umlaut = _stem_change(nominative, stem)
        if umlaut is None:
            continue
        if literal == "e" and stem.endswith("a"):  # Latin -ae: Subfamilia-e
            break
        if literal == "" and not _REDUCED.search(nominative):
            if not umlaut:  # Kasus; with umlaut it is Liquidä from Liquida
                found = _loan(gender, nominative, plural, NOTE_ZERO)
            break
        found = PluralType(
            _class(gender, suffix), gender, nominative, stem, suffix, f"{stem}-{literal}", umlaut
        )
        break
    if found is None:
        found = (
            _irregular(gender, nominative, plural)
            or _inside(gender, nominative, plural)
            or _loan(gender, nominative, plural)
        )

    if genitive == "ns" and gender == "n":
        found = replace(found, plural_class=IRREGULAR, suffix=None)
    elif genitive == "weak" and gender == "m" and found.suffix == EN:
        found = replace(found, plural_class=MARKED_N, genitive_variants=misfits)
    elif genitive == "weak":
        weak_forms = tuple(g for g in singular.genitives if g not in misfits)
        found = replace(found, genitive_variants=weak_forms)
    else:
        found = replace(found, genitive_variants=misfits)
    if gender not in GENDERS:
        found = replace(found, plural_class=None, note=NOTE_NO_GENDER)
    elif note and not found.note:
        found = replace(found, note=note)
    return found


def _without_suffixless(found: list[PluralType]) -> list[PluralType]:
    """The plurals of one singular without the one that has no suffix after a full
    syllable, if there is another plural: of ``Keks`` and ``Kekse`` only ``Kekse`` is kept,
    of ``KZ`` and ``KZs`` only ``KZs``. A plural without a suffix after a reduced syllable
    is an ordinary e-plural and stays (``Onkel`` beside ``Onkels``)."""
    suffixless = (NOTE_ZERO, NOTE_CAPITALS)
    if any(f.note not in suffixless for f in found):
        return [f for f in found if f.note not in suffixless]
    return found


def noun_types(noun: Noun, gender: str = "") -> list[tuple[Singular | None, PluralType]]:
    """The plurals of a noun table, each with the singular it is built on.

    Every singular is combined with every plural, because the table does not say which of
    them belong together. ``gender`` is the gender given in the heading of the section; it
    is used where the table gives none. A noun without a singular has gender ``nd``."""
    if not noun.singulars:
        return [(None, plural_only_type(plural)) for plural in noun.plurals]
    result = []
    for singular in noun.singulars:
        if singular.gender not in GENDERS and gender in GENDERS:
            singular = replace(singular, gender=gender)
        found = _without_suffixless([plural_type(singular, plural) for plural in noun.plurals])
        result += [(singular, f) for f in found]
    return result


def adjectival_types(template: Template) -> list[PluralType]:
    """The plurals of ``Deutsch adjektivisch Übersicht``.

    With ``Stamm`` the noun is declined like an adjective and is ``adjectival``; its plural
    is the strong form, the stem plus ``-e`` (``Beigeordnet-e``). Otherwise the table gives
    a noun with an attributive adjective, and the class is that of the noun, its last word
    (``graue Star-e``)."""
    params = template.params()
    gender = (params.get("Genus") or "").strip()
    if "Stamm" in params:
        if "kein Plural" in params:
            return []
        plural = _clean(params["Stamm"])
        if not plural:
            return []
        stem = plural.removesuffix("e")
        literal = "e" if plural.endswith("e") else ""
        if "kein Singular" in params or gender not in GENDERS:
            gender = NO_GENDER
        return [PluralType(ADJECTIVAL, gender, None, stem, None, f"{stem}-{literal}")]
    plurals = _forms(params.get("Nominativ Plural stark"))
    singulars = _forms(params.get("Nominativ Singular stark"))
    if not singulars or gender not in GENDERS:
        return [plural_only_type(plural) for plural in plurals]
    words = singulars[0].split(" ")
    genitives = tuple(
        g.split(" ")[-1]
        for key in ("Genitiv Singular stark", "Genitiv Singular stark*")
        for g in _forms(params.get(key))
    )
    head = Singular(gender, words[-1], genitives)
    result = []
    for plural in plurals:
        plural_words = plural.split(" ")
        word = plural_type(head, plural_words[-1])
        before = plural_words[:-1]
        result.append(
            replace(
                word,
                singular=singulars[0],
                stem=" ".join([*before, word.stem]),
                segmented=" ".join([*before, word.segmented]),
                note=word.note or NOTE_ATTRIBUTE,
            )
        )
    return _without_suffixless(result)


NAME_TABLES = frozenset(
    {
        "Deutsch Nachname Übersicht",
        "Deutsch Vorname Übersicht m",
        "Deutsch Vorname Übersicht f",
        "Deutsch Vorname Übersicht n",
        "Deutsch Toponym Übersicht",
        "Deutsch Eigenname Übersicht",
        "Deutsch Name Übersicht",
    }
)
NOTE_NAME = "name without a plural in -s"
_SIBILANT = ("s", "ß", "x", "z")


def name_types(template: Template, name: str, gender: str) -> list[PluralType]:
    """The plurals of a name table. A name whose genitive singular and nominative plural
    both end in ``-s`` is ``default`` (``Müller-s``); other plurals of names get no class.

    ``Deutsch Nachname Übersicht`` gives no forms: the template builds genitive and plural
    in ``-s``, except after a sibilant. The other tables give a plural as an argument, if
    there is one; the genitive is built in ``-s`` unless it is given."""
    table = read_noun(template)
    if template.name == "Deutsch Nachname Übersicht" and not table.plurals:
        plurals = () if name.endswith(_SIBILANT) else (name + "s",)
    else:
        plurals = table.plurals
    if template.name.startswith("Deutsch Vorname Übersicht"):
        gender = template.name[-1]
    elif template.name == "Deutsch Nachname Übersicht":
        gender = "mf"  # the table has a masculine and a feminine singular
    given = [g for singular in table.singulars for g in singular.genitives]
    genitives = given or ([] if name.endswith(_SIBILANT) else [name + "s"])
    result = []
    for plural in plurals:
        if plural == name + "s" and any(g.endswith("s") for g in genitives):
            result.append(PluralType(DEFAULT, gender, name, name, S, f"{name}-s"))
        else:
            result.append(
                PluralType(None, gender, name, plural, None, f"{plural}-", note=NOTE_NAME)
            )
    return result
