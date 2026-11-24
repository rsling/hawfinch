# Open questions

Points that need discussion before the affected part is implemented.

## Stable identifiers for word senses (required)

Senses and lexical units need identifiers that stay the same across extraction runs. Wiktionary offers none: senses are numbered `[1]`, `[2a]`, … within an entry, and editors renumber them. Ways to identify senses across runs have to be explored.

One option raised: send each sense description to a local language model (via Ollama) and have it match the description to a known abstract sense that comes with its own description. Possibly overkill, but as a by-product it would yield a GermaNet-like sense inventory. This would be the later abstraction layer foreseen in [the lexeme model decision](decisions/0002-lexeme-model.md); senses start word-specific.

## Stable identifiers for lexemes

Lexemes follow Wiktionary's part-of-speech sections, which editors can split or merge. A policy for keeping lexeme identifiers stable across runs is needed.

## Linking word formation to the right homonym

Wiktionary's word-formation descriptions link to pages, not to sections. When a page holds several lexemes (Bank), the constituent of a complex word has to be assigned to one of them.

## Syllable boundaries in IPA

Wiktionary's transcriptions mark stress but not syllable boundaries. The boundaries must not be taken from the orthographic "Worttrennung". The method is undecided; nothing is to be implemented before it has been discussed.

## Syllable and morpheme boundaries that do not coincide

`Ge·sund·heit` versus `Gesund:heit`, `läuft` versus `läuf-t`. Presumably syllable segmentation and morphological segmentation are stored in separate fields. Not confirmed.

## Other structured information in the dumps

During extractor development, examine what information beyond the [extraction profile](schema/profile.md) is present in structured form.
