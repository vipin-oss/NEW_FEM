# Reviewer risks — where the manuscript answers them, and what it does not

Ten points a referee is likely to raise.  "Where it is addressed" names the
section of `main.tex`; "still open" says what a careful referee can still
object to after reading it.  Nothing here is hidden from the paper: every item
appears in §7 (Limitations and unverified items) or where the number is used.

Updated after the independent-route round (criteria I1–I9, G1–G2, A2, N2).

| # | item | status | where | graded by |
|---|---|---|---|---|
| 1 | overlap with FEM-4 | partial | §1 | — |
| 2 | `μ` assumed, not measured | open (by construction) | §7 item 2, §5.5 | F2, G2 |
| 3 | `ρ` unverified | open (needs a source) | §7 item 1 | — |
| 4 | fractional KV is unbounded | **addressed** | §5.5, §7 item 7, Fig. 9 (`fig:zetasurf`) | I4, I5 |
| 5 | window small, `a/L` range | **addressed** | §5.4, §7 item 7 | V1d, I8 |
| 6 | flattening of the flexo curve | partial | §5.5, §7 item 4 | T4, T5, G2 |
| 7 | plane stress versus plane strain | partial | §4.2, §4.5, §7 item 3 | C1–C4 |
| 8 | placeholders and unverified constants | open (by construction) | §7, README | — |
| 9 | "two couplings on one plate?" | **addressed** | §1, §5.5, §8, `tab:config` | G1, G2 |
| 10 | which modulus, which permittivity | **addressed** | §4.1, `tab:axes`, §4.5 | I9 |

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

## 2. The flexoelectric coefficient is assumed, not measured

**Risk.** Every flexoelectric number could be an artefact of `μ = 1e-6 C/m`.

**Where it is addressed.** §7 item 2 says so in the first line; §5.5 opens
with "(a *nominal* value: no measured flexoelectric coefficient for BaTiO₃ is
used here, and the whole panel scales as `μ²`)"; check F2 (constant-strain
patch test against `μκh/κ33`) fixes the *implementation*, not the material, and
the paper says that too.  The panel is therefore a scaling law with a free
constant, which is what it is presented as.

**Still open.** A referee may ask for at least a range of published `μ` values
(10⁻⁶ … 10⁻⁴ C/m) with the panel redrawn for the ends of the range.  That is
still a one-line change to `run_demos.py` and remains undone.

## 3. Mass density is unverified

**Risk.** All frequencies scale as `ρ^{-1/2}`; `ρ = 6020 kg/m³` has no primary
source in the repository.

**Where it is addressed.** §7 item 1; the frequency axes of Figs. 2, 7 and 8
are the only places it enters, and the paper states that the coupling factors,
the size-effect ratio and the damping ratios do not depend on it.  Every ratio
quoted in the abstract is `ρ`-free.

**Still open.** It must be sourced before submission.  Until then no frequency
in the paper should be read as a prediction.

## 4. The fractional Kelvin–Voigt element is unbounded — **now answered**

**Risk.** `|C*(ω)| ~ (ωτ)^α` grows without limit, so the model cannot be a
material law over a wide band.

**Where it is addressed.** §5.2 quantifies the error against a fractional
Zener element: the KV/Zener modulus ratio is 1.035 at `ωτ = 0.3`, 1.345 at
`ωτ = 1`, 9.14 at 10 and 90.9 at 100.  The band `ωτ ≤ 1` is now drawn on
Fig. 9 (`fig:zetasurf`) — the floor of the surface is shaded for `ωτ ≤ 1`, a dashed line marks
`ωτ = 1`, and the region beyond carries no shading and is labeled "not
claimed".  §7 item 7 states the bound as a limitation rather than leaving it
to be inferred from an axis range.  The pole solver behind the figure is
itself checked against the roots of the same equation as a polynomial over
five orders and two decades (I4), and at `α = 1` both routes return `ωτ/2`
exactly (I5).

**Still open.** The element is unbounded *by construction*; the paper's claim
must remain "used, and valid, for `ωτ ≲ 1`", not "physically correct".  A
referee who wants a bounded element is asking for the Zener model, which §5.5
tabulates as the comparison.

## 5. The window is small compared with the plate (`a/L` range) — **now answered**

**Risk.** The nonlocal window is `3 × 1 µm` on a `200 µm` plate, i.e.
`a/L ≈ 0.015`; a nonlocal model used far below its own length scale is a
gradient model in disguise.

**Where it is addressed.** §2.3 derives the second-moment form and states that
only `M` enters, so the window is a two-parameter object (`M_xx`, `M_yy`) and
the paper measures the *sensitivity* to it: Fig. 3 (`fig:petals`) covers aspect ratios 2–10 at
fixed long half-width, and Fig. 10 (`fig:domain`) covers `l/L_x = 0.01 … 0.2`.  The bound is
now stated in words in §5.4 ("the bound claimed for the model is `a/L ≤ 0.2`,
which is the right-hand edge of this figure") and again in §7 item 7, and the
second-moment factors that the argument rests on are now obtained by
quadrature rather than read off the formula in the code (I8).

**Still open.** No case is run with `a/L > 0.2`, where the second-moment
truncation itself would break — the paper now says so instead of implying it.

## 6. The flattening of the flexoelectric curve below 2 µm

**Risk.** The curve in Fig. 7a (`fig:thickness`) rolls over from `h^-2` to `h^-0.66`, which can
be read as a numerical artefact.

**Where it is addressed.** §5.5 gives the three local slopes (−1.92, −1.52,
−0.66), the mesh witness (96×4 vs 48×4 agree to 0.04 % and 0.35 % at the two
ends, check T4), the `μ = 0` residual (1.0×10⁻¹⁰, check T5), and the
independent signature in `f₁` (210.4, 108.0, 50.2, 34.7 kHz against pure
Euler–Bernoulli scaling 210, 105, 42, 21).  §7 item 4 concedes that the
*attribution* to the window-to-thickness ratio is an interpretation.

**New since the last revision.** Table `tab:config` separates the two mechanisms that act
on this curve: the piezoelectric share of the bending coupling is at the
round-off floor at every thickness (G1), while switching the piezoelectric
constants off outright changes the flexoelectric coupling by 24 % at the
thinnest plate (G2) — i.e. the roll-over is not a piezoelectric artefact, but
the *size* of the reported growth (24 rather than 31) is set by the
piezoelectric stiffness of the same mode.

**Still open.** The physical explanation is a story, not a measurement.  A
referee may accept it as such (the paper says it is) or ask for a run with the
window scaled with `h` to separate the two mechanisms.  That run is not done.

## 7. Plane stress versus plane strain

**Risk.** A 2-D reduction is a modeling choice; a three-dimensional solution
would not need it.

**Where it is addressed.** §4.2 and `tab:kinematics` give both choices for all four
polarization/kinematics combinations, with the mode index named so that the
comparison is between the same mode.  The plane-stress value is then compared
with the 3-D free-bar closed form in §4.5 (check C2): the 2-D model sits 2.8 %
below the 3-D bar, and the paper attributes that gap to the dropped `e31 εzz`,
i.e. to the reduction itself rather than to the discretisation (which `C1`
shows is at 10⁻⁵).

**Still open.** The 2.8 % gap is *not* removed, and a referee writing in 3-D
will notice that the "thickness-independent piezo coupling" is a 2-D statement.
The paper's defense — that the gap is constant in `h` so the *trend* survives
— is stated but not shown as a separate number.

## 8. Placeholder material and bibliographic data

**Risk.** The manuscript's self-citations, author block and journal name are
placeholders, and `ρ` and `μ` have no primary source.

**Where it is addressed.** The placeholders are marked `% TODO` and listed in
`README.md`; the two unverified constants are stated in §7 and again where
they are used, and no number in the abstract depends on `μ` or on `ρ`.  Every
number in the abstract now carries an explicit verdict in
`results/abstract_audit.md` — checked or not checked, with the reason — and the
coverage check (A2) fails if the abstract grows a number without one.

**Still open.** All of it, by construction.  These are the items that must be
filled in before the paper is submitted; none of them can be resolved from the
repository, and none of them is silently glossed over in the text.

## 9. "Are the two couplings on the same plate?" — **new, now answered**

**Risk.** The paper quotes a piezoelectric `k² = 0.5581` and a flexoelectric
`k²` for "the same plate", which invites the reading that one device carries
both and that the two factors should be added.

**Where it is addressed.** §1 now has a paragraph headed *Two devices, not
one*; the abstract and §8 say the same thing; Table `tab:axes` gives the axes, the two
poling directions and the two tensors; and Table `tab:config` answers the quantitative
version of the question head-on for the bending device.  The piezoelectric
charge of a bending mode is odd in `y − h/2`, so its integral over a face
electrode vanishes and the piezoelectric-only `k²` of that mode is
`1.0×10⁻¹⁰` at every thickness (G1).  The two effects are nevertheless not
separable *inside one run*: the piezoelectric terms change the elastic
stiffness of the same mode and shift the flexoelectric coupling by up to 24 %
at the thinnest plate (G2), which is why the reported growth is 24 and the
`e = 0` idealisation would be 31.  Both are quoted to two significant digits
because the `h = 1 µm` point itself moves at the 1e-3 level between numeric
stacks (`tab:sens`); the sensitivity, and the tolerance it forces on N1, is
now recorded rather than discovered by a reader running the suite.  The spread
is `(max - min) / midpoint`, so it is a property of the model rather than of
the machine, and the paper states it as an upper bound — within 0.5 % — which
N1 checks as `spread ≤ 0.5`; measuring it from the running stack instead was
the defect that made the suite fail on a different Python version.

**Still open.** Nothing quantitative.  A referee could ask for the combined
case at a *single* thickness with both couplings designed to be comparable,
which would need a `μ` three orders of magnitude larger than the nominal one;
that is a parameter study, not a missing check.

## 10. Which modulus goes with which permittivity — **new, now answered**

**Risk.** The flexoelectric closed form quotes `x = 3μ²/(C^p h² κ)` with a
number (`1.6946×10¹¹ Pa`) that the closed-form section of the same paper does
not print, because that section is a different poling direction
(`9.5500×10¹⁰ Pa`).  A reader who takes the printed modulus and the printed
permittivity gets `x = 6.34×10⁻⁴`, 77 % from the value the paper reports.

**Where it is addressed.** `tab:axes` sets the axes, the Voigt
indices and both plane-stress tensors side by side; §4.1 states which modulus
belongs to which orientation and carries a paragraph headed *The modulus and
the permittivity must come from one configuration*; §4.5 (Step 3) now names the
poling axis and the Voigt convention before the tensor is printed; and check
I9 runs the same bending field in all four poling/electrode pairings, so that
the pairing which produced `6.34×10⁻⁴` is shown to correspond to no
configuration (the short-face pairings collect exactly zero charge).

**Still open.** Nothing.  This was a notation defect, not a modeling one: no
number in the paper changed when it was fixed.

## 12. Several coupling factors near the same value

**Risk.** A referee reading §6.2, Table 3, Appendix C.4 and the ring-down
section meets numbers near 0.56 and near 0.46 and may take them for estimates
of one quantity that disagree.

**Where it is addressed.** Table `tab:coupling` lists every coupling factor the
paper quotes, one row each, with the boundary condition, mesh, electrode pair,
`μ`, matrix and formula, and names the entry of
`results/coupling_provenance.json` that reproduces it.  The provenance file is
recomputed from the archived results on every run and graded (N4), and it
reproduces each archived value exactly, so the distinction is checked, not
asserted: behind 0.46 there are two quantities (`K_uu` vs `K_sc`, 1.5 %) plus a
`μ` difference (0.07 %), and behind 0.56 there are four measures of one tensor
set separated by the clamped edge (0.22 %) and the window (0.26 %).

**Still open.** Nothing numerical.  The new table has never been typeset, so
its width is unchecked.

---

## Status summary

* **Answered in this revision:** 4 (validity band on Fig. 9 and the explicit
  `ωτ ≤ 1` bound), 5 (`a/L ≤ 0.2` as an assumed operating range), 9 (the two configurations,
  with `tab:config`), 10 (the modulus/permittivity pairing, with Table `tab:axes`
  and I9), 12 (one row per coupling factor, `tab:coupling`, graded N4), and 1
  (`fem1` carries its published record and the unpublished `fem4`/`fem5` are
  deleted, so the only self-citation is published).
* **Partly answered:** 6 (the flattening is
  converged and now separated from the piezoelectric terms, but its physical
  attribution is still an interpretation), 7 (the 2.8 % 2-D gap is documented,
  not removed).
* **Open, and cannot be closed from this repository:** 2 (`μ`), 3 (`ρ`), 8
  (placeholders).

The full inventory of numbers that no independent route reproduces is
`results/unverified_numbers.md`, regenerated on every run and graded (N2) so
that it cannot cite a number the manuscript no longer contains.
