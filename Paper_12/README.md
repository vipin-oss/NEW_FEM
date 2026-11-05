# Paper_12 — manuscript (FEM-6)

`main.tex` is the elsarticle manuscript for the FEM-6 framework.
Title: *A C¹ Bogner–Fox–Schmit finite element framework for fractional-memory
piezoelectric–flexoelectric strain-gradient solids with a rectangular nonlocal
averaging window*.

## Build

```
pdflatex main
pdflatex main          # twice, for \ref and the table numbers
```

There is no bibliography database: the reference list is an inline
`thebibliography` block, so `bibtex` is not needed.

**Not compiled in this repository.** No TeX distribution is installed in the
environment where the manuscript was written, so `main.tex` has been checked
only mechanically (balanced environments, no non-ASCII characters, every
`\ref` has a `\label`, every `\cite` has a `\bibitem`) — not by a LaTeX run.
Compile it once on your side before reading it as finished.

## Figures

`figures/` holds copies of `results/figures/fig1..fig5`, produced by
`python3 python/run_demos.py`.  They are copied, not generated in place: if you
re-run the demos, copy them again.

| file | in the paper |
|---|---|
| `fig1_k2_orientation.png` | Fig. 1, window orientation and aspect ratio |
| `fig2_memory_response.png` | Fig. 5, ring-down for α = 1, 0.9, 0.7 |
| `fig3_damping_ratio.png` | Fig. 4, damping ratio versus α |
| `fig4_domain_comparison.png` | Fig. 3, window shape versus second moment |
| `fig5_flexo_thickness.png` | Fig. 2, thickness sweep (flexo vs piezo) |

## Where the numbers come from

Every number in the text is a value from `python3 python/run_all.py`
(29/29 checks, `results/SUMMARY.md`):

| in the paper | source |
|---|---|
| Table 1 (29 checks) | `results/summary.json` → `checks` |
| Table 2 (plane stress/strain) | `results/material_comparison.json` |
| Table 3 (memory matrix, S1) | `results/memory_variants.json` → `S1` |
| Table 4 (KV vs Zener, S2) | `results/memory_variants.json` → `S2` |
| Table 5 (application) | `results/material_comparison.json` → `case` |
| §5.1 orientation numbers | `results/demo.json` → `orientation` |
| §5.5 thickness numbers | `results/demo.json` → `flexo_thickness` |
| Fig. 4 damping numbers | `results/demo.json` → `damping` |

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

The manuscript says these in §7 (Limitations) and repeats them where the
numbers are used.  They are not placeholders in the text — they are stated as
unverified on purpose:

* `rho = 6020 kg/m³` — affects every frequency as `rho^-1/2`; no primary
  source in this work.
* `mu = 1e-6 C/m` — nominal; the flexoelectric panels scale as `mu^2` and are
  sensitivity studies, not predictions for BaTiO₃.
* The plane-stress reduction is a modelling choice (worth up to 35 % in k²).
* The saturation of the flexoelectric size effect below 2 µm is converged but
  its attribution to the window/thickness ratio is an interpretation.
