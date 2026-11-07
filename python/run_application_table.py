"""
run_application_table.py -- the worked 200 x 10 um plate, all four
polarization / kinematics combinations, in one table.

For each combination the extensional (poling x) or bending (poling y) mode is
identified, its short-circuit and open-circuit frequencies are taken from the
same mesh, and the coupling is the two-solve value

    k^2 = (w_open^2 - w_short^2) / w_open^2 ,

i.e. the denominator is the *short-circuit* matrix.  (Sweeps are graded by the
mode-free measure instead -- see docs/checker report -- because identifying a
mode by its coupling is fine for one geometry and circular in a sweep.)

V0 is the open-circuit voltage of that mode when its tip displacement is
exactly 10 nm.

Run:  python3 python/run_application_table.py
      -> results/application_table.json, results/application_table.md
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

RES = os.path.join(ROOT, "results")
L, H = 200e-6, 10e-6
CASES = [("y", "plane_strain", "bending"),
         ("y", "plane_stress", "bending"),
         ("x", "plane_strain", "extensional"),
         ("x", "plane_stress", "extensional")]


def one(poling, kin, want):
    m = mt.batio3(poling, kin)
    core = mt.to_core(m)
    core.mu = 0.0                       # piezoelectric case only
    mesh = f6.mesh_rect(24, 2, L, H)
    mdl = f6.assemble(mesh, core,
                      f6.second_moment("cuboid", 3e-6, 1e-6, 0.0),
                      gradient=True)
    # through-thickness electrodes for the poling-y family, end electrodes for
    # the poling-x family
    pair = ("bottom", "top") if poling == "y" else ("left", "right")
    Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=pair)
    Koc, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    ws, _ = f6.modes(Ksc, M, 6)
    wo, Phi = f6.modes(Koc, M, 6)
    k2 = (wo ** 2 - ws ** 2) / wo ** 2
    j = int(np.argmax(k2))
    # scale the eigenvector so that the largest nodal displacement in the mode
    # is exactly 10 nm (never max(|phi|): the C1 dofs mix derivatives)
    amp = np.zeros(idx.size)
    for n in range(mesh.nnode):
        for c in (0, 4):
            r = int(np.searchsorted(idx, mdl.mech_dof[n][c]))
            if r < idx.size and idx[r] == mdl.mech_dof[n][c]:
                amp[r] = Phi[r, j]
    i3 = 0
    disp = np.zeros(mesh.nnode)
    for n in range(mesh.nnode):
        d3 = []
        for c in (0, 4):
            r = int(np.searchsorted(idx, mdl.mech_dof[n][c]))
            d3.append(Phi[r, j] if r < idx.size
                      and idx[r] == mdl.mech_dof[n][c] else 0.0)
        disp[n] = float(np.linalg.norm(d3))
    x0 = Phi[:, j] * (10e-9 / disp.max())
    return {"poling": poling, "kinematics": kin, "mode": want,
            "mode_index": j + 1,
            "f_kHz": float(wo[j] / 2e3 / np.pi),
            "f_short_kHz": float(ws[j] / 2e3 / np.pi),
            "k2": float(k2[j]),
            "f1_kHz": float(wo[0] / 2e3 / np.pi),
            "k2_mode1": float(k2[0]),
            "V0_V": float(abs(d @ x0) / beta)}


def main():
    rows = [one(*c) for c in CASES]
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "application_table.json"), "w") as fh:
        json.dump({"rows": rows,
                   "note": "24x2 mesh, window 3x1 um, mu = 0, k^2 denominator "
                           "= short-circuit matrix"}, fh, indent=1)
    hdr = ("| poling | kinematics | mode | f (kHz) | k^2 | V0 (V) |\n"
           "|---|---|---|---|---|---|\n")
    lines = [f"| {r['poling']} | {r['kinematics'].replace('_', ' ')} | "
             f"{r['mode']} | {r['f_kHz']:.1f} | {r['k2']:.4f} | "
             f"{r['V0_V']:.2f} |" for r in rows]
    with open(os.path.join(RES, "application_table.md"), "w") as fh:
        fh.write("# 200 um x 10 um BaTiO3 plate, first mode of each family\n\n")
        fh.write(hdr + "\n".join(lines) + "\n")
    for r in rows:
        print(f"  {r['poling']}, {r['kinematics']:13s} {r['mode']:11s} "
              f"{r['f_kHz']:8.1f} kHz  k2={r['k2']:.4f}  V0={r['V0_V']:7.2f} V")
    return 0


if __name__ == "__main__":
    sys.exit(main())
