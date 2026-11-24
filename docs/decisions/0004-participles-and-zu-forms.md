# 0004: Participles, zu-infinitives and gerundives

Date: 2026-11-24

## Decision

1. **Partizip I is derivation, not inflection.** `-end` is a derivational suffix that forms adjectives (`bedeut:end`). The Partizip I is therefore not a word form of the verb, and Wiktionary's `Partizip I` sections, which are form entries, are not extracted.
2. **An `-end` word is a lexeme only if Wiktionary lists it with its own meaning.** The suffix is productive and its result predictable, so a lexeme of its own is justified only where the meaning is not predictable. The signal is that Wiktionary gives the word a lemma section with its own senses (`Adjektiv`, `Adverb`, `Präposition`, …). Such words are complex lexemes, and their declined and compared forms are their word forms.
3. **Partizip II is an inflected form of the verb** (`ge-kauf-t`) and is stored in the verb's word-form table. The periphrastic perfect and passive are generated from it.
4. **Declined Partizip II forms follow rule 2.** `gekaufte` and `gekauftem` are stored only as word forms of an adjective lexeme that Wiktionary lists with its own meaning (`verliebt`, `verrückt`). Otherwise they are not stored.
5. **zu-infinitives and gerundives are not stored**, like periphrastic forms: Wiktionary's `Erweiterter Infinitiv` entries (`aufzustocken`), its `Dekliniertes Gerundivum` entries (`aufzuwärmende`) and the `Flexion:…/Gerundivum` pages. They can be generated on demand, like the periphrastic forms, even where `zu` is written inside the word.

## Extent in the dump of 2026-11-01

| | Pages |
|---|---|
| `Partizip I` form entry only | 14,151 |
| `Partizip I` and a lemma section with its own senses (bedeutend, reizend, anscheinend, während) | 231 |
| `Adjektiv` ending in `-end` without a `Partizip I` section | 369 |
| `Partizip II` form entry only | 13,604 |
| `Partizip II` and an `Adjektiv` section (verliebt, dezidiert) | 982 |
| `Erweiterter Infinitiv` / `Dekliniertes Gerundivum` entries | 6,568 / 18,005 |

The 369 `-end` adjectives without a `Partizip I` section are mostly compounds (krebserregend, körnerfressend), but some contain no participle at all (horrend, stupend, abertausend). Segmentation must therefore not split off `-end` by its spelling alone; it follows the word-formation analysis in M2.

## Consequences

- The word-form table of a verb holds no Partizip I and no zu-forms.
- The generator for periphrastic forms in the user interface also produces zu-infinitives and gerundives.
- Where Wiktionary lists both a `Partizip II` section and an `Adjektiv` section for one spelling, they are two lexemes, as [0002](0002-lexeme-model.md) requires: the verb form and the adjective.
