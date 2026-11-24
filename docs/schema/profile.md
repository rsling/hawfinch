# Extraction profile

What the database must contain. This is the requirements list that the release schema will implement; column names and types are not fixed yet. Where each item comes from in German Wiktionary is recorded in [the extraction strategy decision](../decisions/0001-extraction-strategy.md). The reasoning behind the lexeme, sense and lexical-unit split is in [the lexeme model decision](../decisions/0002-lexeme-model.md). Unsettled points are in [open questions](../open-questions.md).

## Basic definitions

- A **lexeme** is a stem together with all its form-side properties: spelling, part of speech, inflection, segmentation, pronunciation, etymology. It is the largest set of senses that share every field stored on the lexeme. Whenever any lexeme-level field differs between senses, there are two lexemes.
- A **sense** is one meaning with its definition. Initially senses are word-specific: one per Wiktionary gloss. A mapping to abstract senses shared across words may be added later as a further layer.
- A **lexical unit** is the pairing of one lexeme with one sense. It carries everything that holds for that lexeme in that sense only.
- The form of a lexeme is its **stem**, not its dictionary form. Verbs are stored without the infinitive suffix (`kauf`, not `kaufen`).
- **Periphrastic forms are never stored** (for example "geglaubt haben würde"). They can be generated on the fly from the stored forms. Only single-word inflected forms go into the word-form table.
- **zu-infinitives and gerundives are never stored either** (`aufzustocken`, `aufzuwärmende`), even where `zu` is written inside the word. The **Partizip I is derivation, not inflection**: an `-end` word is a lexeme only where Wiktionary lists it with its own meaning. The Partizip II is a word form of the verb; its declined forms are stored only for adjective lexemes. See [0004](../decisions/0004-participles-and-zu-forms.md).
- **Proper nouns are a part of speech of their own**, separate from common nouns. A noun in a given sense is a common noun if it has a conceptual plural or a mass use, and otherwise a proper noun, with some classes fixed by name. Sections mixing both are split into two lexemes. See [0003](../decisions/0003-proper-nouns.md).
- **`Abkürzung` is not a part of speech.** Short words and abbreviated names are ordinary lexemes with the part of speech they are used as, and their form is recorded in `coding`. Orthographic abbreviations (`Einw.`) are not lexemes. See [0005](../decisions/0005-abbreviations.md).
- Where a distinction cannot be read off the markup, an optional local language model may make it. A release records whether one was used. See [0006](../decisions/0006-language-model.md).
- All segmentation uses the symbols defined in [segmentation conventions](../features/segmentation.md).

Lexeme or lexical unit? A different inventory of forms means a different lexeme (Wort with plural Wörter versus Worte). A restriction on the same forms, or a syntactic property, belongs to the lexical unit ("no plural in this sense", transitivity, choice of auxiliary).

Origin labels below: **extracted** (read from Wiktionary), **derived** (computed by us from extracted data), **ours** (produced by analysis in this project, not in Wiktionary).

## Lexemes

Ideally two tables, one for simplex and one for complex lexemes.

| Item | Origin | Notes |
|---|---|---|
| Spelling | extracted | |
| Spelling variants | extracted | |
| Orthographic syllable segmentation | extracted | |
| Part of speech | extracted/derived | German Wiktionary labels, with two exceptions. Proper nouns are a part of speech of their own, recognised from the labels or, if configured, by a language model ([0003](../decisions/0003-proper-nouns.md)). `Abkürzung` is replaced by the part of speech the word is used as ([0005](../decisions/0005-abbreviations.md)). Definitions in [part of speech](../features/part-of-speech.md). |
| Coding | derived | `regular`, `short` (spoken as such: `KKW`, `CVJM`, `Uni`) or `abbreviation` (read as the full word: `BT`). Clippings such as `Uni` are recognised from the Herkunft in M2. See [0005](../decisions/0005-abbreviations.md). |
| Grammatical gender (nouns) | extracted | |
| Plural type (nouns) | derived | Regular case: umlaut yes/no plus suffix. Irregular cases must be representable too. |
| Umlaut in comparative/superlative (adjectives) | derived | yes/no |
| Stem allomorphs (verbs) | extracted/derived | Four stems; identical for weak verbs. |
| IPA transcription with syllable segmentation | extracted + ours | Transcriptions need a consistency check and possibly normalisation. Syllable boundaries are not in Wiktionary; see the open question before implementing anything. |
| Underlying phonological representation | ours | Not in Wiktionary. |
| Syllable count | derived | |
| Mora count | derived | |
| Trochaic | derived | yes/no |
| Links to all word forms | extracted/derived | Separate table, see below. |
| Links to lexemes containing this lexeme via word formation | derived | |
| Full word-formation segmentation | derived | Only if the word has itself undergone word formation. The main source is the "Herkunft" section. |
| Grammatical quirks holding for the whole lexeme ("no plural", "only plural", …) | extracted | Structured in Wiktionary. |

## Senses

| Item | Origin | Notes |
|---|---|---|
| Stable identifier | ours | Required; method open. |
| Definition | extracted | The Wiktionary gloss. |

## Lexical units

One row per pairing of a lexeme with a sense.

| Item | Origin | Notes |
|---|---|---|
| Lexeme and sense | derived | |
| Restrictions and syntactic properties in this sense | extracted | "No plural in this sense", transitivity, auxiliary, and similar labels. |
| Links to synonyms, hyponyms and other semantic relations | extracted | |
| English translations | extracted | If possible. For later automatic word-by-word glossing. |
| Link into the examples table | extracted | If possible. |

## Word forms

Inflected forms of a lexeme, in a separate table linked from the lexeme table.

| Item | Origin | Notes |
|---|---|---|
| Spelling | extracted | |
| Spelling variants | extracted | |
| Segmentation into inflectional affixes and stem | derived | Inflection only. Word formation is recorded on the lexeme. |
| Orthographic syllable segmentation | extracted | |
| IPA transcription with syllable segmentation | extracted + ours | Same caveat as for lexemes. |
| Syllable count | derived | |
| Mora count | derived | |
| Trochaic | derived | yes/no |
| Grammatical features | extracted | Number, person, case, etc. |

## Affixes

Preliminary; to be done if feasible.

| Item | Origin | Notes |
|---|---|---|
| Spelling | extracted | |
| Spelling variants | extracted | |
| Orthographic syllable segmentation | extracted | |
| IPA transcription | extracted | |
| Underlying representation | ours | |
| Syllable count | derived | |
| Mora count | derived | |
| Trochaic | derived | yes/no |
| Affix type | extracted | Prefix or suffix. |
| Base word class | extracted/derived | One row per base class if the affix combines with several. |
| Semantic effect | extracted, then generalised | E.g. nomen actionis. Wiktionary gives natural-language descriptions. Strategy: collect the descriptions in a separate table, reference them from the affix table, then try to generalise over them. |

## Examples

A separate table: primary key plus the example text. Lexical units link into it.

## Orthographic abbreviations

A stub table in release 1 ([0005](../decisions/0005-abbreviations.md)). It holds written abbreviations that are not lexemes (`Einw.`, `kastil.`, `v. v.`) and is not analysed further.

| Item | Origin | Notes |
|---|---|---|
| Spelling | extracted | |
| Meaning lines | extracted | Raw, as in Wiktionary. |

## To do during extractor development

Examine what other information is present in the dumps in structured form beyond the items above, and decide whether to add it.

## Consequences for the user interface

Because periphrastic forms are not stored, the interface should include a small function that generates them on request from the stored forms.
