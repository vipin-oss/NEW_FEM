# Page budget (estimate, not a measurement)

No TeX in this environment, so nothing here is compiled. Text width 481.9 pt, text height 714.3 pt, 100 characters per line, 12 pt per line; figure heights from each PDF's MediaBox and its `width=` option, table heights from row counts.

| block | amount | pt | pages |
|---|---|---|---|
| body figures | 11 | 3124 | 4.37 |
| body tables | 6 | 884 | 1.24 |
| body prose and display maths | 15860 words | 14065 | 19.69 |
| appendix figures | 0 | 0 | 0.00 |
| appendix tables | 4 | 721 | 1.01 |
| appendix prose |  | 1281 | 1.79 |
| reference list | 68 entries | 2543 | 3.56 |
| **sum** | | **22617** | **31.66** |

## Where the body stands

| | body content | pages of area |
|---|---|---|
| this revision | 18072 pt | 25.30 |
| `47a21a3` | 16346 pt | 22.88 |
| **change** | **+1726 pt** | **+2.42** |

Package content: 22474 -> 22617 pt (31.46 -> 31.66 pages).

## From area to pages

The last counted PDF (`47a21a3`) was 34 pages for 31.46 pages of area, so a page of area costs 1.08 printed pages -- floats leave gaps that cannot be filled.

**Estimated PDF now: 34.2 pages (target 30, previous 34).** To reach 30 another 2787 pt = 3.9 pages of area has to go.

## Biggest items now

| float | pt | pages | in |
|---|---|---|---|
| `fig:orientation` (figure) | 495 | 0.69 | body |
| `fig:geometry` (figure) | 450 | 0.63 | body |
| `fig:fields` (figure) | 296 | 0.41 | body |
| `fig:ringdown` (figure) | 263 | 0.37 | body |
| `fig:convergence` (figure) | 244 | 0.34 | body |
| `tab:verification` (table) | 238 | 0.33 | appendix |
| `fig:thickness` (figure) | 237 | 0.33 | body |
| `fig:damping` (figure) | 236 | 0.33 | body |
| `fig:design` (figure) | 231 | 0.32 | body |
| `fig:designmap` (figure) | 230 | 0.32 | body |

| section | words of source | pages of area |
|---|---|---|
| Introduction | 1751 | 2.07 |
| Formulation | 2490 | 3.80 |
| Particular cases | 822 | 1.01 |
| Boundary conditions | 915 | 1.23 |
| Finite element formulation | 1693 | 2.38 |
| Validation and limiting cases | 1588 | 2.00 |
| Numerical results and discussion | 4331 | 4.50 |
| Parameter identification and limitations | 1284 | 1.54 |
| Conclusions | 536 | 0.58 |
| CRediT authorship contribution statement | 68 | 0.09 |
| Declaration of competing interest | 30 | 0.03 |
| Data availability | 49 | 0.06 |
| Acknowledgements | 20 | 0.03 |


## Levers, measured but **not applied** (round 20 was scope-locked)

To reach 30 pages, 2787 pt of area (3.9 pages) has to go. Ranked by what each is worth:

| lever | saves | pages | cost to the paper |
|---|---|---|---|
| Appendix B to supplementary material (4 floats, 238 pt) | 238 pt | 0.3 | the verification table is the evidence of Sec. 6.1; a supplementary file is standard practice but changes the submission |
| all ten body figures to 0.85\textwidth | 469 pt | 0.7 | axes get smaller; none is removed |
| `tab:verification` at \footnotesize with tighter rules | 48 pt | 0.1 | 54 rows at 9 pt instead of 12 |
| Sec. 2 and Sec. 5 tightened by a quarter | 1104 pt | 1.5 | prose only: the two sections have never been shortened |


The estimate carries about one page of error and is not a substitute for `pdflatex`.
