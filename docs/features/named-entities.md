# Named entities

Every lexical unit has a field `named_entity`. It records whether Wiktionary marks the word, in this sense, as a name, and if so, the noun its definition uses to say what is named ([0003](../decisions/0003-named-entities.md)).

## Values

| Value | Meaning | Examples |
|---|---|---|
| `default` | Wiktionary does not mark the entry as a name: not a name as far as we know | Haus, Estnisch, TÜV |
| a noun lemma | marked as a name; the head noun of the sense's definition | Gützkow `Stadt`, Eisenhauer `Nachname`, Danzig [2] `Asteroid` |
| `unspecified` | marked as a name, but the definition has no head noun | |

The two fixed values cannot clash with heads, which are capitalised German nouns. Heads are not checked against a list of types: any noun can be a head.

## Marking

A sense is marked as a name if any of the following holds:

- **Name label.** Its section has a name label in the heading: `Toponym`, `Nachname`, `Vorname`, `Eigenname`, `Göttername`, `Bauwerksname` or `Straßenname`. Usually it stands next to `Substantiv` (`{{Wortart|Substantiv|Deutsch}}, {{m}}, {{Wortart|Toponym|Deutsch}}`).
- **Name table.** Its section has a name table: `Deutsch Toponym Übersicht`, `Deutsch Nachname Übersicht`, `Deutsch Vorname Übersicht m/f/n`, `Deutsch Eigenname Übersicht` or `Deutsch Name Übersicht`.
- **`{{K}}` label.** The sense itself carries a name label in `{{K|…}}` (one of the labels above, or `Familienname`).

Nothing else marks a sense. There are no patterns on the definition, and no inference from hypernyms, categories or capitalisation. A name that Wiktionary does not mark is `default`.

The name labels are not parts of speech ([part of speech](part-of-speech.md#names)).

## The head

The head is read from the sense's line in `Bedeutungen`:

1. **What comes first is skipped:** the sense number, `{{K|…}}` labels, text labels ending in a colon (`Geografie:`, `historisch:`, `kurz für:`), and asides in parentheses.
2. **The head is the first common noun.** That means the first word that Wiktionary lists as a common noun (the title of a `Substantiv` section without a name label), or an inflected form of one. Words before it are passed over:
   - articles;
   - adjectives and participles (`deutschsprachiger Nachname`, `US-amerikanischer Bundesstaat`);
   - names (`Kenia` in `in Kenia gesprochene Sprache`).
3. **Some heads give way to the next noun,** because they only say that the entry is a name or a form of one. These are `Name`, `Bezeichnung`, `Form`, `Kurzform`, `Kurzbezeichnung`, `Nebenform`, `Schreibweise`, `Variante`, `Spitzname`, `Beiname` and `Toponym`:
   - `Name verschiedener Orte` → `Ort`;
   - `weibliche Form des Familiennamens Kostow` → `Familienname`;
   - `Toponym mehrerer Ortschaften` → `Ortschaft`.

   Other heads stay, even when they say little: `Teil` (`östlicher Teil Frankreichs`), `Gruppe`.
4. **The head is stored as its lemma.** Inflected forms are looked up in the word-form table (`eines der acht Tore` → `Tor`). Compounds are kept whole (`Hafenstadt`, `Nebenfluss`, `Bantusprache`).
5. **No head** gives `unspecified`.

## Limits

- **A noun in a phrase before the head is taken instead of it:**
  - `im Landkreis Konstanz am Bodensee … gelegene Gemeinde` gives `Landkreis`;
  - Karthago, `im Nordosten Tunesiens gelegene antike, phönizische Küstenstadt`, gives `Nordosten`.

  This is the main source of errors. It is to be reduced with the definition parsing in M3.
- **Common senses in sections labelled as names get a head too.** In the Jungfrau section labelled `Eigenname`, most senses are common nouns. Sense 1, `eine weibliche Person, die noch nie Geschlechtsverkehr hatte`, gets `Person`. Such senses are not filtered in release 1.
- **The marking is Wiktionary's.** These are `default`:
  - most language names (Estnisch);
  - some place names (Rheingau, Trasimenischer See);
  - abbreviated names labelled `Abkürzung` (TÜV, ADAC).

## Not in this field

- **Types.** Grouping heads into types (`Stadt`, `Großstadt` and `Ortsteil` as settlements; `Fluss` and `Nebenfluss` as rivers) is left to the analyses. They can use the head's own segmentation (`Neben.fluss`, M2) and the hypernyms (`Oberbegriffe`), which are extracted as semantic relations in M3.
- **Adjectives derived from names** (Berliner, kafkaesk, karthagisch) carry no name marking. Their link to a name comes from word formation in M2. The base of `karthagisch` is the lexeme Karthago, so an analysis can follow that link to the `named_entity` of Karthago's lexical units.

Measurements on the dump of 2026-11-01 are in [the feasibility results](../feasibility.md#named-entities).
