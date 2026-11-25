# Feasibility test

The gate before M1 in [the roadmap](roadmap.md), defined in [the extraction strategy](decisions/0001-extraction-strategy.md). This file records the results; the raw tables are in `data/interim/feasibility/` (not tracked).

## Data

Pinned to the dump of 2026-11-01, because Kaikki's current file was built from exactly this dump (wiktextract `19f9a30`, wikitextprocessor `6f96ddf`).

| File | Size | Check |
|---|---|---|
| `dewiktionary-20261101-pages-articles.xml.bz2` | 272 MB | SHA-1 as published |
| `dewiktionary-20261101-categorylinks.sql.gz` | 89 MB | SHA-1 as published |
| `dewiktionary-20261101-linktarget.sql.gz` | 35 MB | SHA-1 as published |
| `kaikki/raw-wiktextract-data.jsonl.gz` | 312 MB | none published; size, hashes and source dump date recorded |

Reproduce:

```sh
uv run hawfinch fetch --date 20261101 --categories --kaikki
uv run python extract/scripts/feasibility.py cache --date 20261101       # 80 s
uv run python extract/scripts/feasibility.py inventory --date 20261101   # 2 min
```

The page cache (`data/interim/20261101/pages.parquet`, 289 MB) holds all 1,423,063 pages of the dump: 1,273,799 in the main namespace (1,196 redirects) and 71,989 in `Flexion:`.

## Step 1: inventory

What the markup of German entries looks like, counted before writing any extractor.

### Entries and parts of speech

972,213 main-namespace pages have a German entry. No page has more than one: homonyms (Bank) are separate part-of-speech sections (level 3) inside one German entry (level 2).

**Our section parsing agrees with the categories of the same dump.** For every part-of-speech label, the set of pages with a `{{Wortart|<label>|Deutsch}}` heading was compared with the members of the category `<label> (Deutsch)`:

| Label | Pages (ours) | Category | Only ours | Only category | API, 2026-11-24 |
|---|---|---|---|---|---|
| Deklinierte Form | 522,734 | 522,735 | 0 | 1 | 524,660 |
| Konjugierte Form | 226,643 | 226,643 | 0 | 0 | 226,719 |
| Substantiv | 141,927 | 141,932 | 0 | 5 | 143,011 |
| Adjektiv | 18,260 | 18,262 | 0 | 2 | 18,327 |
| Dekliniertes Gerundivum | 18,005 | 18,005 | 0 | 0 | |
| Verb | 14,599 | 14,599 | 0 | 0 | 14,602 |
| Partizip II | 14,587 | 14,587 | 0 | 0 | |
| Partizip I | 14,382 | 14,382 | 0 | 0 | |
| Toponym | 11,953 | 11,955 | 0 | 2 | |
| Erweiterter Infinitiv | 6,568 | 6,568 | 0 | 0 | |
| Nachname | 6,262 | 6,263 | 0 | 1 | |
| Superlativ / Komparativ | 6,219 / 6,209 | 6,219 / 6,210 | 0 | 0 / 1 | |

Across all 40 labels compared, one page is found only by us and 42 only by the category. The causes: a heading glued to the end of the previous line (Missstimmung), an entry without a language heading (Unterschützes), categories set by hand or by `{{K|…}}` labels (-e, Riese, most of the 14 Grußformel cases), and pages missing from the XML dump. The API figures in 0001 are 0.1–1 % higher, which is growth after the dump.

Part-of-speech sections by their first label:

| Label | Sections | Label | Sections |
|---|---|---|---|
| Deklinierte Form | 525,473 | Erweiterter Infinitiv | 6,569 |
| Konjugierte Form | 229,225 | Komparativ | 6,247 |
| Substantiv | 145,212 | Superlativ | 6,241 |
| Adjektiv | 18,232 | Abkürzung | 5,049 |
| Dekliniertes Gerundivum | 18,005 | Redewendung | 2,713 |
| Verb | 14,981 | Adverb | 1,521 |
| Partizip II | 14,637 | Wortverbindung | 1,245 |
| Partizip I | 14,559 | Gebundenes Lexem | 511 |

- **Several labels in one heading:** 24,292 sections, 170 combinations. Almost all are name labels as a second label after Substantiv: Toponym (11,366), Nachname (6,258), Vorname (1,659), Eigenname (536), plus Substantiv + Wortverbindung (1,546). Names are therefore inside the Substantiv counts.
- **German entries without a part-of-speech section:** 31,794. They are spelling-variant stubs: `{{Schweizer und Liechtensteiner Schreibweise|…}}` (about 20,300) and `{{Alte Schreibweise|Fluss|Reform 1996}}` (about 11,300). A structured source for the spelling-variants item.
- **Level-3 headings without `{{Wortart}}`:** 176, mostly "Schweizer und Liechtensteiner Schreibweise" and "Alte Schreibweise".
- **Heading word different from the page title:** 3,397 entries: case variants of affixes (`auto-, Auto-`), links in multi-word headings, `{{(R)}}` trademark marks.

### Heading templates

- **Nouns:** gender is a template in the heading: f 53,214, m 47,722, n 36,604, mf 6,348; variable gender nm 432, mn. 175, nf 87, fn 66, fm 62, mfn 19; plural-only nPl. 19, kPl. 17, fPl. 7, mPl. 5; `adjektivische Deklination` 2,905.
- **Verbs:** rarely labelled in the heading (unreg. 45, trans. 28, intrans. 20, refl. 9).
- **Adjectives:** indekl. 42.

### Blocks

The parts of a part-of-speech section are lines holding one template. Sections containing the block (share of all sections with that label):

| Block | Substantiv | Verb | Adjektiv | Deklinierte Form | Konjugierte Form |
|---|---|---|---|---|---|
| Worttrennung | 99.9 % | 100 % | 100 % | 100 % | 100 % |
| Aussprache | 100 % | 100 % | 100 % | 100 % | 100 % |
| Bedeutungen | 99.7 % | 100 % | 99.7 % | | |
| Herkunft | 73.1 % | 88.5 % | 53.3 % | | |
| Wortbildungen | 14.2 % | 53.0 % | 26.0 % | | |
| Alternative Schreibweisen | 8.0 % | 4.3 % | 8.5 % | 2.5 % | 2.2 % |
| Grammatische Merkmale | | | | 100 % | 100 % |
| Grundformverweis Dekl / Konj | | | | 100 % | 100 % |

- `{{Verbherkunft}}` occurs in 8,987 verb sections (60 %).
- `{{QS Herkunft}}` (Herkunft flagged as incomplete) occurs in 10,856 noun, 386 verb and 1,009 adjective sections.
- The only subsection is `==== {{Übersetzungen}} ====`.
- `{{Lautschrift}}` occurs in nearly every section, lemma or form entry. Whether it holds a transcription is checked in step 2.

### Inflection tables on lemma pages

- **Nouns:** `Deutsch Substantiv Übersicht` 122,875; `Deutsch Toponym Übersicht` 9,877; `Deutsch Nachname Übersicht` 6,253; `Deutsch adjektivisch Übersicht` 2,956; `Deutsch Vorname Übersicht m/f/n` 1,656; `Deutsch Substantiv Übersicht -sch` 513; `Deutsch Eigenname Übersicht` 419; `Deutsch Name Übersicht` 320. 399 noun sections have no table, 60 have two.
  - Arguments: the eight case-number cells and `Genus`.
  - Parallel genders: `Genus 1/2/3` with numbered singular cells; 1,650 sections have two genders.
  - Parallel plurals: `… Plural 1/2/3`; 3,074 sections have at least two plurals, 189 have three.
  - Variant forms are starred: `Genitiv Singular*` 25,178, `Dativ Singular*` 18,090.
- **Positional arguments in all lemma tables are image options**, not grammar (`|Bild=Haus.jpg|mini|1|caption`), and must be ignored.
- **Verbs:** `Deutsch Verb Übersicht` in 14,956 of 14,981 sections, with nine principal forms and `Hilfsverb`, plus starred variants (`Imperativ Singular*` 10,818, `Hilfsverb*` 792).
- **Adjectives:** `Deutsch Adjektiv Übersicht` in 18,189 of 18,232 sections: `Positiv`, `Komparativ`, `Superlativ`, starred variants, and `keine weiteren Formen` (482).

### The `Flexion:` namespace

- **Not German only:** 64,109 of the 71,985 pages (redirects excluded) have a German section. The rest are Czech, Polish, Spanish, Latin, … The language is the argument of the heading template (`{{Verbkonjugation|Deutsch}}`, `{{Adjektivdeklination|Deutsch}}`, `{{Gerundivumdeklination|Deutsch}}`), not of `{{Sprache}}`.
- **German headings:** adjective declension 41,322, verb conjugation 15,731, gerundive declension 8,643, plus a few for adverbs, numerals and pronouns. A page can hold several conjugations (laufen and fahren have two each): 1,569 pages have two level-2 sections, and 107 have three or more.
- **Coverage:** 98.5 % of verb lemma pages have a `Flexion:` page (14,374 of 14,599), as do 97.1 % of adjective lemma pages (17,731 of 18,260). Adjective declension pages also exist for participles: Partizip I 13,168, Partizip II 10,186.
- **Verb templates:** `Deutsch Verb regelmäßig` 12,039, `Deutsch Verb unregelmäßig` 3,245, `… schwach trennbar reflexiv` 301, `… schwach untrennbar reflexiv` 283.
  - The stems are positional arguments, and they are split into parts: `{{Deutsch Verb regelmäßig|ka|u|f|e|n|gekauft|…}}`; `unregelmäßig` uses up to eleven positions.
  - What each position means has to be read from the template documentation (the `Vorlage:` pages are in the dump).
  - Single forms can be overridden by named arguments (`2. Singular Indikativ Präsens Aktiv` 328 times, and so on).
  - `Teil 1` (4,548) is probably the separable particle.
- **Adjective template:** `Deklinationsseite Adjektiv` (41,353) has named stems: `Positiv-Stamm` 41,346, `Komparativ-Stamm` 6,466, `Superlativ-Stamm` 6,479; the other pages presumably use defaults. Alternatives and `-ohne-e` variants are rare.

### Form entries

- **Uniform structure:** Worttrennung, Aussprache, Grammatische Merkmale and `{{Grundformverweis Dekl|…}}` or `{{Grundformverweis Konj|…}}` are present in practically all form entries.
- **zu-forms:** the form-entry types include Dekliniertes Gerundivum (18,005) and Erweiterter Infinitiv (6,569). Nearly all are single words, because `zu` is infixed in separable verbs: `aufzuwärmende`, `aufzustocken`. Only 80 and 23 titles contain a space.

### Markup quality

45 part-of-speech sections, out of about a million German ones, have unbalanced `{{ }}` or `[[ ]]`.

### Consequences of step 1

- Section and part-of-speech parsing is not a risk. It reproduces the categories exactly except for a handful of broken pages, which become fixtures.
- **Verb stems** need the positional arguments of the four German verb templates decoded from their documentation. That is the first task of step 2, since the gate depends on it.
- **Names share `Substantiv` sections** with a second label. Decided since: the name labels are not parts of speech, and they mark named entities on the lexical unit ([0003](decisions/0003-named-entities.md)). See [proper nouns](#proper-nouns) for the first approach and [named entities](#named-entities) for the current one.
- **zu-infinitives and declined gerundives** are single words. Decided since: they are not stored, Partizip I is derivation, and declined Partizip II forms are stored only for adjective lexemes ([0004](decisions/0004-participles-and-zu-forms.md)).
- The spelling-variant stubs and the variant blocks (`Alternative Schreibweisen`, `Nebenformen`, `Nicht mehr gültige Schreibweisen`) together cover the spelling-variants item.

## Proper nouns

**Superseded.** This tested the first version of [0003](decisions/0003-named-entities.md), in which proper nouns were a part of speech of their own. That version was revised on 2026-11-25; see [named entities](#named-entities). This section is kept as a record. The `proper-nouns` subcommand has been removed; the commands below run at commit `dcc2a95`.

Can proper nouns be told from common nouns by Wiktionary's part-of-speech labels? Rule under test: a section is a proper noun if one of its labels is a name label (`Toponym`, `Nachname`, `Vorname`, `Eigenname`, `Göttername`, `Bauwerksname`, `Straßenname`), and a common noun if it is labelled `Substantiv` without one.

```sh
uv run python extract/scripts/feasibility.py proper-nouns --date 20261101              # 10 s
uv run python extract/scripts/feasibility.py proper-nouns --date 20261101 --evaluate   # after annotation
```

The rule gives 21,264 proper-noun sections and 124,972 common-noun sections.

### Method

- **Sample:** 500 sections drawn at random from each class (seed 20261124) and shuffled together.
- **Blind annotation:** each item showed only the title and the senses, without labels, table or the rule's class. Four separate Claude agents annotated 250 items each, following a written guideline with the definition above and a list of borderline classes to flag rather than decide. The categories were proper, common, mixed, or unclear.
- **Adjudication:** every item where the annotation disagreed with the rule, or that was flagged as borderline (40 of 1,000), was adjudicated by Claude in this session.
- **Human review:** after adjudication, the user reviewed `adjudicated.tsv` ([conclusion](#conclusion)). The sample, the annotation and the adjudication are in `data/interim/feasibility/proper_nouns/`: `sample.tsv`, `sample_key.tsv`, `annotation.tsv` and `adjudicated.tsv`.

### Results

The adjudication left 11 items in borderline classes: language names, taxa, a cultivar and descriptive designations. These classes were then decided in the first version of 0003, and the table counts them accordingly. The `decided` column of `adjudicated.tsv` holds the class of each adjudicated item under that version.

| Rule says | Proper | Common | Mixed | No senses |
|---|---|---|---|---|
| proper noun (500) | 494 | 1 | 4 | 1 |
| common noun (500) | 11 | 486 | 3 | 0 |

- **Precision is high:** 494 of 500 detected proper nouns are proper nouns (98.8 %, 95 % interval 97.4–99.4 %).
  - The one false positive is a potato variety (Idiafrit). Cultivars are common nouns under 0003.
  - The rest are four mixed sections and one entry without senses. The mixed sections are Ben (given name and the name particle) and Buick, Ferrari and Maserati (the manufacturer and a car of that make).
- **Recall is lower.** 11 of 500 common-noun sections are proper nouns without a name label:
  - 5 clear names: Xetra, Trasimenischer See, Rheingau, Dornberg, and DVPA (a party abbreviation);
  - 4 language names: Dzongkha, Banda, Estnisch, Inupiaq;
  - 2 descriptive designations: Covid-19-Pandemie, Rheineinzugsgebiet.

  Extrapolated, that is 2.2 % of the class (1.2–3.9 %), or about 2,750 missed proper nouns (1,540–4,870). Recall of the labels alone is about 88 % (81–93 %). Before the classes were decided, only the 5 clear names counted as misses, which gave about 94 %.
- **The misses carry almost no signal in the markup.**
  - Of the clear names, only Xetra has a name table, and only Trasimenischer See a name-shaped definition. Better rules on the markup will not close the gap.
  - Language names are the exception, since their first meaning line usually calls them a language.
    - A pattern requiring that line to be headed by `Sprache`, `-sprache` or `Varietät` finds 453 sections. In a check of 40 of them, 37 were language names.
    - In the sample it catches 3 of the 4 language names and no common noun. It misses Inupiaq, `in Alaska gesprochene Varietät …`, because a capitalised word comes before the head noun.
    - The pattern became part of the label rule in the first version of 0003, and was dropped with the revision.
  - **With the pattern,** about 2,330 proper nouns are missed (1,120–4,450), for a recall of about 90 % (83–95 %). Precision stays at about 99 %. These figures count the pattern's hits in the whole class (453, about 92 % correct) rather than extrapolating its 3 hits in the sample.
- **Mixed sections:**
  - 3 common-noun sections (0.6 %, about 750 in the class): Zwilling (the constellation), Goldenes Kalb (the biblical idol), Reformation (the historical movement).
  - 4 proper-noun sections (0.8 %, about 170).
  - Labels on single senses (`{{K|Eigenname}}`, `{{K|Toponym}}`) mark only 10 sections in the whole dump, so mixed sections are almost never marked.
- **The borderline classes needed a rule.** The annotators were inconsistent on taxa, so case-by-case judgment was not enough. In the common-noun sample, language names came to 4 in 500 (about 1,000 in the class) and taxa to 3 (about 750).
- **Abbreviated names:** among the 303 sections labelled `Abkürzung` + `Substantiv`, about half name organisations (TÜV, ADAC, ISO, NSA, AfD). The rule classifies them all as common nouns. Another 4,878 sections are labelled `Abkürzung` alone and are outside the noun population altogether. They are handled by [0005](decisions/0005-abbreviations.md).

### Conclusion

The labels are a reliable base: what they mark as a proper noun is one. They do not reach high recall on their own: about 10 % of proper nouns end up among the common nouns even with the language pattern, and mixed sections cannot be found from the markup.

This led to the first version of 0003, with the label rule plus the language pattern, and to [0006](decisions/0006-language-model.md), an optional language model for the rest. On review of `adjudicated.tsv`, the user concluded that properness cannot be decided for a lemma without context. Both decisions were revised on 2026-11-25: 0003 now records [named entities](#named-entities), and 0006 is withdrawn.

## Named entities

The basis for the revised [0003](decisions/0003-named-entities.md): senses that Wiktionary marks as names get the head noun of their definition in the field `named_entity` ([definition](features/named-entities.md)).

**This was an exploratory measurement,** made with ad-hoc scripts that are not part of the feasibility driver. Inflected heads were approximated by stripping endings and matching noun titles, since the word-form table does not exist yet. It is to be repeated with the definition parser of M3.

**Marked sections:** 21,637, with 24,625 senses (meaning lines with a sense number).

| Marked by | Sections |
|---|---|
| name label | 21,236 |
| name table only | 396 (mostly language names) |
| `{{K}}` name label only | 5 |

- **Hypernyms are too sparse to serve as the value.** `Oberbegriffe` cover 40 % of the marked senses: 60 % of `Toponym` senses, 41 % of `Eigenname` senses, and almost no given or family names.
- **Definition heads cover nearly everything:**
  - the head is a noun lemma for 96.8 % of senses;
  - an inflected form of one for 2.3 %;
  - there is no head (`unspecified`) for 1.0 %.

  Passing over "name" and "form" heads changed 1.9 % of senses. There are 1,254 different heads. The most frequent are Nachname 5,463, Stadt 3,850, Vorname 1,647, Ortsteil 1,083, Gemeinde 833, Familienname 807, Stadtteil 769, Ort 763, Hauptstadt 491 and Fluss 411.
- **A check of 60 random senses found 4 wrong heads:**
  - 3 came from a phrase before the head: `Landkreis` for `im Landkreis Konstanz … gelegene Gemeinde`, `Süden` for `den Süden Vietnams … umfassende Region`, and `Gode` for `eine 1951 von Alexander Gode geschaffene Plansprache`;
  - 1 came from nested parentheses in a `{{K}}` label, a bug in the exploration script.

  A fifth head, `Form` for `weibliche Form des Familiennamens Kostow`, led to adding `Form` and `Toponym` to the heads that give way to the next noun.
- **Section labels do not hold for every sense,** which is why the head comes from each sense's own definition. The section of Venus is labelled `Göttername`, but its first sense is the planet. Freia, a given name, also has an asteroid sense. Danzig is a city and an asteroid.
- **Sections with only name labels:** 88 (Englisch, Greenpeace, DDR, Miraculix). They are given `Substantiv`.
- **Types were tried and are not needed.**
  - A draft list of 472 head nouns, mapped to types, typed 95.1 % of marked senses without a language model. Compounds matched by their last part (Hafenstadt as Stadt).
  - Where a sense had both a hypernym and a head (9,017 senses), the two gave the same type in 98.1 %.
  - This showed that no language model is needed. Types are left to the analyses.

## Abbreviations

A survey of the sections labelled `Abkürzung`, for [0005](decisions/0005-abbreviations.md).

```sh
uv run python extract/scripts/feasibility.py abbreviations --date 20261101   # 5 s
```

5,191 German sections carry the label. Results are in `data/interim/feasibility/abbreviations/`.

| Spelling | Sections | With IPA |
|---|---|---|
| abbreviation period (`Einw.`, `e. V.`) | 1,760 | 170 |
| all capitals (`KKW`, `UWG`) | 1,871 | 534 |
| mixed case (`Lkw`, `GmbH`, `BeurkG`) | 1,068 | 112 |
| spaces, no period (mostly E numbers: `E 401`) | 332 | 64 |
| lower case (`km`) | 97 | 27 |
| single letter | 63 | 34 |

- **Part of speech:** of the 4,878 sections labelled only `Abkürzung`, 157 have a gender in the heading. The other 4,721 have no signal of a part of speech in their markup at all.
- **IPA on period abbreviations** transcribes the full word: `Temp.` has `tɛmpəʁaˈtuːɐ̯`, `preuß.` has `ˈpʁɔɪ̯sɪʃ`. The IPA test of 0005 cannot apply to them.
- **All capitals:** 1,337 of the 1,871 sections have no IPA. Many are short stubs whose only content is the expansion (`LPD`, `BBL`, `UWG`), and probably spoken letter by letter. So a missing transcription is a weak sign that a word is read as the full word.
- **Codes:** vehicle registration codes (`MIL`, `RE`), unit symbols (`MHz`, `Lj`) and E numbers are among the sections.
