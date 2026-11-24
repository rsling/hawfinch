# analysis

Data analyses for the publication, in R and Python.

- `studies/`: one self-contained directory per analysis.
- `R/`, `py/`: helpers shared across studies (loading a release, plot themes).
- `output/`: generated figures and tables. Not tracked by git; `paper/` reads from here.
- `release.txt`: the data release all analyses are pinned to.

Analyses read a data release from `data/release/` and never import code from `extract/`.

The R environment is not pinned yet. Run `renv::init()` here when the first R analysis is written, and commit the resulting `renv.lock`.
