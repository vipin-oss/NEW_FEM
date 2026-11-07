# Platform sensitivity of the h = 1 um flexoelectric coupling

One model (48$\times4$, poling $y$, electrodes on the long faces, $\mu=10^{-6}$ C/m), five eigensolver paths, three numeric stacks.  The deviations are relative to the **midpoint** of the equivalent rows, never to the running stack, so the same table is produced on every machine.

**h = 1 um: spread 0.182 %; h = 10 um: spread 1.164e-05 %.**  The growth factor ranges 23.92-23.96.

| stack | path | $k^2$ (h = 1 um) | dev [%] | $k^2$ (h = 10 um) | dev [%] | growth |
|---|---|---|---|---|---|---|
| py3.11.2 np1.26.4 sp1.11.4 | dense eigh, scaled | 4.17282e-03 | -0.036 | 1.74373e-04 | -4.72e-06 | 23.93 |
| py3.11.2 np1.26.4 sp1.11.4 | dense eigh, unscaled | 4.17237e-03 | -0.046 | 1.74373e-04 | -2.48e-06 | 23.93 |
| py3.11.2 np1.26.4 sp1.11.4 | QZ (eig, general) | 4.17333e-03 | -0.023 | 1.74373e-04 | -4.33e-06 | 23.93 |
| py3.11.2 np1.26.4 sp1.11.4 | numpy eig, all modes | 4.17811e-03 | +0.091 | 1.74373e-04 | -5.82e-06 | 23.96 |
| py3.11.2 np1.26.4 sp1.11.4 | dense eigh, 12 modes | 7.65028e-03 | +83.270 | 3.03405e-04 | +7.40e+01 | 25.21 |
| py3.11.2 np1.26.4 sp1.11.4 | sparse eigsh, 12 modes | 7.67843e-03 | +83.945 | 3.03405e-04 | +7.40e+01 | 25.31 |
| py3.11.2 np2.0.2 sp1.13.1 | dense eigh, scaled | 4.17583e-03 | +0.036 | 1.74373e-04 | -5.55e-06 | 23.95 |
| py3.11.2 np2.0.2 sp1.13.1 | dense eigh, unscaled | 4.17051e-03 | -0.091 | 1.74373e-04 | -5.58e-06 | 23.92 |
| py3.11.2 np2.0.2 sp1.13.1 | QZ (eig, general) | 4.17336e-03 | -0.023 | 1.74373e-04 | -4.58e-06 | 23.93 |
| py3.11.2 np2.0.2 sp1.13.1 | numpy eig, all modes | 4.17319e-03 | -0.027 | 1.74373e-04 | +5.82e-06 | 23.93 |
| py3.11.2 np2.0.2 sp1.13.1 | dense eigh, 12 modes | 7.68783e-03 | +84.170 | 3.03405e-04 | +7.40e+01 | 25.34 |
| py3.11.2 np2.0.2 sp1.13.1 | sparse eigsh, 12 modes | 7.67843e-03 | +83.945 | 3.03405e-04 | +7.40e+01 | 25.31 |
| py3.11.2 np2.2.6 sp1.15.3 | dense eigh, scaled | 4.17583e-03 | +0.036 | 1.74373e-04 | -5.54e-06 | 23.95 |
| py3.11.2 np2.2.6 sp1.15.3 | dense eigh, unscaled | 4.17051e-03 | -0.091 | 1.74373e-04 | -5.58e-06 | 23.92 |
| py3.11.2 np2.2.6 sp1.15.3 | QZ (eig, general) | 4.17336e-03 | -0.023 | 1.74373e-04 | -4.58e-06 | 23.93 |
| py3.11.2 np2.2.6 sp1.15.3 | numpy eig, all modes | 4.17318e-03 | -0.027 | 1.74373e-04 | +1.48e-06 | 23.93 |
| py3.11.2 np2.2.6 sp1.15.3 | dense eigh, 12 modes | 7.68783e-03 | +84.170 | 3.03405e-04 | +7.40e+01 | 25.34 |
| py3.11.2 np2.2.6 sp1.15.3 | sparse eigsh, 12 modes | 7.67843e-03 | +83.945 | 3.03405e-04 | +7.40e+01 | 25.31 |
| py3.11.2 np2.4.6 sp1.17.1 | dense eigh, scaled | 4.17329e-03 | -0.024 | 1.74373e-04 | -3.68e-06 | 23.93 |
| py3.11.2 np2.4.6 sp1.17.1 | dense eigh, unscaled | 4.17325e-03 | -0.026 | 1.74373e-04 | -3.84e-06 | 23.93 |
| py3.11.2 np2.4.6 sp1.17.1 | QZ (eig, general) | 4.17288e-03 | -0.034 | 1.74373e-04 | -4.25e-06 | 23.93 |
| py3.11.2 np2.4.6 sp1.17.1 | numpy eig, all modes | 4.17082e-03 | -0.084 | 1.74373e-04 | -3.75e-06 | 23.92 |
| py3.11.2 np2.4.6 sp1.17.1 | dense eigh, 12 modes | 7.66536e-03 | +83.632 | 3.03405e-04 | +7.40e+01 | 25.26 |
| py3.11.2 np2.4.6 sp1.17.1 | sparse eigsh, 12 modes | 7.67537e-03 | +83.872 | 3.03404e-04 | +7.40e+01 | 25.30 |

The h = 1 um value is the least reproducible number in the paper: it is a small difference of two nearly equal eigenvalues of a pencil with condition $\sim10^{12}$, so it inherits the eigenvector accuracy of the stack.  Two significant digits (4.2e-3, growth 24) are stable across every row of this table; the fourth digit is not, which is why the manuscript quotes two.

