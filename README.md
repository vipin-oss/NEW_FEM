# NEW_FEM — FEM-6 reference implementation

Independent, from-the-equations implementation of the **FEM-6** model
(fractional-memory piezoelectric strain-gradient plate on the FEM-1 BFS C1
element), used to audit the delivered MATLAB code and blueprint.

The Python code is authoritative; the MATLAB file is a mirror for delivery.

## Contents

```
python/fem6_core.py          element, assembly, potential condensation,
                             modes, L1 Caputo stepping, complex pole
python/materials.py          the material record (BaTiO3, Zgonik/FEM-5 set),
                             plane-strain / plane-stress reduction, checks
python/run_material_check.py plane strain vs stress comparison + anisotropy
python/run_flexo_check.py    flexoelectric patch test F1-F5 (exact, mesh independent)
python/run_memory_variants.py memory on K_eff vs K_uu; KV vs fractional Zener
python/run_verification.py   V1–V7 verification suite (~40 s)
python/run_all.py            ONE command: whole suite + one pass/fail table (29 checks)
python/run_demos.py          figures 1–5 + results/demo.json
matlab/FEM6_memory_piezo_SG_2D_v2.m   corrected MATLAB mirror + self-tests
docs/FEM6_checker_report.md           answers to the four blueprint questions,
                                      findings A/B/C/D, revised blueprint
docs/FEM6_cuboid_coefficient.md       Q1 in full (second-moment derivation)
docs/FEM6_thickness_sweep.md          figure 5: the three artefacts it had and
                                      the secular/static replacements
Paper_12/main.tex                     the elsarticle manuscript (step 8);
Paper_12/README.md                    placeholders and number provenance
results/verification.{md,json}        verification output
results/demo.json, results/figures/   demo output
```

## Run

```bash
python3 python/run_all.py              # ~1 min 40 s, writes results/SUMMARY.md
python3 python/run_verification.py     # 40 s, writes results/
python3 python/run_demos.py            # 50 s, writes figures
```

Requires `numpy`, `scipy`, `matplotlib`. No hard-coded paths: both scripts
resolve `results/` relative to the repository root.

## Model in one screen

Mechanical dofs per node (C1 Hermite): `u, u_x, u_y, u_xy, v, v_x, v_y, v_xy`.
Potential dofs per node: `φ, φ_x, φ_y, φ_xy`. Eight mechanical and four
potential dofs per node, 12 total.

```
[ K_uu + K_g   K_up ] [ q ]   [ f ]
[ K_upᵀ        A    ] [ φ ] = [ 0 ]        K_g = ½ ∫ M_mn B_,mᵀ C B_,n
```

with `M = ⟨ξξ⟩` the second-moment tensor of the averaging window
(cuboid `diag(a_x²/3, a_y²/3)`, 3-D ellipsoid `diag(l²/5, l²/5)` — the latter
reproduces FEM-1's `l²/10`). Condensing `φ` on the electrode gives
`K_eff = K_uu + K_up A⁻¹ K_upᵀ` and

```
k_eff² = (ω_open² − ω_short²) / ω_open² .
```

Memory: `M q̈ + K_eff [ q + τ^α D^α q ] = f`, Caputo `D^α` discretised by L1
with `b_k = (k+1)^{1-α} − k^{1-α}`, `b_0 = 1`, and Newmark (β=¼, γ=½) with the
memory term implicit.

## Status

Verification: all seven cases pass and the FEM-1 benchmark is reproduced
(4.2339 µm vs 4.23 µm published, at `l/L = 0.2` on a 20x4 mesh).

Delivered-code audit, revised: the L1 memory stencil of the delivered
`modal_fractional` reproduces the analytic transfer function to 0.52 % worst
case over `alpha = 1.0..0.3` x `Omega/w0 = 0.25..2`, and its explicit stability
bound sits just beyond the documented `gamma > 1.5` warning, so **both stand as
delivered** (an earlier finding to the contrary was my own mis-transcription
and is withdrawn; see `docs/FEM6_A1_clarification.md`). Open items: the
demonstration configuration cannot produce an electrode voltage
(`k_eff^2 = 2e-10`, physics not a bug) and the material set is a placeholder.

`matlab/` is frozen and unverified - Python is authoritative. MATLAB is not
available in this environment, so the mirror has never been executed.
