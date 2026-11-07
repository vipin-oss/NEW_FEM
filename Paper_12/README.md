# Paper_12 — manuscript (FEM-6)

`main.tex` is the elsarticle manuscript for the FEM-6 framework.
Title: *A C¹ Bogner–Fox–Schmit finite element framework for fractional-memory
piezoelectric–flexoelectric strain-gradient solids with a rectangular nonlocal
averaging window*.

## Build

```
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

The bibliography is `references.bib`; `bibtex` is required. A full TeX Live is
not available in this build environment, so the mandated sequence above remains
to be run by the author. An offline Tectonic diagnostic compiles the manuscript
to 33 pages with 0 undefined references and no doubled appendix or run-in
heading; `results/paper_structure.md` records the independent structural audit:
balanced braces and environments, every `\ref` having a `\label`, every
`\cite` having a bibliography entry, all twelve included figures present,
`\input` files present, and 102/102 quoted numbers agreeing with the JSON they
came from. Compile it once with a full distribution before reading it as
finished.

## Figures

Ten vector figures, all produced by `python3 python/run_paper_figures.py`
(part of `run_all.py`); the PDFs are copied into `figures/`.

| file | figure | message |
|---|---|---|
| `P1_geometry.pdf` | Fig. 1 | the two electrode configurations and the window |
| `P2_petals.pdf` | Fig. 2 | f₁ and k² against window angle, as polar petals |
| `P3_map_k2_AR_theta.pdf` | Fig. 3 | the same sweep over (θ, aspect ratio) |
| `P4_mode_shape_potential.pdf` | Fig. 4 | deformed mode with the open-circuit potential in color |
| `P5_root_locus.pdf` | Fig. 5 | complex poles over α and ωτ |
| `P6_ringdown.pdf` | Fig. 6 | ring-down for four Caputo orders |
| `P7_thickness.pdf` | Fig. 7 | flexo size effect against a constant piezo coupling |
| `P8_mode_tracking.pdf` | Fig. 8 | one mode shape at four thicknesses (MAC) |
| `P9_damping_surface.pdf` | Fig. 9 | ζ over the (α, ωτ) plane |
| `P10_window_shape.pdf` | Fig. 10 | window shape versus second moment |

`results/figures/paper/` holds the same set as PDF + PNG; the PNGs are for
quick inspection only.

## Where the numbers come from

Every number in the text is a value from `python3 python/run_all.py`
(60/60 checks):

| in the paper | source |
|---|---|
| `tab:verification` (60 checks, Appendix B) | `results/summary.json` → `checks`, rendered by `python/make_paper_table.py` into `table_verification.tex` (never typed by hand) |
| `tab:application` (plane strain vs stress, four cases) | `results/application_table.json` → `rows` |
| `tab:memory` (memory matrix, S1) | `results/memory_variants.json` → `S1` |
| `tab:modulus` (KV vs Zener, S2, Appendix C) | `results/memory_variants.json` → `S2` |
| §5.1 orientation numbers | `results/paper_figures_data.json` → `polar` |
| §5.4 thickness numbers | `results/demo.json` → `flexo_thickness` |
| coupling closed forms (C1–C4) | `results/coupling_check.json` |
| `tab:coupling` (every coupling factor, eight rows) | `results/coupling_provenance.json`, recomputed by `coupling_provenance.py`, rendered by `make_coupling_table.py`, graded N4 by `check_coupling_provenance.py` |
| §4.4 derivation and `tab:closedform` | `results/k2_closed_form.json`, `table_closed_form.tex`, `table_wrong_series.tex` |
| mode tracking (K1–K2) | `results/mode_tracking.json` |
| `tab:independent` (independent routes, I1–I9) | `results/independent_checks.json`, rendered by `run_independent_checks.py` into `table_independent.tex` |
| `tab:axes` (axes, Voigt indices, the two poling configurations) | the same JSON, rendered into `table_axes.tex` (panel F5) |
| `tab:config` (piezo-only / flexo-only / both on one bending mode) | `results/config_table.json`, rendered by `run_config_table.py` into `table_config.tex`, graded G1–G2 |
| the list of unverified numbers | `results/unverified_numbers.md`, written by `list_unverified.py`, graded N2 |
| `tab:sens` (platform sensitivity of the h = 1 µm point) | `results/sensitivity.json`, written by `run_sensitivity.py`, graded U1–U3 |
| abstract, number by number | `results/abstract_audit.md`, `results/abstract_audit.json` (criterion A2) |
| poles and damping map | `python/fem6_core.py::complex_frequency` with branch continuation |

`python3 python/derive_k2_closed_form.py` reproduces the coupling factor from
the material constants, step by step, and also reproduces the superseded
`0.3582` series as `k^2/(1+k^2)` of the current one — that identity is what
identifies the earlier number as the same formula applied twice.

`python3 python/check_paper_numbers.py` re-checks 51 of those claims against
the JSON and writes `results/paper_number_audit.md`; it is graded as criterion
N1, so a stale number in the text fails the suite.

`python3 python/run_independent_checks.py` (criteria I1–I9, `tab:independent`) is the
other half of that argument: it reproduces eight headline numbers along routes
that never touch the assembled matrices — Euler–Bernoulli and Timoshenko beam
theory, the real roots of a polynomial that the fractional pole equation
becomes for rational order, a three-scalar energy identity for the
flexoelectric coupling in the uniform-curvature limit, and a quadrature for
the second moments of the three window shapes.  Its last panel is the one
that settles the indexing question: the flexoelectric polarization of the
bending field is normal to the long faces, so only a plate poled along $y$ can
collect it, and the modulus that belongs with the permittivity
$\kappa_{33}$ is then $C^p_{xx}=\SI{1.6946e11}{\pascal}$ -- the entry that the
poling-$x$ table of Sec.~\ref{sec:closedform} calls $C^p_{22}$.  The pairing of
the poling-$x$ modulus $\SI{9.55e10}{\pascal}$ with $\kappa_{33}$ gives
$6.34\times10^{-4}$, 77 % away from the finite element value, and corresponds
to no configuration.

`python3 python/run_config_table.py` (criteria G1–G2, `tab:config`) answers
the question that follows from the two configurations: what do the
piezoelectric terms do on the *bending* device?  Three materials, one
geometry, the same mode.  With `μ = 0` the piezoelectric coupling of that mode
is `1.0e-10` at every thickness — the piezoelectric charge of a bending mode is
odd in `y − h/2` and integrates to zero over a face electrode — so the device
is not piezoelectric by accident.  With `e = 0` the flexoelectric coupling
grows by 31 instead of the 24 reported for the real crystal: the
piezoelectric terms shift the flexoelectric coupling by up to 24 % at the
thinnest plate, through the elastic stiffness of the same mode.

`python3 python/run_sensitivity.py` (criteria U1–U3, `tab:sens`) runs one
model through four mathematically equivalent eigensolver paths on whatever
numpy/scipy stack invoked it, and merges the runs of other stacks that were
written with `--emit`.  The h = 1 µm flexoelectric coupling — a difference of
nearly equal eigenvalues of a pencil with condition ~10¹² — spreads by 0.18 %
over four stacks (numpy 1.26.4 / 2.0.2 / 2.2.6 / 2.4.6, scipy 1.11.4 /
1.13.1 / 1.15.3 / 1.17.1) and four paths, while the h = 10 µm value spreads by
1.5e-5 %.

The spread is `(max - min) / midpoint` over all equivalent rows, and the table's
deviations are taken from that same midpoint — *never* from the stack that
happens to be running.  The first version of this script measured deviations
from the running stack, and that number is a statement about the machine: it
read 0.11 % here and 0.15 % on the reviewer's Python 3.13 / numpy 2.5.3 /
scipy 1.18.1 stack for the same range.  The paper therefore quotes the point as
4.2e-3, the growth as 24, and the spread as an upper bound — "within 0.5 %" —
which N1 checks as `spread ≤ 0.5`, so a different stack cannot fail the row by
sitting at one end of the range.  The two 5e-3 relative-tolerance rows for
4.2e-3 and 24 remain for the same reason.  Truncating the secular sum to
twelve modes moves k² by more than 80 %, which is why the sum runs over the
whole spectrum.

`python3 python/list_unverified.py` (criterion N2) writes
`results/unverified_numbers.md`: every number in the paper that no independent
route reproduces, with the reason, checked against `main.tex` so that it cannot
cite a number the text no longer contains.

`python3 python/audit_abstract_claims.py` (criterion A2) lists every numeric
token of the abstract with the verdict `hua` (an independent route
reproduces it) or `nahi hua` (traceable, but no independent route), in
`results/abstract_audit.md`.  It fails if the abstract grows a number without
a verdict, so the two cannot drift apart.  The six that are *not* checked
independently are the extensional $k^2=0.4650$, the $\zeta$ ratio $0.449$,
$\zeta_{\rm eff}=0.15023$ (only its distance from $0.15000$ has an exact
reference), the $19\,\%$ window-orientation effect, the $0.09\,\%$ spread of
the piezo $k^2$ over the thickness sweep, and the $24$ growth factor of the
flexoelectric one.  All six are finite element outputs; the operators behind
them are verified, the numbers themselves are not.

## Placeholders that must be filled before submission

Each is marked `% TODO` in `main.tex`.

1. **Author, affiliation, corresponding e-mail.**  Not supplied in the
   delivered material.
2. **Self-citations `fem1`, `fem4`, `fem5`.**  The three papers of this series
   are cited (they carry the novelty claims and the FEM-4 overlap that the
   introduction pre-empts) but their bibliographic details are placeholders —
   restore them from the delivered FEM-1 / FEM-4 / FEM-5 packages.
3. **Journal name** in `\journal{}` — currently *Finite Elements in Analysis
   and Design*; change to the target journal.

## Unverified items, restated

The manuscript says these in the Limitations section and repeats them where
the numbers are used.  They are not placeholders in the text — they are stated
as unverified on purpose:

* `rho = 6020 kg/m³` — affects every frequency as `rho^-1/2`; no primary
  source in this work.
* `mu = 1e-6 C/m` — nominal; the flexoelectric panels scale as `mu^2` and are
  sensitivity studies, not predictions for BaTiO₃.
* The plane-stress reduction is a modeling choice (worth 12 % in k² for the
  extensional case, 35 % for the y-coupled one, and 2.8 % below the 3-D
  closed form before any kinematics is chosen).
* The saturation of the flexoelectric size effect below 2 µm is converged but
  its attribution to the window/thickness ratio is an interpretation.

## Reviewer risks

`REVIEWER_RISKS.md` lists the eight points a referee is most likely to raise,
each with the section that already addresses it and what is still missing.

## Journal-layout restructure (FEM-1 style)

`main.tex` now follows the layout of the published FEM-1 paper: elsarticle
`[final,3p,times,fleqn]`, the same geometry and line spacing, numbered
sections, `Figure n:` / `Table n:` captions with the parameter list in
parentheses, numbered references from `references.bib`. The body is split into
`sec/01_introduction.tex` … `sec/92_appendixB.tex`; `main.tex` holds only the
preamble, the front matter and the back matter. Twelve vector figures
(F1–F9, FB1–FB2, F11_designmap) and every table that carries numbers — in the body and in
Appendix C — are generated by `run_all.py`; none is typed by hand.

References: every entry is either copied verbatim from the FEM-1 reference file
(58 published entries, all with DOIs) or, for the flexoelectric,
fractional-viscoelastic and harvesting literature that the new subject needs,
tagged `note = {UNVERIFIED: ...}` in `references.bib` when no publisher record
could be checked; fifteen entries carry that explicit flag. Entries resolved against Crossref carry their verified
fields; nothing is invented.
