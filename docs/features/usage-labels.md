# Usage labels

Wiktionary marks senses that are archaic or restricted to a region. Release 1 uses these marks for one thing: to leave entries out of the database.

The rule is the user's (2026-11-26).

## Rule

**A part-of-speech section is left out if every one of its senses is marked as archaic, regional, Austrian or Swiss.** It gives no lexeme, no senses and no word forms.

- **A section with at least one unmarked sense stays**, with all its senses. The marked senses keep their labels: the lexical unit records which of the four kinds it carries.
- **The rule holds for every part of speech.**
- **A qualified label does not count** (`besonders österreichisch`, `sonst veraltet`): it says that the sense is also in use elsewhere, or otherwise.
- **The four kinds are not told apart** for the rule: a section with one Swiss and one South German sense is left out (`Aaser`).
- **A section without sense lines** is not left out.

## Kinds of label

| Kind | Values |
|---|---|
| Archaic | `veraltet`, `veraltend` and their abbreviations (`va.`, `vatd.`, `Bedva.`, `tlwva.`), `archaisch`, `altertümlich`. Not `historisch`, which marks things of the past, not words of the past. |
| Regional | `regional`, `landschaftlich`, `mundartlich`, `dialektal`, the names of dialects and regions (`bairisch`, `norddeutsch`, `Sachsen`, `Luxemburg`), and their abbreviations |
| Austrian | `österreichisch`, `Österreich`, and the names of Austrian regions (`Wien`, `Tirol`, `Vorarlberg`) |
| Swiss | `schweizerisch`, `Schweiz`, `Liechtenstein`, `CH&LI` |

The list of regional values was compiled from the values that occur in the dump of 2026-11-01. It is not complete, and a new value in a later dump is not recognised.

## Derivation

1. Take the lines of the block `Bedeutungen` that give a sense (`:[1] …`).
2. Read the labels of each line. They come in three forms:
   - arguments of `{{K|…}}`: `{{K|Schweiz|ugs.}}`;
   - label templates without named arguments: `{{österr.}}`;
   - italic text at the start of the line: `''bairisch-österreichisch, salopp:''`.
3. Drop the labels of a `{{K}}` or of an italic text that also holds a qualifier: `besonders`, `auch`, `meist`, `sonst`, `oft`, `häufig`, `vor allem`, `überwiegend`, `vorwiegend`, `teilweise`, `teils`, `außer`, `allgemein`.
4. The section is left out if every sense line has at least one label left.

The rule is applied in one place, `hawfinch.features.selection`, and not in the readers of the single features. It gives the part-of-speech sections of a lemma page with the labels of their senses, and every reader takes its sections from there.

## Verbs

Verb stems are read from `Flexion:` pages, the senses are on the lemma page, and a `Flexion:` page does not say which verb section of the lemma page a conjugation belongs to. The conjugations of a page are therefore left out only if all verb sections of the lemma page are. Where some verb sections are left out and others stay (51 lemma pages), all conjugations are kept for now.

## Limits

- **Regional and archaic forms in unmarked entries are not found.** `Wägen` beside `Wagen`, `Smokinge` beside `Smokings` and `Stäte` beside `Staaten` are plurals in the noun table of an entry without a mark; if anything, a note in prose says where or when they are used. They are taken as they stand in release 1, and are candidates for a patch list. They need inspection by hand during the analyses.
- **Entries that Wiktionary does not mark are not found** either: the rule takes Wiktionary's marking without heuristics.

## Numbers

In the dump of 2026-11-01, 5,677 of 190,876 lemma sections with senses are left out (3.0 %): 3,525 noun, 1,134 verb, 487 adjective and 531 other sections. A further 2,921 sections have a label on some senses, and 608 have only qualified labels. See the [feasibility test](../feasibility.md#usage-labels).
