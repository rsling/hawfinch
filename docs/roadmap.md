# Roadmap

Date: 2026-11-24

Release 1 is the extractor and nothing else. It is reached in three milestones, each ending in a tagged data release. After release 1 the extractor is feature-frozen. What follows it is noted briefly [at the end](#after-release-1).

The order of the milestones follows one dependency. By the split rule in [the lexeme model](decisions/0002-lexeme-model.md), a lexeme is only final once all its form-side fields exist, including segmentation. So the form side is finished first (M1, M2), and senses and lexical units are attached to final lexemes last (M3).

Every milestone also delivers the feature definitions in `features/` and the schema documentation in `schema/` for what it adds, plus test fixtures and validation checks.

## Gate: feasibility test

Comes before M1 and is not a milestone. It is defined in [the extraction strategy](decisions/0001-extraction-strategy.md): read noun, verb and adjective arguments from a real dump, measure coverage per profile item, and compare counts with the Kaikki file.

Its results set the numeric coverage targets in the exit criteria below and may move items between milestones. If Herkunft parsing or the stem arguments on `Flexion:` pages fail badly, this roadmap is revised before M1 starts.

## M1: Inflection (release v0.1.0)

The whole pipeline runs end to end on a narrow slice, so that every later milestone only adds features.

- **Pipeline:** `fetch`, a streaming dump reader, selection of German entries, a wikitext parser for sections and templates, and working `extract`, `validate` and `export` subcommands.
- **Release format:** Parquet tables, a DuckDB file and `MANIFEST.json`, with the CC BY-SA licence and attribution text shipped in the release.
- **Lexeme table:** spelling, spelling variants, part of speech (German labels), gender, orthographic syllables, IPA as found, and lexeme-level quirks (no plural, only plural). Nouns, verbs and adjectives are covered in full; other parts of speech get the basic fields only.
- **Verb stems:** read from `Flexion:` arguments and stored without the infinitive suffix.
- **Word-form table:** forms from form entries and noun tables, with grammatical features, spelling variants, orthographic syllables, and IPA where present. Missing single-word forms are generated from stems and marked as generated.
- **Derived fields:** plural type, adjective umlaut, inflectional segmentation (`läuf-t`).
- **Validation:** consistency checks, a coverage report per profile item, and a count comparison against Kaikki.
- **Identifiers:** provisional, and documented as unstable.

Exit criteria:

- A release builds reproducibly from one dump with one documented command sequence.
- Coverage of the noun, verb and adjective items meets the targets set after the feasibility test.
- `schema/` describes every table and column of the release.

## M2: Word formation and phonology (release v0.2.0)

Completes the form side. Lexemes are final after this milestone.

- **Herkunft:** a rule-based parser for nouns and adjectives; `{{Verbherkunft}}` for verbs, with the prefix list ported from `Modul:Verb`.
- **Segmentation:** alignment of constituents with the surface string, and full segmentation with `.`, `+`, `:` and `=`.
- **Lexeme split by segmentation** (`Wach.stube` versus `Wachs.tube`) and the distinction between simplex and complex lexemes.
- **Containing-lexeme links:** obtained by inverting the segmentations and cross-checked against `Wortbildungen`.
- **Homonym linking of constituents:** an [open question](open-questions.md) that needs a decision in this milestone.
- **Affix table:** spelling, syllables, IPA, type, base class counted from our own segmentations, and the collected semantic descriptions.
- **Phonology:** consistency check and normalisation of IPA, and syllable count. IPA syllabification, mora count and the trochaic flag follow once the syllabification method has been discussed; nothing is implemented before that. The discussion belongs at the start of M2.
- **Lexeme identifiers:** the policy for keeping them stable is decided here, since lexemes are now final.

Exit criteria:

- The agreed share of complex nouns, verbs and adjectives is segmented, and unparsed Herkunft lines are reported by cause.
- The phonological fields are present for the agreed share of lexemes and word forms.

If the feasibility test shows Herkunft parsing to be hard, phonology is the part to split off into a milestone of its own.

## M3: Senses, lexical units, freeze (release v1.0.0)

- **Senses and lexical units:** senses with their definitions, lexical units, and resolution of sense references (`[1, 2]`, `[1–3]`, `[2a]`, `[*]`).
- **Lexical-unit properties:** restrictions, transitivity, auxiliary and similar labels.
- **Semantic relations, English translations, and the examples table.**
- **Stable sense identifiers:** the scheme must be decided before this milestone starts. It is the one unsolved requirement for the freeze.
- **Other structured information:** a survey of what else the dump holds in structured form, with a decision per item to add it or leave it out.
- **Freeze:** the schema is documented completely, every feature has its definition in `features/`, the validation report is complete, the licence version is confirmed against the dump, and release v1.0.0 is pinned in `analysis/release.txt`.

After the freeze the schema does not change. Bug fixes and re-runs on newer dumps produce releases with the same schema, and the analyses move to a newer release only by a deliberate change of the pin.

## Not in release 1

- **Underlying phonological representation.** It is our own analysis, not extraction, and is expected to come out of the phonology study.
- **Abstract senses shared across words.** Senses stay word-specific, as [the lexeme model](decisions/0002-lexeme-model.md) foresees.
- **Generalisation over the semantic descriptions of affixes.** Release 1 only collects the descriptions.

## After release 1

- **Release 2, the user interface.** Planned in detail once v1.0.0 exists. The app reads a data release only and includes the generator for periphrastic forms.
- **Analyses for the paper.** Exploratory, so they have no roadmap. They run against the pinned release, in parallel with the work on the interface. Extractor defects found during analysis are fixed in a release with the same schema; they do not add features.
- **Corpus linking.** A later phase that joins usage data from web corpora onto releases by lexeme identifier.
