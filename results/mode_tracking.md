# Mode tracking across the thickness sweep

Same 48x4 mesh topology at every thickness; bending configuration (poling y, through-thickness electrodes).

| h (um) | f1 (kHz) | f2/f1 | MAC vs h=10 mode 1 | off-diagonal max |
|---|---|---|---|---|
| 10 | 210.41 | 6.21 | 1.000000 | 2.56e-31 |
| 5 | 108.03 | 6.25 | 0.999749 | 2.07e-07 |
| 2 | 50.19 | 6.27 | 0.999357 | 1.10e-06 |
| 1 | 34.68 | 6.27 | 0.999186 | 2.24e-06 |

Minimum MAC: 0.999186; largest off-diagonal MAC: 2.24e-06; smallest f2/f1: 6.21.

A MAC of 1 means the same shape; the off-diagonal entries stay at round-off, so the tracked mode is not drifting towards a neighbor, and f2/f1 stays above 2, so no crossing is approached.
