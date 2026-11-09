# Mode tracking across the thickness sweep

Same 48x4 mesh topology at every thickness; bending configuration (poling y, through-thickness electrodes).

| h (um) | f1 (kHz) | f2/f1 | MAC vs h=10 mode 1 | off-diagonal max |
|---|---|---|---|---|
| 10 | 209.00 | 6.21 | 1.000000 | 2.50e-28 |
| 5 | 107.34 | 6.25 | 0.999756 | 2.48e-07 |
| 2 | 49.95 | 6.27 | 0.999375 | 1.23e-06 |
| 1 | 34.59 | 6.27 | 0.999208 | 2.47e-06 |

Minimum MAC: 0.999208; largest off-diagonal MAC: 2.47e-06; smallest f2/f1: 6.21.

MAC uses a pullback to the reference thickness. These sampled shapes and spectral gaps support branch identification at the tested points; they do not prove absence of crossings between samples.
