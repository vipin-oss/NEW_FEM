# FEM-6 — independent checker report

**Scope.** I read the blueprint (`FEM6_Blueprint.md`), the delivered code
(`FEM6_memory_piezo_SG_2D.m`), and the FEM-1 manuscript, then **re-implemented
the whole model from the equations** (no MATLAB in this environment) in
`python/fem6_core.py` + `python/run_verification.py` + `python/run_demos.py`,
and ran every verification case in the blueprint plus six additional ones. All
numbers quoted below are produced by those scripts, not copied from the
manuscripts. Nothing here is a paraphrase of another reviewer's opinion; where
the blueprint's own working notes are wrong I say so and show the number that
contradicts them.

Files:

| file | content |
|---|---|
| `python/fem6_core.py` | element, assembly, condensation, modes, L1 stepping, complex pole |
| `python/run_verification.py` | V1–V7, 40 s, writes `results/verification.{md,json}` |
| `python/run_demos.py` | figures 1–4, writes `results/demo.json` |
| `matlab/FEM6_memory_piezo_SG_2D_v2.m` | corrected MATLAB mirror |
| `docs/FEM6_cuboid_coefficient.md` | Q1 in full |

**Verdict.** The model is publishable, the *implementation as delivered is not*:
two blocking defects (the L1 weights and, depending on how Q1 is settled, the
gradient coefficient), one physical dead end (the demonstration cannot produce a
voltage), and a material set that cannot be justified as BaTiO₃. Details and
fixes below; every fix is verified in the Python reference.

---

## 1. The four questions

### Q1 — cuboid coefficient: `1/2 · M`, i.e. `1/6` where FEM-1 wrote `1/10`

Write the nonlocal stiffness with the **second-moment tensor**,

```
K_g = (1/2) ∫ M_mn (B_,m)ᵀ C (B_,n) dA ,        M = ⟨ξ ξ⟩ .            (Q1.1)
```

Then the coefficient is shape-independent and only `M` changes:

| window | `M_xx` | `c_shape` in `c·l²∫(B_,xᵀCB_,x + B_,yᵀCB_,y)` |
|---|---|---|
| segment / rectangle / cuboid, half-width `a` | `a²/3` | **1/6** |
| 2-D ellipse, semi-axis `l` | `l²/4` | 1/8 |
| 3-D ellipsoid, semi-axis `R` | `R²/5` | **1/10** ← FEM-1 |

So **FEM-1's 1/10 is the 3-D-ellipsoid entry**; a cuboid needs **1/6**, i.e.
`M = a²/3` with the universal `1/2`. Verified (`V1`):

* `K_g` with `M = (l²/5)I` reproduces FEM-1's `(l²/10)(K_xx + K_yy)` to
  `3.4×10⁻¹⁶`;
* `K_g(cuboid, a=l) / K_g(ellipsoid, l) = 1.666667` (= 5/3);
* equal `M` ⟹ identical matrices (difference `0.0`);
* with `1/6` the FEM-1 benchmark is reproduced (4.234 µm at `l/L = 0.2`, paper
  4.23 µm); with the doubled-halving `1/12` it is not.

**Two traps.**

1. *Keeping 1/10 in front of the cuboid moment* is 5× too small (frequencies
   off by `√5`). This is the error the blueprint's note is circling.
2. The blueprint's "corrected" column (1/12, 1/16, 1/20) is the **energy**
   coefficient. `U = ½qᵀK_g q`, so the stiffness entries are 1/6, 1/8, 1/10.
   Putting 1/12 into `K_g` halves the model and breaks the FEM-1 benchmark.

**The consequence nobody has written down:** because only `M` enters, **two
windows with the same `M` are indistinguishable**. A cuboid and an ellipse with
`l = a√(3/5)` give bit-identical results, as do a rotated and an unrotated
window with the same `M`. The planned *cuboid-versus-ellipsoid* comparison is
therefore not identifiable at second order — see finding B5 and
`docs/FEM6_cuboid_coefficient.md` §4 for the reframing.

### Q2 — memory on the full condensed `K_eff` or only on the mechanical block?

**Recommendation: keep the full condensed `K_eff` as the baseline, but stop
calling it "the mechanical damping".**

The condensed operator is `K_eff = K_uu + K_up Z`, `Z = A⁻¹K_upᵀ`. The second
term is the piezoelectric back-stress: in open circuit the depolarisation field
resists the strain, so `K_eff > K_uu`. A relaxation mechanism inside the
material (defect hopping, domain-wall motion) is driven by the *total* stress,
which in the quasi-static condensed description is `K_eff q`. So applying the
Caputo kernel to `K_eff` is the consistent homogenisation **provided** the
electrical response is instantaneous.

Three caveats that must appear in the text:

1. **It predicts dielectric relaxation.** With the kernel on `K_eff`, a step
   displacement gives a voltage that decays as `t^{-α}` — i.e. the model says
   the dielectric constant relaxes with the same `τ, α` as the mechanics. That
   is a strong assumption. Verified consequence: in the ring-down demo the
   open-circuit voltage decays with the same envelope as the displacement.
   If the paper reports `V(t)`, it must say this.
2. **With the mechanical-only variant the modal problem is not diagonal**, since
   `Φᵀ K_uu Φ = Λ + Φᵀ(K_uu − K_eff)Φ` and the second term is full. Then the
   scalar "one ζ per mode" picture collapses and each modal equation is coupled
   through the memory term. This is a real cost, not a detail.
3. **k_eff² keeps its meaning only in the `K_eff` form.** `k² = (ω_oc² −
   ω_sc²)/ω_oc²` follows from the condensation identity; if the memory acts on
   `K_uu` alone, the identity holds at `t = 0` but not during relaxation.

So: baseline `K_eff` (as delivered), and report the `K_uu` variant as a
*sensitivity* in one sentence with one number. Do not present the choice as
obvious.

### Q3 — fractional Kelvin–Voigt vs fractional Zener

**KV is acceptable for the FEM demonstration, but it is not a physically
admissible constitutive law at high frequency, and the paper should say so.**

`σ = C(ε + τ^α D^α ε)` ⟹ `C*(ω) = C(1 + (iωτ)^α)`, so `|C*| ~ ω^α → ∞`. A real
solid has a bounded glassy modulus. The fractional **Zener** (springpot in
series with a spring, or the three-parameter Cole–Cole form)

```
C*(ω) = C_∞ (C_0 + C_∞ (iωτ)^α) / (C_∞ + C_0 (iωτ)^α)
```

is bounded at both ends, gives a Cole–Cole loss peak with the correct asymmetry,
and reduces to KV in the limit `C_∞ → ∞` (rigid series spring). Recommendation:

* keep KV for the numerical demonstration (it is the one that keeps `K_eff`
  proportional and the modal system diagonal — a genuine advantage);
* add one paragraph stating that the unbounded high-frequency modulus is a
  modelling artefact, that the Zener form removes it, and that at the
  frequencies of interest (`ωτ ≪ 1`) the two differ by `O((ωτ)^{2α})`;
* if a reviewer asks for the Zener, it is a one-line change in the modal
  equation and does not disturb anything else.

Do **not** claim KV is "the physically consistent choice" — with the dielectric
relaxation caveat of Q2 it is doubly exposed.

### Q4 — plane strain and placeholder materials

**For verification, yes. For the publication, no — with two specific fixes.**

1. **Plane strain is the wrong limit for this device.** The plate is
   200 × 10 µm with a 10 µm thickness: thickness ≈ width, so neither plane
   strain nor plane stress is exact; plane **stress** is the closer
   approximation for a thin film, plane strain for a long bar. Pick one and
   state the criterion, or (better) do one 3-D check on a coarse mesh and show
   the 2-D model is within a few percent.
2. **An isotropic `C` with a 4 mm `e` and `κ` is not a material.** The
   piezoelectric tensor must be compatible with the elastic symmetry; an
   isotropic body admits only `e = 0` (or the special isotropic
   piezoelectric class). Any reviewer with a materials background will stop
   reading at that table.
3. **The anisotropy ratio is off by 30×.** The delivered `κ = diag(1.2×10⁻⁸,
   1.0×10⁻⁸)` gives `κ11/κ33 = 1.2`; tetragonal BaTiO₃ has `κ11/κ33 ≈ 39`
   (`1.95×10⁻⁸` vs `5.0×10⁻¹⁰`). That single number changes the capacitance by
   20× and the voltage by the same factor.
4. Fix: use the FEM-5 set (given in §4) as the default and keep the
   placeholders behind a switch, labelled "placeholder, for code verification
   only". A verification case may use any material; a results section may not.

---

## 2. Findings

Severity: **A** = wrong result / must fix before submission, **B** = must fix
(argument or number is indefensible), **C** = improvement, **D** = cosmetic.
Per the workflow playbook I act on A and B only.

### A1 (blocking) — the L1 weights miss `b₀`, so α = 1 has no damping

The Caputo derivative at `t_n` on a uniform grid is

```
D^α q(t_n) = dt^{-α}/Γ(2-α) · Σ_{k=0}^{n-1} b_k (q_{n-k} − q_{n-k-1}) ,
b_k = (k+1)^{1-α} − k^{1-α},   b_0 = 1 .                              (A1.1)
```

The delivered convolution starts at `b_1`, so the newest increment carries
`b_1 = 2^{1-α} − 1` instead of 1. At `α = 1` that is **zero**: the damping
term disappears completely, and at `α = 0.7` it is 0.23 instead of 1.

Evidence — same model, same `dt`, same history length, late-time free-decay
amplitude (should be `~1e-9`):

| α | delivered scheme | corrected scheme | ratio |
|---|---|---|---|
| 1.0 | `4.58×10⁻⁸` | `1.40×10⁻⁹` | **32.6** |
| 0.7 | `1.68×10⁻⁹` | `5.56×10⁻¹⁰` | 3.0 |

Consequences: the closed-form `α = 1` comparison (blueprint verification case
3) **cannot** pass with the delivered code unless the tolerance is loose enough
to hide the missing damping; the `ζ(α)` curve in the paper is systematically
low; and the "α = 1 recovers classical Kelvin–Voigt" claim — the one that
validates the whole discretisation — is the one that fails.

I also confirmed the *positive* side: with the corrected weights the scheme is
second-order accurate in time, relative error `7.96e-3 / 4.04e-3 / 2.04e-3 /
1.02e-3` at `N_t = 200/400/800/1600` (observed order **0.99**), and the
steady-state harmonic amplitude matches the analytic transfer function
`H(Ω) = 1/(−Ω² + ω₀²(1 + (i Ω τ)^α))` to `0.04–0.4 %` for `α = 1.0, 0.7, 0.5`
at `Ω/ω₀ = 0.5, 1, 2`. **That harmonic test is the verification case that is
missing from the blueprint** — it is the only one that catches A1.

Fix: shift the weight vector by one (`b(1) = 1`) and keep the same convolution
indexing; or equivalently start the sum at `k = 0`. One line, in
`modal_fractional` and in any other place the history is built.

### A2 (blocking, depending on Q1) — gradient coefficient

See §1/Q1. If the delivered code uses `0.1 * L` with `L = R diag([lx², ly²]) Rᵀ`
on a mesh whose length scale was fitted as a *cuboid* half-width, the model is
5× too soft, `f ∝ √5`, and every length-scale statement is wrong. If it uses
the ellipsoid `l` consistently, it is right and only the caption needs fixing.
Decision needed before any figure is final. The corrected form is

```
Kg = 0.5 * ( M11*(Bx'*C*Bx) + M12*(Bx'*C*By + By'*C*Bx) + M22*(By'*C*By) )
M  = R*diag([ax^2/3, ay^2/3])*R'          % cuboid
M  = R*diag([lx^2/5, ly^2/5])*R'          % ellipsoid (= FEM-1's 1/10 * l^2)
```

### A3 (blocking for the demonstration) — the bending mode cannot produce a voltage

In the delivered configuration (homogeneous plate, through-thickness
electrodes) the charge on the electrode is

```
Q = ∫ e31 ε_xx dA ,      ε_xx = −y κ  ⟹  Q ∝ ∫ y dA = 0                     (A3.1)
```

for a section symmetric about the neutral axis. With a clamped-free plate the
cancellation is not exact but it is complete to numerical precision. Measured
(V4, 20×4, BaTiO₃, poling "y"):

```
f_short = 224732.2475 Hz ,  f_open = 224732.2475 Hz ,  k² = 2.27×10⁻¹⁰
min eig(K_oc − K_sc)/max|eig| = −3.7×10⁻¹⁶
```

i.e. `K_oc = K_sc` to machine precision, `k²` is numerical noise, and the
sensor output is zero. This is *physics, not a bug* — and it is exactly what
the paper would be reporting if it kept this configuration.

What does work (V4, poling "x", left/right electrodes, length extension):

| mode | f_sc (Hz) | f_oc (Hz) | k_eff² |
|---|---|---|---|
| 1 | 165 932.53 | 165 932.53 | 0 |
| 2 | 1 033 874.06 | 1 033 874.06 | 0 |
| 3 | 2 869 208.29 | 2 869 208.29 | 0 |
| 4 | 5 280 148.29 | 5 552 809.46 | 0.0958 |
| 5 | 5 552 809.46 | 7 163 154.29 | **0.3991** |
| 6 | 9 038 751.63 | 9 038 751.63 | 0 |

Three options, in order of effort:

1. **Switch the demonstration to length extension** (free — the code already
   supports it): `k² = 0.40`, a real voltage, and the memory effect is visible
   in the ring-down. Requires the electrode pair to be `left/right`.
2. **Bimorph/unimorph**: break the symmetry (two layers with opposite poling);
   the net charge is proportional to the asymmetry. Bigger change, standard
   result.
3. **Add flexoelectricity**: `D = e ε + μ ∇ε`. A strain-gradient theory that
   already computes `∇ε` is the natural home for `μ`, and flexoelectricity is
   precisely the mechanism that produces charge in *bending* of a homogeneous
   plate. This would turn the paper's weakness into its novelty. Larger
   change, but the terms are already assembled (`B_,x`, `B_,y`).

Do **not** ship the current demonstration: `k² = 2×10⁻¹⁰` will be read as a
coding error even though it is correct.

### B1 — the material set is internally inconsistent

`C` isotropic + `e` tetragonal + `κ11/κ33 = 1.2`. Also, in the poled-`x`
configuration the code must swap `C11 ↔ C33` and `κ11 ↔ κ33` along with `e`
(verified in the Python: the four tensors transform together, see §4). Replace
with the FEM-5 set and keep the placeholders behind a flag.

### B2 — explicit central difference with a heuristic stability check

The delivered scheme is explicit with warnings `(w dt)² > 2` and `γ > 1.5`.
Those conditions are for the *undamped* central difference; with the memory term
the effective damping changes every step, so no fixed bound exists. At
`dt/τ = 1/200` (the delivered setting) the scheme is fine; at `α = 0.3` and
`dt/τ = 1` it is not, and the failure is silent.

Fix (implemented and verified here): Newmark `β = 1/4, γ = 1/2` with the L1
term treated implicitly. For each mode,

```
[1 + β dt²(1+c) ω²] q_{n+1} = f − ω²(1+c) q̂ + c ω² (q_n − S_n)
```

where `c = dt^{-α}/Γ(2−α)`, `q̂ = q_n + dt v_n + dt²(½−β)a_n`, and
`S_n = Σ_{k≥1} b_k Δq_{n−k}`. Unconditionally stable for the mechanical part,
same accuracy, no stability tuning. 12 lines.

### B3 — the verification set cannot detect A1

Cases 1–2 (patch, benchmark) are static; case 4 (piezo) is an eigenproblem;
case 3 is the only dynamic one and it is the one that fails. Add: (i) the
harmonic response against the analytic `|H(Ω)|` (catches A1 immediately);
(ii) a time-step refinement study with the observed order (should be 1 for L1 —
we measure 0.99); (iii) `τ → 0` must return the undamped model (residual
`2.08×10⁻⁹`, verified).

### B4 — the electrode constraint is incomplete

Fix the potential value **and** its tangential derivative on the electrode, or
neither. In the C1 space `φ`, `φ,x`, `φ,y` are independent nodal unknowns, so
tying only the nodal `φ` values does not make `φ` constant along the electrode:
the element can still vary along the edge through the derivative dofs. The code
as delivered leaves `φ,x` free on the top face (and `φ,xy` on the bottom),
which is a slightly "leaky" equipotential and biases the capacitance.

Verified fix: on a left/right electrode pair, fix `φ,y = 0` on both faces
(`φ` is constant along a vertical edge ⟹ its tangential derivative vanishes);
on a top/bottom pair, fix `φ,x = 0`. With this, the lumped capacitance matches
the analytic `κ A/L` exactly (`2.4792×10⁻¹¹ F` vs `2.4792×10⁻¹¹ F`, ratio
1.0000, on 4×1, 8×2 and 20×4 meshes). Without it the value drifts with the
mesh.

Alternative (better, C-level): use C0 for `φ`. The potential is a scalar
Laplace field; C1 triples the electric dofs for no accuracy gain and creates
exactly this constraint bookkeeping.

### B5 — "cuboid vs ellipsoid" is not identifiable

See Q1 and the memo. At second order only `M` matters; equal `M` gives
identical matrices (difference `0.0`). Either reframe (recommended) or go to
fourth order (needs C2, out of scope for BFS C1).

### C1 — efficiency

`Aem` is assembled as `ndof × ndof` (85 % zeros), and `eigs(...,'smallestabs')`
runs on the full 12-dof-per-node system. `Aem` can be `nnode × nnode`; the
condensation can be done on the potential block only. On the delivered
24×2 mesh this is invisible; on a 3-D or refined mesh it will not be.

### C2 — units of the memory parameters

`τ^α` has units `s^α`. For `α ≠ 1`, `τ` is not a relaxation time; the
physically meaningful combination is `(ω₀τ)^α`, and the paper must state which
of `τ`, `τ^α`, or `ω₀τ` is being varied. Currently the sweep varies `τ` at fixed
`α`, which means the physical time scale changes with `α` — that is why the
`ζ(α)` curve at fixed `τ` is not a fair comparison across `α`.

### C3 — mode tracking for `k_eff²`

Pair open- and short-circuit modes by shape (MAC), not by index. In the
extensional case the ordering swaps between modes 4/5 as soon as the coupling
is non-zero (table in A3). An index-based formula will silently assign
`k² = 0.398` to the wrong pair on a slightly different mesh.

### C4 — first step of the explicit scheme

`q(:,2) = 0.5 dt² f` omits the `ω²(q + …)` and `c` terms at `n = 0`. It is
`O(dt²)` and harmless, but it is another reason the `α = 1` case drifts. The
Newmark start (`a₀ = f − ω²q₀`) removes it.

### D — cosmetic

Unused `i` loop variables, no units in the figure labels, `fo`/`fs` naming,
missing `rng` seed for any stochastic part, no `assert`-based self-test at the
top of the script. Add a self-test block: patch energy, capacitance vs analytic,
`min eig(K_oc − K_sc) ≥ 0`, `min eig(K_sc) > 0`. All four are one-liners and
they would have caught A3 and B4 before any figure was made.

---

## 3. Verification results (all recomputed here)

`python3 python/run_verification.py` → `results/verification.{md,json}`, 40 s.

**V1 patch / operator.** Energy relative error `4.44×10⁻¹⁶`; gradient energy
under constant strain `1.06×10⁻¹²`; ellipsoid `K_g` vs FEM-1 `3.40×10⁻¹⁶`;
cuboid/ellipsoid at equal half-width `1.666667`; at equal `M` `0.0`.

**V2 FEM-1 benchmark** (`E = 2×10¹¹`, `ν = 0.3`, `L_x = 1`, `L_y = 0.2`,
`t_x = 10⁶`, plane strain; analytic `4.55 µm`):

| mesh | dof | `ū` (µm) | `l/L` | ratio to classical |
|---|---|---|---|---|
| 5×1 | 96 | 4.4128 | 0.02 | 0.9974 |
| 10×2 | 264 | 4.4717 | 0.05 | 0.9890 |
| 20×4 | 840 | 4.5003 | 0.10 | 0.9732 |
| 40×8 | 2952 | 4.5143 | 0.20 | **0.9408** |

Paper: classical 4.50 µm, `l/L = 0.2` → 4.23 µm (ratio 0.94). Agreement
`0.1 %` on the absolute value and `1 %` on the ratio.

**V3 mesh convergence.** Relative error `2.35×10⁻² / 1.05×10⁻² / 4.13×10⁻³ /
1.02×10⁻³` against a 60×12 reference; observed order **1.68** (C1 element,
second-order expected; the gradient term degrades it — worth one sentence).

**V4 piezo.** See A3 for the tables. Extras: `β = 9.9166×10⁻⁹ F` for the
through-thickness pair (matches `κ33 A/L` analytically), `min eig(K_sc) > 0`,
`min eig(K_oc − K_sc) ≈ 0`.

**V5 memory.** `α = 1` vs closed form: `7.96e-3/4.04e-3/2.04e-3/1.02e-3`
(order 0.99); harmonic `|H|` ratios `0.9963–1.0037` across `α = 1.0/0.7/0.5` and
`Ω/ω₀ = 0.5/1/2`; `τ → 0` residual `2.08e-9`; L1 off-by-one: `4.58×10⁻⁸` vs
`1.40×10⁻⁹` at `α = 1`. Exact vs small-damping `ζ`:
`0.31416/0.32043/0.28464/0.20969/0.12398` for `α = 1.0/0.9/0.7/0.5/0.3` — note
the small-damping approximation `ζ ≈ ½ωτ` is off by 60 % at `α = 0.3`, so the
paper must use the complex root, not the approximation.

**V6 static modal truncation** (20×4, direct 4.4322 µm): relative error
`1.00 / 1.00 / 1.89×10⁻¹ / 6.68×10⁻² / 5.15×10⁻² / 4.27×10⁻² / 3.19×10⁻²`
for 1/2/4/8/12/16/24 modes. Bending converges slowly in modal space — the paper
should report how many modes the dynamic results actually need.

**V7 domain comparison** (20×4, `u_classical = 4.5003 µm`): ellipsoid
`0.9890/0.9732/0.9408`, cuboid `0.9845/0.9638/0.9220`, cuboid at equal moment
identical to ellipsoid. I.e. the shape changes the numbers only because it
changes `M`.

**Figures** (`python3 python/run_demos.py`): `results/figures/fig1_k2_orientation.png`,
`fig2_memory_response.png`, `fig3_damping_ratio.png`,
`fig4_domain_comparison.png`; numbers in `results/demo.json`.

Memory demo numbers (200×10 µm bar, cuboid `3×10⁻⁶/1×10⁻⁶`, 10 nm axial
release): mode 5 at 7.161 MHz, `k² = 0.402`, `V(t = 0) = 141.5 V` for all `α`
(as it must — the initial condition is the same), with `τ = 3×10⁻⁹ s` chosen so
that `ωτ = 0.13` and the ring-down is **underdamped** over 20 periods; the
`α = 0.7` curve lags the `α = 1` curve, which is the visible signature of the
fractional kernel.

*Warning on `τ`.* The blueprint's `τ = 3×10⁻⁷ s` gives `ωτ = 13.5` for this
mode, i.e. the mode is **overdamped** (`ζ = 6.75`) and the response is a pure
non-oscillating relaxation. That is not an error, but if the paper shows "the
memory effect on the ring-down" with those parameters the reader will see a
decay curve with no oscillation and conclude the code is broken. Either choose
`τ` per mode so that `ωτ = O(0.1–1)`, or show the overdamped case deliberately
as the "creep" limit.

---

## 4. Revised blueprint — concrete delta

1. **§2.2 (gradient term).** Replace `0.1*Lt` by `0.5*Mg` with
   `Mg = R*diag([ax²/3, ay²/3])*R'` (cuboid) or `diag([lx²/5, ly²/5])`
   (ellipsoid). Keep a one-line switch `p.domain ∈ {"cuboid","ellipsoid"}`.
   State `L = 5M ⟺ c = 1/10`.
2. **§3 (memory).** Fix `b₀ = 1`; state the discrete formula (A1.1) in the
   paper; replace the explicit scheme by Newmark + implicit L1; drop the
   `(w dt)² > 2` warnings (or keep them as diagnostics of `dt/τ`).
3. **§4 (verification).** Add: harmonic `|H(Ω)|` (α = 1, 0.7, 0.5), time-step
   order, `τ → 0` limit, and the "equal-`M` windows are identical" check.
   Remove: "cuboid vs ellipsoid" as a *result* (keep as a check).
4. **§5 (material).** One table: `C11 = 2.22e11, C12 = 1.08e11, C13 = 1.11e11,
   C33 = 1.51e11, C44 = 6.10e10 Pa`, `e31 = −0.7, e33 = 6.7, e15 = 34.2 C/m²`,
   `κ11 = 1.9479e-8, κ33 = 4.9583e-10 F/m`, `ρ = 6020`. State the plane-strain
   reduction and the poling axis.
5. **§6 (demonstration).** Switch to length extension (or bimorph, or add
   flexoelectricity). Report `k_eff² = 0.399` for mode 5 and say that the
   bending modes carry no charge *by symmetry* — as a validated prediction, not
   as an omission.
6. **New §7 (limitations).** `M`-only dependence (B5), dielectric relaxation
   implied by Q2, unbounded KV modulus (Q3), plane-strain/plane-stress choice
   (Q4).

## 5. Order of work (my recommendation)

| # | action | severity | effort |
|---|---|---|---|
| 1 | fix `b₀` and re-run every dynamic figure | A1 | 1 h |
| 2 | settle the gradient coefficient, re-run every static figure | A2 | 2 h |
| 3 | decide the demonstration (extension / bimorph / flexo) | A3 | 0.5 d |
| 4 | replace the material set, re-run V4 | B1 | 2 h |
| 5 | Newmark + implicit L1 in the delivered `.m` | B2 | 3 h |
| 6 | electrode tangential-derivative constraint | B4 | 2 h |
| 7 | rewrite the "domain" study as an "`M`/orientation" study | B5 | 0.5 d |
| 8 | add the harmonic + order + τ→0 checks to the paper | B3 | 2 h |
| 9 | mode tracking by MAC | C3 | 1 h |
| 10 | C0 potential, `nnode×nnode` `Aem` | C1/C4 | 1 d (optional) |

Items 1, 2 and 7 change numbers in the manuscript; per the playbook every
changed number must be logged in `CHANGES_AND_AUDIT_NOTES.md` with the old
value, the new value and the reason. The three are the only ones that do.
