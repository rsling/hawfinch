# Patches

Tables that pin data from Wiktionary where extraction by rule is not feasible. The definition, the format and the coverage check are in [0007](../../docs/decisions/0007-patches.md).

One TSV file per patch. The columns are the key, the values, `comment` and `dump`. Rows are identified by content, so a row stops matching when Wiktionary changes the case it names.

- `flexion-sections.tsv`: which verb sections of a lemma page a conjugation of its `Flexion:` page goes with, where the rule leaves it undecided.
