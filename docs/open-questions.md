# Open questions

Points that need discussion before the affected part is implemented. Each question names the milestone of [the roadmap](roadmap.md) that needs it answered.

## Stable identifiers for word senses (required)

Needed before M3 starts.

Senses and lexical units need identifiers that stay the same across extraction runs. Wiktionary offers none: senses are numbered `[1]`, `[2a]`, … within an entry, and editors renumber them. Ways to identify senses across runs have to be explored.

One option raised: send each sense description to a local language model and have it match the description to a known abstract sense that comes with its own description. Possibly overkill, but as a by-product it would yield a GermaNet-like sense inventory. This would be the later abstraction layer foreseen in [the lexeme model decision](decisions/0002-lexeme-model.md); senses start word-specific.

## Stable identifiers for lexemes

Needed in M2, when lexemes become final.

Lexemes follow Wiktionary's part-of-speech sections, which editors can split or merge. A policy for keeping lexeme identifiers stable across runs is needed.

## Linking word formation to the right homonym

Needed in M2.

Wiktionary's word-formation descriptions link to pages, not to sections. When a page holds several lexemes (Bank), the constituent of a complex word has to be assigned to one of them.

## Syllable boundaries in IPA

Needed at the start of M2.

Wiktionary's transcriptions mark stress but not syllable boundaries. The boundaries must not be taken from the orthographic "Worttrennung". The method is undecided; nothing is to be implemented before it has been discussed.

## Syllable and morpheme boundaries that do not coincide

Needed in M1, which stores orthographic syllables and inflectional segmentation side by side.

`Ge·sund·heit` versus `Gesund:heit`, `läuft` versus `läuf-t`. Presumably syllable segmentation and morphological segmentation are stored in separate fields. Not confirmed.

## Coding of short words

Needed in M1, which fills the `coding` field ([0005](decisions/0005-abbreviations.md)).

The IPA test (`short` with a transcription, `abbreviation` without) applies only to sections labelled `Abkürzung`. It is decided for abbreviated names in capitals (`BT`, `CVJM`) and intended for capitalised abbreviations only. Open points:

- **Spellings.** Is "capitalised" all capitals only (`KKW`, `UWG`: 1,871 sections), or also mixed case (`Lkw`, `GmbH`, `BeurkG`: 1,068)? What coding do single letters (63), lower-case spellings (`km`: 97) and spellings with spaces (332) get?
- **Reliability.** 1,337 of the 1,871 all-capitals sections have no IPA transcription. Many are short stubs (`LPD`, `BBL`, `UWG`) that are probably spoken letter by letter. There, a missing transcription reflects unfinished entries more than pronunciation, so the test would code them `abbreviation`.
- **Out of scope?** Vehicle registration codes (`MIL`, `RE`), unit symbols (`MHz`, `Lj`) and E numbers (`E 401`) are among these sections. Should they be lexemes at all?

Survey: [feasibility results](feasibility.md#abbreviations).

## Other structured information in the dumps

Collected throughout; decided in M3, before the freeze.

During extractor development, examine what information beyond the [extraction profile](schema/profile.md) is present in structured form.
