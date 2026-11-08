# Piezoelectric coupling: closed form versus finite element

| quantity | plane stress | plane strain |
|---|---|---|
| 3-D closed form, free bar | 0.57712 | 0.57712 |
| 3-D closed form, uniaxial | 0.37483 | 0.37483 |
| 2-D closed form, $e^TC^-1e/\kappa$ | 0.56079 | 0.51317 |
| FEM, unconstrained plate 48x4 | 0.56079 | 0.51317 |
| FEM, clamped plate 48x4 | 0.55957 | 0.51149 |
| FEM, clamped plate 24x2 | 0.55884 | 0.51069 |

FEM versus the 2-D closed form: 0.000 % (free), 0.217 % (clamped).
2-D model versus the 3-D free bar: 2.83 % -- the plane-stress reduction drops the $e_{31}\varepsilon_{zz}$ term, which is the price of the 2-D idealisation, not an error of the implementation.
