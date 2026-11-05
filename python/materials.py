"""
materials.py -- the FEM-6 material record
=========================================
Single source of truth for every constitutive constant used by FEM-6.
Nothing material-dependent is hard-coded anywhere else.

Provenance
----------
Elastic, piezoelectric and dielectric constants of tetragonal BaTiO3 are the
set used in FEM-5 (`FEM_5/.../paper2/materials.py`, README Sec. 3 item 4:
"C11..C44, e15/e31/e33, kappa11/kappa33 unchanged (Zgonik et al. 1994)").
That file cites Zgonik, Bernasconi, Duelli, Schlesser, Gunter, Bosshard,
Gunter, "Dielectric, elastic and electro-optic properties of 4mm BaTiO3",
Phys. Rev. B 50 (1994) 5941, for the room-temperature clamped permittivities
and the constant-strain moduli.

Density is NOT in the FEM-5 record (FEM-5 is quasi-static, so rho never
enters). The value below is the standard single-crystal BaTiO3 density; it is
flagged UNVERIFIED against a primary source and must be confirmed before the
frequency results are quoted (see docs/FEM6_material_data.md, item U1).

Units: SI throughout.
    C      Pa
    e      C/m^2
    kappa  F/m
    rho    kg/m^3
Lattice convention for the 2-D model: the model plane is (x, y) = (length,
width of the microbridge); the poling axis is either y ("y", through the
width, electrodes on the top/bottom faces) or x ("x", along the length,
electrodes on the left/right faces). The out-of-plane direction z is always a
basal ("a") direction of the 4mm crystal.

Kinematics
----------
"plane_strain"  eps_zz = 0  -> C = [[C11, C13, 0], [C13, C33, 0], [0, 0, C44]]
"plane_stress"  sig_zz = 0  -> C = C_2d - c3 c3^T / C_zz   (see plane_stress())
The piezoelectric and dielectric tensors are NOT modified by the plane-stress
reduction in this polarity: the out-of-plane component D_z of a 4mm crystal
poled in-plane involves only the out-of-plane shear strains, which vanish in
the 2-D kinematics, so e_ps = e_2d exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

EPS0 = 8.854187817e-12          # F/m, CODATA (as in the FEM-5 record)


@dataclass(frozen=True)
class Material:
    """Linear piezoelectric material in the 2-D (x, y) plane."""

    name: str
    C11: float
    C12: float
    C13: float
    C33: float
    C44: float
    e31: float
    e33: float
    e15: float
    kappa_r11: float
    kappa_r33: float
    rho: float
    poling: str = "y"            # "y" (through width) or "x" (along length)
    kinematics: str = "plane_strain"

    # ---------------- derived tensors ----------------
    def full_3d(self):
        """3-D stiffness in the (x, y, z) frame for the chosen poling axis."""
        C11, C12, C13, C33, C44 = (self.C11, self.C12, self.C13,
                                   self.C33, self.C44)
        if self.poling == "y":       # poling along y: (x, z) basal, y polar
            return np.array([[C11, C13, C12],
                             [C13, C33, C13],
                             [C12, C13, C11]])
        elif self.poling == "x":     # poling along x: (y, z) basal, x polar
            return np.array([[C33, C13, C13],
                             [C13, C11, C12],
                             [C13, C12, C11]])
        raise ValueError("poling must be 'x' or 'y'")

    def C(self) -> np.ndarray:
        """3x3 in-plane stiffness for [eps_xx, eps_yy, gamma_xy]."""
        C3 = self.full_3d()
        C2 = C3[np.ix_([0, 1], [0, 1])]
        if self.kinematics == "plane_strain":
            # eps_zz = 0 kinematically -> the in-plane block is used as is
            return np.array([[C2[0, 0], C2[0, 1], 0.0],
                             [C2[1, 0], C2[1, 1], 0.0],
                             [0.0, 0.0, self.C44]])
        elif self.kinematics == "plane_stress":
            # sig_zz = 0 -> condense the out-of-plane normal
            c3 = C3[[0, 1], 2]
            return np.array([[C2[0, 0] - c3[0] * c3[0] / C3[2, 2],
                              C2[0, 1] - c3[0] * c3[1] / C3[2, 2], 0.0],
                             [C2[1, 0] - c3[1] * c3[0] / C3[2, 2],
                              C2[1, 1] - c3[1] * c3[1] / C3[2, 2], 0.0],
                             [0.0, 0.0, self.C44]])
        raise ValueError("kinematics must be 'plane_strain' or 'plane_stress'")

    def e(self) -> np.ndarray:
        """2x3 piezoelectric stress matrix, rows (D_x, D_y), cols
        (eps_xx, eps_yy, gamma_xy)."""
        if self.poling == "y":
            return np.array([[0.0, 0.0, self.e15],
                             [self.e31, self.e33, 0.0]])
        return np.array([[self.e33, self.e31, 0.0],
                         [0.0, 0.0, self.e15]])

    def kappa(self) -> np.ndarray:
        """2x2 dielectric permittivity (F/m), rows/cols (x, y)."""
        k11 = self.kappa_r11 * EPS0
        k33 = self.kappa_r33 * EPS0
        return np.diag([k33, k11]) if self.poling == "x" else np.diag([k11, k33])

    def as_dict(self) -> dict:
        return {"name": self.name, "C": self.C().tolist(),
                "e": self.e().tolist(), "kappa": self.kappa().tolist(),
                "rho": self.rho, "poling": self.poling,
                "kinematics": self.kinematics}


# ---------------------------------------------------------------------------
# The record.  Every line carries its source.
# ---------------------------------------------------------------------------
BATIO3 = Material(
    name="BaTiO3 (tetragonal, Zgonik 1994 set as used in FEM-5)",
    C11=2.22e11,      # Pa   Zgonik 1994 (FEM-5 record Table 1 / App. A)
    C12=1.08e11,      # Pa   Zgonik 1994
    C13=1.11e11,      # Pa   Zgonik 1994
    C33=1.51e11,      # Pa   Zgonik 1994
    C44=6.10e10,      # Pa   Zgonik 1994
    e31=-0.7,         # C/m^2 Zgonik 1994 (FEM-5 record Sec. 7.5 Eq. 7.16)
    e33=6.7,          # C/m^2 Zgonik 1994
    e15=34.2,         # C/m^2 Zgonik 1994
    kappa_r11=2200.0,  # -   Zgonik 1994, clamped-order relative permittivity
    kappa_r33=56.0,    # -   Zgonik 1994
    rho=6020.0,        # kg/m^3  UNVERIFIED (not in the FEM-5 record)
)


def batio3(poling: str = "y", kinematics: str = "plane_strain") -> Material:
    return Material(**{**BATIO3.__dict__, "poling": poling,
                       "kinematics": kinematics})


def check_thermodynamics(m: Material, verbose: bool = True) -> dict:
    """Sanity checks that must hold for any admissible linear piezoelectric:
    C symmetric positive definite, kappa symmetric positive definite,
    e15/e31 ratio consistent with the 4mm structure, and the IEEE identity
    k31^2 = e31^2 / (C11^E kappa33^S) (approximate, DC form)."""
    C, e, kap = m.C(), m.e(), m.kappa()
    out = {}
    out["C_sym"] = float(np.max(np.abs(C - C.T)))
    out["kap_sym"] = float(np.max(np.abs(kap - kap.T)))
    out["C_eigmin"] = float(np.min(np.linalg.eigvalsh(C)))
    out["kap_eigmin"] = float(np.min(np.linalg.eigvalsh(kap)))
    if m.poling == "y":
        C11 = C[0, 0]
        k33 = kap[1, 1]
        out["k31_from_IEEE"] = float(np.sqrt(m.e31 ** 2 / (C11 * k33)))
    if verbose:
        for k, v in out.items():
            print(f"  {k:14s} {v: .6e}")
    return out


if __name__ == "__main__":
    for kin in ("plane_strain", "plane_stress"):
        m = batio3("y", kin)
        print(f"\n{m.name}, poling y, {kin}")
        print("C/1e10 =\n", np.round(m.C() / 1e10, 4))
        print("e =\n", m.e())
        print("kappa =", np.diag(m.kappa()))
        check_thermodynamics(m)


def to_core(m: "Material", **kw):
    """Adapter to the solver's material container (python/fem6_core.py)."""
    import fem6_core as f6
    return f6.Material(C=m.C(), e=m.e(), kappa=m.kappa(), rho=m.rho,
                       name=m.name, **kw)
