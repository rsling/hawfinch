# 0003: Named entities

Date: 2026-11-24, revised 2026-11-25

## Context

The first version of this decision made proper nouns a part of speech of their own. A noun sense was to be common if it had a conceptual plural or a mass use, and proper otherwise. Some classes were fixed by name, and sections mixing both were to be split into two lexemes. Detection used Wiktionary's name labels, or an optional language model ([0006](0006-language-model.md)).

The adjudicated feasibility sample showed that this cannot work. Properness cannot be decided for a lemma without context: language names, taxa, cultivars, holidays and brands each needed a rule of their own, and many sections mix readings ([results](../feasibility.md#proper-nouns)).

What Wiktionary does give is a marking of names, plus a definition for each sense:

- The marking is a name label in the heading (`{{Wortart|Toponym|Deutsch}}` next to `Substantiv`), a name table, or a name label on a single sense.
- Each definition is headed by a noun that says what is named: `Stadt in Hessen`, `Fluss in Deutschland`, `deutschsprachiger Nachname`.

## Decision

1. **There is no proper-noun part of speech.** Lexemes keep Wiktionary's part of speech: Rhein and Müller are `Substantiv`. The name labels (`Toponym`, `Nachname`, `Vorname`, `Eigenname`, `Göttername`, `Bauwerksname`, `Straßenname`) are not parts of speech. A section whose only labels are name labels is a `Substantiv`. No section is split because of names.
2. **Lexical units get a field `named_entity`:**
   - `default`: Wiktionary does not mark the entry as a name. This means "not that we know of", not "not a name".
   - a noun lemma such as `Stadt`, `Nebenfluss`, `Nachname` or `Göttin`: Wiktionary marks the entry as a name, and this noun heads the definition of the sense.
   - `unspecified`: the entry is marked as a name, but its definition has no head noun.
3. **Release 1 takes what Wiktionary gives, without heuristics.** A sense counts as marked if:
   - its section has a name label or a name table;
   - or the sense itself carries a name label in `{{K|…}}`.

   Nothing else marks a sense: no patterns on the definition, and no inference from hypernyms or categories.
4. **The value is the head noun of the definition, as Wiktionary gives it.**
   - Heads are stored as lemmas (`Länder` → `Land`), and compounds are kept whole (`Hafenstadt`).
   - Heads that only say "name" or "form" (`Name verschiedener Orte`, `weibliche Form des Familiennamens Kostow`) give way to the noun that follows them: `Ort`, `Familienname`.
   - The hypernyms in `Oberbegriffe` do not go into this field. They are semantic relations of the lexical unit, extracted in M3 like the others.

   The exact rules are in [the named-entity feature](../features/named-entities.md).
5. **No types in release 1.** Grouping heads into types (`Stadt`, `Hafenstadt` and `Ortsteil` as settlements) is left to the analyses, which can do it procedurally. They can draw on the segmentation of the head itself (`Hafen.stadt`, M2) and on the hypernym relations (M3).
6. **No language model.** Nothing in this decision needs one, and [0006](0006-language-model.md) is withdrawn.

## Consequences

- **The field belongs to the lexical unit,** since the named thing differs between the senses of one section. Danzig is a city and an asteroid. Venus, in a section labelled `Göttername`, is a goddess and a planet. Because the head comes from each sense's own definition, the planet sense gets `Planet` despite the section's label. No lexeme is split by this field.
- **It comes with senses in M3.** M1 takes the part of speech from Wiktionary's labels alone.
- **Names that Wiktionary does not mark are `default`.** Examples:
  - most language names (Estnisch is a plain `Substantiv`);
  - some place names (Rheingau, Trasimenischer See);
  - abbreviated names in sections labelled `Abkürzung` (TÜV, ADAC).

  The analyses will show whether a later release should go further.
- **Common senses in sections labelled as names get a head too.** In the Jungfrau section labelled `Eigenname`, sense 1, `eine weibliche Person, die noch nie Geschlechtsverkehr hatte`, gets `Person`. Release 1 does not filter these, but the head makes them visible.
- **Measured on the dump of 2026-11-01:** 99 % of marked senses have a head, and there are 1,254 different heads ([results](../feasibility.md#named-entities)). The parser's known weakness is a phrase standing before the head (`im Landkreis Konstanz … gelegene Gemeinde`). It is improved together with the definition parsing in M3.
