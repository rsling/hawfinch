# 0002: Lexemes, senses and lexical units

Date: 2026-11-24

## Decision

The database separates three things.

- **Lexeme:** a stem with all its form-side properties (spelling, part of speech, inflection, segmentation, pronunciation, etymology).
- **Sense:** a meaning with an identifier and a definition.
- **Lexical unit:** the pairing of one lexeme with one sense, as its own table with attributes.

Rules:

1. **Split rule.** A lexeme is the largest set of senses that share every field stored on the lexeme. If any lexeme-level field differs between senses, they belong to different lexemes. This covers more than inflection: `Wach.stube` and `Wachs.tube` share spelling, gender and plural but differ in segmentation; `über=setz` and `über:setz` differ in particle status and stress.
2. **No merging across Wiktionary sections.** Where German Wiktionary keeps two part-of-speech sections for one spelling, they remain two lexemes, even if their inflection is identical.
3. **Lexeme versus lexical unit.** A different inventory of forms makes a different lexeme (Wort: Wörter versus Worte). A restriction on the same forms, or a syntactic property, is recorded on the lexical unit: "no plural in this sense", transitivity, *haben* versus *sein*.
4. **Senses start word-specific.** Each Wiktionary gloss is one sense belonging to one lexeme. A mapping to abstract senses shared across words can be added later as a further layer without changing the tables.

## Background

The original definition was "a lexeme is a unique form paired with a unique word sense". German Wiktionary, however, records gender, plural and inflection once per part-of-speech section, and all senses in a section share them. Making every sense its own lexeme would have repeated that grammar on every row.

## Reasons

- Grammar is stated once and cannot drift apart between senses of the same word.
- Lexemes do not depend on sense identifiers, which are still an open problem. Word forms, segmentation and word-formation links attach to lexemes and stay valid whatever happens to the sense layer.
- Type counts are right: a noun with fifteen senses counts once in a phonological or morphological count, not fifteen times.
- The model matches the source. Wiktionary opens a new section where grammar differs (Bank: Bänke versus Banken), so sections map almost one-to-one onto lexemes.
- The lexical unit is exactly the original "form paired with sense", so nothing from the original idea is lost. Translations, examples and semantic relations attach there.

Without rule 3, most polysemous verbs would split by sense because transitivity and auxiliary often vary, which would bring back the duplication.

## Known costs

- A split is only possible where the difference is detectable in the data. Milch lists two plurals in one section and explains the difference in prose; it stays one lexeme with two plural variants.
- Lexeme identifiers can change between runs when Wiktionary editors split or merge sections. This is milder than the sense-identifier problem but needs a policy.
- Word-formation links point at pages in Wiktionary, not at sections, so linking a complex word to the right one of several homonymous lexemes needs disambiguation.
