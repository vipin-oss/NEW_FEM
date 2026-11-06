# Page budget (estimate, not a measurement)

No TeX in this environment, so nothing here is compiled. Text width 481.9 pt, text height 714.3 pt, 100 characters per line, 12 pt per line; figure heights from each PDF's MediaBox and its `width=` option, table heights from row counts.

| block | amount | pt | pages |
|---|---|---|---|
| body figures | 10 | 3137 | 4.39 |
| body tables | 6 | 956 | 1.34 |
| body prose and display maths | 13441 words | 11509 | 16.11 |
| appendix figures | 1 | 349 | 0.49 |
| appendix tables | 12 | 2826 | 3.96 |
| appendix prose |  | 1176 | 1.65 |
| reference list | 62 entries | 2319 | 3.25 |
| **sum** | | **22272** | **31.18** |

## Where the body stands

| | body content | pages of area |
|---|---|---|
| this revision | 15602 pt | 21.84 |
| `47a21a3` | 16346 pt | 22.88 |
| **change** | **-744 pt** | **-1.04** |

Package content: 22475 -> 22272 pt (31.46 -> 31.18 pages).

## From area to pages

The last counted PDF (`47a21a3`) was 34 pages for 31.46 pages of area, so a page of area costs 1.08 printed pages -- floats leave gaps that cannot be filled.

**Estimated PDF now: 33.7 pages (target 30, previous 34).** To reach 30 another 2441 pt = 3.4 pages of area has to go.

## Biggest items now

| float | pt | pages | in |
|---|---|---|---|
| `tab:verification` (table) | 666 | 0.93 | appendix |
| `fig:orientation` (figure) | 528 | 0.74 | body |
| `tab:independent` (table) | 420 | 0.59 | appendix |
| `fig:geometry` (figure) | 363 | 0.51 | body |
| `fig:modeshape` (figure) | 349 | 0.49 | appendix |
| `fig:ringdown` (figure) | 329 | 0.46 | body |
| `fig:fields` (figure) | 310 | 0.43 | body |
| `fig:damping` (figure) | 302 | 0.42 | body |
| `fig:window` (figure) | 282 | 0.40 | body |
| `fig:thickness` (figure) | 281 | 0.39 | body |

| section | words of source | pages of area |
|---|---|---|
| Introduction | 1417 | 1.80 |
| Formulation | 1936 | 2.55 |
| Particular cases | 711 | 0.81 |
| Boundary conditions | 840 | 1.09 |
| Finite element formulation | 1322 | 1.64 |
| Numerical results and discussion | 5546 | 6.27 |
| Parameter identification and limitations | 961 | 1.08 |
| Conclusion | 317 | 0.38 |
| Data availability | 51 | 0.06 |
| Conflict of Interest Disclosure Statement | 31 | 0.04 |
| Acknowledgements | 20 | 0.03 |


## Levers, measured but **not applied** (round 20 was scope-locked)

To reach 30 pages, 2441 pt of area (3.4 pages) has to go. Ranked by what each is worth:

| lever | saves | pages | cost to the paper |
|---|---|---|---|
| Appendix B to supplementary material (4 floats, 1647 pt) | 1647 pt | 2.3 | the verification table is the evidence of Sec. 6.1; a supplementary file is standard practice but changes the submission |
| all ten body figures to 0.85\textwidth | 471 pt | 0.7 | axes get smaller; none is removed |
| `tab:verification` at \footnotesize with tighter rules | 133 pt | 0.2 | 54 rows at 9 pt instead of 12 |
| Sec. 2 and Sec. 5 tightened by a quarter | 749 pt | 1.0 | prose only: the two sections have never been shortened |


The estimate carries about one page of error and is not a substitute for `pdflatex`.
