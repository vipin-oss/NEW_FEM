# Page budget (estimate, not a measurement)

No TeX in this environment, so nothing here is compiled. Text width 481.9 pt, text height 714.3 pt, 100 characters per line, 12 pt per line; figure heights from each PDF's MediaBox and its `width=` option, table heights from row counts.

| block | amount | pt | pages |
|---|---|---|---|
| body figures | 11 | 3120 | 4.37 |
| body tables | 6 | 884 | 1.24 |
| body prose and display maths | 14146 words | 12823 | 17.95 |
| appendix figures | 0 | 0 | 0.00 |
| appendix tables | 4 | 721 | 1.01 |
| appendix prose |  | 1268 | 1.78 |
| reference list | 68 entries | 2543 | 3.56 |
| **sum** | | **21359** | **29.90** |

## Where the body stands

| | body content | pages of area |
|---|---|---|
| this revision | 16826 pt | 23.56 |
| `47a21a3` | 16342 pt | 22.88 |
| **change** | **+484 pt** | **+0.68** |

Package content: 22471 -> 21359 pt (31.46 -> 29.90 pages).

## From area to pages

The last counted PDF (`47a21a3`) was 34 pages for 31.46 pages of area, so a page of area costs 1.08 printed pages -- floats leave gaps that cannot be filled.

**Estimated PDF now: 32.3 pages (target 30, previous 34).** To reach 30 another 1532 pt = 2.1 pages of area has to go.

## Biggest items now

| float | pt | pages | in |
|---|---|---|---|
| `fig:orientation` (figure) | 495 | 0.69 | body |
| `fig:geometry` (figure) | 450 | 0.63 | body |
| `fig:fields` (figure) | 293 | 0.41 | body |
| `fig:ringdown` (figure) | 263 | 0.37 | body |
| `fig:convergence` (figure) | 244 | 0.34 | body |
| `fig:window` (figure) | 238 | 0.33 | body |
| `tab:verification` (table) | 238 | 0.33 | appendix |
| `fig:thickness` (figure) | 237 | 0.33 | body |
| `fig:damping` (figure) | 236 | 0.33 | body |
| `fig:design` (figure) | 231 | 0.32 | body |

| section | words of source | pages of area |
|---|---|---|
| Introduction | 1326 | 1.66 |
| Formulation | 2455 | 3.77 |
| Particular cases | 761 | 0.94 |
| Boundary conditions | 895 | 1.21 |
| Finite element formulation | 1608 | 2.27 |
| Numerical results and discussion | 5034 | 5.60 |
| Parameter identification, positioning and limitations | 1278 | 1.53 |
| Conclusions | 354 | 0.40 |
| CRediT authorship contribution statement | 68 | 0.09 |
| Declaration of competing interest | 30 | 0.03 |
| Data availability | 49 | 0.06 |
| Acknowledgements | 20 | 0.03 |


## Levers, measured but **not applied** (round 20 was scope-locked)

To reach 30 pages, 1532 pt of area (2.1 pages) has to go. Ranked by what each is worth:

| lever | saves | pages | cost to the paper |
|---|---|---|---|
| Appendix B to supplementary material (4 floats, 238 pt) | 238 pt | 0.3 | the verification table is the evidence of Sec. 6.1; a supplementary file is standard practice but changes the submission |
| all ten body figures to 0.85\textwidth | 468 pt | 0.7 | axes get smaller; none is removed |
| `tab:verification` at \footnotesize with tighter rules | 48 pt | 0.1 | 54 rows at 9 pt instead of 12 |
| Sec. 2 and Sec. 5 tightened by a quarter | 1078 pt | 1.5 | prose only: the two sections have never been shortened |


The estimate carries about one page of error and is not a substitute for `pdflatex`.
