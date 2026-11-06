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
total word count of the package falls by only 400.

## 4. Verified by execution

| gate | result |
|---|---|
| `python/run_all.py` | **62/62 checks pass** (8 min) |
| `python/check_paper_numbers.py` | **90/90** claims agree with their JSON, 0 stale-token hits of 12 |
| `python/check_final_consistency.py` | **57/57** numbers in abstract, conclusion, Highlights and captions traced, 0 untraced (N5) |
| `python/check_coupling_provenance.py` | 10/10, every coupling factor equals its archive entry |
| `python/run_dt_study.py` | 0.150111 / 0.150057 / 0.150029 vs 0.150000, order **0.97** |
| `python/check_float_order.py` | order agrees, 10 figures, 6 body tables, 9 Appendix-C tables |
| `python/check_paper_structure.py` | nothing to report; no missing graphic or `\input` |
| `python/list_unverified.py` | 29 entries, 0 stale |
| `python/audit_abstract_claims.py` | 0 uncovered tokens |
| `Paper_12/check_refs.py` | 62 entries, 0 field mismatches, Crossref offline |

## 5. UNVERIFIED — no TeX distribution and no network in this environment

| item | status |
|---|---|
| **Compilation** | not run. `pdflatex → bibtex → pdflatex ×2` has never been executed on this tree |
| **Page count** | **not measured.** The last PDF the author reports is 34 pages and the target is ≤ 30. The sanctioned changes remove ~889 words of prose and three floats from the body; that is of the order of one to two pages, so **≤ 30 is not established** by anything here. If the compile is still above 30, the next candidates, in order, are: the 54-row verification table (Appendix B, ~1 page), Secs. 3–4, which have never been shortened, and the eleven figures, which are all still `width=\textwidth` |
| **On which page each float lands** | not measured; `check_float_order.py` verifies citation *order*, not page placement |
| **Overfull/underfull boxes** | not measured; the height of the new five-column `tab:coupling` and of the three tables moved to Appendix C is untested |
| **DOI resolution** | not checked: Crossref unreachable. `fem1` (10.1016/j.finel.2026.104681) and the 13 `TO VERIFY` entries are unchecked, not confirmed |
| **Typeset heading of `\paragraph`** | the 21 trailing periods were removed in round 19 on the evidence of the author's compiled PDF; the result has not been compiled here |
