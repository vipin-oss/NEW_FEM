# Figure 5: the thickness sweep, and the three artefacts it had

This note records what figure 5 (`results/figures/fig5_flexo_thickness.png`,
built by `python/run_demos.py :: fig_flexo_thickness`) actually computes, why
the first version of it was not usable, and what is now claimed from it.

Everything below is produced by `python3 python/run_all.py`; nothing is quoted
from a paper.

---

## 1. What was wrong

The sweep varies the plate thickness `h = 10, 5, 2, 1 µm` on a
`L = 200 µm` plate, flexoelectric bending (through-thickness electrodes,
poling `y`) against length-extensional piezoelectricity (end electrodes,
poling `x`). The first version of the figure had three defects.

### 1.1 The piezo column picked a different mode at every thickness

It read k² as `argmax(k²)` over the first 14 modes of the plate and took the
largest. Thin plates push several bending modes below the extensional one, so
the index of the argmax marched with thickness:

| h (µm) | argmax index | k² at that index |
|---|---|---|
| 10 | 4 | 0.4583 |
| 5 | 5 | 0.4519 |
| 2 | 7 | 0.3128 |
| 1 | 9 | 0.3621 |

Non-monotone, and not a property of the material — a property of the index.
Tracking by "nearest frequency" instead was no better (k² = 0.0976 at
`h = 5 µm`).

**Replacement.** The *mode-free* quasi-static coupling of the electrode pair,

```
x = dᵀ K_uu⁻¹ d / β ,      k² = x / (1 + x) ,
```

which uses no eigenvector and therefore cannot jump modes. `K_uu` is the
short-circuit mechanical stiffness, `d` and `β` the rank-one open-circuit
update (`K_open = K_sc + d dᵀ/β`). It is the standard static/blocked coupling
of the port, evaluated with every mechanical dof free.

The solve is done on the diagonally scaled system (`cond ≈ 1e12` instead of
`1e27`, the raw matrix trips a `LinAlgWarning`); scaled and unscaled agree to
six digits.

### 1.2 The flexo column differenced two nearly equal eigenvalues

k² was taken as `(ω_open² − ω_short²)/ω_open²` from two separate eigensolves.
For a thin flexoelectric plate k² is `1e-4 … 4e-3`, i.e. the two eigenvalues
agree to that relative precision, and the pencil has `cond(K) ≈ 1e12`. The
noise of the difference is the size of the answer:

| h = 1 µm, mesh | two-solve k² | secular k² (§1.2) |
|---|---|---|
| 24 × 2 | 3.94e-3 | 3.85e-3 |
| 48 × 4 | 4.47e-3 | 4.17e-3 |
| 96 × 4 | 3.30e-3 | 4.16e-3 |

With `µ = 0` the two-solve column returned `−1.3e-7`, `+7.5e-4`,
`+1.1e-4` and `+4.4e-3` on different meshes — for a coupling that is
*identically zero* by symmetry (a pure bending field puts zero net charge on
through-thickness electrodes).

**Replacement.** Because the open-circuit matrix is a rank-one update of the
short-circuit one, the open-circuit fundamental frequency is the root in
`(ω₀², ω₁²)` of the secular equation

```
1 + Σ_i s_i / (ω_i² − y) = 0 ,        s_i = (d · φ_i)² / β ,
```

with `(ω_i, φ_i)` the mass-normalised *short-circuit* modes. One eigensolve,
no difference of close eigenvalues (the eigenvector sign cancels inside `s_i`),
`f` is strictly increasing between poles so bisection is unconditionally safe.
The `µ = 0` residual drops to `1.0e-10`, i.e. to round-off, and the value is
then mesh-stable.

### 1.3 `materials.batio3()` already carries `µ = 1e-6`

`BATIO3` has `mu = 1.0e-6` (the FEM-5 sensitivity value), so the "piezo only"
column silently evaluated the flexoelectric model with the flexo on and
returned exactly the flexo number. Both piezo-only columns now build
`mu = 0.0` explicitly.

---

## 2. What is computed now

Same plate at every thickness (`L = 200 µm`, `48 × 4`), window fixed at
half-widths `3 × 1 µm` throughout (`M_11 = a₁²/3`), so the size effect is
driven by `h` alone. `96 × 4` is run at the two ends of the range as a
witness, not as a second curve.

| h (µm) | flexo k² (48×4) | 96×4 witness | rel. diff | µ = 0 residual | k² piezo (mode-free) |
|---|---|---|---|---|---|
| 10 | 1.7437e-04 | 1.7444e-04 | 4e-4 | 1.0e-10 | 0.55814 |
| 5 | 6.5873e-04 | — | — | 1.0e-10 | 0.55843 |
| 2 | 2.6416e-03 | — | — | 1.0e-10 | 0.55858 |
| 1 | 4.1736e-03 | 4.1589e-03 | 3.5e-3 | 1.0e-10 | 0.55861 |

* flexo k² grows by **×23.9** from `h = 10 µm` to `1 µm`;
* local log-log slopes **−1.92, −1.52, −0.66** (steep end approaching the
  `h⁻²` asymptote, shallow end flattening below `h ≈ 2 µm`);
* piezo k² is **thickness independent to 0.09 %** (`0.55814 → 0.55861`) and
  mesh independent to `5.7e-4`.

> **Correction (this revision).** An earlier version of this table reported the
> piezo column as `0.35821 → 0.35840`.  That number came from `_static_k2`
> solving `x = dᵀK⁻¹d/β` against the **open-circuit** matrix and then applying
> `k² = x/(1+x)`; by Sherman–Morrison the first step already returns `k²`, so
> the helper produced `k²/(1+k²)` — `0.55814/(1+0.55814) = 0.35821` exactly.
> The corrected values are the ones above; the closed form from the material
> constants (`eᵀC⁻¹e/κ`, plane stress) gives `0.56079`, and the free-plate FEM
> reproduces it to the fifth decimal.  See
> `python/derive_k2_closed_form.py` and `results/k2_closed_form.md`.

The piezo statement is the predictive one: the same plate keeps the same
electromechanical coupling whatever its thickness, while the flexoelectric
bending coupling grows as the plate is thinned. It is that contrast that the
figure exists to show.

### What is *not* claimed

* The flattening at `h ≲ 2 µm` is **converged** (T4: 96×4 agrees to 0.35 %),
  so it is not a mesh artefact, but the *interpretation* — that the fixed
  `3 × 1 µm` averaging window becomes comparable to the plate thickness and
  smears the through-thickness strain gradient — is a reading of the numbers,
  not something this sweep separates from the gradient-elastic stiffening of
  the thin plate. The fundamental frequency shows the same effect: `f₁ =
  210.4, 108.0, 50.2, 34.7 kHz`, where pure Euler–Bernoulli scaling from the
  `h = 10 µm` point predicts `210, 105, 42, 21 kHz`.
* No single asymptotic slope is quoted. `−1.92` at the thick end and `−0.66`
  at the thin end are both reported.
* The static (mode-free) flexo coupling is **not** used as a size-effect
  measure: it is dominated by the piezoelectric thickness-extension
  contribution (`≈ 0.55` for the bending electrode pair regardless of `µ`), so
  it cannot isolate the flexoelectric term. It is used only where the model is
  piezoelectric without flexo (panel b).

---

## 3. Grading

`run_all.py` now grades the five properties that make the panel admissible:

| id | criterion |
|---|---|
| T1 | piezo k² (mode-free), max/min over h < 1.005 |
| T2 | piezo k², 24×2 vs 48×4, max rel. diff < 1e-3 |
| T3 | flexo k² strictly increasing as h falls |
| T4 | flexo k², 48×4 vs 96×4 witness, rel. diff < 2 % |
| T5 | flexo k² at µ = 0 / value < 1e-5 |

All five pass; the suite reports 29/29.
