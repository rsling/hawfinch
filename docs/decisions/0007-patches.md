# 0007: Patches

Date: 2026-11-26, extended 2026-11-27

## Context

The extractor reads Wiktionary's markup without heuristics. In some places the markup does not contain what is needed, or contains it ambiguously, and no rule can recover it. Two cases came up in the feasibility test:

- a `Flexion:` page does not say which verb section of the lemma page a conjugation belongs to ([usage labels](../features/usage-labels.md#verbs));
- regional and archaic plurals in the noun table of an unmarked entry (`Wägen`, `Smokinge`) carry no mark ([usage labels](../features/usage-labels.md#limits)).

Until now the documents spoke loosely of "patch lists" for such cases. This decision defines the term.

Points 1 to 3 are the user's definition (2026-11-26). Points 4 to 7 were proposed by Claude and accepted by the user (2026-11-27).

## Decision

1. **A patch is a table that we create.** It does one of three things to data from Wiktionary where automatic extraction is not feasible:
   - it **filters** the data (removes items);
   - it **amends** the data (adds or corrects items);
   - it **makes the data unambiguous** (chooses among readings that the markup leaves open).
2. **A patch pins data to what we have decided, regardless of what Wiktionary says.** Where a patch has a row, its content goes into the release, and the markup is not consulted for that item.
3. **Before each data release, every patch table is checked for full coverage** of the relevant cases in the new Wiktionary snapshot. The extractor finds the relevant cases of the new snapshot by rule; a case without a row in the patch stops the release until the row is written.
4. **Storage:** one TSV file per patch in `extract/patches/`, tracked in git. Patches are our own work, not derived from a dump, so they do not go under `data/`.
5. **A row is identified by content, not by position.** The key columns name the case as it appears in the dump: for a conjugation, the page title, the preterite, the participle, the auxiliary and whether it is reflexive. Section numbers and the order of templates shift between dumps. When Wiktionary changes the content, the row stops matching, and the check reports it.
6. **Columns:** the key, then the values, then `comment` (why the row says what it says) and `dump` (the snapshot the row was checked against).
7. **The check reports three things:**
   - `missing`: relevant cases without a row. They stop the release.
   - `unmatched`: rows that match no case in the snapshot. They are reviewed and removed or rewritten.
   - `pinned`: rows that match a case the rule now decides by itself. They are reviewed: the row still applies, but may no longer be needed.

   A release records each patch table in `MANIFEST.json` with its checksum and the number of rows applied.

## Patches

| Table | Feature | Key | Value | Relevant cases | Rows (dump 2026-11-01) |
|---|---|---|---|---|---|
| `flexion-sections.tsv` | which verb sections a conjugation goes with ([usage labels](../features/usage-labels.md#verbs)) | `title`, `preterite`, `participle`, `auxiliary`, `reflexive` | `decision`: `kept` or `left out` | conjugations that `flexion_selection` leaves `undecided` | 1 (`tauen`) |

## Consequences

- A patch is used only where extraction by rule is not feasible. What a rule can decide is decided by the rule.
- Every patch needs a rule that finds its relevant cases, otherwise its coverage cannot be checked.
- Because a patch overrides Wiktionary, a later correction in Wiktionary does not reach the release by itself. The `pinned` and `unmatched` reports are where it shows.
- The code is in `hawfinch.patches`: `PatchSpec` describes a table, `read_patch` reads and checks it, and `check` gives the coverage. The feature that needs a patch defines its spec and its key (`FLEXION_PATCH` and `conjugation_key` in `hawfinch.features.selection`).
- The coverage check runs in the feasibility scripts for now (`patch.tsv` of the verbs script). In M1 it moves to `validate`, which stops a release on a missing row.
