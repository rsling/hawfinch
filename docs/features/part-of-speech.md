# Part of speech

Lexemes carry the part-of-speech labels of German Wiktionary (`{{Wortart|<label>|Deutsch}}`), in German, with the exceptions below.

- Wiktionary's form-entry labels (`Deklinierte Form`, `Konjugierte Form`, `Partizip I`, `Partizip II`, `Erweiterter Infinitiv`, `Dekliniertes Gerundivum`, `Komparativ`, `Superlativ`) are not parts of speech of lexemes. What happens to these entries is set by [0004](../decisions/0004-participles-and-zu-forms.md).
- `Abkürzung` is not a part of speech either ([below](#abbreviations)).
- The name labels are not parts of speech ([below](#names)).
- A section that only points to another spelling is not a lexeme, whatever its label ([below](#spelling-variants)).

## Names

There is no proper-noun part of speech ([0003](../decisions/0003-named-entities.md)). German Wiktionary marks names with a second label in the heading, usually next to `Substantiv`: `Toponym`, `Nachname`, `Vorname`, `Eigenname`, `Göttername`, `Bauwerksname` and `Straßenname`. These labels say that the word is a name, not what part of speech it is.

- The part of speech is the other label: Rhein (`Substantiv` + `Toponym`) is a `Substantiv`.
- **A section whose only labels are name labels is a `Substantiv`.** There are 88 such sections in the dump of 2026-11-01, among them Englisch, Greenpeace, DDR and Miraculix. This includes sections with `Abkürzung` beside the name label, since `Abkürzung` is not a part of speech either.
- **What the name labels mark** goes into the `named_entity` field of the lexical unit ([named entities](named-entities.md)). They never split a section.

## Spelling variants

**A section that only points to the entry of another spelling is not a lexeme.** It has no sense lines and holds `{{Schweizer und Liechtensteiner Schreibweise|…}}` or `{{Alte Schreibweise|…}}`. The lexeme is the entry it points to: `verrussen` is the Swiss spelling of `verrußen`, `Flußbett` the old spelling of `Flussbett`.

The rule is the user's (2026-11-26).

- **Most such entries have no part-of-speech section at all** (about 20,300 in the dump of 2026-11-01, see the [inventory](../feasibility.md#entries-and-parts-of-speech)), and are not lexemes anyway. A few wrap the template in a `Wortart` heading: 20 sections with the part of speech of a lexeme (the verbs `russen` and `verrussen`, the nouns `Riss`, `Riß`, `Nußbaum`), and 41 form entries.
- **The rule holds for every part of speech.** Like the rule for archaic and regional entries, it is applied in one place, `hawfinch.features.selection`.
- **A section of another spelling that has senses of its own stays** (`Goldwage`, `schwarzweiß`).
- **Spelling variants listed in an entry** (`Alternative Schreibweisen`, `zutage fördern` beside `zu Tage fördern`) are a different matter and still open ([open questions](../open-questions.md#verb-stems)).

## Abbreviations

Wiktionary's `Abkürzung` label is replaced by the part of speech a word is used as, and the lexeme field `coding` records its form ([0005](../decisions/0005-abbreviations.md)):

| `coding` | Meaning | Examples |
|---|---|---|
| `short` | short word spoken as such | `KKW`, `CVJM`, `Lkw`, `Uni`, `Kita`, `Sponti` |
| `regular` | all other lexemes | |

- **Sections labelled `Abkürzung`** are lexemes only if they are spelled in all capitals or mixed case and have an IPA transcription, a noun table, a gender in the heading or a second part-of-speech label. These lexemes are `short`. All other sections go into the stub table.
- **Part of speech:** the other label in the heading if there is one. Without one, the lexeme is a `Substantiv`, and its gender is empty unless a noun table gives it.
- **Vehicle registration codes** (`MIL`, `WL`) are recognised by `Kennzeichen` or `Unterscheidungszeichen` in the meaning line. A section with only such senses is a stub; elsewhere those senses are dropped.
- **Other spellings are never lexemes.** Sections with a period, in lower case, with a single letter or with spaces are stubs even if they have a noun table, a gender or a second label (`k. o.`, `dpa`, `kcal`, the letter names).
- **Abbreviations transcribed as the full word** (candidates: `Mio`, `Adm`, `Mt`) are not lexemes either. How they are recognised is settled when the first data release is built.
- **Clippings and syllable words** (`Uni`, `Kita`, `Akku`, `Azubi`, `Sponti`, `Fundi`): Wiktionary labels them plain `Substantiv`. They are `short`, recognised from the Herkunft in M2.
- **The stub table** holds what is not a lexeme: sections without a signal (`BBodSchG`, `BT`), orthographic abbreviations (`Einw.`, `kastil.`, `v. v.`), unit symbols (`km`, `MHz`), E numbers and registration codes. In release 1 it has their spelling and raw meaning lines.
- A lexeme without the `Abkürzung` label is never coded by these rules: an ordinary noun without a transcription is `regular`.
