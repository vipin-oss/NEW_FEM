# FEM-6 material record — BaTiO₃, sources, plane-strain/plane-stress decision

Every constant below is used by `python/materials.py` (single source of truth;
nothing material-dependent is hard-coded elsewhere) and appears with its
source and unit. Nothing here was copied from a draft: the values were read
from the FEM-5 record and then **re-checked by running the solver**
(`python/run_material_check.py` → `results/material_comparison.{md,json}`).

## 1. The set

Source: the constants used in **FEM-5**, which in turn cites
**Zgonik, Bernasconi, Duelli, Schlesser, Günter, Bosshard, Günter,
*Phys. Rev. B* **50** (1994) 5941** for the elastic, piezoelectric and clamped
dielectric tensors of tetragonal BaTiO₃ at room temperature. (FEM-5 record:
`paper2/materials.py`, header comment "provenance Zgonik et al. 1994"; README
§3 item 4: "C11..C44, e15/e31/e33, kappa11/kappa33 unchanged (Zgonik 1994)".)

| symbol | value | unit | source |
|---|---|---|---|
| `C11` | 2.22×10¹¹ | Pa | Zgonik 1994 (via FEM-5 record Table 1 / App. A) |
| `C12` | 1.08×10¹¹ | Pa | Zgonik 1994 |
| `C13` | 1.11×10¹¹ | Pa | Zgonik 1994 |
| `C33` | 1.51×10¹¹ | Pa | Zgonik 1994 |
| `C44` | 6.10×10¹⁰ | Pa | Zgonik 1994 |
| `e31` | −0.7 | C/m² | Zgonik 1994 (FEM-5 record §7.5 Eq. 7.16) |
| `e33` | +6.7 | C/m² | Zgonik 1994 |
| `e15` | +34.2 | C/m² | Zgonik 1994 |
| `κ_r11` | 2200 | – | Zgonik 1994, clamped-order relative permittivity |
| `κ_r33` | 56 | – | Zgonik 1994 |
| `ε0` | 8.854187817×10⁻¹² | F/m | CODATA, as in the FEM-5 record |
| `ρ` | 6020 | kg/m³ | **U1 — UNVERIFIED**: not in the FEM-5 record (FEM-5 is quasi-static), value is the standard single-crystal BaTiO₃ density; a primary source must be added before the frequency results are quoted. |

Derived: `κ11 = 2200 ε0 = 1.947921×10⁻⁸ F/m`,
`κ33 = 56 ε0 = 4.958345×10⁻¹⁰ F/m`, **`κ11/κ33 = 39.3`** — the
dielectric anisotropy of the real crystal (the placeholder set had 1.2, a
factor 33 too low).

## 2. Plane strain or plane stress for the 200 × 10 µm bridge?

**Recommendation: plane stress**, with plane strain kept as a cross-check.

Reason: for a 2-D idealisation the correct limit is set by the **free-surface
distance**, not by the thickness. The specimen is 200 µm long, 10 µm wide and
10 µm thick, so the out-of-plane distance to a free surface (5 µm) is *smaller*
than any in-plane feature of the response (the shortest bending wavelength we
resolve is ~2L/24 ≈ 17 µm) and comparable to the width. The out-of-plane
stress is therefore essentially unconstrained (σ_zz ≈ 0), which is plane
stress. Plane strain (ε_zz = 0) would be right for a long bar whose out-of-plane
direction is constrained by a much wider body — not for a free-standing
microbridge.

The reduction used (`materials.Material.C()`): with the out-of-plane direction
z being a basal axis, `C_ps = C_2d − c₃c₃ᵀ/C_zz`. The piezoelectric and
dielectric tensors are **not** modified: for 4 mm BaTiO₃ poled in-plane, `D_z`
involves only the out-of-plane shear strains, which vanish in the 2-D
kinematics, so `e_ps = e_2d` exactly.

Measured (24×2 mesh, cuboid window a = 3/1 µm, 8 modes):

| poling | kinematics | f₁ (kHz) | f_ext (kHz) | k²_ext | V at 10 nm end shortening |
|---|---|---|---|---|---|
| y (through width) | plane strain | 220.460 | 6721.815 | +0.175 | 3.53 V |
| y | **plane stress** | 208.732 | 6360.999 | +0.114 | 2.42 V |
| x (along length) | plane strain | 165.571 | 7160.990 | +0.402 | **141.55 V** |
| x | **plane stress** | 147.727 | 6725.793 | +0.458 | 139.06 V |

Ratios (plane stress / plane strain): f₁ ×0.947 and ×0.892; f_ext ×0.946 and
×0.939. So the choice moves frequencies by 5–11 % — **not** negligible, and it
must be stated, not left implicit. The earlier FEM-4/FEM-5 papers used plane
strain; FEM-6 should either state the plane-stress assumption explicitly or
show both.

## 3. Two consequences worth writing into the paper

**M1 — `k31` is small with this set; transverse transduction is negligible.**
The IEEE DC identity gives
`k31 = |e31|/√(C11 κ33) = 0.7/√(2.22×10¹¹ × 4.958×10⁻¹⁰) = 0.0667`, i.e.
`k31² = 0.0045`. All the usable coupling in this material comes from `e33`
along the poling axis: the length-extensional mode reaches `k² = 0.40`
(poling x) because it is driven by `e33`, not `e31`. This is exactly why a
*bending* transducer in this set produces no usable voltage (checker report
A3: `k² = 2×10⁻¹⁰` with a placeholder set, and `V₁ = 3.5 V` only through the
small `e31` path when the electrodes are through the width). **Do not**
switch `e31` to the commonly quoted −4.4 C/m² without logging it: that
multiplies `k31²` by 39 and would change every voltage number in the paper.
Flag as decision **M1**, old/new/reason.

**M2 — independent check of the voltage scale.** For a uniform axial strain
`ε = u_tip/L = 10 nm / 200 µm = 5×10⁻⁵`, the closed-circuit estimate is
`V = (e33/κ33) ε L = 1.35×10⁵ V/m × 2×10⁻⁴ m = 135.1 V`. The solver returns
**141.55 V** for the same end shortening with the mode shape of the axial
mode — 4.6 % above the uniform-strain estimate, as expected (the mode shape is
not uniform). This validates both the coupling assembly and the electrode
condensation from an independent direction.

## 4. Reproduce

```bash
python3 python/materials.py             # prints C, e, kappa + thermodynamic checks
python3 python/run_material_check.py    # 2 s, writes results/material_comparison.*
```

The thermodynamic checks in `materials.check_thermodynamics()` are symmetry and
definiteness only (`C = Cᵀ`, `κ = κᵀ`, positive eigenvalues). They **do not**
validate the tensor values themselves — that is the job of the source citation
and of §3/M2.
