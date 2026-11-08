"""
run_material_check.py -- plane strain vs plane stress for the FEM-5 / Zgonik
BaTiO3 set on the FEM-6 microbridge, and the dielectric-anisotropy check.

Writes results/material_comparison.md and .json.
Run:  python3 python/run_material_check.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fem6_core as f6          # noqa: E402
import materials as mt          # noqa: E402

L, H, TH = 200e-6, 10e-6, 10e-6
NX, NY = 24, 2
NM = 8


def solve(poling, kin, Mg):
    m = mt.batio3(poling, kin)
    core = mt.to_core(m)
    mesh = f6.mesh_rect(NX, NY, L, H)
    model = f6.assemble(mesh, core, Mg, gradient=Mg.any())
    Koc, M, idx, (d, beta) = f6.reduce(model, "open", pair=("left", "right")
                                       if poling == "x" else ("bottom", "top"))
    Ksc, _, _, _ = f6.reduce(model, "short", pair=("left", "right")
                             if poling == "x" else ("bottom", "top"))
    wo, Phi = f6.modes(Koc, M, NM)
    ws, _ = f6.modes(Ksc, M, NM)
    k2 = (wo ** 2 - ws ** 2) / wo ** 2
    j = int(np.argmax(k2))
    # "10 nm of end shortening": scale on the axial displacement dof of the
    # node at x = L.  (The C1 eigenvector mixes u, u_x, u_y, u_xy, so a max
    # over all dofs would be scaled by a derivative dof, not by a displacement.)
    tip = int(np.argmax(mesh.nodes[:, 0]))
    row = int(np.searchsorted(idx, model.mech_dof[tip][0]))
    x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))
    V0 = float(abs(d @ x0) / beta)
    return {"poling": poling, "kinematics": kin,
            "f_open_kHz": [float(x / 2e3 / np.pi) for x in wo],
            "f_short_kHz": [float(x / 2e3 / np.pi) for x in ws],
            "k2": [float(x) for x in k2], "j_max": j,
            "f_ext_kHz": float(wo[j] / 2e3 / np.pi), "k2_ext": float(k2[j]),
            "beta": float(beta), "V0_at_10nm": V0}


def main():
    out = {"geometric": {"L_um": L * 1e6, "H_um": H * 1e6, "th_um": TH * 1e6,
                         "mesh": [NX, NY], "modes": NM},
           "case": [], "material": mt.BATIO3.as_dict()}
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    for poling in ("y", "x"):
        for kin in ("plane_strain", "plane_stress"):
            r = solve(poling, kin, Mg)
            out["case"].append(r)
            print(f"poling {poling} {kin:12s}: f1 {r['f_open_kHz'][0]:9.3f} kHz  "
                  f"f_ext {r['f_ext_kHz']:9.3f} kHz  k2_ext {r['k2_ext']:+.4f}  "
                  f"V0 {r['V0_at_10nm']:.3e} V  beta {r['beta']:.3e} F")

    # ratio plane_stress / plane_strain
    for poling in ("y", "x"):
        a = next(c for c in out["case"] if c["poling"] == poling
                 and c["kinematics"] == "plane_strain")
        b = next(c for c in out["case"] if c["poling"] == poling
                 and c["kinematics"] == "plane_stress")
        out[f"ratio_{poling}"] = {
            "f1": b["f_open_kHz"][0] / a["f_open_kHz"][0],
            "f_ext": b["f_ext_kHz"] / a["f_ext_kHz"],
            "k2_ext": b["k2_ext"] / a["k2_ext"] if a["k2_ext"] else None,
            "V0": b["V0_at_10nm"] / a["V0_at_10nm"] if a["V0_at_10nm"] else None}
        print(f"  plane_stress/plane_strain, poling {poling}: "
              f"f1 {out[f'ratio_{poling}']['f1']:.4f}, "
              f"f_ext {out[f'ratio_{poling}']['f_ext']:.4f}")

    # dielectric anisotropy of the record
    k = np.diag(mt.batio3("y").kappa())
    out["kappa_ratio_11_over_33"] = float(k[0] / k[1])
    out["k31_ieee"] = float(np.sqrt(mt.batio3("y").e31 ** 2 /
                                    (mt.batio3("y").C()[0, 0] * k[1])))
    print(f"  kappa11/kappa33 = {out['kappa_ratio_11_over_33']:.1f}, "
          f"k31 (IEEE, DC) = {out['k31_ieee']:.4f}")

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "material_comparison.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    md = ["# Material check: plane strain vs plane stress (FEM-5 / Zgonik set)",
          "", f"Microbridge {L*1e6:.0f} x {H*1e6:.0f} um, cuboid window "
          f"a = (3.0, 1.0) um, mesh {NX}x{NY}, {NM} modes.", "",
          "| poling | kinematics | f1 (kHz) | f_ext (kHz) | k2_ext | V0 @10 nm (V) |",
          "|---|---|---|---|---|---|"]
    for c in out["case"]:
        md.append(f"| {c['poling']} | {c['kinematics']} | {c['f_open_kHz'][0]:.3f} "
                  f"| {c['f_ext_kHz']:.3f} | {c['k2_ext']:+.4f} "
                  f"| {c['V0_at_10nm']:.4e} |")
    md += ["", "Ratios (plane stress / plane strain):"]
    for poling in ("y", "x"):
        r = out[f"ratio_{poling}"]
        md.append(f"- poling {poling}: f1 x{r['f1']:.4f}, f_ext x{r['f_ext']:.4f}")
    md += ["", f"kappa11/kappa33 = {out['kappa_ratio_11_over_33']:.1f} "
           f"(used: 2200/56, Zgonik 1994)", "",
           f"k31 from the IEEE DC identity = {out['k31_ieee']:.4f} "
           f"(k31^2 = {out['k31_ieee']**2:.4f})"]
    with open(os.path.join(ROOT, "results", "material_comparison.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    print("-> results/material_comparison.{md,json}")


if __name__ == "__main__":
    main()
