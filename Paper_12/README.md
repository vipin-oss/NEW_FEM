# Paper_12 — manuscript (FEM-6)

`main.tex` is the elsarticle manuscript for the FEM-6 framework.
Title: *A C¹ Bogner–Fox–Schmit finite element framework for fractional-memory
piezoelectric–flexoelectric strain-gradient solids with a rectangular nonlocal
averaging window*.

## Build

```
pdflatex main
pdflatex main          # twice, for \ref and the generated table
```

There is no bibliography database: the reference list is an inline
`thebibliography` block, so `bibtex` is not needed.

**Not compiled.** No TeX distribution exists in the environment where the
manuscript was written (`pdflatex`, `latexmk`, `xelatex`, `tectonic` all
absent; `pip install tectonic` finds no distribution).  What *was* checked
mechanically is recorded in `results/paper_structure.md`:
balanced braces and environments, every `\ref` having a `\label`, every
`\cite` having a `\bibitem`, all ten included figures present, `\input`
files present, and 26/26 quoted numbers agreeing with the JSON they came from.
Compile it once before reading it as finished.

## Figures

Ten vector figures, all produced by `python3 python/run_paper_figures.py`
(part of `run_all.py`); the PDFs are copied into `figures/`.

| file | figure | message |
|---|---|---|
| `P1_geometry.pdf` | Fig. 1 | the two electrode configurations and the window |
| `P2_petals.pdf` | Fig. 2 | f₁ and k² against window angle, as polar petals |
| `P3_map_k2_AR_theta.pdf` | Fig. 3 | the same sweep over (θ, aspect ratio) |
| `P4_mode_shape_potential.pdf` | Fig. 4 | deformed mode with the open-circuit potential in colour |
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
(41/41 checks):

| in the paper | source |
|---|---|
| Table 1 (41 checks) | `results/summary.json` → `checks`, rendered by `python/make_paper_table.py` into `table_verification.tex` (never typed by hand) |
| Table 2 (plane strain vs stress, four cases) | `results/application_table.json` → `rows` |
| Table 3 (memory matrix, S1) | `results/memory_variants.json` → `S1` |
| Table 4 (KV vs Zener, S2) | `results/memory_variants.json` → `S2` |
| §5.1 orientation numbers | `results/paper_figures_data.json` → `polar` |
| §5.4 thickness numbers | `results/demo.json` → `flexo_thickness` |
| coupling closed forms (C1–C4) | `results/coupling_check.json` |
| §4.4 derivation and Table 3 | `results/k2_closed_form.json`, `table_closed_form.tex`, `table_wrong_series.tex` |
| mode tracking (K1–K2) | `results/mode_tracking.json` |
| poles and damping map | `python/fem6_core.py::complex_frequency` with branch continuation |

`python3 python/derive_k2_closed_form.py` reproduces the coupling factor from
the material constants, step by step, and also reproduces the superseded
`0.3582` series as `k^2/(1+k^2)` of the corrected one — that identity is what
identifies the earlier number as the same formula applied twice.

`python3 python/check_paper_numbers.py` re-checks 32 of those claims against
the JSON and writes `results/paper_number_audit.md`; it is graded as criterion
N1, so a stale number in the text fails the suite.

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
* The plane-stress reduction is a modelling choice (worth 12 % in k² for the
  extensional case, 35 % for the y-coupled one, and 2.8 % below the 3-D
  closed form before any kinematics is chosen).
* The saturation of the flexoelectric size effect below 2 µm is converged but
  its attribution to the window/thickness ratio is an interpretation.

## Reviewer risks

`REVIEWER_RISKS.md` lists the eight points a referee is most likely to raise,
each with the section that already addresses it and what is still missing.
