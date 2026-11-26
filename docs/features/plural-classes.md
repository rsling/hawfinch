# Plural classes

Every noun lexeme with a plural has three fields that describe it: `plural_class`, `plural_stem` and `plural_segmented`. They are derived by comparing the nominative singular with the nominative plural in Wiktionary's noun table; the class also needs the gender and, for masculine nouns, the genitive singular.

The classification is the user's (2026-11-26). It presupposes that the gender of every noun is known and that simplex and complex stems are told apart elsewhere in the database; neither is part of the class.

## Classes

| Class | Masculine | Neuter | Feminine |
|---|---|---|---|
| `primary` | `-e` (Stühl-e, Tag-e, Lehrer-) | `-e` (Jahr-e, Fenster-) | `-en` (Frau-en, Tante-n) |
| `secondary` | `-en`, strong genitive (Staat-en) | `-en` (Ohr-en) | `-e` (Ängst-e, Mütter-) |
| `marked-n` | `-en`, weak genitive (Mensch-en) | | |
| `marked-r` | `-er` (Männ-er) | `-er` (Lämm-er) | |
| `default` | `-s` (Opa-s) | `-s` (Auto-s) | `-s` (Oma-s) |

| Class | Nouns |
|---|---|
| `loan` | loan plurals of any gender, with or without truncation (Finit-a, Muse-en, Kibbuz-im), and plurals without a suffix where the elision is not phonotactic (Kasus-, Hindu-, Volt-), if the noun has no other plural |
| `irregular` | Herz and its compounds (des Herzens, die Herz-en), and substitutive plurals (Kaufmann, Kaufleut-e) |
| `adjectival` | nouns declined like adjectives (Beamter, Angestellte) |

- **`primary`** is the plural that is normal for the gender: `-e` for masculine and neuter nouns, `-en` for feminine nouns.
- **`secondary`** is the opposite suffix.
- **`marked-n`** holds the weak masculine nouns, with `-en` in the plural and in the genitive singular.
- **`marked-r`** holds all `-er` plurals.
- **`default`** holds all `-s` plurals.
- **`loan`, `irregular` and `adjectival`** do not fix a suffix. Where it is needed, it is read from the segmented plural.

Suffix types, not literal suffixes, define the classes:

- **A plural without a suffix is an `-e` plural** if the singular ends in a reduced syllable (Lehrer, Fenster, Mädchen, Mütter): the elision is phonotactic. After a full syllable it is a `loan` plural.
- **`-en` and `-n` are one suffix** (Frau-en, Tante-n, Kartoffel-n).

## Plural stem

`plural_stem` is the stem as it appears in the plural: `Stühl` for Stühle, `Tag` for Tage, `Baut` for Bauten, `Finit` for Finita. Whether a noun has an alloform with umlaut in the plural follows from comparing it with the singular. This is needed for masculine nouns with `-e` plural, where the umlaut cannot be predicted (Tag-e, but Stühl-e); feminine simplex stems always take it in an `-e` plural.

The stem is literal, with a doubled consonant where the spelling has one (`Buss`, `Lehrerinn`, `Kenntniss`).

## Segmented plural

`plural_segmented` is the literal nominative plural with the inflectional boundary `-` between stem and suffix ([segmentation](segmentation.md)). It is stored for convenience.

- **The boundary is always there**, also where there is no suffix: `Stühl-e`, `Tante-n`, `Auto-s`, `Box-es`, `Lehrer-`, `Mütter-`, `Kasus-`. The last `-` of the form is therefore always the boundary, also in words with a hyphen (`UN-Vertreter-`).
- **Loan plurals** have the boundary before the plural ending, and never inside the part the plural shares with the singular: `Finit-a`, `Muse-en`, `Mysteri-en`, `Fossil-ien`, `Tempor-a`, `Atlant-en`, `Thema-ta`, `Kakte-en`. A loan plural without a recognisable ending has it at the end (`Gentlemen-`).
- **Nouns written as several words** have it in the word that inflects: `Leutnant-e zur See`, `Quaestion-es Juris`, `graue Star-e`.

## Special cases

- **Nouns without a singular** have the gender `nd`, and their class follows from the ending alone:
  - `-e` and `-en` are `primary`, by a convention that is arbitrary: an `-e` plural is taken as that of a masculine or neuter stem (`Leut-e`), an `-en` plural as that of a feminine stem (`Ferie-n`, `Kost-en`).
  - A reduced syllable without a suffix is `primary` as well, an `-e` that is blocked phonotactically (`Geschwister-`, `Trümmer-`, `Mittel-`).
  - `-s` is `default` (`Hot Pant-s`, `Short-s`).
  - Everything else is a `loan` plural (`Mammali-a`, `Spaghett-i`, `Planta-e`).
- **A plural without a suffix after a full syllable is dropped if the noun has another plural.** Wiktionary lists `Keks` beside `Kekse` and `KZ` beside `KZs`; only `Keks-e` and `KZ-s` become lexemes. A plural without a suffix after a reduced syllable is an ordinary `-e` plural and stays (`Onkel-` beside `Onkel-s`).
- **Abbreviations in capitals whose only plural has no suffix** have no class (`VWL`, `POS`, `USA`). The field is empty; there is no class for them.
- **Plurals in `-leute`** of nouns in `-mann` and `-frau` are substitutive plurals and always `irregular` (`Kaufleut-e`). They stay with the noun in whose table they stand.
- **Names** whose genitive singular and nominative plural both end in `-s` are `default` (`Müller-s`, `Arthur-s`). Other plurals of names have no class.
- **Different plurals are different lexemes.** A noun table with several plurals gives one lexeme per plural (Wort: Wört-er, Wort-e), each with its own class, and in most cases they are linked to different senses. The same holds for several genders. A table with several genders and several plurals does not say which plural goes with which gender, so every combination becomes a lexeme, and some of them are not words of German (`Bruch`: masculine `Brüche`, neuter `Brücher`, but not the reverse). This is accepted for release 1. Which senses belong to which lexeme is not in Wiktionary's markup; it is left open and is to be found from usage data later.
- **A genitive in `-ns` belongs to a singular in `-n`**: `des Friedens` to `Frieden`, not to `Friede`. Traditionally these are two lexemes. Where a table gives such a genitive as its main form, the plural is compared with the singular in `-n`, which makes it `primary` (`Frieden-`).
- **A weak genitive as a variant is enough** for `marked-n`: `des Elbs`, `des Elben`, `die Elb-en`. The genitive that does not fit the class is stored in a table of variant forms, like the variant stems of verbs. The same table holds weak genitives of nouns that are not `marked-n` (`des Magneten`, `die Magnet-e`).
- **Native suffixes on a stem the singular does not have** are classified by their suffix, and the stem field holds the alloform: `Baut-en` (`secondary`), `Jung-s` (`default`), `Kinderchen-` (`primary`).
- **Nouns written as several words** take the class of the word that inflects: the last one as a rule, otherwise the first one that changes (`Leutnant-e zur See` is `primary`, `Quaestion-es Juris` is `loan`). A noun with an attributive adjective is a lexeme and takes the class of its head noun (`graue Star-e`).
- **Genitive in `-s` and `-es`.** Where Wiktionary gives both (`des Stuhls`, `des Stuhles`), only the form in `-es` is stored. The variation is not recorded.

## Derivation

1. Read the genders, the nominative and genitive singular and all nominative plurals from `Deutsch Substantiv Übersicht`: parallel genders (`Genus 1`, `Nominativ Singular 1`), parallel plurals (`Nominativ Plural 2`) and starred variants (`Nominativ Plural*`).
2. Try the native suffixes on the plural, the longest first: `-en`, `-er`, `-es`, `-e`, `-n`, `-s`, none. A suffix fits if the rest is the singular, the singular with its last `a`, `o`, `u` or `au` umlauted (also `Säl-e` from `Saal`), or either of these with the final consonant doubled.
3. The suffix type and the gender give the class. A masculine noun with `-en` is `marked-n` if one of its genitives is the nominative plus `-n` or `-en`.
4. If no native suffix fits, the plural is a `loan` plural, apart from the special cases above.
5. `Deutsch adjektivisch Übersicht` with the argument `Stamm` gives an `adjectival` noun; its plural is the strong form (`Beigeordnet-e`). With full forms it gives a noun with an attributive adjective.
6. The tables for names give a plural as an argument, if there is one. `Deutsch Nachname Übersicht` gives no forms: the template builds genitive and plural in `-s`, except after `s`, `ß`, `x` and `z`.
7. Where the table gives no gender, the gender in the heading of the section is used. Without a gender there is no class.
8. Of the plurals of one singular, the one without a suffix after a full syllable is dropped if there is another.
9. Sections whose senses are all marked as archaic, regional, Austrian or Swiss are left out before any of this ([usage labels](usage-labels.md)).
