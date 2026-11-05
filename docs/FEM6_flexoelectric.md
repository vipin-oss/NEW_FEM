# FEM-6 flexoelectric extension — formulation, matrices, sign convention

Purpose: the piezoelectric term alone gives **zero** electrode charge in pure
bending of a homogeneous plate (checker report A3; measured `k_eff² = 2.3×10⁻¹⁰`).
Flexoelectricity couples polarization to the **strain gradient**, which does not
cancel through the thickness, so it is the mechanism that makes a bending-mode
sensor possible — and it is the natural partner of a theory that already
assembles strain gradients.

The formulation follows the author's own FEM-4 (C¹ BFS piezoelectric–flexoelectric
element) so that FEM-6 stays consistent with it: same electric enthalpy, same
BFS mechanical interpolation, same "shear-free" flexoelectric specialization.

---

## 1. Electric enthalpy

With `ε` the infinitesimal strain, `η = ∇ε` the Mindlin Form-II strain gradient
(6 independent components in 2-D), `E = −∇φ` the electric field,

```
H(q, φ) = ½ ∫ εᵀ C ε dΩ + ½ ∫ ηᵀ A η dΩ
        − ∫ Eᵀ (e ε + μ η) dΩ − ½ ∫ Eᵀ κ E dΩ                            (1)
```

Constitutive relations obtained from (1):

```
σ = C ε − eᵀ E                    (stress)
τ = A η − μᵀ E                    (double stress; not needed explicitly)
D = e ε + μ η + κ E               (electric displacement)                 (2)
```

FEM-6 replaces the Mindlin `½∫ηᵀAη` of FEM-4 by the second-moment (Aifantis)
form used throughout this work,

```
U_g = ½ ∫ M_mn (ε_,m)ᵀ C (ε_,n) dΩ ,        M = ⟨ξ ξ⟩ ,                   (3)
```

i.e. the same `A`-slot is filled by the nonlocal tensor rather than by
`C44 ℓ² I`. Equation (3) is *not* used in the flexoelectric coupling: the
coupling needs only the **basis** `Bη`, not the modulus, so (1)–(2) remain
unchanged. This is the reason the two extensions (nonlocal elasticity,
flexoelectricity) compose without any new coupling block.

## 2. The flexoelectric tensor: shear-free, single constant

Full 4 mm flexoelectricity needs three independent constants `μ11, μ12, μ44`.
FEM-4 uses the *shear-free* specialization `μ44 = 0`, i.e. only the gradients of
the **normal** strains contribute. We keep that, and take the further
single-constant ("conformal") reduction

```
D = e ε + μ ∇(ε_xx + ε_yy) + κ E                                          (4)
```

which corresponds to `μ11 = μ12 = μ`, `μ44 = 0`. In components, with

```
η = [ ε_xx,x , ε_xx,y , ε_yy,x , ε_yy,y , γ_xy,x , γ_xy,y ]ᵀ               (5)
```

the coupling matrix is the 2×6 constant

```
μ_V = μ [ 1  0  1  0  0  0 ]        rows: (D_x , D_y)                     (6)
        [ 0  1  0  1  0  0 ]
```

**Why this is the right minimal choice.** For a plate in bending,
`ε_xx = −y κ(x)`, so

```
D_y = μ ∂ε_xx/∂y = −μ κ(x) ,                                               (7)
```

which is **uniform through the thickness**. The electrode integral
`Q = ∫D_y dA` therefore does not cancel, unlike the piezoelectric term
`∫e31 ε_xx dA ∝ ∫y dA = 0`. A single constant already captures the whole
bending-mode transduction, and (7) gives an *analytic* check to test the code
against (§5).

Sign convention: `D_y = −μ κ` means that for `μ > 0` a positive (sagging)
curvature gives a negative `D_y` and hence a negative electrode charge on the
`+y` face. Only the product `μ × κ` is physical here; the sign of `μ` is
absorbed into the poling/electrode convention and must be stated once in the
paper.

## 3. Weak form and the discrete blocks

Test with `(δq, δφ)`; `E = −B_φ φ`, `ε = B q`, `η = B_η q`:

```
mechanical:  ∫ δεᵀ C ε + ∫ δηᵀ (∂U_g/∂η) − ∫ δEᵀ(eε + μη) = ∫ δuᵀ b
electric:    ∫ δEᵀ (e ε + μ η + κ E) = 0        (no free charge)          (8)
```

Substituting `δE = −B_φ δφ` and keeping the bilinear terms:

```
K_uu = ∫ Bᵀ C B + ½ ∫ M_mn B_,mᵀ C B_,n        (existing)
K_uφ = ∫ Bᵀ eᵀ B_φ + ∫ B_ηᵀ μ_Vᵀ B_φ          ← the flexoelectric addition  (9)
K_φφ = ∫ B_φᵀ κ B_φ                            (existing)
```

`K_φu = K_uφᵀ` **exactly**, because both come from the same bilinear term
`−∫Eᵀμη` of (1) — this is FEM-5's "Correction 2" and it is satisfied by
construction here: the *same* `B_ηᵀ μ_Vᵀ B_φ` block is added to the mechanical
row, not only to the electrical one. Adding it to only one side would break the
Hessian symmetry and silently change `K_eff = K_uu + K_uφ K_φφ⁻¹ K_φu`.

Note that no new mechanical stiffness appears: the flexoelectric energy is
bilinear in `(q, φ)`, so it enters `K_eff` only through the condensation, which
is why `k_eff²` increases and the electromechanical coupling becomes non-zero
for the bending mode.

### Element matrices

`B_η` is 6×32, built from the same bicubic Hermite shape functions as `B`:

| row | dofs | expression |
|---|---|---|
| 0 `ε_xx,x`  | `u` | `N_xx` |
| 1 `ε_xx,y`  | `u` | `N_xy` |
| 2 `ε_yy,x`  | `v` | `N_xy` |
| 3 `ε_yy,y`  | `v` | `N_yy` |
| 4 `γ_xy,x`  | `u, v` | `N_xy`, `N_xx` |
| 5 `γ_xy,y`  | `u, v` | `N_yy`, `N_xy` |

with `N` the 16 nodal Hermite functions (value, `∂_x`, `∂_y`, `∂_xy` per node)
and `u, v ∈ {1..4}, {5..8}` the eight mechanical dofs per node. The element block is `∫ B_ηᵀ μ_Vᵀ B_φ dΩ`. With the C1 potential of FEM-6 the
electric dofs per node are `(φ, φ_x, φ_y, φ_xy)` and `B_φ` is the 2×16 gradient
of the bilinear potential shape functions restricted to those four positions,
so the element block is 32×16 (FEM-4 used a C0 potential with one dof per node
and hence 32×4). The rank of the block is unchanged by the extra derivative
dofs; the electrode tie then removes them.

## 4. What changes in the solver

Only one line: `Kuphi += B_eta.T @ mu_V.T @ Bp` accumulated at each Gauss
point, with `μ_V` from (6). Everything downstream — the electrode tie, the
Schur condensation `Z = A⁻¹K_uφᵀ`, `K_eff`, `k_eff²`, the modal problem, the
memory term — is untouched, because the coupling is still linear in `φ`.

## 5. Analytic check (exact, hand-checkable)

**Uniform-curvature patch test.** Impose on the mesh the pure-bending field

```
u = κ x y ,   u_x = κ y ,   u_y = κ x ,   u_xy = κ
v = −κ x²/2 , v_x = −κ x ,  v_y = 0 ,     v_xy = 0                        (10)
```

for which `ε_xx = κ y`, `ε_yy = γ_xy = 0`, so `∂ε_xx/∂y = κ` and
`D_y = μ κ` — uniform, hence no cancellation in the electrode integral. With
`C = κ33 (L·b)/h` and `Q = μ κ (L·b)`,

```
V = μ κ h / κ33 .                                                          (11)
```

This is exact for any mesh (the field is in the interpolation space) and any
`μ`, so it tests the coupling assembly, the electrode tie and the condensation
in one shot. **Measured (`python/run_flexo_check.py`):**

| check | result |
|---|---|
| patch test, `μ = 0` | `V = 0.000e+00` exactly |
| patch test, `μ = 1e-6` | `V = 2.016802e-02 V` vs analytic `2.016802e-02 V`, ratio **1.0000000000** |
| mesh 4×1 / 8×2 / 24×2 | `2.016802e-02` for all three — mesh independent |
| linearity, `V(2μ)/V(μ)` | **2.0000000000** |

**Warning for the paper.** The tempting closed form for a *cantilever*,
`V = μ h θ_tip/(κ33 L)`, is **wrong** — it assumes a uniform curvature and
`ε_yy = 0`, neither of which holds. It over-predicts by a factor 4 here and
gets the sign wrong. Use (11) with imposed curvature if a closed form is
wanted; for the cantilever report the computed number only.

## 6. What the coupling buys: the bending mode is no longer silent

Cantilever, plane stress, 24×2, tip load 1 mN, through-thickness electrodes:

| `μ` (C/m) | `k_eff²` (mode 1) | `V` (V) | `f₁` (kHz) |
|---|---|---|---|
| 0 | +1.02×10⁻⁹ | 3.4×10⁻¹³ | 208.7 |
| 1×10⁻⁷ | +1.25×10⁻⁶ | 3.70×10⁻⁶ | 208.7 |
| 3×10⁻⁷ | +1.13×10⁻⁵ | 1.11×10⁻⁵ | 208.7 |
| 1×10⁻⁶ | +1.25×10⁻⁴ | 3.68×10⁻⁵ | 208.7 |
| 3×10⁻⁶ | +1.08×10⁻³ | 1.08×10⁻⁴ | 208.7 |
| 1×10⁻⁵ | +8.65×10⁻³ | 2.78×10⁻⁴ | 208.7 |

`k_eff²` scales as `μ²` to within 1 % (two decades of `μ`, factor 100 in
`k_eff²` per decade), i.e. the coupling is a genuine second-order effect and
not a numerical artefact. **A3 is solved in principle**: a homogeneous plate in
bending now has a finite electromechanical coupling, and the whole effect is
controlled by one parametric constant that must be declared as assumed.
