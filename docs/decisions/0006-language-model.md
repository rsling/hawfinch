# 0006: Optional local language model

Date: 2026-11-24

## Context

Some distinctions the database needs cannot be read off Wiktionary's markup. The first is proper versus common noun at the level of single senses ([0003](0003-proper-nouns.md)). The label rule misses names without a name label, and mixed sections are almost never marked ([feasibility results](../feasibility.md#proper-nouns)).

## Decision

1. The extractor can use a local language model served by `llama-server` (llama.cpp). Using it is optional: without one, the rule-based detection is used and its lower accuracy is accepted. Release builds for publication are expected to use a model.
2. The model is set in the extractor's configuration. The default entries are:
   - server: `http://classyboudoir:8080`
   - model: `unsloth/Qwen3.5-122B-A10B-GGUF:UD-Q4_K_XL`

   Anyone building a release can remove the server and go without a model, or configure a smaller one.
3. **First use:** classifying the senses of noun sections as proper or common ([0003](0003-proper-nouns.md)). This covers names without a name label and mixed sections, which are split. The same classification gives a part of speech to sections labelled only `Abkürzung` ([0005](0005-abbreviations.md)).

## Consequences

- **No silent fallback.** If a server is configured but cannot be reached, the run stops with an error. Falling back to the label rule would change the part of speech of thousands of lexemes without notice. To build without a model, remove the server from the configuration.
- **Answers are cached** per section text, model and prompt version, under `data/interim/`, and requests are sent with temperature 0. A re-run on the same dump sends no requests. A newer dump only sends requests for sections whose text changed.
- **The release manifest records the mode.** That is either "label rule only", or the model with its quantisation and the prompt version (`unsloth/Qwen3.5-122B-A10B-GGUF:UD-Q4_K_XL`).
  - The model is taken from what the server reports, because `llama-server` answers with whatever model it was started with. If that is not the configured model, the run stops.
  - The manifest does not record the server address.
- **Evaluation:** before a model's classifications go into a release, they are measured against the 1,000 sections annotated in the feasibility test, with the classes of 0003 applied. Their precision and recall go into the validation report.
- The configuration file does not exist yet. It is created, with the defaults above, together with the first code that reads it in M1.
- The same server may later be used for [sense identifiers](../open-questions.md#stable-identifiers-for-word-senses-required).
