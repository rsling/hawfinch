# 0001: Extraction strategy

Date: 2026-11-24

## Decision

We write our own extractor, which reads template arguments directly from the German Wiktionary XML dump. The Kaikki JSONL produced by wiktextract serves as a validation baseline, not as our input. A fork of wiktextract's German extractor is the fallback if our own parsing of some section proves harder than expected.

## Reasons

- Almost everything in the [extraction profile](../schema/profile.md) is stored in German Wiktionary as explicit template arguments or formulaic lines. Reading it needs no template or Lua expansion.
- wiktextract's German extractor discards or flattens several things the profile depends on: syllabification of non-lemma forms, the `Genus` argument, parallel plurals, person in verb forms, and any word-formation structure.
- What wiktextract adds through Lua expansion is mainly the full verb tables from `Flexion:` pages. Most of that is periphrastic forms, which we never store. The single-word forms follow from the stem arguments on those pages.
- wiktextract has no releases. Both of its repositories are used at unpinned master, the output schema changes without version numbers, and Kaikki overwrites its files in place. That is workable for a baseline but weak as the foundation of a citable resource.

## Basis

Read on 2026-11-24: the German extractor in wiktextract (`src/wiktextract/extractor/de/`, all modules and tests), the wiktextract and wikitextprocessor pipeline code, the Kaikki downloads for the German edition, `Wiktionary:Download`, the dump index, and the raw wikitext of about 60 German entries, form pages, affix pages and `Flexion:` pages. Nothing was run. Statements about wiktextract's behaviour come from reading its code and tests, and the coverage claims for our own approach are untested until we try them on a dump.

## What German Wiktionary offers

- **`Wiktionary:Download` is outdated.** It recommends `pages-articles.xml.bz2`, describes importing into MySQL with MWDumper, and points to DBnary for RDF. It says nothing about wiktextract, HTML dumps, the API, or licences.
- **The dump is small.** `dewiktionary-latest-pages-articles.xml.bz2` is 272 MB (dump of 2026-11-01) and contains the main namespace plus `Flexion:`, `Verzeichnis:`, `Vorlage:` and `Modul:`. `categorylinks.sql.gz` (89 MB) holds template-generated categories such as Singularetantum, with no expansion needed.
- **Other sources, not used as primary:** DBnary (RDF; its German etymology file is empty), Wikidata lexemes (a separate project, about 242,000 German lexemes), and HTML dumps (public copies frozen in March 2025).
- **Licence:** the site footer states CC BY-SA 4.0; an older licence page still says CC BY-SA 3.0 plus GFDL.

Size, from the API on 2026-11-24:

| | Count |
|---|---|
| German lemma entries | 187,325 |
| Nouns / verbs / adjectives | 143,011 / 14,602 / 18,327 |
| Declined-form entries | 524,660 |
| Conjugated-form entries | 226,719 |
| `Flexion:` pages (verbs and adjectives only) | about 55,700 |
| Suffix / prefix entries | 173 / 147 |

## How wiktextract works

- **Pipeline:** pass 1 loads the dump's pages, templates and Lua modules into SQLite. Pass 2 parses each page in parallel and calls the edition-specific `parse_page`. Templates can be expanded through a sandboxed Lua 5.1 runtime. Kaikki's German run takes about two hours.
- **Output:** JSONL, one record per part-of-speech heading, validated by Pydantic models. The German-edition file (`kaikki.org/dewiktionary/`) is about 3.1 GB, 310 MB gzipped, rebuilt roughly weekly and stamped with the dump date and both commit hashes. All languages are in one file; German entries are selected by `lang_code == "de"`. This is not the same as "German" on the English-edition pages of kaikki.org.
- **Licences:** code MIT; data CC BY-SA and GFDL. The authors ask for a citation of Ylonen (2022), "Wiktextract: Wiktionary as Machine-Readable Structured Data", LREC.
- **Maintenance:** the German extractor has 65 tests and still receives changes. Whether its main author is still active in 2026 is unclear.

### Word senses in wiktextract

- Each `:[n]` line under `Bedeutungen` becomes a `Sense` with `glosses` and a `sense_index` string copied from Wiktionary (`"1"`, `"2a"`, `"1, 2"`, `"1–3"`).
- Sub-senses (`::[a]` under `[2]`) become `"2a"` and inherit the parent's gloss and labels.
- Labels from `{{K|…}}` and abbreviation templates (`{{ugs.}}`, `{{kPl.}}`, `{{trans.}}`) become English `tags` where a mapping exists, otherwise German `raw_tags`.
- Only examples are attached to senses. Synonyms, antonyms, hypernyms, hyponyms, derived words and translations each carry the raw `sense_index` string; ranges and lists are not resolved.
- There is no stable sense ID. The index is unique only within one record and changes when editors renumber. `[*]` (all senses) is not recognised.

Whichever input we use, we must build our own sense identifiers and resolve sense references ourselves. See [open questions](../open-questions.md) and [the lexeme model](0002-lexeme-model.md).

## Fit against the extraction profile

"Direct" means readable from template arguments or section lines without expansion.

### Lexemes

| Item | In German Wiktionary | wiktextract | Our approach |
|---|---|---|---|
| Spelling | page title | yes | direct |
| Spelling variants | `Alternative Schreibweisen`, `Nebenformen`, `Nicht mehr gültige Schreibweisen`; Swiss forms marked `{{CH&LI}}` | yes | direct |
| Orthographic syllables | `Worttrennung` line with `·`, covering lemma plus plural, preterite, participle, comparative, superlative | lemma only; nothing for pluralia tantum | direct |
| Part of speech | `{{Wortart\|…}}` in the heading | yes, mapped to coarse English labels | direct, keep German labels |
| Gender | heading template and `Genus` argument of the noun table | heading only | direct, from `Genus` |
| Plural type | all 8 case/number forms are explicit arguments; parallel plurals numbered (`Nominativ Plural 1/2`); `—` for none | forms present, parallel plurals merged | derive umlaut and suffix by comparing singular and plural; unclassifiable cases keep the explicit forms |
| Adjective umlaut | `Positiv`, `Komparativ`, `Superlativ` arguments | yes | derive |
| Verb stem allomorphs | `Deutsch Verb Übersicht` gives 9–10 principal forms; `Flexion:` pages give stems as arguments (present, past, subjunctive II, participle, 2nd/3rd singular) | forms as strings with pronouns, no stems | direct from `Flexion:` arguments |
| IPA | `{{Lautschrift}}`; stress marked, no syllable boundaries | IPA string | direct for the transcription; syllable boundaries undecided |
| Underlying representation | not present | no | our analysis |
| Links to word forms | form entries with `Grammatische Merkmale` lines and `{{Grundformverweis}}` | form entries exist, but person is lost and the lemma template is ignored | direct; missing single-word forms generated from stems and marked as generated |
| Containing lexemes | `Wortbildungen` lists; `Verzeichnis:Deutsch/Wortbildungen/<affix>` pages | linked words only | invert our own segmentations, cross-check with `Wortbildungen` |
| Full segmentation | `Herkunft` prose (see below) | prose plus a flat list of links | rule-based parser |
| Semantic relations | one section each, lines prefixed with sense references | yes, unresolved sense strings | direct, resolve references |
| "No plural" and similar | structured: `—` cells, `Genus=0`, `{{kPl.}}`/`{{kSg.}}` in `Worttrennung`, categories Singularetantum (28,752) and Pluraletantum (943) | sense-level labels only | direct |
| English translations | `{{Ü-Tabelle}}` per sense with `{{Ü\|en\|…}}` | yes | direct |
| Examples | `Beispiele` lines with sense references and citations | yes, attached to senses | direct |

### Is "Herkunft" structured?

Mostly not: it is stored as prose, not generated from structured data. Two things make it usable.

- **Verbs:** 8,775 entries use `{{Verbherkunft}}`, which generates the sentence from arguments (separable or not, category of the particle, base verb). The prefix is found by a longest-match list in `Modul:Verb`, which we would port.
- **Nouns and adjectives:** the wording follows the templates on the help page closely. A typical line is `[[Determinativkompositum]] aus den Substantiven ''[[Kind]]'' und ''[[Garten]]'' sowie dem [[Fugenelement]] ''[[-er]]''`. The type is a link (69,622 lemma entries mention Determinativkompositum, 14,778 Derivatem, 20,440 Fugenelement), constituents are italic links, and affixes are recognisable by their hyphen.

Limits:

- Constituents are given as lemmas, so we must align them with the surface string ourselves ("Stamm des Verbs fahren" → `Fahr`).
- Umlaut is described in prose.
- About 10,900 German entries are flagged as lacking Herkunft, and some complex words have etymology only (Lehrer, Verkäufer).
- The connecting words vary ("aus", "zu", "von", "zum Stamm des Verbs", "zusammengesetzt aus"), and the linking element may be named between the constituents or after them.

### Word forms

| Item | In German Wiktionary | Our approach |
|---|---|---|
| Spelling, variants | form-entry title; starred table arguments (`Dativ Singular*=Hause`) | direct |
| Inflectional segmentation | not present | derive from stem and form |
| Orthographic syllables | `Worttrennung` on the form entry | direct; forms without an entry need another solution |
| IPA | `{{Lautschrift}}` on the form entry (since a 2015 vote, not on the lemma) | direct; gaps remain |
| Grammatical features | formulaic line, e.g. `3. Person Singular Indikativ Präsens Aktiv des Verbs '''[[laufen]]'''` | direct |

Form entries are numerous but not complete for rare lemmas.

### Affixes

Spelling, syllables, IPA and affix type are direct. Base category and semantic effect are prose, with category words linked (`zur Ableitung eines [[Adjektiv]]s von einem [[Verb]]`) and occasional labels such as `{{K|Nomen Actionis}}`. Base categories can also be counted from our own segmentations, which is likely more reliable than the prose. Collecting the descriptions in a separate table and generalising later fits the data.

## Next step

A feasibility test on a real dump: read the arguments for nouns, verbs and adjectives, measure coverage per profile item (for instance the share of complex nouns whose Herkunft line parses), and compare counts against the Kaikki file.
