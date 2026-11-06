# Round 18 — audit, then correction

Scope rule for this round: **audit first, correct only what the audit
confirmed, re-run only what the corrections touch**. No new physics, no forced
agreement between numbers that are not the same quantity.

Two stages:

* **Stage 1** — a claim-by-claim audit of the round-18 brief against the code,
  the archived JSON and a fresh recomputation. Every row is classified
  **confirmed**, **disproved**, **manuscript-only** (a wording/notation defect
  with no numerical consequence) or **code-level**.
* **Stage 2** — the edit made for each confirmed row, and the re-run that
  backs it.

Everything marked UNVERIFIED was not measured: there is no TeX distribution in
this environment, so nothing about compilation, page count, float placement,
overfull boxes or rendered reference numbering has been observed.

---

## Stage 1 — audit

### A. Citations and self-citation

| # | claim in the brief | finding | class | evidence |
|---|---|---|---|---|
| A1 | unpublished self-citations must go; only FEM-1 may be self-cited | **confirmed defect.** `fem1` was an `@misc` placeholder with `TODO` fields; `fem4` and `fem5` had no published record at all and were cited in four files (`01_introduction.tex`, `02_formulation.tex`, `03_particular_cases.tex`, `91_appendixA.tex`), and two comments in `main.tex` (`:2`, `:40`) named "FEM-6" | manuscript-only | `grep -n "fem[0-9]"` over `Paper_12/`; `references.bib` before the edit: 64 entries, 3 of them `@misc` |
| A2 | Sec. 3.1 attribution | **confirmed defect.** "the model reduces to the piezoelectric strip of [FEM-1]" attributed a piezoelectric model to a paper on strain-gradient elasticity | manuscript-only | `sec/03_particular_cases.tex:35` before the edit |
| A3 | reference [62] must be the Gupta *et al.* record, TODO removed | **confirmed.** The entry was a placeholder; the required record was absent from the file | manuscript-only | `references.bib` (old `@misc{fem1}`) |
| A4 | Sec. 7 must read "Parameter identification and limitations"; no "validated/experimentally" wording | **confirmed.** The title was "Experimental calibration protocol and limitations" and the intro promised parameters "obtained experimentally", although no experiment is reported | manuscript-only | `sec/07_calibration_limitations.tex:3`, `sec/01_introduction.tex:156` before the edit; the surviving "experiments on micron-scale beams" (`01:36`) is a statement about the literature, not about this paper, and was kept |

A naive `grep fem[2-6]` finds nothing in the text: `fem2`, `fem3` and `fem6` never
existed as bib entries, so the mention-level work is prose, not citation
deletion. That is why A1 was carried out by rewriting passages, not by a
search-and-replace.

### B. Scientific and numerical claims

| # | claim in the brief | finding | class | evidence |
|---|---|---|---|---|
| B1 | `l1_weights` uses `0**0` and is wrong at α = 1 | **confirmed as a code-level latent bug, disproved as a numerical error.** `l1_weights(n,α)` returns `(k+1)^(1−α) − k^(1−α)`; at α = 1 numpy evaluates `0.0**0.0 = 1.0`, so `b[0] = 0`. Index 0 is never read — the transient applies the newest weight implicitly — so no result changed. **Separately, the manuscript carried a real error**: Eq. (22) printed `Σ_{k=0}^{n} b_{n−k} Δu^{n+1−k}`, which pairs the newest increment with the *oldest* weight, contradicting Eq. (12) (which is correct) | code-level + manuscript-only | `python/fem6_core.py:696` (`l1_weights`), used once at `:748`; `sec/05_finite_element.tex:109` before the edit; `l1_weights(4,1.0)` returned `[0,0,0,0,0]` |
| B2 | do not force agreement between the coupling factors; unify if the same, explain if different | **confirmed: three labels were wrong, and no two of the numbers are the same quantity.** Recomputing all of them (`python/coupling_provenance.py`, 8 rows) reproduced the archive **bit for bit**: `0.560786` (free, no window, μ = 0) = the closed form `0.5607863` to `1.2×10⁻¹¹` relative; `0.559571` (left edge clamped, no window); `0.558137` (clamped + window, 48×4) = `demo.json flexo_thickness[0].k2_ext`; `0.557968` (same build, 24×2); `0.464982` (mode-based, `K_oc` vs `K_uu`) = `memory_variants.json k2`; `0.458297` (mode-based, `K_oc` vs `K_sc`, μ = 10⁻⁶); `0.457972` (same, μ = 0) = `application_table.json rows[3].k2`. So there are **two** quantities behind the 0.46 cluster (matrix `K_uu` vs `K_sc`, gap 1.5 %) and the second pair differs only in μ (0.07 %); behind the 0.56 cluster there are four measures of one tensor set, separated by the clamp (0.22 %) and the window (0.26 %). The text called `0.5596` "the mode-based value of the clamped 48×4 model" (it is mode-**free**), called `0.55814` "the free-strip value of Appendix C" (it is the **clamped** value **with the window on**), and the ring-down caption called `0.4583` "the mode-free quasi-static measure" (it is **mode-based**) | manuscript-only (values were right, labels were not) | `results/coupling_provenance.json`; `results/coupling_provenance_check.json` (10/10, relative difference 0); upstream keys as listed |
| B2b | — | The μ = 10⁻⁶ rows must be distinguished from μ = 0: `mt.batio3()` carries μ = 10⁻⁶ by default, so a script that forgets it reports 0.55844 instead of 0.55814. The first version of `coupling_provenance.py` made exactly that mistake; zeroing `core.mu` fixed it and the mode-based rows were unaffected (0.46498 both ways) | code-level (checker) | the first run printed 0.55844 / 0.55823; after `core.mu = 0.0`, 0.55814 / 0.55797 |
| B3 | charge/voltage convention | **confirmed defect.** The sentence read "the charge is read as `q = dᵀu/β`". With `Q = dᵀu − βV`, that ratio is the open-circuit **voltage**, not a charge | manuscript-only | `sec/05_finite_element.tex:79` before the edit |
| B4 | no conflation of the two phenomena | **partly confirmed.** No sentence anywhere said which of memory / window / μ acts on damping / stiffness / coupling; each was introduced in its own section and the reader had to assemble the distinction | manuscript-only | `grep -n "kept apart"` before the edit: no hits |
| B5 | a/L ≤ 0.2 is an assumed operating range, not a validated threshold | **confirmed.** "The bound claimed for the model is a/L ≤ 0.2 … because there the second-moment truncation itself is what fails" claims a located failure that was never computed | manuscript-only | `sec/06_results.tex:599` and `:612` before the edit |
| B6 | the transmissibility/small-loss statement | **confirmed defect.** The small-loss logarithmic decrement was printed as `π(ωτ)^α sin(πα/2)/2`, which is ζ, not δ — at α = 1 it gives 0.471 against the exact `πωτ = 0.9425`. And "a measurement at two amplitudes fixes the pair" cannot be right: one decrement gives one number | manuscript-only | `sec/07_calibration_limitations.tex:104` before the edit; cross-checked against δ = πωτ at α = 1 and the 1.2 % small-loss statement already in the text |
| B7 | recompute before quoting | **confirmed sound.** Every quoted coupling factor regenerates exactly from the dt-converged archives; nothing needed a new run | — | `results/coupling_provenance_check.json`, 10/10 at relative difference 0 |

### C. Presentation

| # | claim in the brief | finding | class | evidence |
|---|---|---|---|---|
| C1 | periods in run-in headings | ~~disproved as a defect~~ **corrected in round 19: confirmed defect.** I checked only that all 21 sites were *consistent*; consistency was the wrong question, because the class prints its own terminator, so `\paragraph{Window.}` sets as "Window.." — visible about 20 times in the compiled `Paper_12_4.pdf` | **CONFIRMED** — my "consistent, unchanged" verdict was wrong | `grep -rho "\\\\paragraph{[^}]*}"` → 21 hits, all `….`; the compiled PDF supplied by the author shows the doubled periods. Fixed in round 19 (see the addendum) |
| C2 | unit macros and editorial asides | `{\nano\second}` is correct siunitx in every one of the 8 occurrences (the plural defect of an earlier round is gone). The asides "easy to get wrong", "worth recording", "both easy to misplace" survived | manuscript-only | `grep -n "nano"`, `grep -n "easy to\|worth recording"` |
| C3 | equation (27) text, table row 100 vs 24 | **not confirmed in round 18; confirmed and fixed in round 19.** I looked for the pair 100/24 in the thickness table (`tab:C2`), where it is not; it belongs to the worked-example table `tab:worked`, whose "flexoelectric growth" row quoted only the FEM factor 24 while the text claimed the analytic route "gives the factor by which it grows" — that factor is 100, because $x\propto h^{-2}$ | **CONFIRMED** (round 19) | `sec/06_results.tex` "Flexoelectric bending" paragraph and the `tab:worked` row; see the addendum |
| C4 | a suspicious row of the anisotropy table | **not confirmed.** `table_C1_orientation.tex` is monotone in θ for all three aspect ratios and consistent with the sweep of Fig. 4 | no edit | `Paper_12/table_C1_orientation.tex`, `check_paper_numbers` row "orientation sweep" |
| C5 | "eight thicknesses" | **disproved as a defect.** The eight are 10, 7, 5, 3.5, 2.7, 2, 1.4, 1 µm, listed once in Table C.2 and matched by the text and the figure | consistent, unchanged | `table_C2_thickness.tex:23–31` |
| C6 | page count ≤ 30 | **unmeasurable here.** No TeX in the environment. Nothing was cut for length in this round, because a cut made without a page count would be a guess | UNVERIFIED | — |

---

## Stage 2 — what was changed

Only the confirmed rows. Files: `Paper_12/{references.bib, main.tex,
sec/01_introduction.tex, sec/02_formulation.tex, sec/03_particular_cases.tex,
sec/05_finite_element.tex, sec/06_results.tex,
sec/07_calibration_limitations.tex, sec/91_appendixA.tex, table_coupling.tex,
AUTHOR_TODO.md}`, `python/{fem6_core.py, coupling_provenance.py,
make_coupling_table.py, check_coupling_provenance.py, run_all.py}`.

1. **Self-citation (A1–A3).** `fem1` now carries

   > V. Gupta, S. Kumawat, A. K. Yadav, T. Maruyama, B. Almohsen, *Finite
   > element analysis of second-order strain-gradient elasticity with
   > ellipsoidal nonlocal characteristic lengths*, Finite Elements in Analysis
   > and Design **263** (2027) 104681, doi:10.1016/j.finel.2026.104681

   `fem4` and `fem5` are deleted, together with every mention and the two
   "FEM-6" comments in `main.tex`. The passages they supported now cite the
   published literature instead: the introduction cites the one-scale
   theory (`fem1`) for the elastic side and Aifantis for the scalar reduction,
   and Mindlin, Toupin, Kogan, Yudin–Tagantsev and Zubko for the coupled side.
   The bibliography holds **62 entries**, all cited. No new reference was
   invented: the keys used are existing entries (`Aifantis1992`,
   `Mindlin1965`, `Toupin1962`, `Mindlin1968`, `Kogan1964`,
   `YudinTagantsev2013`), and two keys that did not exist were *removed* from
   the drafts of the new sentences rather than created.

2. **Sec. 3.1 (A2).** The plane-stress reduction with `e = 0` "reduces to the
   linear piezoelectric strip of the plane-stress reduction, with the
   strain-gradient stiffness retained" — no paper attributed.

3. **Sec. 7 (A4).** Title and both subsection titles renamed; the introduction
   now says the parameters are "identified from measurements".

4. **L1 indexing (B1).** Eq. (22) and the history sum now read `b_k`, the
   paragraph states that `b_0` carries the unknown increment, and the α = 1
   limit is restated correctly: `b_0 = 1`, `b_j = 0` for `j ≥ 1`, so the
   operator becomes the backward difference and Kelvin–Voigt is recovered to
   `O(Δt)` — the ring-down's accuracy is described as measured by the step
   refinement of Sec. 6.1, not as an assumed convergence order.
   `fem6_core.l1_weights` sets `b[0] = 1.0` explicitly; `l1_weights(4,1.0)` now
   returns `[1,0,0,0,0]` and `l1_weights(4,0.7)` is unchanged, so **no archived
   number moved** (the suite reproduces all 60 checks).

5. **Coupling factors (B2).** New Table `tab:coupling` in Sec. 6.2
   (`Paper_12/table_coupling.tex`, generated by
   `python/make_coupling_table.py` from `results/coupling_provenance.json`):
   eight rows, each with boundary condition, mesh, μ, matrix, formula and the
   JSON entry that reproduces it. The text now says explicitly that the 1.5 %
   between 0.4650 and 0.4583 is the choice of memory matrix, that the 0.07 %
   between 0.4583 and 0.4580 is μ, and that nothing is averaged. The three
   wrong labels (B2) are gone from the text, from Table 3's caption, from
   Fig. 2's caption and from the ring-down caption.

6. **Charge and voltage (B3).** The two electrode relations are printed with
   their units — `Q = dᵀu − βV` (charge when driven) and `V_oc = dᵀu/β`
   (voltage when open) — and the sentence says they are not interchangeable.

7. **Three effects (B4).** One sentence in Sec. 2.2: the memory acts on the
   damping at fixed eigenfrequency, the window on the stiffness at fixed
   memory, μ on the coupling at fixed geometry, and no result below is
   attributed to one when it was computed with another changed.

8. **Window range (B5).** `a/L ≤ 0.2` is an "assumed operating range, not a
   validated truncation threshold", in Sec. 7.3 and twice in Sec. 6.3, with the
   reason: no experiment and no exact averaging operator is available here.

9. **Small-loss decrement (B6).** `ζ = (ωτ)^α sin(πα/2)/2`, hence
   `δ ≈ π(ωτ)^α sin(πα/2)`, checked at α = 1 against `δ = πωτ` and against the
   1.2 % small-loss error already quoted; a single decrement fixes only the
   product, so the pair needs two frequencies.

10. **Editorial asides (C2).** Reworded as statements of fact.

---

## Stage 2 — the gates, actually run

| gate | command | result |
|---|---|---|
| full suite | `python/run_all.py` (with figures) | **60/60 PASS**, 7 min 15 s; `results/SUMMARY.md`, `results/summary.json` |
| manuscript numbers | `python/check_paper_numbers.py` | **85/85 agree, 0 stale-token hits of 12** |
| provenance (new) | `python/check_coupling_provenance.py` | **10/10**, every recomputed row equal to the archive at relative difference 0 |
| float order | `python/check_float_order.py` | agrees: figs 1–10, **tabs 1–9** (the new table is #3) |
| structure / labels | `python/check_paper_structure.py` | nothing to report |
| unverified list | `python/list_unverified.py` | 29 entries, 0 stale |
| abstract claims | `python/audit_abstract_claims.py` | 3 held, 5 not held, 3 inputs, 0 uncovered tokens |
| references | `Paper_12/check_refs.py` | 62 entries, 47/58 FEM-1 references carried, 0 field mismatches; Crossref offline, 62 unchecked |

`run_all.py` now also runs `coupling_provenance.py → make_coupling_table.py →
check_coupling_provenance.py` and gates the result as **N4**.

---

## UNVERIFIED

* **Compilation, page count, float placement, overfull boxes.** No TeX
  distribution in this environment. The paper was **not** compiled, and the
  30-page target is unmeasured.
* **The new table has never been typeset.** Seven columns at `\footnotesize`
  may still be too wide; `\small` or a landscape float is the fallback.
* **Rendered reference numbers.** `elsarticle-num` numbers by citation order,
  so "[62]" in the brief cannot be confirmed to be the Gupta entry in the
  typeset output; the *entry* is exactly as specified.
* **DOI resolution** for `fem1` (10.1016/j.finel.2026.104681) and for the 13
  entries carrying `TO VERIFY`: Crossref is unreachable, so they are
  unchecked, not confirmed.
* ~~**C3**~~ — reproducible after all, and fixed in round 19 (see the addendum
  at the end); **C4** could not be reproduced in the current files and was
  therefore not edited.

---

# Round 19 addendum — the four leftovers

Nothing else was touched. Each item below is one of the four, with the lines it
changed.

### 1. Run-in headings printed ".."

**Confirmed, and my round-18 verdict was wrong.** I had checked only that the 21
sites were *consistent* with each other; consistency was the wrong question,
because the class prints its own terminator, so a source title ending in a
period sets as `Window..`. The compiled `Paper_12_4.pdf` the author supplied
shows it about 20 times. The period inside the braces is removed at all 21
sites:

| file | sites (line of the `\paragraph`) |
|---|---|
| `Paper_12/sec/06_results.tex` | 193, 210, 227, 253, 283, 444, 512, 527, 542, 555, 720, 762, 792, 806 (14) |
| `Paper_12/sec/07_calibration_limitations.tex` | 67 (1) |
| `Paper_12/sec/91_appendixA.tex` | 24, 37, 46, 56, 67, 79 (6) |

`grep -c '\\paragraph{[^}]*\.}'` over `main.tex` and `sec/*.tex` is **0** after
the edit. **The typeset heading output is UNVERIFIED**: there is no TeX here, so
the only evidence for the class behaviour is the PDF the author compiled. If the
class turns out to print no terminator at all, the fix is to restore the 21
periods, which is a one-line `sed`.

### 2. The flexoelectric growth sentence (round-18 item C3)

The sentence claimed that "the analytic route gives the order of the effect and
the factor by which it grows". It gives a factor of **100**, because
$x=3\mu^{2}/(C^{p}_{xx}h^{2}\kappa_{yy})$ scales as $h^{-2}$, while the finite
element coupling — $k^{2}$, which equals $x$ to first order while
$k^{2}\ll1$ — grows by **24** over the same span. The two routes are not the same
quantity and the text now says so, with the gap read as the window averaging the
through-thickness gradient, **stated as a hypothesis** because the
second-moment model carries no through-thickness resolution. At
$h=\SI{10}{\micro\metre}$ the FEM value is **2.05** times below the analytic $x$
($3.5704\times10^{-4}/1.7437\times10^{-4}=2.047$).

| where | change |
|---|---|
| `Paper_12/sec/06_results.tex:263–283` | new sentence set: $h^{-2}$ (100) against FEM (24), the 2.05 factor, the window-average hypothesis, and the local slopes ($-1.96$, $-1.52$, $-0.43$) now described as approaching the analytic $h^{-2}$ at large $h$ |
| `Paper_12/sec/06_results.tex:320` | `tab:worked`, row "flexoelectric growth": `factor $24$` → `$100$ ($h^{-2}$) vs $24$ (FEM)`; the other cells of the row are unchanged |
| `python/check_paper_numbers.py` | two rows added so the new numbers are graded: `100` from `worked_example.json` $(h_{\max}/h_{\min})^{2}$ and `2.05` from `x_analytic_h10 / demo k2_flexo[0]` (rel. tol. 5e-3) |

No other number moved: `demo.json` and `worked_example.json` were not re-run,
they already held `x_analytic_h10 = 3.57041e-4` and `growth = 23.935`.

### 3. `references.bib` comments and the "nanos" typo

| change | detail |
|---|---|
| comment block removed | the four lines from `%% --- part 3: placeholders for self-citations ---` through the note naming `[FEM-1]`, `[FEM-4]`, `[FEM-5]`. No entry was removed: the file still holds **62** entries, all cited. `grep -n "FEM-4\|FEM-5\|placeholder" references.bib` is now **empty** |
| **defect found and fixed** | the file ended with `}}`: **595 opening and 596 closing braces**, a stray brace left by the round-18 `fem1` replacement (it is present in `8c07ba8` and absent in `2a88232`). BibTeX would have had to recover from it; it is removed, and the braces now balance 595/595 |
| "nanos" | one hit in the whole repository, `nanostructures` (`sec/01_introduction.tex:67,110`), which is a word and not a unit. Nothing to fix |

`Paper_12/check_refs.py` re-run: 62 entries, 47/58 FEM-1 references carried,
0 field mismatches (Crossref still offline).

### 4. `tab:coupling` width

The first version was seven natural-width columns plus a
`p{0.30\textwidth}` source column, about **540 pt** against a `\textwidth` of
about 470 pt — that is why it had never been typeset: it would have been
overfull. It is now six columns at `\small`, `\tabcolsep` 4 pt, two short
`p{}` columns (0.20 and 0.24 of the text width) and abbreviated measure and
header labels:

```
$k^{2}$ | build | mesh | $\mu$ | measure | archive
```

with $x=d^{\mathsf T}K_{sc}^{-1}d/\beta$ and
$k^{2}_{s}=(\omega_{oc}^{2}-\omega_{s}^{2})/\omega_{oc}^{2}$ defined once in the
caption, and the $\mu$ unit moved into the caption as well. Estimated width
$0.44\,\textwidth+160\,\mathrm{pt}\approx370$ pt at
$\textwidth\approx470$ pt, i.e. about 0.78 of the text block.

* **Every value is unchanged**: the eight numbers, their order, their build,
  mesh, $\mu$ and matrix are the same. `check_coupling_provenance.py` still
  passes 10/10 and still finds `$%.5f$` of every row in the table.
* Files: `python/make_coupling_table.py` (rewritten to emit the six-column
  body), `Paper_12/table_coupling.tex` (regenerated), and the caption and
  `\footnotesize → \small` in `Paper_12/sec/06_results.tex:96–116`.
* **The width is still UNVERIFIED**: the 370 pt figure is arithmetic on
  nominal character widths, not a measurement. If it is overfull on Overleaf,
  the next step is to drop the `mesh` column into the `build` column (it is the
  same for six of the eight rows).

---

## Round 19 — gates actually run

| gate | result |
|---|---|
| `python/check_paper_numbers.py` | **87/87 agree** (85 round-18 rows + the 2 new ones), 0 stale-token hits of 12 |
| `python/check_coupling_provenance.py` | 10/10, table still quotes all 8 rows |
| `python/check_float_order.py` | agrees: figs 1–10, tabs 1–9 |
| `python/check_paper_structure.py` | nothing to report |
| `python/list_unverified.py` | 29 entries, 0 stale |
| `python/audit_abstract_claims.py` | 0 uncovered tokens |
| `Paper_12/check_refs.py` | 62 entries, 0 field mismatches |
| `python/run_all.py` | **60/60 checks pass** |

## Round 19 — UNVERIFIED

* **Compilation, page count, float placement, overfull boxes.** No TeX in this
  environment. In particular the doubled-period fix is verified only against the
  compiled PDF the author supplied, not re-compiled here.
* **The heading output of `\paragraph`** after the edit: the class must supply
  the single terminator for the text to read "Window. For half-widths …".
* **The width of `tab:coupling`**: 370 pt is an estimate from nominal widths,
  not a measurement; and it has still never been typeset.
* **DOI resolution** for `fem1` and the 13 `TO VERIFY` entries (Crossref
  unreachable).
