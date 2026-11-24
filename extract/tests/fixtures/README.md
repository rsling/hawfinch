# Test fixtures

Small real pages from German Wiktionary, one per parsing edge case. They are copied verbatim from the dump named below and are **not** covered by the repository's BSD licence: their text is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) by the Wiktionary contributors. The authors of each page are listed in its version history at `https://de.wiktionary.org/w/index.php?title=<title>&action=history`; the revision used is recorded in the file.

| File | Source | Edge case |
|---|---|---|
| `mini-dump.xml` | `dewiktionary-20261101-pages-articles.xml.bz2`: siteinfo and the pages µm, Fluß, Häuser, Flexion:kaufen | dump reader: redirect page, German entry without part-of-speech section (old spelling), form entry, `Flexion:` namespace |
