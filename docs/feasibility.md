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

| Spelling | Sections | With IPA | Lexemes | Stubs |
|---|---|---|---|---|
| abbreviation period (`Einw.`, `e. V.`) | 1,760 | 170 | | 1,760 |
| all capitals (`KKW`, `UWG`) | 1,871 | 534 | 691 | 1,180 |
| mixed case (`Lkw`, `GmbH`, `BeurkG`) | 1,068 | 112 | 133 | 935 |
| spaces, no period (mostly E numbers: `E 401`) | 332 | 64 | | 332 |
| lower case (`km`) | 97 | 27 | | 97 |
| single letter | 63 | 34 | | 63 |

The last two columns apply the rule of 0005: a lexeme is in all capitals or mixed case and has an IPA transcription, a noun table, a gender in the heading or a second part-of-speech label. All other spellings are stubs whatever they contain; 22 of those sections have a noun table, a gender or a second label (`k. o.`, `dpa`, `kcal`, twelve letter names).

- **Part of speech:** of the 4,878 sections labelled only `Abkürzung`, 157 have a gender in the heading. The other 4,721 have no signal of a part of speech in their markup at all.
- **IPA on period abbreviations** transcribes the full word: `Temp.` has `tɛmpəʁaˈtuːɐ̯`, `preuß.` has `ˈpʁɔɪ̯sɪʃ`. An IPA test cannot apply to them.
- **A missing IPA says little.** 1,337 of the 1,871 sections in all capitals have none. Many are short entries whose only content is the expansion (`BBL`, `UWG`), and they are probably spoken letter by letter.
- **Lexemes (824):**
  - 643 have an IPA transcription. The other 181 have a noun table, a gender or a second label only (`BaFin`, `DIN`, `KMK`, `HJ`).
  - 444 have a part-of-speech signal (a second label, a name label or a gender), and 85 more have a noun table. 295 have neither and are `Substantiv` by default.
- **Stubs in all capitals or mixed case (2,108):**
  - 872 have at most one sense, no audio file and no example. Many are abbreviations of laws (`BBodSchG`, `TabakStG`).
  - 504 have an audio file and 754 an example. Real short words are among them: `DWD`, `ASB`, `THG`, `IgG`, `KKH`.
- **Vehicle registration codes** are recognised by `Kennzeichen` or `Unterscheidungszeichen` in the meaning line. 7 sections with a signal consist of such senses only (`AS`, `WL`) and count as stubs above. 38 lexemes have such a sense beside others (`AU`, `MD`). Of the stubs, 95 are registration codes only.
- **Other codes:** unit symbols (`MHz`, `Lj`, `km`) and E numbers are stubs by their spelling or for lack of a signal.

## Step 2: coverage

Whether each item of the [profile](schema/profile.md) can be read from the dump, measured item by item. So far: verb stems.

### Verb stems

Can the stems of a verb be read from the template arguments on its `Flexion:` page, without expanding the template? The test reads every conjugation, derives the stems, generates the principal forms from them and compares these with `Deutsch Verb Übersicht` on the lemma page. The two sources are written independently by Wiktionary's editors.

```sh
uv run python extract/scripts/feasibility.py verbs --date 20261101   # 2 s
```

The reader and the generator are in `hawfinch.features.inflection`; results are in `data/interim/feasibility/verbs/`.

#### What the arguments mean

Read from the documentation pages of the templates (`Vorlage:Deutsch Verb …/Doku`) and, for the rules that build the forms, from the template code.

| Template | Conjugations | Arguments |
|---|---|---|
| `Deutsch Verb regelmäßig` | 12,039 | `1`–`5`: the infinitive cut into five pieces, the last four letters separately (`ka\|u\|f\|e\|n`; `ch` counts as one letter). `6`: Partizip II. `Teil 1`, `Teil 2`: separable parts. `haben`: any value means `sein`. |
| `Deutsch Verb schwach untrennbar reflexiv` | 283 | The same six positions. |
| `Deutsch Verb schwach trennbar reflexiv` | 301 | The particle first, then the same six. |
| `Deutsch Verb unregelmäßig` | 3,245 | `1`: particle. `2`: present stem. `3`: preterite, first person singular. `4`: subjunctive II stem. `5`: Partizip II without the particle. `6`: present stem of the second and third person singular. `7`: stem-final behaviour (`e`, `e-`, `e2`, `em`, `-s`). `8`: `i` for the e/i change, `n` for mixed inflection. `9`, `11`: alternative subjunctive II stem and preterite. `10`: infinitive of a modal verb, `tun` or `wissen`. `T2`: second particle. `ViD`: spelling of the particle when separated (`Brust`). `Wv`: written as several words (`Rad fahren`). |

- Single forms can be replaced by named arguments. In the templates for weak verbs the value is the whole form with its pronoun and particle (`du rutschst ab,<br />du rutscht ab`); in `unregelmäßig` it is the bare verb.
- Switches remove groups of forms: `unpersönlich`, `Imperativ=0`, `Präsens Aktiv=0`, and `Hauptsatzkonjugation=0` for verbs without finite forms in main clauses (`bausparen`).
- All 15,868 template calls could be read. Positional and numbered arguments are mixed freely (`aus|2=kenn`), which the template scanner handles as MediaWiki does.

#### Stems

- **Weak verbs** have one stem: the infinitive without `-en`, or without `-n` after `el`, `er`, `ie` and `ee` (`sammel`, `wander`, `knie`, `tee`).
- **Strong and irregular verbs** give four stems directly: present (`geb`), present of the second and third person singular (`gib`), preterite (`gab`) and subjunctive II (`gäb`).
  - Of the 3,245 conjugations, 13 have one distinct value among the four, 810 two, 1,602 three and 820 four.
  - The Partizip II is given as a word. A participle stem (`ge-sung-en` → `sung`) is derived by removing the particle, `ge-` and the suffix. It differs from all four other stems in 840 conjugations.
  - Mixed verbs give the preterite with the weak suffix (`dachte`); the stem `dach` is derived by removing it (203 conjugations).
- **Stems stored** (decided on 2026-11-25): present, present of the second and third person singular, preterite and participle. The subjunctive II stem is not one of them, because it mostly follows from the preterite stem: it is the same or differs only by umlaut (`gäb` from `gab`).
- **Variant stems** go into a table of their own, one row per stem, with the lexeme, the stem field, the stem and the conjugation class. `variants.tsv` has 712 rows for 490 conjugations:

  | Source | Field | Rows | Examples |
  |---|---|---|---|
  | Same conjugation | subjunctive | 275 | `würf` (`warf`), `stünd` (`stand`), `renn` (`rann`, for `rennte`) |
  | Same conjugation | preterite | 45 | `hub` besides `hob`, `schwomm` besides `schwamm` |
  | Same conjugation | 2nd/3rd singular | 1 | `gebär` (`gebärst` besides `gebierst`) |
  | Parallel conjugation | preterite | 190 | `frug`, weak `back` besides `buk` |
  | Parallel conjugation | participle | 142 | `sog`, `schrock` |
  | Parallel conjugation | 2nd/3rd singular | 44 | `back` besides `bäck` |
  | Parallel conjugation | subjunctive | 15 | `send` |

  - Subjunctive stems are listed only if they follow from none of the preterite stems: `hüb` follows from `hub` and is not listed. The table does not say whether such a stem is the only one (`würfe`) or a variant (`stünde` besides `stände`). This is intended.
  - A parallel conjugation is a later conjugation on the same page with the same particles and reflexivity. Its stems are listed where they differ from the first one's. 166 of these rows come from a weak conjugation beside a strong one, where the stem is the present stem and the difference is the class.
  - A second Partizip II with the same stem is not a variant stem (`gesalzt` besides `gesalzen`, `viergeteilt` besides `gevierteilt`). Such forms are stored as word forms only.
  - Single forms that are not built on a stem of the verb (`beutst`, `ward`) are not stems either.
- **Conjugation class** is read from the template and its arguments: 12,623 weak, 2,929 strong, 203 mixed, 113 irregular (the modal verbs, `wissen`, `tun`, `sein`, with their prefixed and particle verbs). Mixed stems need it: `dach` gives `dachte` only with the class.
- **Particles** are explicit in every template, so `ab=kauf` needs no list of particles. 7,230 conjugations are separable.
- **Inseparable prefixes** are not arguments of the templates, so they are split off by rule: `ver:bleib`, `ent:mann`, `an=er:kenn`.
  - A stem has a prefix if it begins with `be`, `emp`, `ent`, `er`, `ge`, `miss`, `ver`, `zer`, `durch`, `hinter`, `über`, `um`, `unter` or `wider`, the rest contains a vowel, and the Partizip II has no `ge-` (`verblieben`; but `gebettelt`, `geerbt`, `gegeben`).
  - Weak verbs in `-ieren` never have `ge-`. They are split only if the rest is the stem of a verb without prefix and particle (`ver:barrikadier`, but `verifizier`, `zertifizier`, `erodier`). This misses verbs whose base is not in Wiktionary (`entstalinisier`, `verabsolutier`).
  - The same condition holds for `ge`, which often belongs to the base (`gestalt`, `geduld`). So `ge:hör` and `ge:fall` are split, and opaque verbs are not (`gewinn`, `gescheh`, `gebär`). A few are still split wrongly, because the rest happens to be a verb: `ge:sund`, `ge:wicht`, `ge:witter`, `ge:fährd`.
  - 3,475 conjugations get a prefix: `ver` 1,174, `be` 916, `er` 383, `ent` 284, `über` 195, `zer` 147, `um` 112, `durch` 81, `unter` 77, `ge` 62, others 44. In 547 of them the rest is not itself a verb (`ver:gold`, `be:auftrag`, `ent:larv`).
  - The stem fields hold the stems without the prefix, as they do without particles: `geh`, `ging`, `gang` for `ver:geh` as for `ab=geh`. The 3,237 strong, mixed and irregular conjugations then share 224 sets of stems; the most frequent are those of `gehen` (97 conjugations), `stehen` (92), `ziehen` (91) and `kommen` (91).
  - Only one prefix is split off, and only native ones. Prefixes of loan verbs (`de:mobilisier`) cannot be recognised by form (`dekorier`, `regier`); they are left to the Herkunft analysis of M2.
- **`sein`** has placeholder stems in the template, because its present forms are all given one by one (9 conjugations with its combinations `ab sein`, `dabei sein`). It gets the stems `s` (`sind`, `seid`, `sei`, `ist`), `b` (`bin`, `bist`), `w` and the participle stem `wes`.
- A further 11 conjugations have real stems and give single forms besides them, as variants (`gebären`: `gebierst` and `gebärst`; `bieten`: `beutst`; `werden`: `ward`) or as gaps (`schwären` has no imperative).

#### Agreement with the overview tables

A lemma page can hold several verb sections and a `Flexion:` page several conjugations (trennbar and untrennbar, weak and strong, reflexive, `haben` and `sein`). Each overview table is paired with the conjugation of the same page name that reproduces most of its forms. Of the 14,977 overview tables, 205 have no `Flexion:` page with a German verb template; the other 14,772 are compared.

| | Tables | Share |
|---|---|---|
| All eight main forms generated, variants identical | 9,785 | 66.2 % |
| All eight main forms generated, variants differ | 4,768 | 32.3 % |
| At least one main form not generated | 219 | 1.5 % |

- **98.5 % of the tables are reproduced** from the stems in their main forms.
- **Variants differ** mostly because the conjugation lists more of them than the overview table: `sammle`, `sammele` and `sammel`, or both imperatives `kauf` and `kaufe`. Variants are not a test of the stems.
- **The 219 tables that differ** contain 404 differing forms; they are listed in `mismatches.tsv`.
  - In 151 forms the table has a dash where the conjugation has a form, and in 30 the reverse. These are verbs restricted to the third person or without an imperative, marked on one side only (`killen`, `reifen`, `verölen`).
  - In 223 forms both sides have a form. They have not been adjudicated one by one. About 70 were read; most are slips in the overview table (`holzte herum` as present, `fahre kaputt` as subjunctive II, a form in the wrong cell). A few are loan words where the template's rule and the editors disagree (`designest` or `designst`, `tiltet` or `tilt`).
  - No class of verbs stands out: the share of differing tables is between 0 and 2.7 % in every class except two. Mixed verbs have 8 of 180 (`rannte` entered where the table should have `rennte`, `wandte` beside `wendete`). Modal verbs, `tun` and `wissen` have 14 of 103, mostly the variant `tu` beside `tue` and imperatives of modal verbs.
- **The auxiliary differs in 115 tables** (0.8 %).
- **Conjugations without a table of their own:** 1,245 of the 15,868 are not the best match of any overview table.
  - 1,094 have the same stems as a paired conjugation on the same page. They are the reflexive conjugation or the second auxiliary of the same verb.
  - 151 have other stems. These are parallel weak and strong conjugations (`fragen` with `frug`, `saugen` with `sog`) which the lemma page shows as starred variants in one table.

#### Sample for checking

`sample.tsv` holds 117 conjugations: nine drawn at random (seed 20261125) from each of thirteen classes, with the lexeme stem, the stems as they were then, the participles and the auxiliary, one conjugation per line. The columns `correct` and `comment` are filled in by hand.

Checked by the user on 2026-11-25, before the changes it led to:

- **111 of 117 conjugations are correct.** The six wrong ones are all combinations with `sein` (`ab sein`, `dafür sein`), which showed the template's placeholder stems. They now have `s`, `b`, `w`, `wes`.
- **19 lexeme stems lacked the boundary after an inseparable prefix** (`verbleib` for `ver:bleib`). The rule above now marks 18 of them; `de:mobilisier` is left to M2.
- **Class labels** called strong verbs with single forms given (`gebären`) and mixed verbs irregular. The labels are now `strong, single forms given` and `mixed`.
- **Spelling variants** are separate conjugations: `zutage fördern` and `zu Tage fördern`, `zugrunde richten` and `zu Grunde richten`. Of 70 verbs written as several words, 7 pairs differ only in spaces or capitals, and 30 also have a page written as one word (`bekanntgeben`). See the open questions.
- **Combinations with `sein`** (`ab sein`, `dabei sein`) are a copula with a predicative element, not verbs. The 8 conjugations written as several words whose verb is `sein` are left out of the stem table; the sample then has 111 rows.

A rerun keeps the annotated rows (`sample.annotated.tsv`) and shows them with their current values.

#### Consequences

- **The gate is passed for verb stems.** They are read directly from the arguments, and the forms generated from them agree with an independent source in 98.5 % of the tables. The remaining tables are inconsistencies between two Wiktionary pages more often than faults of the reader, and become a validation report.
- **The generator is needed anyway:** M1 generates missing single-word forms from stems. The present version covers the eight principal forms; the full paradigm follows the same rules.
- **Open points** are recorded in [open questions](open-questions.md#verb-stems): spelling variants of verbs written as several words, combinations with `sein`, prefixes of loan verbs.
