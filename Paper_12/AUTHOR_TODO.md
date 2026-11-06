# Author TODO

Everything in this list has to be supplied or confirmed by the author before the
paper is submitted. Line numbers refer to the state of the repository at the
tag `fem6-verified`; the file names are given so the line can be found again
after an edit.

## 1. Front matter (`Paper_12/main.tex`)

| what | where |
|---|---|
| author name and superscripts | `Paper_12/main.tex:63` (`Author name to be supplied$^{1,*}$`) |
| affiliation | `Paper_12/main.tex:66` |
| corresponding e-mail | `Paper_12/main.tex:67` |
| ORCID | `Paper_12/main.tex:63` -- add `\author[inst1]{Name\fnref{1}\corref{cor1}}` style blocks if the journal wants them |
| journal name in `\journal{}` | `Paper_12/main.tex:51` |
| running title / short title | not present; add if the journal asks for one |

## 2. Acknowledgement (`Paper_12/main.tex`)

The acknowledgement names the Haryana State Research Fund and the sanction
number `14/66-2026 SPD/HSHEC/HSRF-(38)`, dated 13 July 2026. **Confirm both the
fund name and the sanction number against the sanction letter**;
`Paper_12/main.tex:131`--`133` are the lines to edit.

## 3. The three self-citations (`Paper_12/references.bib`)

Entries `fem1`, `fem4` and `fem5` (`Paper_12/references.bib:730`, `:738`, `:746`) are placeholders with `note = {TODO: journal, volume, pages ...}`.
They are cited in `01_introduction.tex`, `03_particular_cases.tex`,
`02_formulation.tex` and Appendix A. Supply the full record for each; do not
leave the `{FEM-1}` style titles in the submitted version.

## 4. Bibliography entries that are not verified

These entries carry `note = {TO VERIFY: ...}` because their fields were not
matched against a publisher record (Crossref is not reachable from the machine
that built this repository). Check each against the journal page:

| key | line |
|---|---|
| `Mindlin1968` | `Paper_12/references.bib:584` |
| `Kogan1964` | `Paper_12/references.bib:594` |
| `YudinTagantsev2013` | `Paper_12/references.bib:606` |
| `Zubko2013` | `Paper_12/references.bib:617` |
| `Cross2006` | `Paper_12/references.bib:629` |
| `Caputo1967` | `Paper_12/references.bib:641` |
| `BagleyTorvik1983` | `Paper_12/references.bib:653` |
| `Koeller1984` | `Paper_12/references.bib:665` |
| `ColeCole1941` | `Paper_12/references.bib:677` |
| `HavriliakNegami1967` | `Paper_12/references.bib:688` |
| `EnelundLesieutre1999` | `Paper_12/references.bib:700` |
| `Roundy2003` | `Paper_12/references.bib:712` |
| `ErturkInman2011` | `Paper_12/references.bib:722` |

`Paper_12/check_refs.py` re-runs the comparison as soon as network access is
available and rewrites `results/reference_audit.md`.

## 5. Parameters that are nominal, not measured

| quantity | value used | where |
|---|---|---|
| mass density `\rho` | 6020 kg/m^3 | `Paper_12/sec/06_results.tex` (Table `tab:params`) |
| flexoelectric coefficient `\mu` | 1e-6 C/m | same table; scales every bending coupling as `\mu^2` |

Both are flagged in the text. If measured values are available, replacing them
changes every absolute kilohertz and every bending coupling; the script
`python/run_all.py` regenerates all of them.

## 6. What the author must not change without re-running

Every number in the manuscript is checked against the JSON in `results/` by
`python/check_paper_numbers.py`. If a number is edited by hand the check fails
and the audit file `results/paper_number_audit.md` names the row.
