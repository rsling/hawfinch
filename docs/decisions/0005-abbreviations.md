# 0005: Abbreviations and short words

Date: 2026-11-24, revised 2026-11-25

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
2. **Lexemes get a field `coding`** with two values:
   - `short`: a short word that is spoken as such (`KKW`, `CVJM`, `Lkw`).
   - `regular`: all other lexemes.
3. **Only sections with a signal of word status become lexemes.** A section labelled `Abkürzung` is a lexeme if it is spelled in all capitals or mixed case (`KKW`, `Lkw`, `GmbH`) and has at least one of:
   - an IPA transcription;
   - a noun table (`Deutsch Substantiv Übersicht`);
   - a gender in the heading;
   - a second part-of-speech label.

   All such lexemes are `short`. In the dump of 2026-11-01 these are 824 of the 2,939 sections in all capitals or mixed case.
4. **Everything else is a stub.** Sections without any of these signals are mostly unfinished entries whose only content is the expansion (`BBodSchG`, `UWG`), and they are not lexemes. They go into the stub table, so that what was left out of the main tables can be examined. This includes:
   - sections in all capitals or mixed case without a signal (2,108), among them written abbreviations read as the full word (`BT`);
   - orthographic abbreviations with a period (`Einw.`, `kastil.`, `v. v.`);
   - codes: vehicle registration codes (`MIL`, `WL`), unit symbols (`km`, `MHz`) and E numbers (`E 401`);
   - all sections in other spellings (lower case, single letters, spaces), whatever they contain. A noun table, a gender or a second label does not make them lexemes: `dpa`, `kcal`, `k. o.` and the letter names (`a`, `b`, …) are stubs.
5. **Vehicle registration codes are removed by a pattern on the meaning line** (`Kennzeichen`, `Unterscheidungszeichen`). Wiktionary does not mark them in the markup. A section whose senses are all registration codes is a stub; in other sections, only those senses are dropped.
6. **A section without a part-of-speech signal is a `Substantiv`**, with the gender left empty unless a noun table gives one.
7. **Clippings and syllable words are `short` too:** `Uni`, `Kita`, `Akku`, `Azubi`, `Sponti`, `Fundi`. They share their phonotactic and morphological properties with words like `LKW`. Wiktionary labels them plain `Substantiv`, so they are recognised from the Herkunft in M2; until then they are `regular`.
8. **A lexeme without an IPA transcription is `short` like the others.** 181 lexemes have a noun table, a gender or a second label, but no transcription (`BaFin`, `DIN`, `KMK`). They are short words that Wiktionary has not transcribed, and they need no separate list.
9. **Abbreviations whose transcription gives the full word are not lexemes.** Some sections in mixed case may be transcribed as the full word, as period abbreviations are (candidates: `Mio`, `Adm`, books of the Bible such as `Mt`). They are to be removed. How they are recognised is not settled; it is re-evaluated when the first data release is built.

## Rejected: coding by IPA alone

The first version of this decision had a third value, `abbreviation`, for written abbreviations read as the full word, and assigned it to every section without an IPA transcription. The [survey](../feasibility.md#abbreviations) showed that a missing transcription mostly means an unfinished entry: 1,337 of the 1,871 sections in all capitals have none, and most of them are spoken letter by letter. The value is dropped for lexemes.

## Consequences

- `coding` is a lexeme-level field. By [0002](0002-lexeme-model.md), a difference in it makes two lexemes.
- The cut between lexeme and stub follows how complete the Wiktionary entry is, not a linguistic class. Real short words with unfinished entries are stubs (`DWD`, `ASB`, `THG`). Of the 2,108 stubs in all capitals or mixed case, 504 have an audio file and 754 have an example.
- 295 lexemes get their part of speech by default alone (no label, gender or noun table). They are to be examined once a beta of the extractor exists.
- The stub table holds more than orthographic abbreviations.
- `UFO` carries `Abkürzung` but its variant `Ufo` does not. Both are `short`: `UFO` by this decision, `Ufo` from its Herkunft in M2.
- `k. o.` is a stub, although it is used as an adjective.
