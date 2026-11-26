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

## Verb stems

Raised by the [feasibility test](feasibility.md#verb-stems).

Settled on 2026-11-25:

- **Stems stored:** present, present of the second and third person singular, preterite, participle.
- **Variant stems** are stored in a table of their own (lexeme, stem field, stem, conjugation class), not in doubled columns. A second Partizip II with the same stem (`gesalzt`, `viergeteilt`) is stored as a word form only.
- **Subjunctive II** follows from the preterite stem and is not stored, except for stems that do not follow (`würf`, `stünd`). These go into the table of variant stems. It does not distinguish a sole stem (`würfe`) from a variant (`stünde` besides `stände`): grammars make that distinction, and only usage data can show whether it is real.
- **Conjugation class** (weak, strong, mixed, irregular) is a field of the lexeme. Mixed verbs store the stem without the weak suffix (`dach`).
- **Parallel conjugations** (`fragen`: `fragte` and `frug`; 151 conjugations): one lexeme with variant stems.
- **Auxiliary:** 699 conjugations repeat another one on the same page with the other auxiliary (`heimfahren`: `ist heimgefahren`, `hat ihn heimgefahren`). They are not lexemes of their own; the auxiliary is a property of the lexical unit.
- **Reflexive verbs:** in release 1, every reflexive conjugation in Wiktionary is a lexeme of its own, whether the verb is only reflexive (299 pages) or also has a non-reflexive conjugation (383 pages: `merken`, `sich merken`). Wiktionary's marking is noisy here; corpus data is expected to improve it later.
- **Verbs written as several words** (`Rad fahren`, `ab sein`) are lexemes.
- **`sein`** has the stems `s` (also for `ist`), `b`, `w` and the participle stem `wes`.
- **`gebären`:** `gebär` is a variant stem of the second and third person singular (`gebärst` besides `gebierst`), like `frug` for the preterite. The rule: a form given without the vowel change makes the present stem a variant; other single forms (`beutst`) are not stems.
- **Inseparable prefixes** are marked in the lexeme stem (`ver:bleib`), by the rule described in the [feasibility test](feasibility.md#stems). The stem fields hold bare stems (`geh`, `ging`, `gang` for `ver:geh`).
- **Combinations with `sein`** written as several words (`ab sein`, `dabei sein`; 8 conjugations) are not lexemes and are removed.
- **Single forms given besides the stems** (11 conjugations):
  - Archaic variants (`beutst`, `ward`) are alternative forms, not stems.
  - Forms that follow from the stems are not stored separately: `sieh`/`siehe` from the stem of the second and third person singular, `werd`/`werde` and `berstet` from the present stem.
  - `schwären` gets no special treatment.

Open:

- **Spelling variants of one verb** (`zutage fördern`, `zu Tage fördern`) are one lexeme. Wiktionary links them in the block `Alternative Schreibweisen`; how reliable that block is will be measured together with the nouns. Among verbs written as several words there are 7 such pairs, and 30 that also exist written as one word (`bekanntgeben`, `bekannt geben`).
- **Prefixes of loan verbs** (`de:mobilisier`, `prä:disponier`) cannot be told from stems that merely begin alike (`dekorier`, `regier`). Left to the Herkunft analysis in M2.
- **`ge` as a prefix.** It is split only where the rest is a verb in Wiktionary, which leaves `gewinn`, `gescheh`, `geling`, `genes` and `gebär` whole and still splits `ge:sund`, `ge:wicht` and `ge:witter` wrongly. To be corrected with the Herkunft analysis in M2.

## Plural classes

Raised by the [feasibility test](feasibility.md#plural-classes). The classes are defined in [plural classes](features/plural-classes.md).

Settled on 2026-11-26:

- **Eight classes:** `primary`, `secondary`, `marked-n`, `marked-r`, `default`, `loan`, `irregular`, `adjectival`.
- **A plural without a suffix is an `-e` plural** after a reduced syllable and a `loan` plural otherwise; `-n` is `-en`.
- **Plural stem** instead of an umlaut field: the literal stem of the plural (`Stühl`, `Baut`).
- **Segmented plural** with the boundary always present (`Lehrer-`).
- **Masculine `-er`** is `marked-r`. **`Herz`** and **substitutive plurals** (`Kaufleute`) are `irregular`. **Nouns declined like adjectives** are `adjectival`.
- **Nouns without a singular** have gender `nd` and a class by their ending: `Leut-e`, `Ferie-n` and `Geschwister-` `primary`, `Hot Pant-s` `default`, `Mammali-a` `loan`.
- **Names** with genitive and plural in `-s` are `default`.
- **Different plurals, and different genders, in one table are different lexemes.** Which senses go with which of them is left open and is to be found from usage data.
- **A genitive in `-ns`** belongs to a singular in `-n`. Where Wiktionary has no entry of its own for the noun in `-e` (`Friede`), that lexeme is missing; this is accepted.
- **A weak genitive as a variant** makes a noun `marked-n`; the genitive that does not fit goes into a table of variant forms.
- **Genitive in `-s` and `-es`:** only the form in `-es` is stored.
- **Stems that the singular does not have** (`Baut-en`, `Jung-s`) are classified by their suffix.
- **Nouns written as several words** take the class of the word that inflects. **Nouns with an attributive adjective** (`grauer Star`) are lexemes with the class of their head noun.
- **Archaic, regional, Austrian and Swiss entries:** a section is left out if all its senses are marked ([usage labels](features/usage-labels.md)); 5,677 of 190,876 lemma sections.
- **A plural without a suffix after a full syllable is dropped** if the noun has another plural (`Keks` beside `Kekse`, `KZ` beside `KZs`).
- **Abbreviations in capitals whose only plural has no suffix** (`VWL`, `POS`; 27) have no class. There is no class `unspecified`.
- **Plurals of names that are not in `-s`** (759: `Volker`, `Annaliesen`) have no class.
- **Several genders and several plurals in one table** (291 tables): every singular is combined with every plural, because the table does not say which belong together. Some of the combinations are not words of German. Accepted for release 1; to be looked at during the analyses and fixed in a later version, possibly by patch lists that correct deficiencies of Wiktionary.
- **Marked senses in sections that stay** (2,921 sections) are kept with their label.
- **Regional and archaic forms in unmarked entries** (`Smokinge`, `Wägen`, `Stäte`) cannot be recognised from sense labels. They stay in release 1 and are candidates for a patch list; they need inspection by hand during the analyses.
- **Qualified labels** (`besonders österreichisch`, `sonst veraltet`; 608 sections with only such labels) do not count as marks.
- **The rule for archaic and regional entries holds for every part of speech.** The feasibility scripts for plurals and verb stems apply it.

Open:

- **Where the rule for archaic and regional entries is applied.** At present each feasibility script calls it. It belongs in one place, where the part-of-speech sections of a page are selected, so that every feature reader sees only the sections that stay; the link from a `Flexion:` page to the verb sections of its lemma page belongs there as well. To be refactored.
- **Verb sections of one lemma page of which only some are left out** (51 pages): their conjugations are all kept, because a `Flexion:` page does not say which section a conjugation belongs to.
- **Nouns without gender** (7 combinations, `Radionachricht`): neither the table nor the heading gives one. For compounds it could be taken from the head noun in M2.
- **Nouns without a singular in `-er`** are `primary` without a suffix, also where the form is an `-er` plural (`Seevölker`, `Stadtväter`); without a singular the two cannot be told apart.
- **Nouns written as several words in which two words inflect** (`Agent-s Provocateurs`, `Persona-e gratae`) have the boundary in the first one only.

## Other structured information in the dumps

Collected throughout; decided in M3, before the freeze.

During extractor development, examine what information beyond the [extraction profile](schema/profile.md) is present in structured form.
