# Independent checks of the headline numbers

Each row compares a number used in the paper with a value obtained along a route that does not share the code path that produced it.

## F1 -- fundamental frequency of the elastic strip (e = mu = 0, no gradient term)

$L=\SI{200}{\micro\metre}$, depth $h=\SI{10}{\micro\metre}$, $\rho=\SI{6020}{\kilo\gram\per\cubic\metre}$ (unverified), beam modulus $E_b=1/(\bm C_p^{-1})_{xx}=7.6327e+10$ Pa (a wide plate would use $C^p_{11}=9.5500e+10$ Pa).

| boundary | closed form | value (kHz) | FEM 48x4 | 96x4 | 128x4 | err vs EB | err vs Timoshenko |
|---|---|---|---|---|---|---|---|
| clamped-free | Euler-Bernoulli | 143.8 | 144.6 | 144.2 | 144.1 | +0.543 % | +0.635 % |
| clamped-free | Timoshenko | 143.7 | -- | -- | -- | (EB row) | -- |
| clamped-clamped | Euler-Bernoulli | 915.0 | 919.2 | 914.1 | 912.9 | +0.456 % | +1.040 % |
| clamped-clamped | Timoshenko | 909.7 | -- | -- | -- | (EB row) | -- |

## F2 -- damping ratio of the fractional Kelvin-Voigt element

`zeta` from the Newton pole of `fem6_core.complex_frequency` against the roots of the same equation rewritten as a polynomial in $w=s^{1/q}$ for $\alpha=p/q$ (`numpy.roots`).

| $\omega\tau$ | $\alpha$ | $p/q$ | $\zeta$ (Newton) | $\zeta$ (polynomial) | rel. diff | $\omega\tau/2$ |
|---|---|---|---|---|---|---|
| 0.3 | 1 | 1/1 | 0.150000 | 0.150000 | 2.2e-16 | 0.150000 |
| 0.3 | 0.9 | 9/10 | 0.166079 | 0.166079 | 5.3e-14 | 0.150000 |
| 0.3 | 0.7 | 7/10 | 0.179384 | 0.179384 | 5.8e-13 | 0.150000 |
| 0.3 | 0.5 | 1/2 | 0.158580 | 0.158580 | 4.0e-15 | 0.150000 |
| 0.3 | 0.3 | 3/10 | 0.107711 | 0.107711 | 6.8e-12 | 0.150000 |
| 1 | 1 | 1/1 | 0.500000 | 0.500000 | 2.2e-16 | 0.500000 |
| 1 | 0.9 | 9/10 | 0.480460 | 0.480460 | 3.3e-13 | 0.500000 |
| 1 | 0.7 | 7/10 | 0.370619 | 0.370619 | 7.7e-14 | 0.500000 |
| 1 | 0.5 | 1/2 | 0.245360 | 0.245360 | 2.2e-15 | 0.500000 |
| 1 | 0.3 | 3/10 | 0.134530 | 0.134530 | 1.4e-10 | 0.500000 |

## F3 -- flexoelectric coupling in the uniform-curvature limit

A plate carrying the exact pure-bending field $u=\kappa xy$, $v=-\kappa x^2/2$ has $\varepsilon_{xx}=\kappa y$, $\varepsilon_{yy}=0$, $\gamma_{xy}=0$: a uniform strain gradient $\partial\varepsilon_{xx}/\partial y=\kappa$ and a neutral axis on the edge $y=0$.  Its one degree of freedom is fixed by three scalars -- charge $q=\mu\kappa L$, bending energy $U=\tfrac12 C^p_{11}\kappa^2Lh^3/3$ and capacitance $\kappa_{33}L/h$ -- so

$$x=\frac{(\mu L)^2}{(C^p_{11}h^3L/3)(\kappa_{33}L/h)}=\frac{3\mu^2}{C^p_{11}h^2\kappa_{33}}=3.570415e-04$$

The finite element value is read off the same prescribed field as $x=\beta V^2/(u^{\mathsf T}Ku)$.  For contrast, the same plate bent about its **mid-plane** would have $U\propto h^3/12$ and hence $x=12\mu^2/(C^p_{11}h^2\kappa_{33})=1.4282e-03$ -- exactly four times larger, the factor being $\int_0^h y^2dy=h^3/3$ against the mid-plane $h^3/12$.  Using the beam modulus $E_b$ instead of the constrained $C^p_{11}$ would give $1.7869e-03$, which the finite element solution rules out.

| mesh | $V_{oc}$ FEM | $V=\mu\kappa h/\kappa_{33}$ | $x$ FEM | $x$ analytic | rel. diff |
|---|---|---|---|---|---|
| 8x2 | 2.016802e-02 | 2.016802e-02 | 3.570415e-04 | 3.570415e-04 | 1.5e-11 |
| 24x4 | 2.016802e-02 | 2.016802e-02 | 3.570415e-04 | 3.570415e-04 | 2.6e-11 |
| 48x8 | 2.016802e-02 | 2.016802e-02 | 3.570415e-04 | 3.570415e-04 | 1.8e-10 |
| 96x4 | 2.016802e-02 | 2.016802e-02 | 3.570415e-04 | 3.570415e-04 | 1.3e-10 |

## F4 -- the second-moment factors of the three window shapes

Integrated over each shape and divided by its measure, not taken from the formula in the code.

| shape | $M_{ii}/a_i^2$ printed | quadrature, $a_1=1$ | quadrature, $a_2=0.6$ |
|---|---|---|---|
| cuboid | $1/3$ | 0.333333333333 vs 0.333333333333 | 0.333333333333 vs 0.333333333333 |
| ellipse (2-D) | $1/4$ | 0.249999166667 vs 0.250000000000 | 0.250000000000 vs 0.250000000000 |
| ellipsoid (3-D) | $1/5$ | 0.200000000000 vs 0.200000000000 | 0.200000000000 vs 0.200000000000 |

Worst relative difference 3.3e-06.


## F5 -- the same bending field in four poling/electrode pairings

The flexoelectric polarization of $u=\kappa xy$, $v=-\kappa x^2/2$ is $\bm D=\mu\kappa\hat{\bm y}$: normal to the long faces, parallel to the short ones.  So only the long faces collect it, and the permittivity that then enters is the one along $y$ -- $\kappa_{33}$ for a plate poled along $y$, $\kappa_{11}$ for one poled along $x$.  The coupling factor fixes the modulus only once that pairing is fixed.

| configuration | $C^p_{xx}$ [Pa] | $\kappa_{yy}$ [F/m] | $V_{oc}$ [V] | $x$ FEM | $x$ closed form |
|---|---|---|---|---|---|
| poling y, electrodes top/bottom | 1.6946e+11 | 4.9583e-10 | 2.017e-02 | 3.5704e-04 | 3.5704e-04 |
| poling x, electrodes top/bottom | 9.5500e+10 | 1.9479e-08 | 5.134e-04 | 1.6127e-05 | 1.6127e-05 |
| poling x, electrodes left/right | 9.5500e+10 | 1.9479e-08 | -7.482e-14 | 2.1796e-29 | 0.0000e+00 |
| poling y, electrodes left/right | 1.6946e+11 | 4.9583e-10 | -1.975e-15 | 3.3619e-31 | 0.0000e+00 |

The Step-3 modulus $\SI{9.55e10}{\pascal}$ with the poling-$y$ permittivity would give $x=6.3355e-04$, 77 % away from the finite element value, and no configuration of this geometry produces that pairing.  The beam modulus of the poling-$y$ plate is 1.3544e+11 Pa, and $\kappa_{11}/\kappa_{33}=39.3$.

