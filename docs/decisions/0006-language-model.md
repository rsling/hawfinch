# 0006: Optional local language model (withdrawn)

Date: 2026-11-24, withdrawn 2026-11-25

**Withdrawn.** This decision let the extractor use an optional local language model served by `llama-server`. Its first use was to classify noun senses as proper or common, under the first version of [0003](0003-named-entities.md). It also covered the part of speech of sections labelled only `Abkürzung`.

0003 now records named entities from Wiktionary's own marking and the heads of its definitions. No part of the extractor needs a model any more, so:

- the extractor has no model configuration;
- release manifests record no model;
- no answer cache is kept.

The full text is in the git history.

A language model remains one option among others for [sense identifiers](../open-questions.md#stable-identifiers-for-word-senses-required), with no decision taken.
