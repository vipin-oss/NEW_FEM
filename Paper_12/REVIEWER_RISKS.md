# Reviewer risks — where the manuscript answers them, and what it does not

Eight points a referee is likely to raise.  "Where it is addressed" names the
section of `main.tex`; "still open" says what a careful referee can still
object to after reading it.  Nothing here is hidden from the paper: every item
appears in §7 (Limitations and unverified items) or where the number is used.

---

## 1. Overlap with FEM-4 (the previous paper of the series)

**Risk.** The paper could read as FEM-4 plus a memory term.

**Where it is addressed.** §1 (Introduction) states the FEM-4 overlap
explicitly and confines the new claims to three: the quantitative choice
between the two candidate memory matrices, the equal-`M` equivalence of window
shapes with the closed forms `a²/3`, `a²/4`, `a²/5`, and the coupling/damping
design map.  §5.2 reports the memory-matrix result as a number (`0.449`, i.e.
55 % less dissipation) rather than as a claim.

**Still open.** The self-citation is a placeholder (`% TODO`), so a referee
cannot check the overlap against the actual FEM-4 text.  This is the single
most likely desk-reject trigger and the first thing to fix.

---

## 2. The flexoelectric coefficient is assumed, not measured

**Risk.** Every flexoelectric number could be an artefact of `μ = 1e-6 C/m`.

**Where it is addressed.** §7 item 2 says so in the first line; §5.4 opens
with "(a *nominal* value: no measured flexoelectric coefficient for BaTiO₃ is
used here, and the whole panel scales as `μ²`)"; check F2 (constant-strain
patch test against `μκh/κ33`) fixes the *implementation*, not the material, and
the paper says that too.  The panel is therefore a scaling law with a
free constant, which is what it is presented as.

**Still open.** A referee may ask for at least a range of published `μ` values
(10⁻⁶ … 10⁻⁴ C/m) with the panel redrawn for the ends of the range.  That is a
one-line change to `run_demos.py` and would remove the objection cheaply.

---

## 3. Mass density is unverified

**Risk.** All frequencies scale as `ρ^{-1/2}`; `ρ = 6020 kg/m³` has no primary
source in the repository.

**Where it is addressed.** §7 item 1; the frequency axes of Figs. 2, 7 and 8
are the only places it enters, and the paper states that the coupling factors,
the size-effect ratio and the damping ratios do not depend on it.  Every
ratio quoted in the abstract is ρ-free.

**Still open.** It must be sourced before submission.  Until then no frequency
in the paper should be read as a prediction.

---

## 4. The fractional Kelvin–Voigt element is unbounded

**Risk.** `|C*(ω)| ~ (ωτ)^α` grows without limit, so the model cannot be a
material law over a wide band.

**Where it is addressed.** §5.3 (memory study, S2) quantifies the error
against a fractional Zener element: the KV/Zener modulus ratio is 1.035 at
`ωτ = 0.3`, 1.345 at `ωτ = 1`, 9.14 at 10 and 90.9 at 100, so the model is
defensible only for `ωτ ≲ 1`, and the paper says that in the same paragraph as
the numbers.  The pole figures (Figs. 5 and 9) are drawn over the whole range
including the region where the model should not be trusted.

**Still open.** The reader has to combine the figure range with the S2 table to
see the validity window; a shaded band on Fig. 9 marking `ωτ > 1` would make it
impossible to miss, and is worth adding.

---

## 5. The window is small compared with the plate (`a/L` range)

**Risk.** The nonlocal window is `3 × 1.5 µm` on a `200 µm` plate, i.e.
`a/L ≈ 0.015`; a nonlocal model used far below its own length scale is a
gradient model in disguise.

**Where it is addressed.** §2.3 derives the second-moment form and states that
only `M` enters, so the window is a two-parameter object (`M_xx`, `M_yy`) and
the paper measures the *sensitivity* to it: Fig. 3 covers aspect ratios 2–10 at
fixed long half-width, and Fig. 10 covers `l/L_x = 0.01 … 0.2` for the
averaging error.  The range is stated in every caption that uses it.

**Still open.** No case is run with `a/L > 0.2`, where the second-moment
truncation itself would break.  The paper should say in §7 that the model is
only claimed for `a/L ≲ 0.2`; currently the bound is implied by Fig. 10 rather
than stated.

---

## 6. The flattening of the flexoelectric curve below 2 µm

**Risk.** The curve in Fig. 7(a) rolls over from `h^-2` to `h^-0.66`, which can
be read as a numerical artefact.

**Where it is addressed.** §5.4 gives the three local slopes (−1.92, −1.52,
−0.66), the mesh witness (96×4 vs 48×4 agree to 0.04 % and 0.35 % at the two
ends, check T4), the `μ = 0` residual (1.0×10⁻¹⁰, check T5), and the
independent signature in `f₁` (210.4, 108.0, 50.2, 34.7 kHz against pure
Euler–Bernoulli scaling 210, 105, 42, 21).  §7 item 4 concedes that the
*attribution* to the window-to-thickness ratio is an interpretation.

**Still open.** The physical explanation is a story, not a measurement.  A
referee may accept it as such (the paper says it is) or ask for a run with the
window scaled with `h` to separate the two mechanisms.  That run is not done.

---

## 7. Plane stress versus plane strain

**Risk.** A 2-D reduction is a modelling choice; a three-dimensional solution
would not need it.

**Where it is addressed.** §4.1 and Table 2 give both choices for all four
polarisation/kinematics combinations, with the mode index named so that the
comparison is between the same mode.  The plane-stress value is then compared
with the 3-D free-bar closed form in §4.4 (check C2): the 2-D model sits 2.8 %
below the 3-D bar, and the paper attributes that gap to the dropped `e31 εzz`,
i.e. to the reduction itself rather than to the discretisation (which `C1`
shows is at 10⁻⁵).

**Still open.** The 2.8 % gap is *not* removed, and a referee writing in 3-D
will notice that the "thickness-independent piezo coupling" is a 2-D statement.
The paper's defence — that the gap is constant in `h` so the *trend* survives
— is stated but not shown as a separate number.

---

## 8. Placeholder material and bibliographic data

**Risk.** The manuscript's self-citations, author block and journal name are
placeholders, and `ρ` and `μ` have no primary source.

**Where it is addressed.** The placeholders are marked `% TODO` and listed in
`README.md`; the two unverified constants are stated in §7 and again where
they are used, and no number in the abstract depends on `μ` or on `ρ`.

**Still open.** All of it, by construction.  These are the items that must be
filled in before the paper is submitted; none of them can be resolved from the
repository, and none of them is silently glossed over in the text.
