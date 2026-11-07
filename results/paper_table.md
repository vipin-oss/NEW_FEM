# The full criterion table (archive copy)

62/62 checks pass.

| quantity | value obtained | requirement | source |
|---|---|---|---|
| patch energy, rel. error | 4.44e-16 | < 1e-12 | `results/verification.json` |
| gradient energy under constant strain | 1.06e-12 | < 1e-9 | `results/verification.json` |
| K_g(ellipsoid) vs FEM-1 (l^2/10) | 3.40e-16 | < 1e-12 | `results/verification.json` |
| K_g(cuboid)/K_g(ellipsoid), equal a | 1.666667 | = 5/3 = 1.666667 | `results/verification.json` |
| cuboid vs ellipsoid at equal M | 0.00e+00 | = 0 (< 1e-12) | `results/verification.json` |
| FEM-1 benchmark, u_R at l/L = 0.20 | 4.2339 um | within 2 % of 4.23 um (paper) | `results/verification.json` |
| observed mesh order | 1.68 | > 1.5 | `results/verification.json` |
| bending mode k_eff^2 (piezo only) | 2.27e-10 | < 1e-6 (no net charge in bending) | `results/verification.json` |
| length-extensional max k_eff^2 | 0.3991 | > 0.35 | `results/verification.json` |
| alpha = 1 vs closed-form KV, order | 0.99 | > 0.9 | `results/verification.json` |
| L1 at alpha = 1, order from the N/2N/4N sequence | 0.97 (zeta 0.150111 -> 0.150029) | 0.9 - 1.1 | `results/verification.json` |
| harmonic |H|, worst deviation | 0.37 % | < 2 % | `results/verification.json` |
| tau -> 0 residual | 2.08e-09 | < 1e-6 | `results/verification.json` |
| delivered L1 stencil vs analytic |H| | 0.52 % | < 1 % | `results/verification.json` |
| static truncation, 24 modes | 3.19e-02 | < 5e-2 | `results/verification.json` |
| static truncation, monotone decreasing | yes | monotone | `results/verification.json` |
| equal-M cuboid vs ellipsoid, max rel. diff | 0.00e+00 | < 1e-12 | `results/verification.json` |
| flexo patch test, mu = 0 | 0.00e+00 V | = 0 | `results/flexo_check.json` |
| flexo patch test vs mu*kappa*h/kappa33 | 1.0000000000 | = 1 (1e-10) | `results/flexo_check.json` |
| flexo linearity V(2mu)/V(mu) | 2.0000000000 | = 2 | `results/flexo_check.json` |
| bending k_eff^2 with flexo (mu=1e-6) | 1.25e-04 | > 1e-5 | `results/flexo_check.json` |
| kappa11/kappa33 | 39.3 | > 30 (real crystal, was 1.2) | `results/material_comparison.json` |
| zeta(K_eff, alpha=1) vs omega*tau/2 | 0.15003 vs 0.15000 | within 2 % | `results/memory_variants.json` |
| zeta(K_uu)/zeta(K_eff) at alpha=1 | 0.450 | in (0, 1) -- the choice matters | `results/memory_variants.json` |
| KV/Zener modulus at omega*tau = 1, alpha = 1 | 1.345 | > 1.3 (KV unbounded) | `results/memory_variants.json` |
| FEM k^2 (unconstrained strip) vs 2-D closed form e^T C^-1 e/kappa | 0.56079 vs 0.56079 | rel. diff < 1e-3 | `results/coupling_check.json` |
| 2-D model vs 3-D free bar (plane-stress reduction) | 2.83 % | < 5 % (documented modelling gap) | `results/coupling_check.json` |
| FEM k^2, clamped strip, 96x4 vs 48x4 | 0.55992 vs 0.55957 | rel. diff < 1e-3 | `results/coupling_check.json` |
| FEM k^2, clamped strip, 24x2 vs 48x4 | 0.13 % | < 0.5 % (coarse mesh) | `results/coupling_check.json` |
| lowest MAC of mode 1 vs the h = 10 um shape (4 thicknesses) | 0.99919 | > 0.999 | `results/mode_tracking.json` |
| worst f2/f1 over the thickness sweep (mode off-diagonal) | 2.3e-06, f2/f1 >= 6.21 | off-diag < 1e-5, ratio > 6 | `results/mode_tracking.json` |
| closed form e'C^-1 e/kappa vs FEM coupling (free strip) | 0.56079 vs 0.56079 | rel. diff < 1e-3 | `results/?` |
| the superseded series is exactly k^2/(1+k^2) of the new one | 3.5e-06 | < 1e-5 (same formula applied twice) | `results/?` |
| clamped-free f1, FEM 48x4 vs Euler-Bernoulli closed form | 144.6 vs 143.8 kHz | |err| < 1 % (+0.54 %) | `results/?` |
| clamped-clamped f1, FEM 48x4 vs Euler-Bernoulli closed form | 919.2 vs 915.0 kHz | |err| < 1 % (+0.46 %) | `results/?` |
| clamped-free f1 at 128x4 vs Euler-Bernoulli (mesh refinement) | 144.08 kHz | |err| < 0.5 % (+0.20 %) | `results/?` |
| zeta from Newton pole vs polynomial roots (10 alpha, 2 omega*tau) | 1.4e-10 | < 1e-8 | `results/?` |
| zeta at alpha = 1 vs omega*tau/2 (both omega*tau) | 0.0e+00 | < 1e-9 | `results/?` |
| flexo x, uniform curvature: FEM energy triple vs 3 mu^2/(C11 h^2 kappa33) | 3.570415e-04 vs 3.570415e-04 | rel. diff < 1e-8 (worst 1.8e-10) | `results/?` |
| flexo Voc, uniform curvature: FEM vs mu*kappa*h/kappa33 | 1.7e-13 | < 1e-10 | `results/?` |
| every number in the abstract has an independent-check verdict | 4 hua / 8 nahi hua / 3 inputs, 15 tokens | 0 uncovered, 0 stale | `results/?` |
| piezoelectric share of the bending device (poling y, long faces) at every thickness | 5.7e-07 | < 1e-5 (electrically silent bending mode) | `results/?` |
| flexo growth with and without the piezoelectric terms | 23.9 vs 31.1 | reported 24 (2 s.f.) uses the real crystal; 31 with e = 0, both graded at 1 % | `results/?` |
| the same bending field, four poling/electrode pairings: only the long faces collect it, and each pairing with its own permittivity | poled y 3.570e-04 vs 3.570e-04; poled x 1.613e-05 vs 1.613e-05; short-face pairs 7.5e-14 V | rel. diff < 1e-6, short-face charge < 1e-12 | `results/?` |
| window second-moment factors 1/3, 1/4, 1/5 by quadrature | 3.3e-06 | < 1e-5 | `results/?` |
| h = 1 um flexo k^2 over four equivalent solver paths and 4 numeric stacks | spread 0.182 %, k^2 4.1705e-03..4.1781e-03 | < 0.5 % (quoted to 2 s.f.) | `results/?` |
| the same spread at h = 10 um | 1.49e-05 % | < 1e-3 % | `results/?` |
| truncating the secular sum to 12 modes is not an alternative | 85 % off | > 50 % (hence the sum runs over all modes) | `results/?` |
| no quantity replaced in the round-16 audit has come back | 0 hits of 14 forbidden tokens | 0 hits | `results/?` |
| every coupling factor recomputed and quoted in one row of the coupling table | 10/10 | all, no averaging | `results/?` |
| every number in the abstract, the conclusion, the Highlights and the captions is traced to the text or the archive | 48/48 traced, 0 untraced | 0 untraced | `results/?` |
| the list of unverified numbers cites only numbers still in the manuscript | 32 entries, 0 stale | 0 stale | `results/?` |
| application table: extensional plane stress is the strongest coupling of the four | 0.4580 | = 0.4580, largest, > 0.4 | `results/?` |
| piezo k^2 (mode-free) over h = 10 -> 1 um, max/min | 1.0009 | < 1.005 (thickness independent) | `results/demo.json` |
| piezo k^2, 24x2 vs 48x4, max rel. diff | 5.7e-04 | < 1e-3 | `results/demo.json` |
| flexo k^2, 48x4 (monotone in h) | 1.74e-04 -> 4.17e-03 | strictly increasing as h falls | `results/demo.json` |
| flexo k^2, 48x4 vs 96x4 witness | 3.5e-03 | < 0.02 | `results/demo.json` |
| flexo k^2 at mu = 0 / value (residual) | 6e-07 | < 1e-5 | `results/demo.json` |
| gradient-energy coefficient: code vs manuscript | 0.5 x int, (1/4)M/((1/20)L)=1.000000000000 | factor 1/2 in the assembly, (1/4)M = (1/20)L, FEM-1 u_R within 2 % | `results/?` |
| paper figures: vector set written | 12 PDF | = 12 (F1-F9, FB1-FB2, F11_designmap) | `results/paper_figures_data.json` |
| orientation sweep rows / k^2 range | 133 rows, 0.3786-0.4677 | 133 rows (114 cuboid + 19 ellipse), k^2 in (0.35, 0.50) | `results/paper_figures_data.json` |
| manuscript numbers vs the JSON they came from | 99/99 | all agree | `results/?` |
