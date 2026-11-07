# Round 2 — computation, code and figures

Working note, not part of the typeset paper. It lists what changed in the code
and in the figures, every number whose printed value moved (old → new, with the
reason and the file that now produces it), the gate status after the change,
and everything that could not be verified in this environment.

Round 1 froze the computation: structure, language and editorial quality only.
Round 2 unfreezes exactly one thing — code, figures and the numbers those
produce. The manuscript text is otherwise untouched except for the
British→American spelling sweep. Every changed number below is re-entered in
`python/check_paper_numbers.py`, so the audit re-derives it from the JSON that
the pipeline writes, and the stale-token gate fails if a retired literal
survives anywhere in `Paper_12/sec/`.

---

## 1. One entry point, deterministic by construction

`python3 python/run_all.py` is still the only entry point; it now runs **28
scripts** and grades **70 checks** (was 62). What was added or tightened:

| item | change |
| --- | --- |
| new pipeline steps | `check_coupled_patch.py`, `check_numerics.py`, `sensitivity_tornado.py`, `run_design_map.py` (the last was initially run by hand, so `design_map.json` could drift from the figure) |
| determinism | a new `python/deterministic.py` pins `OMP/OPENBLAS/MKL/NUMEXPR/VECLIB` threads to 1 and `PYTHONHASHSEED=0`; `run_all.py` exports the same values to its children, and the two stack-sensitive scripts (`run_design_map.py`, `check_numerics.py`) import it directly, so a standalone run reproduces the pipeline bit for bit. The package draws **no random numbers** (`grep -r random python/` is empty), so there is no seed to fix, and pinning the BLAS thread count removes the one remaining run-to-run variation (reduction order) |
| environment | every run writes `results/environment.json` — python, numpy, scipy, matplotlib, platform, git commit, the thread pin, and the statement that no RNG is used; gate **E1** fails if the file is missing |
| dead code | none. All 25 `python/*.py` scripts are either pipeline steps (23) or the two libraries (`fem6_core.py`, `materials.py`). `sync_to_overleaf.py` is the only script outside the pipeline and is documented as a deployment helper in `README.md`, not a computation |
| fail loudly | unchanged: `run_all.py` exits non-zero unless every check passes, and each gate row prints the measured value and its criterion |

Note on the thread pin: pinning changes the last digits of five result files
(`dt_study.json`, `memory_variants.json`, `verification.json`,
`flexo_check.json`, `material_comparison.json`) at the 1e-12 relative level.
No printed number moved because of it. One quantity *is* stack-sensitive at the
2 % level — the smallest flexoelectric coupling of the design map, which is a
difference of nearly equal eigenvalues (condition number 1e27 at
`h = 1 µm`) — see §3.

## 2. Independent verification layer

| gate | what it checks | result |
| --- | --- | --- |
| **P3** | coupled patch test on one element with an exact field (constant strain, constant potential gradient, uniform field), assembled enthalpy vs the analytic one, all five energies | rel. err **7.0e-16** |
| **Y1** | the assembled coupled matrix is symmetric, the saddle blocks are exact transposes, and the inertia is (n_mech, n_phi, 0) | `|S−Sᵀ|/|S|` **1.7e-17**, inertia (96, 14, 0), one null mode of `C_phi` |
| **H1** | generalized eigenproblem vs a Cholesky-standardized pencil, first six modes, `h = 1 µm` | worst rel. diff in ω² **2.3e-4**, `cond K` 7.3e27 |
| **H2** | L1 weights: `b_0 = 1` for every α (the `0**0` case) and cancellation against a 50-digit `Decimal` evaluation | `b_0` ok for α = 0.1…1.0, worst rel. err **3.9e-10** |
| **H3** | time-step independence at α < 1, dt / dt/2 / dt/4 / dt/8 | observed orders **1.97, 1.50** (α = 0.5) and **0.84, 1.47** (α = 0.7) — first order, as the scheme is |
| **H4** | modal truncation of the ring-down, 8 and 20 modes against 40 | K_uu **3.0e-4** / **5.1e-5**, K_eff **2.0e-14** |
| **S3** | tornado over µ, ρ, a₂, τ | reported (below), not graded |
| **E1** | environment record | present |

Two design decisions worth recording:

* The `dt` measure is the L2 difference of the whole record from a 6400-step
  reference on 401 interpolated points. Three cheaper measures were tried and
  rejected: the endpoint voltage, the peak ratio and a coarse-grid peak
  amplitude are each non-monotone in dt (they gave "orders" of −0.06, 3.06 and
  4.17), because the amplitudes are differences of nearly canceling modal
  contributions.
* The truncated modes are compared by ring-down response, not by eigenvalues
  alone: the mode shapes enter through the initial condition, and an
  eigenvalue-only comparison (the old `verification.json` truncation rows,
  6.7 % at 8 modes) measures something the paper never quotes.

## 3. Numbers that changed, old → new

| where | old | new | reason, and where the new value comes from |
| --- | --- | --- | --- |
| §5.4, memory on `K_eff`, 8 vs 40 modes | 2.3e-14 | **2.0e-14** | the sentence now quotes the ring-down truncation measure (`numerics.json`, gate H4) instead of an eigenvalue expansion; re-measured with the pinned numeric stack |
| §5.4, memory on `K_uu`, 8 vs 40 modes | 3.6e-4 | **3.0e-4** | same measure, same source |
| §5.4, memory on `K_uu`, 20 vs 40 modes | 5.9e-5 | **5.1e-5** | same measure, same source |
| §7 and conclusions, smallest flexo `k²` of the design map | 3.69e-6 | **3.6e-6** | `design_map.json` re-generated inside the pipeline (it had initially been produced by a manual run); quoted to two significant digits because this is the one quantity that moves at the 2 % level between numeric stacks — it is a difference of nearly equal eigenvalues in the worst-conditioned corner of the map |
| §7, smallest flexo/piezo ratio of the design map | 6.6e-6 | **6.5e-6** | same re-run; same reason for two significant digits |
| everything else | — | unchanged | `check_paper_numbers.py`: **102/102 agree** (was 99), 0 stale tokens of 14 |

The top of the design-map range moves by 0.02 % between stacks (`1.03e-2` is
stable to all printed digits), so only the two lower endpoints are quoted at
two significant digits.

## 4. Sensitivity (A.4) — `results/sensitivity_tornado.md`

±10 % in each input, against the three headline outputs. Solver rows use the
production 48×4 mesh; ρ and τ enter through exact scaling, which is why their
other columns are exactly zero.

| input | perturbation | factor 24 | flexo k² (1 µm) | damping ζ |
| --- | --- | --- | --- | --- |
| µ | +10 % | −1.2 % | **+19.3 %** | 0 |
| µ | −10 % | +1.2 % | −17.9 % | 0 |
| a₂ | +10 % | **−15.0 %** | 0 | 0 |
| a₂ | −10 % | +18.1 % | 0 | 0 |
| ρ | ±10 % | 0 | 0 | −4.7 % / +5.4 % |
| τ | ±10 % | 0 | 0 | ±10.0 % |

Reading: the flexoelectric coupling carries µ² (19.3 % ≈ 2 × 10 %), so the
*ratio* of the two thicknesses cancels it to within the (1+x) saturation and a
1 % residual from the coupling's own contribution to the stiffness; the window
size is the strongest lever on the ratio; ρ and τ move the damping only, and τ
linearly. No new material data is introduced — the perturbations are ±10 % of
the values already in `materials.py`.

## 5. Figure review

All twelve figures were opened at 220 dpi in Round 3. Defects found and fixed:

| figure | defect | fix |
| --- | --- | --- |
| F3 (fields) | moiré banding across the whole panel from `shading="gouraud"` on the 5×49 nodal array; a diverging map used for a single-signed field; one empty panel slot (whitespace where (f) would be) | the field is now evaluated from the element's **own bicubic Hermite basis** on a fine grid (the computed field, not a smoothed sample of it); the potential stays bilinear, which is what the element carries; sequential map for `w`, diverging only for the antisymmetric `u_x`; layout 2+3 with no empty cell; a color bar per panel |
| F4 (orientation) | `\rm` subscripts were dropped by mathtext, so the panels read "f ext/ext(0)"; color maps were stepped (16 levels); the radial tick label sat on a curve; isoline labels on the frame edge lost their leading digit; a wide empty band between the two rows | `\mathrm` subscripts; 40-level maps with six labeled isolines; radial labels moved to 104° with a white halo; a few points of x-margin so edge labels stay whole; row spacing tightened; aspect-ratio curves now take the shared color of §B6 below |
| F5 (design) | the aspect ratio was colored by its position in this figure's list, so AR = 2 was blue here and AR = 5 was pink here but orange in F4 | one `ar_color(AR)` keyed on the *value* of the aspect ratio (`AR_ORDER`), used by F4 and F5; a sequential log(AR) map was tried first and rejected because it made AR = 2 and AR = 3 indistinguishable inside one panel |
| F6 (damping) | no reference curve for the fractional poles; the y-range clipped the α→1 end of the high-τ curve, hiding the most informative part of panel (a) | the **exact Kelvin–Voigt arc** `y = √(1−x²)` is drawn dashed; the range is widened to 0.60–1.55 so every α = 1 endpoint is visible and lands on the arc (worst deviation 2.9e-7, from evaluating at α = 1 − 1e-7) |
| F11 (design map) | the `a₂/L = 0.2` line was white and sat exactly on the top spine (invisible); white contour labels vanished over the bright part of the map; the `a₂ = h` label was white on a bright background | the boundary is now stated inside the frame (`a₂/L ≤ 0.2`), contours and labels are black with inline spacing, and the `a₂ = h` label carries a white halo |
| all figures | `\rm` in mathtext | `\mathrm` throughout `run_paper_figures.py` and `run_design_map.py` |

Unchanged and deliberately so: the font is `STIXGeneral` (the paper's Times
face), the categorical palette is Okabe–Ito, quantities that repeat across
figures keep one color map (k² → viridis, f_ext → cividis), panel labels stay
(a)(b)(c), and no new figure was added — the two "new figure" slots were filled
in round 1 by F4 and F6, and this round only repaired them. Every figure's data
is written to `results/` (`paper_figures_data.json`, `design_map.json`, …) and
each caption is ≤ 80 words with a numbered discussion paragraph in the text.

## 6. Gate status after round 2

```
python3 python/run_all.py
  70/70 checks pass -> PASS          (was 62/62)
  manuscript numbers: 102/102 agree, 0 stale of 14   (was 99/99)
  structure: braces, environments, refs, cites, graphics — clean
  consistency: 44/44
  float order: agrees
```

## 7. UNVERIFIED

* **Compilation, page count and float placement.** No full TeX Live exists here;
  an offline static Tectonic diagnostic builds a 35-page PDF with 0 undefined
  references and no doubled appendix or run-in heading. The mandated
  `pdflatex; bibtex; pdflatex x2` sequence remains to be run by the author.
* **Figure rendering at press size.** The defects above were judged on 220 dpi
  raster copies; whether 6 pt labels survive the final two-column reduction is a
  typesetting question this environment cannot answer.
* **Seven target figures were reopened at 220 dpi in Round 3.** F1, F2, F7,
  F8, F9, FB1 and FB2 were all inspected full size; F1, F2 and FB2 layout
  overlaps were fixed, and F9 was given distinct line styles and markers.
* **The 2 % stack sensitivity of the design map's lower endpoints** is measured,
  not eliminated. Single-threaded, the map's smallest coupling is 3.608e-6;
  multi-threaded it is 3.687e-6, i.e. the second significant digit moves. The
  text therefore quotes 3.6e-6 and 6.5e-6 — two significant digits, and the
  values the pinned, documented pipeline produces. A different BLAS (or a
  different machine's summation order) may still move that digit; the top of
  the range (1.03e-2) and every other number in the paper are stable to all
  printed digits. This is a property of the worst-conditioned corner of the
  map (cond K ~ 1e27 at h = 1 µm), not of the solver: the same coupling at
  h = 10 µm agrees across stacks to 1e-12.
