# Segmentation conventions

All segmentations in the database use the following boundary symbols. The convention is adapted from Roland Schäfer, *Einführung in die grammatische Beschreibung des Deutschen* (Language Science Press, <https://langsci-press.org/catalog/book/224>).

| Boundary | Symbol | Example |
|---|---|---|
| Syllable (orthographic and phonetic) | `·` | `An·zah·lung` |
| Inflectional affix / stem | `-` | `läuf-t` |
| Compound stems | `.` | `Haus.tür` |
| Linking element in a compound | `+` | `Kind+er.garten` |
| Derivational affix / stem | `:` | `Gesund:heit` |
| Verb particle | `=` | `ab=kauf` |

Notes:

- The syllable symbol is U+00B7 (middle dot), the same character German Wiktionary uses in its "Worttrennung" sections.
- Circumfixes get no special marking; each part is an ordinary inflectional boundary: `ge-koch-t`.
- Lexemes are stored as stems, so verbs appear without the infinitive suffix: `ab=kauf`, not `ab=kaufen`.
- Word-formation boundaries (`.`, `+`, `:`, `=`) belong to the lexeme. Word forms carry only the inflectional segmentation (`-`).
- In IPA strings, the derivation symbol `:` (colon) must not be confused with the length mark `ː` (U+02D0).

## Syllable boundaries in IPA

Phonetic syllabification must **not** be copied from the orthographic "Worttrennung": the two do not align perfectly. German Wiktionary's IPA marks stress but no syllable boundaries, so these boundaries have to come from our own analysis. How to do that is undecided. Do not implement IPA syllabification before it has been discussed (see [open questions](../open-questions.md)).
