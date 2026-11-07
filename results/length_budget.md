# Page budget (estimate, not a measurement)

No full TeX Live here; an offline static Tectonic diagnostic compiles separately. Text width 481.9 pt, text height 714.3 pt, 100 characters per line, 12 pt per line; figure heights from each PDF's MediaBox and its `width=` option, table heights from row counts.

| block | amount | pt | pages |
|---|---|---|---|
| body figures | 12 | 3417 | 4.78 |
| body tables | 6 | 884 | 1.24 |
| body prose and display maths | 17452 words | 15339 | 21.47 |
| appendix figures | 0 | 0 | 0.00 |
| appendix tables | 4 | 721 | 1.01 |
| appendix prose |  | 1692 | 2.37 |
| reference list | 68 entries | 2543 | 3.56 |
| **sum** | | **24595** | **34.43** |

## Where the body stands

| | body content | pages of area |
|---|---|---|
| this revision | 19639 pt | 27.49 |
| `47a21a3` | 16301 pt | 22.82 |
| **change** | **+3338 pt** | **+4.67** |

Package content: 22343 -> 24595 pt (31.28 -> 34.43 pages).

## From area to pages

The last counted PDF (`47a21a3`) was 34 pages for 31.28 pages of area, so a page of area costs 1.09 printed pages -- floats leave gaps that cannot be filled.

**Estimated PDF now: 37.4 pages (target 30, previous 34).** To reach 30 another 4881 pt = 6.8 pages of area has to go.

## Biggest items now

| float | pt | pages | in |
|---|---|---|---|
| `fig:orientation` (figure) | 486 | 0.68 | body |
| `fig:geometry` (figure) | 398 | 0.56 | body |
| `fig:modes` (figure) | 341 | 0.48 | body |
| `fig:fields` (figure) | 296 | 0.41 | body |
| `fig:ringdown` (figure) | 252 | 0.35 | body |
| `fig:convergence` (figure) | 251 | 0.35 | body |
| `fig:damping` (figure) | 249 | 0.35 | body |
| `tab:verification` (table) | 238 | 0.33 | appendix |
| `fig:design` (figure) | 235 | 0.33 | body |
| `fig:thickness` (figure) | 232 | 0.32 | body |

| section | words of source | pages of area |
|---|---|---|
| Introduction | 1855 | 2.20 |
| Formulation | 2760 | 4.08 |
| Particular cases | 918 | 1.10 |
| Boundary conditions | 1045 | 1.38 |
| Finite element formulation | 1904 | 2.60 |
| Validation and limiting cases | 1772 | 2.22 |
| Numerical results and discussion | 4477 | 4.68 |
| Parameter identification and limitations | 1494 | 1.79 |
| Conclusions | 703 | 0.77 |
| CRediT authorship contribution statement | 68 | 0.09 |
| Declaration of competing interest | 30 | 0.03 |
| Data availability | 68 | 0.08 |
| Acknowledgements | 20 | 0.03 |


## Levers, measured but **not applied** (round 20 was scope-locked)

To reach 30 pages, 4881 pt of area (6.8 pages) has to go. Ranked by what each is worth:

| lever | saves | pages | cost to the paper |
|---|---|---|---|
| Appendix B to supplementary material (4 floats, 238 pt) | 238 pt | 0.3 | the verification table is the evidence of Sec. 6.1; a supplementary file is standard practice but changes the submission |
| all twelve body figures to 0.85\textwidth | 512 pt | 0.7 | axes get smaller; none is removed |
| `tab:verification` at \footnotesize with tighter rules | 48 pt | 0.1 | 54 rows at 9 pt instead of 12 |
| Sec. 2 and Sec. 5 tightened by a quarter | 1194 pt | 1.7 | prose only: the two sections have never been shortened |


The estimate carries about one page of error and is not a substitute for `pdflatex`.
