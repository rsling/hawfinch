# app

Web interface with Shiny visualisations for browsing the data. Built last, once the release schema is stable.

Periphrastic verb forms ("geglaubt haben würde") are never stored in the database. The app should include a small function that generates them on request from the stored forms.

The app reads a data release from `data/release/` and never imports code from `extract/`.
