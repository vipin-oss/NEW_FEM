# The strain-gradient coefficient for a cuboid averaging domain

**Q1 of the FEM-6 blueprint.** With the BFS C1 element the nonlocal stiffness is

```
K_g = c ∫_Ω  L_mn (B_,m)ᵀ C (B_,n) dA ,        m,n = x,y                 (1)
```

FEM-1 used `L = diag(l²,l²)` and `c = 1/10`. What are `c` and `L` when the
averaging domain is a **cuboid** of half-widths `a_x, a_y`?

**Short answer.**

> Write the tensor form
> ```
> K_g = (1/2) ∫  M_mn (B_,m)ᵀ C (B_,n) dA ,      M = ⟨ξ ξ⟩ ,               (2)
> ```
> with `M` the true second-moment tensor of the window. Then `c = 1/2` for
> **every** shape, and only `M` changes:
> cuboid `M = diag(a_x²/3, a_y²/3)`, 2-D ellipse `diag(l_x²/4, l_y²/4)`,
> 3-D ellipsoid `diag(l_x²/5, l_y²/5)`.
>
> In FEM-1's parameterisation this is the **shape table**
> `c_shape = (1/2)(1/3, 1/4, 1/5) = (1/6, 1/8, 1/10)` for a segment, a 2-D
> ellipse and a 3-D ellipsoid respectively. **Cuboid → 1/6**, i.e. exactly the
> "1/6 replaces 1/10" of the blueprint note; a 3-D ellipsoid keeps FEM-1's 1/10.
> The corresponding *energy* coefficients are half of these (1/12, 1/16, 1/20);
> putting those into the **stiffness** halves the model (see §4).

Everything below is the derivation and the numerical verification.

---

## 1. Derivation of the shape factor

Take the Aifantis "difference" strain: average the strain over a window `w`
centred at `x`,

```
ε̄(x) = (1/|w|)∫_w ε(x+ξ) dξ ,        ε̃ = ε - ε̄ .                        (3)
```

Expanding `ε(x+ξ)` and using the symmetry of the window (`⟨ξ_p⟩ = 0`),

```
ε̄ = ε + (1/2) M_pq ε_,pq + O(l⁴) ,      M_pq = ⟨ξ_p ξ_q⟩ ,                 (4)
ε̃  = -(1/2) M_pq ε_,pq + O(l⁴) .                                          (5)
```

The gradient energy is `U_g = (1/2)∫ ε̃ᵀ C ε̃ dV`, which is *fourth* order in the
derivatives (`M_pq M_rs ε_,pqᵀ C ε_,rs`). The BFS C1 element cannot represent
that; FEM-1 uses instead the *second*-order surrogate

```
U_g = (1/2) c_shape l² ∫ (ε_,k)ᵀ C (ε_,k) dV ,                            (6)
```

i.e. one length scale, one gradient. The map from (5) to (6) is a
**calibration**, not a derivation: match the second-moment content of the
window to the single length `l` of the surrogate. Requiring that the two forms
give the same energy for a strain field that varies on a scale much larger than
the window fixes

```
c_shape l²  =  (1/2) · (1/κ) · l² ,      κ = M_xx / l² .                   (7)
```

| window (parameter `l` = half-width / semi-axis) | `M_xx/l² = κ` | `c_shape = 1/(2κ)` |
|---|---|---|
| 1-D segment, half-length `a` | 1/3 | **1/6** |
| 2-D rectangle, half-width `a` | 1/3 | **1/6** |
| 3-D cuboid, half-width `a` | 1/3 | **1/6** |
| 2-D ellipse, semi-axis `l` | 1/4 | 1/8 |
| 3-D ellipsoid, semi-axis `R` | 1/5 | 1/10 |

Why `κ = 1/3` for any cuboid: `⟨x²⟩ = (1/3)a²` for a box of half-width `a`, in
1, 2 or 3 dimensions. Why `1/4` for a 2-D ellipse and `1/5` for a 3-D
ellipsoid: `⟨x²⟩ = l²/4` and `R²/5` for the corresponding quadrics.

**FEM-1's `1/10` is therefore the 3-D-ellipsoid entry**, used with a 2-D mesh.
That is legitimate — it fixes a *convention* for `l` — but it must be said
explicitly, because it is the reason the numbers below do not differ by 4/3 or
5/3 in the way a naive reading suggests.

## 2. Verification (recomputed, `python/run_verification.py`, V1)

FEM-1 benchmark: plane strain, `E = 2×10¹¹`, `ν = 0.3`, `L_x = 1`, `L_y = 0.2`,
mesh 20×4.

| check | result |
|---|---|
| patch test, uniform strain, energy relative error | `4.4×10⁻¹⁶` |
| gradient energy under a **constant** strain field | `1.1×10⁻¹²` (zero, as required) |
| `K_g` with `M = (l²/5)I` vs FEM-1's `(l²/10)(K_xx + K_yy)` | `3.4×10⁻¹⁶` |
| `K_g(cuboid, a = l) / K_g(ellipsoid, l)` | **`1.666667` = 5/3** |
| `K_g(cuboid, a = l√(3/5))` vs `K_g(ellipsoid, l)` (equal `M`) | **`0.0`** |
| FEM-1 published: `ū` at `l/L = 0.2` (paper 4.23 µm, ratio 0.94) | 4.234 µm, ratio **0.9408** |

The `5/3` is `(1/3)/(1/5) = M_cub/M_ell` at the same `l`; the last row of the
table is the important one: **two windows with the same `M` give a
bit-identical `K_g`**. That is the structural fact behind Q1's real answer (see
§5).

## 3. What goes wrong if the coefficient is not moved with the moment

Three self-consistent conventions exist. Only one of them is coherent:

| convention | formula | status |
|---|---|---|
| A. Moment form | `K_g = (1/2)∫ M_mn B_,mᵀ C B_,n` | **correct for every shape** |
| B. FEM-1 form | `K_g = (1/10)∫ L_mn B_,mᵀ C B_,n`, `L = l² I` | correct **only** if `M = l²/5` |
| C. Mixed (the trap) | `K_g = (1/10)∫ M_mn B_,mᵀ C B_,n` with cuboid `M = a²/3` | **5× too small** |

Convention C is what one gets by "just replace `l²` with the cuboid moment" in
FEM-1's code. Since C uses `M` where B uses `L = 5M`, the stiffness is off by
exactly 5 → eigenfrequencies are off by `√5 ≈ 2.24`, and the reported
length-scale sensitivity is wrong by the same factor. This is the single most
consequential line in the whole FEM-6 implementation.

The complementary error — halving the coefficient to 1/12 or 1/20 (§0, "energy
coefficient") while leaving it in `K_g` — gives a model that is half as stiff
as FEM-1 and no longer reproduces the published benchmark. Verified: with
`c = 1/2, M = l²/5` the benchmark is reproduced to machine precision; with
`c = 1/4` it is not.

## 4. Consequence 1: the "cuboid vs ellipsoid" study is not identifiable

`K_g` depends on the window **only through `M`**. Therefore:

* a cuboid `(a_x, a_y)` and an ellipse `(l_x, l_y)` with
  `l = a√(3/5)` produce identical stiffness matrices (verified, `0.0`);
* a *rotated* cuboid and an unrotated one with the same `M` are identical;
* "cuboid vs ellipsoid" at equal half-width is just a `5/3` rescaling of the
  length scale — it is the *same* model, not a different one.

So the demonstration "our cuboid window predicts something different from the
FEM-1 ellipsoid window" cannot be sustained at second order. Two honest ways
out:

1. **Reframe (recommended).** Report that the nonlocal response is governed by
   the second-moment tensor `M`; the window *shape* is immaterial at this order.
   This is a positive result: it means `M` can be fitted to the microstructure
   (grain aspect ratio) without committing to a particular window shape, and it
   explains why FEM-1's ellipsoid coefficient transfers to a cuboid once `M` is
   matched.
2. **Go to fourth order**, adding `M_pqrs = ⟨ξ_p ξ_q ξ_r ξ_s⟩` (cuboid
   `a⁴/5`, ellipsoid `R⁴/…`). This *is* shape-dependent, but it needs a C2
   interpolation which the BFS C1 element does not provide. Out of scope.

## 5. Consequence 2: the anisotropy of `M` is the observable

Since only `M` enters, the physically meaningful parametric study is the
orientation of the window, `M(θ) = R(θ) diag(a_x²/3, a_y²/3) R(θ)ᵀ`. Computed
(`python/run_demos.py`, 200×10 µm plate, AR = 2):

| `θ` | 0° | 30° | 60° | 90° |
|---|---|---|---|---|
| `f₁` (kHz) | 167.58 | 170.09 | 174.02 | 177.41 |
| `k_eff²` (bending mode) | `-6×10⁻⁹` | `5×10⁻⁷` | `9×10⁻⁷` | `-8×10⁻⁹` |
| `k_eff²` (length-extensional) | 0.388 | 0.369 | 0.340 | 0.315 |

Two points for the paper: the frequency shift with `θ` is a genuine
microstructure signature and is independent of the shape convention; and the
bending mode carries **no** charge (`k² ≈ 10⁻⁷`, numerical zero) for *any*
orientation — see the checker report, finding A3.

## 6. Recommended text for the manuscript

1. One equation: `K_g = (1/2)∫ M_mn B_,mᵀ C B_,n`, `M = ⟨ξξ⟩`.
2. The 5-row shape table of §1.
3. One sentence relating to FEM-1: "for a 3-D ellipsoid `M = l²/5`, hence
   `(1/2)M = l²/10`, which is the coefficient of FEM-1".
4. Replace the shape study with the orientation/`M` study and state
   explicitly that the shape is invisible at second order.
5. In every caption give both `a` (code parameter) and `M` (physical quantity).
