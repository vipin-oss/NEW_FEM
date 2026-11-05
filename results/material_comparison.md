# Material check: plane strain vs plane stress (FEM-5 / Zgonik set)

Microbridge 200 x 10 um, cuboid window a = (3.0, 1.0) um, mesh 24x2, 8 modes.

| poling | kinematics | f1 (kHz) | f_ext (kHz) | k2_ext | V0 @10 nm (V) |
|---|---|---|---|---|---|
| y | plane_strain | 220.460 | 6721.815 | +0.1749 | 3.5289e+00 |
| y | plane_stress | 208.732 | 6360.999 | +0.1141 | 2.4217e+00 |
| x | plane_strain | 165.571 | 7160.990 | +0.4024 | 1.4155e+02 |
| x | plane_stress | 147.727 | 6725.793 | +0.4580 | 1.3906e+02 |

Ratios (plane stress / plane strain):
- poling y: f1 x0.9468, f_ext x0.9463
- poling x: f1 x0.8922, f_ext x0.9392

kappa11/kappa33 = 39.3 (used: 2200/56, Zgonik 1994)

k31 from the IEEE DC identity = 0.0667 (k31^2 = 0.0045)
