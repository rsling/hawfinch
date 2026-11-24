# Part of speech

Lexemes carry the part-of-speech labels of German Wiktionary (`{{Wortart|<label>|Deutsch}}`), in German, with the exceptions below.

- Wiktionary's form-entry labels (`Deklinierte Form`, `Konjugierte Form`, `Partizip I`, `Partizip II`, `Erweiterter Infinitiv`, `Dekliniertes Gerundivum`, `Komparativ`, `Superlativ`) are not parts of speech of lexemes. What happens to these entries is set by [0004](../decisions/0004-participles-and-zu-forms.md).
- `Abkürzung` is not a part of speech either ([below](#abbreviations)).

## Proper nouns

Proper nouns are a part of speech of their own ([0003](../decisions/0003-proper-nouns.md)).

**Definition.** A noun in a given sense is a common noun if it has a conceptual plural or can be used as a mass noun. Otherwise it is a proper noun: it names a particular individual rather than a kind.

- **Proper nouns:**
  - particular persons and families;
  - places (cities, countries, regions, rivers, mountains, streets, squares) and buildings;
  - deities and mythological individuals;
  - organisations, companies, institutions and parties;
  - celestial bodies as individuals, and constellations;
  - historical events, holidays, named periods, and particular works;
  - language names;
  - descriptive designations of a single referent (Rheineinzugsgebiet, Covid-19-Pandemie).

  Family names and given names are proper nouns, even though many people bear them.
- **Common nouns:**
  - nouns for people by role or origin (Berliner, Papst);
  - months, weekdays and letters;
  - species, both in ordinary usage and as scientific names of species and of plant varieties and cultivars;
  - brand names used as count nouns for products sold under the brand (ein Ferrari);
  - names used for a kind of object (ein Picasso: a painting by Picasso).
- **The list wins over the test.** Holidays and recurring events can be counted by occurrence (drei Weihnachten), and language names have mass-like uses (sein Deutsch ist gut). For now this does not make them common nouns. Categories of their own would describe them best but are not part of release 1.
- **Mixed sections.** A Wiktionary section whose senses fall on both sides is split into a proper and a common lexeme (Ferrari: the manufacturer and the car).

**Detection, label rule.** This mode is used when no language model is configured. It is implemented in `hawfinch.features.partofspeech`.

- A section is a proper noun if one of its labels is a name label: `Toponym`, `Nachname`, `Vorname`, `Eigenname`, `Göttername`, `Bauwerksname` or `Straßenname`.
- A `Substantiv` section is also a proper noun if its first meaning line defines it as a language. The line must be headed by `Sprache`, `-sprache` or `Varietät`; before the head noun there may be at most an article, a subject label (`Sprachwissenschaft:`) and five lower-case words (`die Sprache der Esten`, `austronesische Sprache, die …`, `die Amtssprache Bhutans`). A register label (`Seemannssprache:`, `(Jägersprache)`) does not count. Neither does a title ending in `-sprache` (Fachsprache).
- Any other `Substantiv` section is a common noun.

Measured on the feasibility sample with the classes above ([results](../feasibility.md#proper-nouns)), its precision is about 99 % and its recall about 90 %. Its limits:

- Some names have no name label: Rheingau, Trasimenischer See, Xetra, descriptive designations, and language names defined without the word `Sprache` (Inupiaq: `in Alaska gesprochene Varietät …`). Abbreviated organisation names are a systematic case: TÜV, ADAC, ISO and AfD are labelled `Abkürzung` + `Substantiv`.
- It cannot find mixed sections, so these stay unsplit.

**Detection, language model.** When a model is configured ([0006](../decisions/0006-language-model.md)), every sense of a noun section is classified as proper or common by the definition above. Sections whose senses fall on both sides are split.

## Abbreviations

Wiktionary's `Abkürzung` label is replaced by the part of speech a word is used as, and the lexeme field `coding` records its form ([0005](../decisions/0005-abbreviations.md)):

| `coding` | Meaning | Examples |
|---|---|---|
| `short` | short word spoken as such | `KKW`, `CVJM` (proper noun), `Uni`, `Kita`, `Sponti` |
| `abbreviation` | written abbreviation read as the full word | `BT` (proper noun, read "Bundestag") |
| `regular` | all other lexemes | |

- **Sections labelled `Abkürzung`:** an IPA transcription in Wiktionary makes them `short`, and its absence makes them `abbreviation`. This is decided for abbreviated names in capitals (`BT`, `CVJM`); which other spellings it covers is [open](../open-questions.md#coding-of-short-words). The test is never applied to lexemes without the label: an ordinary noun without a transcription is `regular`.
- **Clippings and syllable words** (`Uni`, `Kita`, `Akku`, `Azubi`, `Sponti`, `Fundi`): Wiktionary labels them plain `Substantiv`. They are `short`, recognised from the Herkunft in M2.
- **Orthographic abbreviations** (`Einw.`, `kastil.`, `v. v.`) are not lexemes. In release 1 they go into a stub table with their spelling and raw meaning lines.
