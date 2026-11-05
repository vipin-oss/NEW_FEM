# Verification table as it appears in the manuscript

54/54 checks pass.

| id | checked quantity | value | criterion | source |
|---|---|---|---|---|
| V1a | patch energy, rel. error | 4.44e-16 | < 1e-12 | `results/verification.json` |
| V1b | gradient energy under constant strain | 1.06e-12 | < 1e-9 | `results/verification.json` |
| V1c | K_g(ellipsoid) vs FEM-1 (l^2/10) | 3.40e-16 | < 1e-12 | `results/verification.json` |
| V1d | K_g(cuboid)/K_g(ellipsoid), equal a | 1.666667 | = 5/3 = 1.666667 | `results/verification.json` |
| V1e | cuboid vs ellipsoid at equal M | 0.00e+00 | = 0 (< 1e-12) | `results/verification.json` |
| V2 | FEM-1 benchmark, u_R at l/L = 0.20 | 4.2339 um | within 2 % of 4.23 um (paper) | `results/verification.json` |
| V3 | observed mesh order | 1.68 | > 1.5 | `results/verification.json` |
| V4a | bending mode k_eff^2 (piezo only) | 2.27e-10 | < 1e-6 (no net charge in bending) | `results/verification.json` |
| V4b | length-extensional max k_eff^2 | 0.3991 | > 0.35 | `results/verification.json` |
| V5a | alpha = 1 vs closed-form KV, order | 0.99 | > 0.9 | `results/verification.json` |
| V5b | harmonic |H|, worst deviation | 0.37 % | < 2 % | `results/verification.json` |
| V5c | tau -> 0 residual | 2.08e-09 | < 1e-6 | `results/verification.json` |
| V5d | delivered L1 stencil vs analytic |H| | 0.52 % | < 1 % | `results/verification.json` |
| V6a | static truncation, 24 modes | 3.19e-02 | < 5e-2 | `results/verification.json` |
| V6b | static truncation, monotone decreasing | yes | monotone | `results/verification.json` |
| V7 | equal-M cuboid vs ellipsoid, max rel. diff | 0.00e+00 | < 1e-12 | `results/verification.json` |
| F1 | flexo patch test, mu = 0 | 0.00e+00 V | = 0 | `results/flexo_check.json` |
| F2 | flexo patch test vs mu*kappa*h/kappa33 | 1.0000000000 | = 1 (1e-10) | `results/flexo_check.json` |
| F3 | flexo linearity V(2mu)/V(mu) | 2.0000000000 | = 2 | `results/flexo_check.json` |
| F4 | bending k_eff^2 with flexo (mu=1e-6) | 1.25e-04 | > 1e-5 | `results/flexo_check.json` |
| M1 | kappa11/kappa33 | 39.3 | > 30 (real crystal, was 1.2) | `results/material_comparison.json` |
| S1a | zeta(K_eff, alpha=1) vs omega*tau/2 | 0.15023 vs 0.15000 | within 2 % | `results/memory_variants.json` |
| S1b | zeta(K_uu)/zeta(K_eff) at alpha=1 | 0.449 | in (0, 1) -- the choice matters | `results/memory_variants.json` |
| S2 | KV/Zener modulus at omega*tau = 1, alpha = 1 | 1.345 | > 1.3 (KV unbounded) | `results/memory_variants.json` |
| C1 | FEM k^2 (unconstrained plate) vs 2-D closed form e^T C^-1 e/kappa | 0.56079 vs 0.56079 | rel. diff < 1e-3 | `results/coupling_check.json` |
| C2 | 2-D model vs 3-D free bar (plane-stress reduction) | 2.83 % | < 5 % (documented modelling gap) | `results/coupling_check.json` |
| C3 | FEM k^2, clamped plate, 96x4 vs 48x4 | 0.55992 vs 0.55957 | rel. diff < 1e-3 | `results/coupling_check.json` |
| C4 | FEM k^2, clamped plate, 24x2 vs 48x4 | 0.13 % | < 0.5 % (coarse mesh) | `results/coupling_check.json` |
| K1 | lowest MAC of mode 1 vs the h = 10 um shape (4 thicknesses) | 0.99919 | > 0.999 | `results/mode_tracking.json` |
| K2 | worst f2/f1 over the thickness sweep (mode off-diagonal) | 2.3e-06, f2/f1 >= 6.21 | off-diag < 1e-5, ratio > 6 | `results/mode_tracking.json` |
| D1 | closed form e'C^-1 e/kappa vs FEM coupling (free plate) | 0.56079 vs 0.56079 | rel. diff < 1e-3 | `results/?` |
| D2 | the superseded series is exactly k^2/(1+k^2) of the new one | 3.5e-06 | < 1e-5 (same formula applied twice) | `results/?` |
| I1 | clamped-free f1, FEM 48x4 vs Euler-Bernoulli closed form | 144.6 vs 143.8 kHz | |err| < 1 % (+0.54 %) | `results/?` |
| I2 | clamped-clamped f1, FEM 48x4 vs Euler-Bernoulli closed form | 919.2 vs 915.0 kHz | |err| < 1 % (+0.46 %) | `results/?` |
| I3 | clamped-free f1 at 128x4 vs Euler-Bernoulli (mesh refinement) | 144.08 kHz | |err| < 0.5 % (+0.20 %) | `results/?` |
| I4 | zeta from Newton pole vs polynomial roots (10 alpha, 2 omega*tau) | 1.4e-10 | < 1e-8 | `results/?` |
| I5 | zeta at alpha = 1 vs omega*tau/2 (both omega*tau) | 0.0e+00 | < 1e-9 | `results/?` |
| I6 | flexo x, uniform curvature: FEM energy triple vs 3 mu^2/(C11 h^2 kappa33) | 3.570415e-04 vs 3.570415e-04 | rel. diff < 1e-8 (worst 1.8e-10) | `results/?` |
| I7 | flexo Voc, uniform curvature: FEM vs mu*kappa*h/kappa33 | 1.7e-13 | < 1e-10 | `results/?` |
| A2 | every number in the abstract has an independent-check verdict | 10 hua / 7 nahi hua / 4 inputs, 20 tokens | 0 uncovered, 0 stale | `results/?` |
| G1 | piezoelectric share of the bending device (poling y, long faces) at every thickness | 5.7e-07 | < 1e-5 (electrically silent bending mode) | `results/?` |
| G2 | flexo growth with and without the piezoelectric terms | 23.9 vs 31.1 | reported 23.9 uses the real crystal; 31.1 with e = 0, both graded | `results/?` |
| I9 | the same bending field, four poling/electrode pairings: only the long faces collect it, and each pairing with its own permittivity | poled y 3.570e-04 vs 3.570e-04; poled x 1.613e-05 vs 1.613e-05; short-face pairs 7.5e-14 V | rel. diff < 1e-6, short-face charge < 1e-12 | `results/?` |
| I8 | window second-moment factors 1/3, 1/4, 1/5 by quadrature | 3.3e-06 | < 1e-5 | `results/?` |
| N2 | the list of unverified numbers cites only numbers still in the manuscript | 31 entries, 0 stale | 0 stale | `results/?` |
| A1 | application table: extensional plane stress is the strongest coupling of the four | 0.4580 | = 0.4580, largest, > 0.4 | `results/?` |
| T1 | piezo k^2 (mode-free) over h = 10 -> 1 um, max/min | 1.0009 | < 1.005 (thickness independent) | `results/demo.json` |
| T2 | piezo k^2, 24x2 vs 48x4, max rel. diff | 5.7e-04 | < 1e-3 | `results/demo.json` |
| T3 | flexo k^2, 48x4 (monotone in h) | 1.74e-04 -> 4.17e-03 | strictly increasing as h falls | `results/demo.json` |
| T4 | flexo k^2, 48x4 vs 96x4 witness | 3.5e-03 | < 0.02 | `results/demo.json` |
| T5 | flexo k^2 at mu = 0 / value (residual) | 6e-07 | < 1e-5 | `results/demo.json` |
| P1 | paper figures: vector set written | 10 PDF | = 10 (P1-P10) | `results/paper_figures_data.json` |
| P2 | orientation sweep rows / k^2 range | 168 rows, 0.3786-0.4677 | 168 rows (144 cuboid + 24 ellipse), k^2 in (0.35, 0.50) | `results/paper_figures_data.json` |
| N1 | manuscript numbers vs the JSON they came from | 51/51 | all agree | `results/?` |
