# 0003: Proper nouns as a part of speech

Date: 2026-11-24

## Decision

1. **Proper nouns are a part of speech of their own,** separate from common nouns. The distinction is central to the planned analyses.
2. **Test.** A noun in a given sense is a common noun if it has a conceptual plural or can be used as a mass noun; otherwise it is a proper noun.
3. **Classes decided explicitly.** The classes below are fixed by name. Where the test seems to point the other way, the list wins:
   - **Proper nouns:** language names (Estnisch, Hindi), descriptive designations of a single referent (Rheineinzugsgebiet, Covid-19-Pandemie, Mackenzie-Flusssystem), constellations, holidays, and named periods.
   - **Common nouns:** scientific names of species and of plant varieties and cultivars. They have a reading as the proper name of a kind, but also a count reading for the individual organisms, like many ordinary common nouns. Brand names used as count nouns for products sold under the brand (ein Ferrari, eine Remington) are common nouns too.
4. **Mixed sections are split.** Where a Wiktionary section holds both proper and common senses, it becomes two lexemes, a proper noun and a common noun, by the split rule of [0002](0002-lexeme-model.md). Ferrari becomes the manufacturer (proper noun) and the car (common noun).
5. **Detection has two modes:**
   - **Without a language model, the label rule is used.** A section with a name label (`Toponym`, `Nachname`, …) is a proper noun. So is a `Substantiv` section whose first meaning line defines it as a language (`die Sprache der Esten`). The rule's lower recall is accepted, and mixed sections stay unsplit.
   - **With a language model configured,** senses are classified one by one ([0006](0006-language-model.md)).

## Consequences

- German Wiktionary has no single label for proper nouns. The full definition, both detection modes and their limits are in [the part-of-speech feature](../features/part-of-speech.md).
- Detection errors contaminate both classes in the analyses. The feasibility test measured the label rule; see [the results](../feasibility.md#proper-nouns). Under the classes decided here, the rule finds about 90 % of proper nouns, and almost all of what it marks is a proper noun.
- Releases built with and without a language model differ in part of speech and in the number of lexemes, since only the model splits mixed sections. The release manifest records which mode was used.
- **Holidays, recurring events and language names do not fit the test well.**
  - Holidays and recurring events can be counted by occurrence (drei Weihnachten, an drei Olympischen Spielen teilnehmen).
  - Language names have mass-like uses (sein Deutsch ist gut).
  - For now they are proper nouns. Categories of their own would describe them best, but they are left out of release 1 to keep the schema simple.
- Abbreviated names (BT, CVJM, TÜV) are proper nouns too; their form is recorded separately ([0005](0005-abbreviations.md)).
