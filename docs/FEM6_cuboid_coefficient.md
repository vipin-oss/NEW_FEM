# The strain-gradient coefficient: `K_g = ½ ∫ M_mn B_,mᵀ C B_,n`, `M` = second moment

**One-page, hand-checkable version.** Every step below can be verified with pen
and paper; the numerical checks at the end are reproduced by
`python3 python/run_verification.py` (V1, V7).

---

## Step A — what the averaging window contributes

Average the strain over a window `w` centred at `x`:

```
ε̄(x) = (1/|w|) ∫_w ε(x + ξ) dξ .                                          (A1)
```

Taylor-expand and use the symmetry of the window (`⟨ξ_p⟩ = 0` for a centred
window):

```
ε̄(x) = ε(x) + ½ M_pq ε_,pq(x) + O(ξ⁴) ,        M_pq = ⟨ξ_p ξ_q⟩ = (1/|w|)∫_w ξ_p ξ_q dξ .
                                                                           (A2)
```

`M` is the **only** thing the window contributes at this order. Its trace is
half the mean square radius, `tr M = ⟨|ξ|²⟩`.

## Step B — the tensor structure is forced

Take the nonlocal energy to be the energy *removed by averaging*,

```
U_g = ½ ∫ [ εᵀ C ε − ε̄ᵀ C ε̄ ] dΩ .                                        (B1)
```

Insert (A2). The `εᵀCε` terms cancel and the cross term doubles the ½ of (A2):

```
ε̄ᵀCε̄ = εᵀCε + εᵀC (M_pq ε_,pq) + O(M²)
⟹  U_g = −½ ∫ εᵀ C M_pq ε_,pq dΩ .                                        (B2)
```

Integrate by parts once, `∫ εᵀC M_pq ε_,pq = ∮ (…) n ds − ∫ ε_,pᵀ C M_pq ε_,q`
(`C` symmetric, `M` constant), and drop the boundary term — the same natural
choice as FEM-1, which carries no double-traction condition:

```
U_g = ½ ∫ M_pq (ε_,p)ᵀ C (ε_,q) dΩ .                                       (B3)
```

With `ε = B q` and `ε_,p = B_,p q`, and `U_g = ½ qᵀ K_g q`:

```
K_g = c ∫ M_mn (B_,m)ᵀ C (B_,n) dΩ ,        c = 1 for (B1).                 (B4)
```

**What is claimed and what is not.** (B4) says the *structure* is forced:
the gradient stiffness is linear in `M`, contracted once on each side, for any
window and any kernel. The *scalar* `c` depends on which energy functional one
identifies with `U_g` (½ for "energy removed", 1 for (B1) as written, ¼ for the
squared difference form); it is a **normalisation**, equivalent to redefining
the length scale. It does not depend on the shape. The paper fixes it once
(next step) and never re-derives it.

## Step C — fixing the convention (and where "½" comes from)

FEM-1 published

```
K_g^(FEM-1) = (l²/10) ∫ ( B_,xᵀ C B_,x + B_,yᵀ C B_,y ) dΩ .              (C1)
```

Comparing (B4) with (C1) term by term, the two agree **exactly** if and only if

```
c · M = (l²/10) I ,        i.e.  M = l²/(10 c) · I .                       (C2)
```

Choose the convention

```
c = ½        and        M = ⟨ξ ξ⟩  (the true second moment).               (C3)
```

Then (C2) gives `M = l²/5` — **the second moment of a 3-D ellipsoid of
semi-axis `l`** (`⟨x²⟩ = R²/5` for a sphere; the same factor for an ellipsoid
along an axis). So FEM-1's `l` is the semi-axis of a 3-D-equivalent ellipsoid,
and FEM-1's coefficient `1/10` is `½ · (1/5)`.

Consequences, both of which are one-line checks:

* **The 5× trap.** Writing `K_g = (1/10)∫ M_mn B_,mᵀCB_,n` with a *cuboid*
  `M = a²/3` gives `a²/30` where (B4) gives `a²/6` — exactly **5× too small**
  (eigenfrequencies off by `√5`). This is the error the blueprint's working
  note is circling.
* **The "1/12" trap.** `1/12` is the *energy* coefficient of a cuboid
  (`U = ½qᵀKq`); putting it into `K_g` halves the stiffness. Measured: the
  FEM-1 benchmark gives 4.2339 µm with `c = ½`, 4.3192 µm with `c = ¼` — the
  published value is 4.23 µm, so `c = ½` is the one that reproduces it.

## Step D — the shape table (elementary integrals)

All three integrals below are one line each, with the window averaged as in
(A2) (`(1/|w|)∫_w ξ² dξ`):

| window (parameter `p`) | `⟨x²⟩` | integral |
|---|---|---|
| rectangle / cuboid, half-width `a` | **a²/3** | `(1/2a)∫_{−a}^{a} ξ² dξ = a²/3` |
| 2-D ellipse, semi-axis `l` | `l²/4` | `∫_{-l}^{l} ξ² · 2√(1−ξ²/l²) dξ / (πl) = l²/4` |
| 3-D ellipsoid, semi-axis `R` | **R²/5** | `(3/(4πR³)) ∫_{|x|≤R} x² dV = R²/5` |

So in the form (B4) with `c = ½`:

```
cuboid     :  c·M = a²/6  =  (1/6) a²     ← replaces FEM-1's 1/10
2-D ellipse:  c·M = l²/8  =  (1/8) l²
3-D ellipsoid: c·M = R²/10 =  (1/10) R²   ← FEM-1's value
```

which is exactly the "1/6 replaces 1/10" of the blueprint, with the ½ *derived*
in Step B and the shape factor `1/3, 1/4, 1/5` coming from Step D.

## Step E — three checks you can do on paper

1. **Constant strain ⟹ no gradient energy.** If `ε = const` then `ε_,m = 0`
   and `K_g q = 0` by (B4). This is why the patch test (V1) passes to
   `4.4×10⁻¹⁶` and why the gradient term cannot corrupt the constant-strain
   field.
2. **FEM-1 reduction.** Put `M = (l²/5) I` in (B4) with `c = ½`: `K_g = (l²/10)∫(B,xᵀCB,x +
   B,yᵀCB,y)` = (C1) exactly. Measured in V1: relative difference
   `3.4×10⁻¹⁶`.
3. **Equal moment ⟹ identical model.** Two windows with the same `M` give the
   same `K_g` **bit for bit**, because `M` is the only window-dependent object
   in (B4). Measured in V1: difference `0.0`; in V7: `a = l√(3/5)` reproduces
   the ellipsoid result to all digits.

## Step F — the paper claim (equal half-width, not equal moment)

The comparison to report is at **equal half-width / semi-axis** `a = l`, which
is the physically meaningful "same window size":

| `l/L` (= `a/L`) | ellipsoid `l²/5` | cuboid `a²/3` | ratio of gradient stiffness |
|---|---|---|---|
| 0.05 | 0.9890 | 0.9845 | 5/3 |
| 0.10 | 0.9732 | 0.9638 | 5/3 |
| 0.20 | 0.9408 | 0.9220 | 5/3 |

(`ū` on the FEM-1 benchmark, 20×4 mesh, normalised by the classical 4.5003 µm;
V7.) The cuboid is stiffer by exactly the second-moment ratio
`(a²/3)/(l²/5) = 5/3` at `a = l`, and **at equal `M` the two are identical to
machine precision**. The paper states both sentences:

> At equal window size the rectangular averaging domain gives a `5/3` larger
> strain-gradient stiffness than FEM-1's ellipsoidal one, which is exactly the
> ratio of their second moments; when the second moments are matched the two
> windows are indistinguishable, confirming that the nonlocal response of this
> class of models is governed by `M` alone and that the window *shape* enters
> only through `M`.

That is a positive, defensible claim (it identifies the governing tensor),
instead of an unidentifiable "shape effect" claim.
