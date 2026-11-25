# 0005: Abbreviations and short words

Date: 2026-11-24

## Context

German Wiktionary uses `Abkürzung` as a part-of-speech label. In the dump of 2026-11-01, 5,191 German sections carry it ([survey](../feasibility.md#abbreviations)):

- 4,878 carry it alone, and 4,721 of these have nothing else that signals a part of speech, not even a gender in the heading;
- 303 carry it together with `Substantiv`;
- 8 carry it with a name label (DDR, ISS, USA).

The label covers three kinds of words:

- written abbreviations of words or phrases: `Einw.`, `kastil.`, `v. v.`;
- short words used as ordinary nouns: `KKW`, `Lkw`, `UFO`;
- abbreviated names: `BT` (Bundestag), `CVJM`, `TÜV`, `WHO`.

## Decision

1. **`Abkürzung` is not a part of speech.**
   - Short words and abbreviated names are lexemes like any other. They have inflection, gender and pronunciation, and their part of speech is the one they are used as: `KKW`, `BT` and `CVJM` are nouns. Whether they name something is recorded like for any other word ([0003](0003-named-entities.md)).
   - `k. o.` is an adjective.
2. **Lexemes get a field `coding`** with three values:
   - `short`: a short word that is spoken as such (`KKW`, `CVJM`).
   - `abbreviation`: a written abbreviation that is read as the full word (`BT` is read "Bundestag").
   - `regular`: all other lexemes.
3. **`short` or `abbreviation` is decided by pronunciation.**
   - If Wiktionary gives an IPA transcription, the coding is `short`; if not, it is `abbreviation`. This follows the usual pattern that an abbreviation read as the full word has no transcription of its own.
   - **The test applies only to sections labelled `Abkürzung`.** An ordinary noun that happens to lack an IPA transcription is never coded `abbreviation`.
   - It is decided for abbreviated names written in capitals (`BT`, `CVJM`). Which other spellings it covers is open ([open questions](../open-questions.md#coding-of-short-words)).
4. **Clippings and syllable words are `short` too:** `Uni`, `Kita`, `Akku`, `Azubi`, `Sponti`, `Fundi`. They share their phonotactic and morphological properties with words like `LKW`. Wiktionary labels them plain `Substantiv`, so they are recognised from the Herkunft in M2; until then they are `regular`.
5. **Orthographic abbreviations get a stub in release 1.** `Einw.` and `kastil.` are not lexemes. They are written to a table of their own with their spelling and the raw meaning lines, and they are not analysed further.

## Consequences

- `coding` is a lexeme-level field. By [0002](0002-lexeme-model.md), a difference in it makes two lexemes.
- Almost no section labelled only `Abkürzung` shows a part of speech in its markup. Their part of speech has to come from the meaning line or a default. How that is done is settled on the data in M1.
- Separating orthographic abbreviations from short words is also settled on the data in M1. The period in `Einw.` is the obvious signal, but not the only one: `MHz` is read as the full word and has no period.
- `UFO` carries `Abkürzung` but its variant `Ufo` does not. Both are `short`: `UFO` by the IPA test, `Ufo` from its Herkunft in M2.
