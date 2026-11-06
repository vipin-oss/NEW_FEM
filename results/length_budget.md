# Page budget (estimate, not a measurement)

No TeX in this environment, so nothing here is compiled. Text width 481.9 pt, text height 714.3 pt, 100 characters per line, 12 pt per line; figure heights from each PDF's MediaBox and its `width=` option, table heights from row counts.

| block | amount | pt | pages |
|---|---|---|---|
| body figures | 11 | 3011 | 4.22 |
| body tables | 6 | 884 | 1.24 |
| body prose and display maths | 14198 words | 12864 | 18.01 |
| appendix figures | 0 | 0 | 0.00 |
| appendix tables | 4 | 1148 | 1.61 |
| appendix prose |  | 1106 | 1.55 |
| reference list | 68 entries | 2543 | 3.56 |
| **sum** | | **21557** | **30.18** |

## Where the body stands

| | body content | pages of area |
|---|---|---|
| this revision | 16759 pt | 23.46 |
| `47a21a3` | 16342 pt | 22.88 |
| **change** | **+417 pt** | **+0.58** |

Package content: 22471 -> 21557 pt (31.46 -> 30.18 pages).

## From area to pages

The last counted PDF (`47a21a3`) was 34 pages for 31.46 pages of area, so a page of area costs 1.08 printed pages -- floats leave gaps that cannot be filled.

**Estimated PDF now: 32.6 pages (target 30, previous 34).** To reach 30 another 1730 pt = 2.4 pages of area has to go.

## Biggest items now

| float | pt | pages | in |
|---|---|---|---|
| `tab:verification` (table) | 666 | 0.93 | appendix |
| `fig:orientation` (figure) | 495 | 0.69 | body |
| `fig:geometry` (figure) | 341 | 0.48 | body |
| `fig:fields` (figure) | 293 | 0.41 | body |
| `fig:ringdown` (figure) | 263 | 0.37 | body |
| `fig:convergence` (figure) | 244 | 0.34 | body |
| `fig:window` (figure) | 238 | 0.33 | body |
| `fig:thickness` (figure) | 237 | 0.33 | body |
| `fig:damping` (figure) | 236 | 0.33 | body |
| `fig:design` (figure) | 231 | 0.32 | body |

| section | words of source | pages of area |
|---|---|---|
| Introduction | 1326 | 1.66 |
| Formulation | 2456 | 3.77 |
| Particular cases | 762 | 0.95 |
| Boundary conditions | 888 | 1.20 |
| Finite element formulation | 1608 | 2.27 |
| Numerical results and discussion | 5073 | 5.64 |
| Parameter identification, positioning and limitations | 1294 | 1.55 |
| Conclusions | 354 | 0.40 |
| CRediT authorship contribution statement | 68 | 0.09 |
| Declaration of competing interest | 30 | 0.03 |
| Data availability | 51 | 0.06 |
| Acknowledgements | 20 | 0.03 |


## Levers, measured but **not applied** (round 20 was scope-locked)

To reach 30 pages, 1730 pt of area (2.4 pages) has to go. Ranked by what each is worth:

| lever | saves | pages | cost to the paper |
|---|---|---|---|
| Appendix B to supplementary material (4 floats, 666 pt) | 666 pt | 0.9 | the verification table is the evidence of Sec. 6.1; a supplementary file is standard practice but changes the submission |
| all ten body figures to 0.85\textwidth | 452 pt | 0.6 | axes get smaller; none is removed |
| `tab:verification` at \footnotesize with tighter rules | 133 pt | 0.2 | 54 rows at 9 pt instead of 12 |
| Sec. 2 and Sec. 5 tightened by a quarter | 1079 pt | 1.5 | prose only: the two sections have never been shortened |


The estimate carries about one page of error and is not a substitute for `pdflatex`.
