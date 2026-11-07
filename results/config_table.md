# Piezoelectric and flexoelectric coupling on the same bending mode

Poling $y$, electrodes on the long faces (gap $h$), 48$\times4$ mesh, $L=\SI{200}{\micro\meter}$, window half-widths $3\times\SI{1}{\micro\meter}$, $\mu=10^{-6}$ C/m.

| $h$ [µm] | $k^2$ piezo only | $k^2$ flexo only ($e=0$) | $k^2$ both (as reported) | piezo share | both/flexo $-1$ |
|---|---|---|---|---|---|
| 10 | 1.00e-10 | 1.7569e-04 | 1.7437e-04 | 5.7e-07 | -0.8 % |
| 5 | 1.00e-10 | 6.5515e-04 | 6.5873e-04 | 1.5e-07 | +0.5 % |
| 2 | 1.00e-10 | 2.8455e-03 | 2.6417e-03 | 3.8e-08 | -7.2 % |
| 1 | 1.00e-10 | 5.4679e-03 | 4.1733e-03 | 2.4e-08 | -23.7 % |

The piezoelectric share of the bending coupling is at most 5.7e-07 -- at the round-off floor of the secular equation -- so the bending device is not a piezoelectric device.  The reason is geometric rather than numerical: the piezoelectric charge of a bending mode is $e_{31}\varepsilon_{xx}+e_{33}\varepsilon_{yy}$, and with $\varepsilon_{xx}=\kappa(y-h/2)$ odd about the mid-plane and $\varepsilon_{yy}\simeq0$ its integral over a face electrode vanishes.

The two effects are nevertheless not separable inside one run, and the table says by how much: the piezoelectric terms change the elastic stiffness of the same mode, so the flexo-only column differs from the reported one by up to 24 % at the thinnest plate (both/flexo $-1$ = -23.7 %).  With the piezoelectric terms switched off the flexoelectric coupling would grow by 31.1 over the range instead of the 23.9 that the paper reports for the real crystal.

