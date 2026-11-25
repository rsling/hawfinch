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

Needed for the first data release; M1 fills the `coding` field ([0005](decisions/0005-abbreviations.md)).

Which sections labelled `Abkürzung` are lexemes is decided. Two points are left for later:

- **Transcriptions of the full word.** Among the lexemes in mixed case, some transcriptions may give the full word, as they do for period abbreviations (candidates: `Mio`, `Adm`, books of the Bible such as `Mt`). These are noise and are to be removed. Not measured yet; how they are recognised is re-evaluated when the first data release is built.
- **Defaulted part of speech.** 295 lexemes are `Substantiv` by default alone. They are to be examined once a beta of the extractor exists.

Survey: [feasibility results](feasibility.md#abbreviations).

## Other structured information in the dumps

Collected throughout; decided in M3, before the freeze.

During extractor development, examine what information beyond the [extraction profile](schema/profile.md) is present in structured form.
