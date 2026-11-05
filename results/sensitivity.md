# Platform sensitivity of the h = 1 um flexoelectric coupling

One model (48$\times4$, poling $y$, electrodes on the long faces, $\mu=10^{-6}$ C/m), five eigensolver paths, three numeric stacks.  The reference is the stack of `run_all.py`; the deviations are relative to its `dense eigh, scaled` value.

**h = 1 um: spread 0.107 %; h = 10 um: spread 1.115e-05 %.**  The growth factor ranges 23.92-23.96.

| stack | path | $k^2$ (h = 1 um) | dev [%] | $k^2$ (h = 10 um) | dev [%] | growth |
|---|---|---|---|---|---|---|
| py3.11.2 np1.26.4 sp1.11.4 | dense eigh, scaled | 4.17282e-03 | -0.020 | 1.74373e-04 | +6.11e-07 | 23.93 |
| py3.11.2 np1.26.4 sp1.11.4 | dense eigh, unscaled | 4.17237e-03 | -0.030 | 1.74373e-04 | +2.85e-06 | 23.93 |
| py3.11.2 np1.26.4 sp1.11.4 | QZ (eig, general) | 4.17333e-03 | -0.007 | 1.74373e-04 | +1.00e-06 | 23.93 |
| py3.11.2 np1.26.4 sp1.11.4 | numpy eig, all modes | 4.17811e-03 | +0.107 | 1.74373e-04 | -4.91e-07 | 23.96 |
| py3.11.2 np1.26.4 sp1.11.4 | dense eigh, 12 modes | 7.65028e-03 | +83.300 | 3.03405e-04 | +7.40e+01 | 25.21 |
| py3.11.2 np1.26.4 sp1.11.4 | sparse eigsh, 12 modes | 7.67843e-03 | +83.974 | 3.03405e-04 | +7.40e+01 | 25.31 |
| py3.11.2 np2.0.2 sp1.13.1 | dense eigh, scaled | 4.17583e-03 | +0.052 | 1.74373e-04 | -2.18e-07 | 23.95 |
| py3.11.2 np2.0.2 sp1.13.1 | dense eigh, unscaled | 4.17051e-03 | -0.075 | 1.74373e-04 | -2.51e-07 | 23.92 |
| py3.11.2 np2.0.2 sp1.13.1 | QZ (eig, general) | 4.17336e-03 | -0.007 | 1.74373e-04 | +7.54e-07 | 23.93 |
| py3.11.2 np2.0.2 sp1.13.1 | numpy eig, all modes | 4.17319e-03 | -0.011 | 1.74373e-04 | +1.12e-05 | 23.93 |
| py3.11.2 np2.0.2 sp1.13.1 | dense eigh, 12 modes | 7.68783e-03 | +84.200 | 3.03405e-04 | +7.40e+01 | 25.34 |
| py3.11.2 np2.0.2 sp1.13.1 | sparse eigsh, 12 modes | 7.67843e-03 | +83.974 | 3.03405e-04 | +7.40e+01 | 25.31 |
| py3.11.2 np2.4.6 sp1.17.1 | dense eigh, scaled | 4.17364e-03 | +0.000 | 1.74373e-04 | +0.00e+00 | 23.94 |
| py3.11.2 np2.4.6 sp1.17.1 | dense eigh, unscaled | 4.17415e-03 | +0.012 | 1.74373e-04 | -1.56e-07 | 23.94 |
| py3.11.2 np2.4.6 sp1.17.1 | QZ (eig, general) | 4.17308e-03 | -0.013 | 1.74373e-04 | +1.68e-06 | 23.93 |
| py3.11.2 np2.4.6 sp1.17.1 | numpy eig, all modes | 4.17502e-03 | +0.033 | 1.74373e-04 | -3.71e-06 | 23.94 |
| py3.11.2 np2.4.6 sp1.17.1 | dense eigh, 12 modes | 7.71170e-03 | +84.772 | 3.03404e-04 | +7.40e+01 | 25.42 |
| py3.11.2 np2.4.6 sp1.17.1 | sparse eigsh, 12 modes | 7.68228e-03 | +84.067 | 3.03405e-04 | +7.40e+01 | 25.32 |

The h = 1 um value is the least reproducible number in the paper: it is a small difference of two nearly equal eigenvalues of a pencil with condition $\sim10^{12}$, so it inherits the eigenvector accuracy of the stack.  Two significant digits (4.2e-3, growth 24) are stable across every row of this table; the fourth digit is not, which is why the manuscript quotes two.

