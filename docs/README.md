# docs

- [`roadmap.md`](roadmap.md): the milestones of release 1 (the extractor) and a short note on what follows it.
- `schema/`: the data dictionary. Start with [`schema/profile.md`](schema/profile.md), the list of what the database must contain. Later: every table and column of a data release.
- `features/`: the linguistic definition of each extracted feature, and how it is derived from Wiktionary markup. [`features/segmentation.md`](features/segmentation.md) defines the boundary symbols used everywhere; [`features/part-of-speech.md`](features/part-of-speech.md) defines proper nouns and the handling of abbreviations.
- `decisions/`: short records of design decisions, one file per decision. [`decisions/0001-extraction-strategy.md`](decisions/0001-extraction-strategy.md) explains why we write our own extractor; [`decisions/0002-lexeme-model.md`](decisions/0002-lexeme-model.md) defines lexemes, senses and lexical units.
- [`open-questions.md`](open-questions.md): points that need discussion before the affected part is implemented.
- [`feasibility.md`](feasibility.md): results of the feasibility test that gates M1.
