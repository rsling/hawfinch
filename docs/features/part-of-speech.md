# Part of speech

Lexemes carry the part-of-speech labels of German Wiktionary (`{{Wortart|<label>|Deutsch}}`), in German, with the exceptions below.

- Wiktionary's form-entry labels (`Deklinierte Form`, `Konjugierte Form`, `Partizip I`, `Partizip II`, `Erweiterter Infinitiv`, `Dekliniertes Gerundivum`, `Komparativ`, `Superlativ`) are not parts of speech of lexemes. What happens to these entries is set by [0004](../decisions/0004-participles-and-zu-forms.md).
- `Abkürzung` is not a part of speech either ([below](#abbreviations)).
- The name labels are not parts of speech ([below](#names)).

## Names

There is no proper-noun part of speech ([0003](../decisions/0003-named-entities.md)). German Wiktionary marks names with a second label in the heading, usually next to `Substantiv`: `Toponym`, `Nachname`, `Vorname`, `Eigenname`, `Göttername`, `Bauwerksname` and `Straßenname`. These labels say that the word is a name, not what part of speech it is.

- The part of speech is the other label: Rhein (`Substantiv` + `Toponym`) is a `Substantiv`.
- **A section whose only labels are name labels is a `Substantiv`.** There are 88 such sections in the dump of 2026-11-01, among them Englisch, Greenpeace, DDR and Miraculix. This includes sections with `Abkürzung` beside the name label, since `Abkürzung` is not a part of speech either.
- **What the name labels mark** goes into the `named_entity` field of the lexical unit ([named entities](named-entities.md)). They never split a section.

## Abbreviations

Wiktionary's `Abkürzung` label is replaced by the part of speech a word is used as, and the lexeme field `coding` records its form ([0005](../decisions/0005-abbreviations.md)):

| `coding` | Meaning | Examples |
|---|---|---|
| `short` | short word spoken as such | `KKW`, `CVJM`, `Uni`, `Kita`, `Sponti` |
| `abbreviation` | written abbreviation read as the full word | `BT` (read "Bundestag") |
| `regular` | all other lexemes | |

- **Sections labelled `Abkürzung`:** an IPA transcription in Wiktionary makes them `short`, and its absence makes them `abbreviation`. This is decided for abbreviated names in capitals (`BT`, `CVJM`); which other spellings it covers is [open](../open-questions.md#coding-of-short-words). The test is never applied to lexemes without the label: an ordinary noun without a transcription is `regular`.
- **Clippings and syllable words** (`Uni`, `Kita`, `Akku`, `Azubi`, `Sponti`, `Fundi`): Wiktionary labels them plain `Substantiv`. They are `short`, recognised from the Herkunft in M2.
- **Orthographic abbreviations** (`Einw.`, `kastil.`, `v. v.`) are not lexemes. In release 1 they go into a stub table with their spelling and raw meaning lines.
