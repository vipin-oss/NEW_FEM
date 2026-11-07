# Flexoelectric verification

mu = 1.0e-06 C/m (parametric, FEM-5 sensitivity value, not source controlled); plane stress; 200x10 um bridge.

| check | result | expected |
|---|---|---|
| F1 patch test, mu = 0 | +0.000e+00 V | 0 |
| F2 patch test, mu = 1e-6 | +2.016802e-02 V vs analytic +2.016802e-02 V | ratio 1, got 1.0000000000 |
| F2 mesh independence | 4x1: +2.016802e-02, 8x2: +2.016802e-02, 24x2: +2.016802e-02 V | identical |
| F3 linearity | V(2mu)/V(mu) = 2.0000000000 | 2 |
| F4 bending k_eff^2, no flexo | +2.299e-09 | ~0 |
| F4 bending k_eff^2, mu = 1e-6 | +1.246e-04 | > 1e-5 |

Analytic identity used in F2 (uniform curvature kappa):
`V = mu * kappa * h / kappa33`

| mu (C/m) | k_eff^2 (mode 1) | V at 1 mN tip load (V) | f1 (kHz) |
|---|---|---|---|
| 0e+00 | +2.299e-09 | -9.771e-14 | 208.732 |
| 1e-07 | +1.250e-06 | +3.695e-06 | 208.732 |
| 3e-07 | +1.126e-05 | +1.108e-05 | 208.728 |
| 1e-06 | +1.246e-04 | +3.683e-05 | 208.688 |
| 3e-06 | +1.082e-03 | +1.076e-04 | 208.351 |
| 1e-05 | +8.651e-03 | +2.780e-04 | 205.746 |

Overall: **PASS**
