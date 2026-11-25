"""Inflectional features: paradigms and inflection classes.

First version, written for the feasibility test: verbs only.

German verb conjugations are on ``Flexion:`` pages, as calls of four templates whose
arguments are stems or pieces of stems (see ``Vorlage:Deutsch Verb …/Doku`` in the dump):

- ``Deutsch Verb regelmäßig|ka|u|f|e|n|gekauft``: the infinitive cut into five pieces (the
  last four letters separately, ``ch`` counting as one letter) and the Partizip II. The
  separable parts are ``Teil 1`` and ``Teil 2``.
- ``Deutsch Verb schwach untrennbar reflexiv``: the same six positions.
- ``Deutsch Verb schwach trennbar reflexiv|ab|arbe|i|t|e|n|abgearbeitet``: the particle
  first, then the same six.
- ``Deutsch Verb unregelmäßig``: ``1`` particle, ``2`` present stem, ``3`` preterite (first
  person singular), ``4`` subjunctive II stem, ``5`` Partizip II without the particle,
  ``6`` present stem of the second and third person singular, ``7`` stem-final behaviour
  (``e``, ``e-``, ``e2``, ``em``, ``-s``), ``8`` vowel change (``i``) and mixed inflection
  (``n``), ``9`` and ``11`` alternative subjunctive II stem and preterite, ``10`` the
  infinitive of a modal verb, of ``tun`` or of ``wissen``, ``T2`` a second particle.

:func:`read_verb` turns such a call into a :class:`Verb`, :func:`stems` gives its stem
allomorphs, and :func:`principal_forms` generates the forms that the lemma page lists in
``Deutsch Verb Übersicht``, so that the two sources can be compared.
"""

from __future__ import annotations

import html
import re
from collections.abc import Collection
from dataclasses import dataclass, field

from hawfinch.wikitext.templates import Template

REGULAR = "Deutsch Verb regelmäßig"
IRREGULAR = "Deutsch Verb unregelmäßig"
REFLEXIVE = "Deutsch Verb schwach untrennbar reflexiv"
REFLEXIVE_SEPARABLE = "Deutsch Verb schwach trennbar reflexiv"
VERB_TEMPLATES = frozenset({REGULAR, IRREGULAR, REFLEXIVE, REFLEXIVE_SEPARABLE})

# Keys of ``Deutsch Verb Übersicht``, used for the generated principal forms as well.
PRESENT_1SG = "Präsens_ich"
PRESENT_2SG = "Präsens_du"
PRESENT_3SG = "Präsens_er, sie, es"
PRETERITE = "Präteritum_ich"
SUBJUNCTIVE = "Konjunktiv II_ich"
IMPERATIVE_SG = "Imperativ Singular"
IMPERATIVE_PL = "Imperativ Plural"
PARTICIPLE = "Partizip II"
PRINCIPAL_FORMS = (
    PRESENT_1SG,
    PRESENT_2SG,
    PRESENT_3SG,
    PRETERITE,
    SUBJUNCTIVE,
    IMPERATIVE_SG,
    IMPERATIVE_PL,
    PARTICIPLE,
)

MODALS = frozenset({"dürfen", "können", "mögen", "müssen", "sollen", "wollen"})
# Stem-final m or n takes an e before -st and -t after these letters: atm-est, rechn-et.
BEFORE_M = ("b", "c", "ch", "d", "f", "g", "j", "k", "p", "s", "t", "v", "w", "x", "z", "ß")
BEFORE_N = (*BEFORE_M, "m")
SIBILANTS = ("s", "ß", "x", "z", "c")  # -st loses its s after these: reis-t, outsourc-t

# Named arguments that replace single forms; each maps to the principal form it replaces.
OVERRIDES = {
    "1. Singular Indikativ Präsens Aktiv": PRESENT_1SG,
    "2. Singular Indikativ Präsens Aktiv": PRESENT_2SG,
    "3. Singular Indikativ Präsens Aktiv": PRESENT_3SG,
    "1. Singular Indikativ Präteritum Aktiv": PRETERITE,
    "1. Singular Konjunktiv Präteritum Aktiv": SUBJUNCTIVE,
    "2. Singular Imperativ Präsens Aktiv": IMPERATIVE_SG,
    "2. Plural Imperativ Präsens Aktiv": IMPERATIVE_PL,
    "Indikativ Präsens (ich)": PRESENT_1SG,
    "Indikativ Präsens (du)": PRESENT_2SG,
    "Indikativ Präsens (man)": PRESENT_3SG,
    "Imperativ (du)": IMPERATIVE_SG,
    "Imperativ (ihr)": IMPERATIVE_PL,
}
ALTERNATIVES = {
    "Indikativ Präsens Alternativform (du)": PRESENT_2SG,
    "Indikativ Präsens Alternativform (man)": PRESENT_3SG,
    "Indikativ Präteritum Aktiv Alternativform (ich)": PRETERITE,
}
_BREAK = re.compile(r"</?br\s*/?>|,|!")
_REF = re.compile(r"<ref[^>]*?/>|<ref[^>]*>.*?</ref>", re.S)
_TAG = re.compile(r"<[^>]*>|''+")
_PRONOUN = re.compile(r"^(?:ich|du|er/sie/es|er, sie, es|er|sie|es|wir|ihr)\s+")


@dataclass(frozen=True, slots=True)
class Verb:
    """One conjugation as read from a ``Flexion:`` page."""

    template: str
    particles: tuple[str, ...]  # separable parts, in order
    infinitive: str  # without the particles
    present: str
    present_2sg: str  # second and third person singular; equals ``present`` if no change
    preterite: str  # first person singular: wusch, dachte
    subjunctive: str  # stem: wüsch, dächt
    participles: tuple[str, ...]  # whole words, with particles
    auxiliary: str
    weak: bool  # read from one of the three templates for weak verbs
    ending: str = ""  # argument 7 of the irregular template
    vowel: str = ""  # argument 8
    special: str = ""  # argument 10
    preterite_alt: str = ""
    subjunctive_alt: str = ""
    distant_particle: str = ""  # spelling of the particle when separated (ViD): Brust
    word_group: bool = False  # written as several words: Rad fahren
    reflexive: bool = False
    impersonal: str = ""  # "es" or "sie"
    no_imperative: bool = False
    no_present: bool = False
    no_preterite: bool = False
    overrides: dict[str, tuple[str, ...]] = field(default_factory=dict, hash=False)
    alternatives: dict[str, tuple[str, ...]] = field(default_factory=dict, hash=False)

    @property
    def separable(self) -> bool:
        return bool(self.particles)

    @property
    def lemma(self) -> str:
        return ("" if not self.word_group else " ").join((*self.particles, self.infinitive))

    @property
    def mixed(self) -> bool:
        """Strong stem with the weak suffix: dach-te, brach-te, konn-te."""
        return not self.weak and "n" in self.vowel and self.preterite.endswith("te")


def _clean(value: str | None) -> str:
    return html.unescape(value or "").strip()


def _forms(value: str) -> tuple[str, ...]:
    """The forms in an override value such as ``du verlöschst,<br />du verlöscht``."""
    result = []
    for part in _BREAK.split(_REF.sub("", html.unescape(value))):
        part = _PRONOUN.sub("", _TAG.sub("", part).strip().rstrip("!").strip())
        if part and part not in result:
            result.append(part)
    return tuple(result)


def _overrides(params: dict[str, str], keys: dict[str, str]) -> dict[str, tuple[str, ...]]:
    result = {}
    for key, form in keys.items():
        if _clean(params.get(key)):
            result[form] = _forms(params[key])
    return result


def _switched_off(params: dict[str, str], *keys: str) -> bool:
    return any(_clean(params.get(key)) for key in keys)


def read_verb(template: Template) -> Verb | None:
    """Read a call of one of the four verb templates; ``None`` if obligatory parts are missing."""
    params = template.params()
    impersonal = _clean(params.get("unpersönlich"))
    # Verbs without finite forms in main clauses (bausparen) have Hauptsatzkonjugation=0.
    no_main = _switched_off(params, "Hauptsatzkonjugation")
    no_present = no_main or _switched_off(params, "Präsens", "Präsens Aktiv")
    no_preterite = no_main or _switched_off(params, "Präteritum", "Präteritum Aktiv")
    no_imperative = bool(impersonal) or _switched_off(
        params, "Imperativ", "Imperativ Präsens Aktiv", "k12ps"
    )
    if template.name == IRREGULAR:
        present, preterite = _clean(params.get("2")), _clean(params.get("3"))
        subjunctive, participle = _clean(params.get("4")), _clean(params.get("5"))
        if not (present and preterite and subjunctive and participle):
            return None
        first = html.unescape(params.get("1") or "")
        word_group = bool(_clean(params.get("Wv")))
        particles = tuple(p for p in (first.strip(), _clean(params.get("T2"))) if p)
        joined = (first.strip() + " " if word_group else first.strip()) + _clean(params.get("T2"))
        special = _clean(params.get("10"))
        infinitive = _clean(params.get("Infinitiv Präsens")) or special
        if not infinitive:
            infinitive = present + ("n" if present.endswith(("el", "er")) else "en")
        # Hilfsverb decides if given; otherwise any value of ``haben`` means sein (haben=0).
        auxiliary = _clean(params.get("Hilfsverb")) or (
            "sein" if _clean(params.get("haben")) else "haben"
        )
        sein = auxiliary == "sein"
        extra = _clean(params.get("Partizip+"))
        return Verb(
            template=template.name,
            particles=particles,
            infinitive=infinitive,
            present=present,
            present_2sg=_clean(params.get("6")) or present,
            preterite=preterite,
            subjunctive=subjunctive,
            participles=tuple(joined + p for p in (participle, extra) if p),
            auxiliary="sein" if sein else "haben",
            weak=False,
            ending=_clean(params.get("7")),
            vowel=_clean(params.get("8")),
            special=special,
            preterite_alt=_clean(params.get("11")),
            subjunctive_alt=_clean(params.get("9")),
            distant_particle=_clean(params.get("ViD")),
            word_group=word_group,
            reflexive=bool(_clean(params.get("reflexiv"))),
            impersonal=impersonal,
            no_imperative=no_imperative,
            overrides=_overrides(params, OVERRIDES),
            alternatives=_overrides(params, ALTERNATIVES),
        )
    if template.name not in VERB_TEMPLATES:
        return None
    offset = 1 if template.name == REFLEXIVE_SEPARABLE else 0
    pieces = [_clean(params.get(str(i + offset))) for i in range(1, 6)]
    infinitive = "".join(pieces)
    participle = _clean(params.get(str(6 + offset)))
    if not infinitive.endswith("n") or len(infinitive) < 3 or not participle:
        return None
    if offset:
        particles = tuple(p for p in (_clean(params.get("1")),) if p)
    else:
        particles = tuple(
            p for p in (_clean(params.get("Teil 1")), _clean(params.get("Teil 2"))) if p
        )
    stem = infinitive[:-2]
    if infinitive.endswith(("eln", "ern", "een")) or not infinitive.endswith("en"):
        stem = infinitive[:-1]
    elif infinitive.endswith("ien") and not infinitive.endswith(("aien", "eien")):
        stem = infinitive[:-1]  # knie-n, not schrei-en
    extra = _clean(params.get("Partizip+"))
    return Verb(
        template=template.name,
        particles=particles,
        infinitive=infinitive,
        present=stem,
        present_2sg=stem,
        preterite=stem,
        subjunctive=stem,
        participles=tuple(p for p in (participle, extra) if p),
        # Any value of ``haben`` means sein in these templates: haben=0, haben=sein, haben=nein.
        auxiliary="sein" if _clean(params.get("haben")) else "haben",
        weak=True,
        word_group=_clean(params.get("Infinitiv")) in {"zweiteilig", "dreiteilig"},
        reflexive=template.name != REGULAR,
        impersonal=impersonal,
        no_imperative=no_imperative,
        no_present=no_present,
        no_preterite=no_preterite,
        overrides=_overrides(params, OVERRIDES),
    )


def _inserts_e(stem: str) -> bool:
    """Whether -st and -t are attached with an e: red-est, atm-et, rechn-et."""
    if stem.endswith(("d", "t")):
        return True
    if stem.endswith("m"):
        return stem[:-1].endswith(BEFORE_M)
    if stem.endswith("n"):
        return stem[:-1].endswith(BEFORE_N)
    return False


def _weak_forms(verb: Verb) -> dict[str, list[str]]:
    stem = verb.present
    liquid = verb.infinitive.endswith(("eln", "ern"))
    if liquid:
        short = stem[:-2] + stem[-1] + "e"  # sammle, wandre
        first = [short, stem + "e"] if stem.endswith("el") else [stem + "e", short]
        first = imperative = [*first, stem]
    elif stem.endswith("e"):  # knien: knie, knie-st
        first, imperative = [stem], [stem]
    elif _inserts_e(stem) and not stem.endswith(("d", "t")):
        first, imperative = [stem + "e"], [stem + "e"]
    else:
        first, imperative = [stem + "e"], [stem + "e", stem]
    e = "e" if _inserts_e(stem) else ""
    second = stem + "t" if stem.endswith(SIBILANTS) else stem + e + "st"
    past = stem + e + "te"
    return {
        PRESENT_1SG: first,
        PRESENT_2SG: [second],
        PRESENT_3SG: [stem + e + "t"],
        PRETERITE: [past],
        SUBJUNCTIVE: [past],
        IMPERATIVE_SG: imperative,
        IMPERATIVE_PL: [stem + e + "t"],
    }


def _strong_forms(verb: Verb) -> dict[str, list[str]]:
    """The rules of ``Vorlage:Deutsch Verb unregelmäßig``, form by form."""
    stem, changed = verb.present, verb.present_2sg
    ending, vowel, special = verb.ending, verb.vowel, verb.special
    tail = changed[-3:] if changed != stem else ""
    is_tun = bool(special) and stem + "n" == special

    if special and not is_tun:
        first = [changed]
    else:
        first = [stem + "e"]

    if tail in {"ält", "läd", "rät", "wir"}:
        second = changed + "st"
    elif ending == "-s":
        second = changed + "t"
    elif ending == "e2":
        second = changed
    elif ending in {"e", "e-"} and vowel != "i":
        second = changed + "est"
    else:
        second = changed + "st"

    if special:
        third = stem + "t" if is_tun else changed
    elif vowel == "i":
        third = changed if ending in {"e", "e-", "e2"} else changed + "t"
    elif tail in {"ält", "rät"}:
        third = changed
    elif tail == "wir":
        third = changed + "d"
    elif tail == "läd":
        third = changed + "t"
    else:
        third = changed + ("et" if ending in {"e", "e-"} else "t")

    plural = stem + ("et" if ending in {"e", "e-", "e2"} else "t")
    if special:
        if is_tun:
            imperative_sg, imperative_pl = [stem, stem + "e"], [stem + "t"]
        elif special == "wissen":
            imperative_sg, imperative_pl = ["wisse"], ["wisset"]
        else:
            imperative_sg, imperative_pl = [], []
    elif changed == "wir":
        imperative_sg, imperative_pl = ["werde"], [plural]
    elif "i" in vowel:
        imperative_sg, imperative_pl = [changed], [plural]
    else:
        imperative_sg, imperative_pl = [stem, stem + "e"], [plural]

    subjunctive = [verb.subjunctive + "e"]
    if verb.subjunctive_alt:
        subjunctive.append(verb.subjunctive_alt + "e")
    preterite = [verb.preterite]
    if verb.preterite_alt:
        preterite.append(verb.preterite_alt)
    return {
        PRESENT_1SG: first,
        PRESENT_2SG: [second],
        PRESENT_3SG: [third],
        PRETERITE: preterite,
        SUBJUNCTIVE: subjunctive,
        IMPERATIVE_SG: imperative_sg,
        IMPERATIVE_PL: imperative_pl,
    }


def principal_forms(verb: Verb) -> dict[str, list[str]]:
    """The forms of ``Deutsch Verb Übersicht`` as the conjugation gives them.

    Each form is a list, because many have variants (``lauf``, ``laufe``); an empty list
    means that the form does not exist. Finite forms of separable verbs are written with
    the particle after the verb, as in the overview tables: ``kaufe ab``.
    """
    forms = _weak_forms(verb) if verb.weak else _strong_forms(verb)
    distant = ""
    if verb.particles:
        distant = " " + " ".join((verb.distant_particle or verb.particles[0], *verb.particles[1:]))
    # Overrides are whole forms in the templates for weak verbs and bare verbs in the other.
    given = {
        key: [v if verb.weak or v.endswith(distant) else v + distant for v in values]
        for key, values in (*verb.overrides.items(), *verb.alternatives.items())
    }
    forms = {key: [value + distant for value in values] for key, values in forms.items()}
    for key in verb.overrides:
        forms[key] = given[key]
    for key in verb.alternatives:
        forms[key] = [*forms[key], *(v for v in given[key] if v not in forms[key])]
    absent = []
    if verb.no_imperative:
        absent += [IMPERATIVE_SG, IMPERATIVE_PL]
    if verb.impersonal:
        absent += [PRESENT_1SG, PRESENT_2SG]
    if verb.no_present:
        absent += [PRESENT_1SG, PRESENT_2SG, PRESENT_3SG]
    if verb.no_preterite:
        absent += [PRETERITE, SUBJUNCTIVE]
    for key in absent:
        if key not in verb.overrides:
            forms[key] = []
    forms[PARTICIPLE] = list(verb.participles)
    return forms


def _participle_stem(verb: Verb, index: int = 0) -> str:
    """The stem inside the Partizip II of a strong or mixed verb: ge-lauf-en, ge-brach-t."""
    if verb.weak:
        return verb.present
    participle = verb.participles[index].replace(" ", "")
    joined = "".join(verb.particles)
    if joined and participle.startswith(joined):
        participle = participle[len(joined) :]
    # ge- is a prefix unless the verb's own stem begins with it: ge-fall-en is gefallen's
    # participle, but ge-gang-en and ge-geb-en have the prefix before a stem in g.
    if participle.startswith("ge") and not verb.present.startswith("ge"):
        participle = participle[2:]
    elif participle.startswith("geg"):
        participle = participle[2:]
    for suffix in ("en", "n", "t"):
        if participle.endswith(suffix):
            return participle[: -len(suffix)]
    return participle


_UMLAUT = {"a": "ä", "o": "ö", "u": "ü"}


def _follows_from_preterite(subjunctive: str, preterite: str) -> bool:
    """Whether a subjunctive II stem is the preterite stem, with umlaut if it can take one:
    ``gäb`` from ``gab``, ``lief`` from ``lief``, ``schri`` from ``schrie``."""
    if preterite.endswith("ie") and subjunctive == preterite[:-1]:
        return True
    if subjunctive == preterite:
        return True
    if len(subjunctive) != len(preterite):
        return False
    differing = [(p, s) for p, s in zip(preterite, subjunctive, strict=True) if p != s]
    return len(differing) == 1 and _UMLAUT.get(differing[0][0]) == differing[0][1]


def conjugation_class(verb: Verb) -> str:
    """``weak``, ``strong``, ``mixed`` (strong stem, weak suffix: ``dach-te``) or ``irregular``
    (the modal verbs, ``wissen``, ``tun``, ``sein``)."""
    if verb.weak:
        return "weak"
    if verb.special or verb.infinitive == "sein":
        return "irregular"
    return "mixed" if verb.mixed else "strong"


STEM_FIELDS = ("present", "present_2sg", "preterite", "participle")
SEIN_STEMS = dict(zip(STEM_FIELDS, ("s", "b", "w", "wes"), strict=True))


def _preterite_stem(verb: Verb, preterite: str) -> str:
    """Without the weak suffix of mixed verbs: ``dach`` from ``dachte``, ``send`` from
    ``sendete``."""
    if verb.mixed and preterite.endswith("te"):
        return preterite[:-2].removesuffix("e")
    return preterite


def stems(verb: Verb, simplex: Collection[str] = ()) -> dict[str, str]:
    """The four stem allomorphs of a verb, without particles and without an inseparable
    prefix (``geh``, ``ging``, ``gang`` for ``ver:geh``; see :func:`split_prefix` for
    ``simplex``).

    ``preterite`` lacks the weak suffix of mixed verbs (``dach`` from ``dachte``).
    ``participle`` is what remains of the Partizip II without ``ge-`` and its suffix; it is
    derived by us, not given by the template. ``sein`` is suppletive and the template gives
    placeholders; it gets ``s`` (``sind``, ``seid``, ``sei``, ``ist``), ``b`` (``bin``,
    ``bist``), ``w`` and ``wes``. Further stems are in :func:`stem_variants`.
    """
    if verb.infinitive == "sein":
        return dict(SEIN_STEMS)
    prefix = split_prefix(verb, simplex)[0]
    result = {
        "present": verb.present,
        "present_2sg": verb.present_2sg,
        "preterite": _preterite_stem(verb, verb.preterite),
        "participle": _participle_stem(verb),
    }
    return {key: stem.removeprefix(prefix) for key, stem in result.items()}


def stem_variants(verb: Verb, simplex: Collection[str] = ()) -> list[tuple[str, str]]:
    """Stems besides the four of :func:`stems`, as ``(field, stem)``.

    - ``subjunctive``: subjunctive II stems that do not follow from a preterite stem:
      ``würf`` (``warf``), ``stünd`` (``stand``, besides the regular ``ständ``), ``renn``
      (``rann``, for ``rennte``); not ``hüb``, which follows from the second preterite
      ``hub``. Whether such a stem is the only one or a variant is not recorded.
    - ``preterite``: a second preterite stem (``hub`` besides ``hob``).
    - ``participle``: the stem of a second Partizip II if it differs (not ``gesalzt`` besides
      ``gesalzen``, which share ``salz``).
    - ``present_2sg``: the present stem, if the forms of the second and third person singular
      are also given without the vowel change (``gebärst`` besides ``gebierst``). Other forms
      given one by one (``beutst``) are not stems.
    """
    if verb.weak or verb.infinitive == "sein":
        return []
    prefix = split_prefix(verb, simplex)[0]
    main = stems(verb, simplex)
    found: list[tuple[str, str]] = []

    preterites = [
        _preterite_stem(verb, p) if verb.mixed else p.removesuffix("e")  # wurde
        for p in (verb.preterite, verb.preterite_alt)
        if p
    ]
    for subjunctive in (verb.subjunctive, verb.subjunctive_alt):
        if verb.mixed:  # sendet-e, dächt-e
            subjunctive = next(
                (subjunctive[: -len(x)] for x in ("et", "t") if subjunctive.endswith(x)),
                subjunctive,
            )
        if subjunctive and not any(_follows_from_preterite(subjunctive, p) for p in preterites):
            found.append(("subjunctive", subjunctive))
    if verb.preterite_alt:
        found.append(("preterite", _preterite_stem(verb, verb.preterite_alt)))
    found += [("participle", _participle_stem(verb, i)) for i in range(1, len(verb.participles))]
    if verb.present_2sg != verb.present:
        plain = {verb.present + "st", verb.present + "est", verb.present + "t"}
        for form in verb.overrides.get(PRESENT_2SG, ())[1:]:
            if form in plain:
                found.append(("present_2sg", verb.present))

    result = []
    for name, stem in found:
        stem = stem.removeprefix(prefix)
        if (name, stem) not in result and main.get(name) != stem:
            result.append((name, stem))
    return result


# Prefixes of native verbs. The last six are particles in other verbs (um=stell, um:stell);
# there the template tells the two apart, because it gives particles as arguments.
PREFIXES = (
    "be", "emp", "ent", "er", "ge", "miss", "ver", "zer",
    "durch", "hinter", "über", "um", "unter", "wider",
)  # fmt: skip
_VOWEL = re.compile(r"[aeiouäöüy]")


def split_prefix(verb: Verb, simplex: Collection[str] = ()) -> tuple[str, str]:
    """Split the present stem into an inseparable prefix and the rest: ``("ver", "bleib")``.

    A stem has a prefix if it begins with one of :data:`PREFIXES`, the rest contains a vowel
    and the Partizip II has no ``ge-`` (``verblieben``; but ``gebettelt``, ``geerbt``). Weak
    verbs in ``-ieren`` never have ``ge-``, so they are split only if the rest is in
    ``simplex``, the present stems of verbs without prefix and particle
    (``ver:barrikadier``, but ``verifizier``). The same holds for ``ge``, which is often
    part of the base instead (``ge:hör``, but ``gesund``, ``gestalt``, ``gewitter``). Only one
    prefix is split off.
    """
    stem = verb.present
    participle = verb.participles[0].replace(" ", "") if verb.participles else ""
    joined = "".join(verb.particles)
    if joined and participle.startswith(joined):
        participle = participle[len(joined) :]
    if not participle.startswith(stem[:2]) or participle.startswith("ge" + stem[:2]):
        return "", stem
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        rest = stem[len(prefix) :]
        if not stem.startswith(prefix) or not _VOWEL.search(rest):
            continue
        if verb.weak and stem.endswith("ier") and rest not in simplex:
            continue
        if prefix == "ge" and rest not in simplex:
            continue
        return prefix, rest
    return "", stem


def is_copula_group(verb: Verb) -> bool:
    """``ab sein``, ``dabei sein``: ``sein`` with a predicative element, written as several
    words. Wiktionary conjugates these as verbs; they are not lexemes."""
    return verb.word_group and verb.infinitive == "sein"


def lexeme_stem(verb: Verb, simplex: Collection[str] = ()) -> str:
    """The stem under which the lexeme is stored: particles marked with ``=`` (``ab=kauf``),
    an inseparable prefix with ``:`` (``ver:bleib``, ``an=er:kenn``); see
    :func:`split_prefix` for ``simplex``.

    Verbs written as several words keep their spaces: ``Rad fahr``.
    """
    if verb.infinitive == "sein":
        return (" " if verb.word_group else "=").join((*verb.particles, "s"))
    prefix, rest = split_prefix(verb, simplex)
    stem = f"{prefix}:{rest}" if prefix else rest
    return (" " if verb.word_group else "=").join((*verb.particles, stem))


_ABSENT = {"", "—", "–", "-"}


def overview_forms(template: Template) -> dict[str, list[str]]:
    """The principal forms in a ``Deutsch Verb Übersicht`` call, variants included.

    Variants are the starred keys (``Imperativ Singular*``). The main form comes first.
    ``Hilfsverb`` is returned as well.
    """
    forms: dict[str, list[str]] = {key: [] for key in (*PRINCIPAL_FORMS, "Hilfsverb")}
    for key, value in template.args:
        if key is None:
            continue
        base = re.sub(r"[*\s\d]+$", "", key)
        if base not in forms:
            continue
        for part in _BREAK.split(_REF.sub("", html.unescape(value))):
            part = _TAG.sub("", part).strip().rstrip("!").strip()
            if part not in _ABSENT and part not in forms[base]:
                forms[base].append(part)
    return forms
