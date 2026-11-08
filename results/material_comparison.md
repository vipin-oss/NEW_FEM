# Material check: plane strain vs plane stress (FEM-5 / Zgonik set)

Microbridge 200 x 10 um, cuboid window a = (3.0, 1.0) um, mesh 24x2, 8 modes.

| poling | kinematics | f1 (kHz) | f_ext (kHz) | k2_ext | V0 @10 nm (V) |
|---|---|---|---|---|---|
| y | plane_strain | 220.398 | 6720.565 | +0.1746 | 3.5316e+00 |
| y | plane_stress | 208.688 | 6359.978 | +0.1138 | 2.4218e+00 |
| x | plane_strain | 165.560 | 7161.976 | +0.4026 | 1.4155e+02 |
| x | plane_stress | 147.715 | 6727.322 | +0.4583 | 1.3907e+02 |

Ratios (plane stress / plane strain):
- poling y: f1 x0.9469, f_ext x0.9463
- poling x: f1 x0.8922, f_ext x0.9393

kappa11/kappa33 = 39.3 (used: 2200/56, Zgonik 1994)

k31 from the IEEE DC identity = 0.0667 (k31^2 = 0.0045)
