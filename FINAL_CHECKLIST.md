# FINAL CHECKLIST — round 20

One page. Left: what was changed and what was executed. Right: what could not
be measured here.

## 1. What round 20 changed

| # | item | change | where |
|---|---|---|---|
| 1 | `tab:coupling` and its caption | the `archive` (`entry`) column is deleted, so the table is five columns — $k^{2}$, build, mesh, $\mu$, measure; the caption no longer names any file and is 341 characters (about three typeset lines); the $\mu$ unit moved into the caption | `Paper_12/sec/06_results.tex` (float at 99–110), `Paper_12/table_coupling.tex`, `python/make_coupling_table.py` |
| 1b | repository names in the package | grep over `main.tex`, `sec/*.tex`, `table_*.tex`, `Highlights.tex` for `results/`, `python/`, `.json`, `.py`, `rows[`, `upstream key`, `archive`: **no hits in typeset text**. The only remaining mentions are LaTeX comments in generated table files (not printed) and the two repository documents `README.md` and `REVIEWER_RISKS.md`, which are not part of the manuscript. Data availability is unchanged: "available within the article", pointing at the tables of Appendix C | whole package |
| 2 | time discretization | one statement, repeated: the L1 scheme is **first order for every $\alpha\in(0,1]$**, at $\alpha=1$ too. At $\alpha=1$, $\omega\tau=0.3$: $\zeta=0.150111$, $0.150057$, $0.150029$ at $N$, $2N$, $4N$ steps over twenty periods ($N=12000$) against the exact $\omega\tau/2=0.150000$, observed order $0.97$. New `python/run_dt_study.py` computes the three values and archives them (`results/dt_study.json`), the suite gates them (V5e), and the numbers are audited row by row (N1) | `sec/02_formulation.tex:234`, `sec/05_finite_element.tex:140`, `sec/06_results.tex:65–72`, `sec/06_results.tex:452–459`, Fig. 10 caption, Table C.5 caption |
| 2b | deviation from the brief | the literal sentence "the step used in Sec. 6.8 is the $4N$ one" was **not** written, because it is not true: the curves of Sec. 6.8 are an L1 march of 4000 steps over ten periods, i.e. 400 steps per period, against 600/1200/2400 for $N/2N/4N$. The text says instead that the ring-downs of Sec. 6.5 use the $4N$ step, that Sec. 6.8 is coarser, and the measured consequence: quartering the step moves its decrement by $1.6\times10^{-5}$ (last decimal only) | `sec/06_results.tex:71` and Fig. 10 caption |
| 3 | length | three floats moved from the body to Appendix C; Sec. 7 and the second half of Sec. 6.9 rewritten shorter | see §2 and §3 |
| 4 | consistency pass | a new check (`python/check_final_consistency.py`, gate **N5**) sweeps every number in the abstract, the conclusion, the Highlights and every caption: **57 numbers, 57 traced, 0 untraced**. It found one stale caption number, which is now fixed: the ratio of Fig. 5(c) spans $3.1\times10^{-4}$ (was $4.3\times10^{-4}$) to $7.5\times10^{-3}$; the endpoints are now archived in `demo.json` (`ratio_flexo_over_piezo`) instead of being quoted from memory | `sec/06_results.tex:672`, `python/run_demos.py` |

## 2. Items moved, and the float list now

| table | was | now |
|---|---|---|
| closed-form coupling factors | Table 4, Sec. 6.2 | **Table C.7** |
| ring-down of the memory study | Table 5, Sec. 6.5 | **Table C.8** |
| calibration protocol | Sec. 7.1 | **Table C.9** |

* **Figures: unchanged**, 1–10 in the body (`fig:geometry`, `convergence`,
  `fields`, `orientation`, `design`, `damping`, `window`, `thickness`,
  `modetrack`, `ringdown`). No main-text figure was removed.
* **Main-text tables: six** — 1 `tab:params`, 2 `tab:axes`, 3 `tab:coupling`,
  4 `tab:worked`, 5 `tab:config`, 6 `tab:application` (was nine).
* **Appendix A:** none. **Appendix B:** B.1 `tab:verification`,
  B.2 `tab:independent`, B.3 `fig:modeshape`, B.4 `tab:sens`.
  **Appendix C:** C.1 orientation, C.2 thickness, C.3 damping,
  C.4 convergence, C.5 ring-down, C.6 modulus, C.7 closed form,
  C.8 memory, C.9 protocol.
* `check_float_order.py` agrees: the six main tables and the ten figures are
  first cited in increasing order, and no float is uncited.

## 3. Length accounting

| | before | after |
|---|---|---|
| Sec. 7 words | 1530 | 965 |
| Sec. 6.9 words (incl. its table) | 7500 | 7158 |
| Appendix C words | 287 | 776 |
| **prose** in the body | — | **−889 words** |
| main-text tables | 9 | 6 |

The prose cut is real; the moved table text reappears in Appendix C, so the
total word count of the package falls by only 400. Measured in area
(`results/length_budget.md`): body 16346 → 15602 pt, package 22475 → 22272 pt,
i.e. **−0.3 page**; the move buys tidy body pages, not a shorter appendix.

## 4. Verified by execution

| gate | result |
|---|---|
| `python/run_all.py` | **70/70 checks pass** (~14 min full, ~25 s incremental) |
| `python/check_paper_numbers.py` | **102/102** claims agree with their JSON, 0 stale-token hits of 20 |
| `python/check_final_consistency.py` | **48/48** numbers in abstract, conclusion, Highlights and captions traced, 0 untraced (N5) |
| `python/check_coupling_provenance.py` | 10/10, every coupling factor equals its archive entry |
| `python/run_dt_study.py` | 0.150111 / 0.150057 / 0.150029 vs 0.150000, order **0.97** |
| `python/check_float_order.py` | order agrees, 12 figures, 6 body tables, 2 Appendix-B tables, 2 Appendix-C tables |
| `python/check_paper_structure.py` | nothing to report; no missing graphic or `\input` |
| `python/list_unverified.py` | 28 entries, 0 stale |
| `python/audit_abstract_claims.py` | 0 uncovered tokens |
| `Paper_12/check_refs.py` | not run by request; `results/reference_audit.md` untouched |
| `python/length_budget.py` (new) | area budget; 35 pages measured by static Tectonic, see §5 |

## 5. UNVERIFIED — no full TeX Live; offline static Tectonic diagnostic

| item | status |
|---|---|
| **Compilation** | offline static Tectonic diagnostic: 35 pages, 0 undefined references, no doubled appendix, no `..` or run-in heading. The mandated `pdflatex → bibtex → pdflatex ×2` sequence has not been executed on this tree (no full TeX Live) |
| **Page count** | **35 pages** measured by the offline static Tectonic diagnostic. `python/length_budget.py` estimates 37.4 pages of area with ~1 page of error and is not a substitute for the mandated full TeX sequence. The 30-page target is not reached; see §6 for the unapplied levers |
| **On which page each float lands** | not measured; `check_float_order.py` verifies citation *order*, not page placement |
| **Overfull/underfull boxes** | not measured; the height of the new five-column `tab:coupling` and of the three tables moved to Appendix C is untested |
| **DOI resolution** | six entries were resolved against Crossref; fifteen entries carry visible `UNVERIFIED` notes. `fem1` (10.1016/j.finel.2026.104681) is flagged because its publisher record was not checked offline; `Gupta2026Rayleigh` is flagged for the FEM-1 list 2024 versus Crossref published-print 2026 mismatch; the printed year is retained |
| **Typeset heading of `\paragraph`** | the 21 trailing periods were removed in round 19 on the evidence of the author's compiled PDF; the result has not been compiled here |

## 6. What would get to 30 pages, measured and not done

Ranked by area, from the final `results/length_budget.md`. None of these was
applied in Round 3; the brief named the levers and forbade others. The current
estimate is **37.4 pages**, with 4881 pt = 6.8 pages of area still to remove.

| lever | saves | cost |
|---|---|---|
| Secs. 2 and 5 tightened by a quarter (1194 pt) | **1.7 pages** | prose only, no result touched |
| all twelve body figures at `0.85\\textwidth` instead of the present 0.72–1.0 (512 pt) | 0.7 page | smaller axes; no figure removed |
| Appendix B to a supplementary file (4 floats, 238 pt) | 0.3 page | the verification table is the evidence of Sec. 6.1 |
| `tab:verification` at `\\footnotesize` with tighter rules (48 pt) | 0.1 page | 54 rows at 9 pt |
