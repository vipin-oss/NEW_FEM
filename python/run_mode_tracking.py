"""
run_mode_tracking.py -- are the four points of the thickness sweep the same
physical mode?

A coupling factor is only meaningful for a named mode.  Thin plates push
several bending modes below the one that couples, so the *index* of a mode can
change with thickness even when the mode itself does not.  The assurance
criterion

    MAC_ij = (phi_i^T M phi_j)^2 / ((phi_i^T M phi_i)(phi_j^T M phi_j))

is 1 for the same shape and 0 for mass-orthogonal shapes, and it is computed
here between the fundamental (short-circuit) mode at each thickness and the
same mode at the reference thickness h = 10 um.  The off-diagonal entries
against the reference modes 2..4 are reported too: if the tracked shape had
drifted into a neighboring mode, they would rise.

The mesh is the same 48x4 topology at every thickness, so the dof vectors are
compared after pulling physical y and xy derivatives back to the reference thickness.

Also reported: the frequency ratios f_j/f_1 at each thickness, which must stay
clear of 1 if no crossing occurs anywhere in the sweep.

Writes results/mode_tracking.json and .md.
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

RESULTS = os.path.join(ROOT, "results")
L = 200e-6
HS = [10e-6, 5e-6, 2e-6, 1e-6]
NX, NY, NM = 48, 4, 4


def mac(a, b, M):
    num = float(a @ M @ b) ** 2
    den = float(a @ M @ a) * float(b @ M @ b)
    return num / den if den > 0 else 0.0


def main():
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    mat = mt.batio3("y", "plane_stress")        # bending, through-thickness
    shapes = {}
    for h in HS:
        mesh = f6.mesh_rect(NX, NY, L, h)
        mdl = f6.assemble(mesh, mt.to_core(mat), Mg)
        Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=("bottom", "top"))
        ws, Phi = f6.modes(Ksc, M, NM)
        shapes[h] = (Phi, M, ws)

    href = HS[0]
    Pref, Mref, wref = shapes[href]
    rows = []
    for h in HS:
        Phi, M, ws = shapes[h]
        mapped = Phi[:, 0].copy()
        mapped[np.isin(idx % 8, [2, 3, 6, 7])] *= h / href
        macs = [mac(mapped, Pref[:, j], Mref) for j in range(NM)]
        rows.append({
            "h_um": h * 1e6,
            "f_kHz": [float(x / 2e3 / np.pi) for x in ws],
            "f_ratio_2_over_1": float(ws[1] / ws[0]),
            "f_ratio_3_over_1": float(ws[2] / ws[0]),
            "mac_mode1_vs_ref": macs[0],
            "mac_offdiag": macs[1:],
        })
        print(f"  h={h*1e6:4.1f} um  f1={ws[0]/2e3/np.pi:8.2f} kHz  "
              f"f2/f1={ws[1]/ws[0]:5.2f}  MAC={macs[0]:.6f}  "
              f"off={np.round(macs[1:], 6)}")

    mins = min(r["mac_mode1_vs_ref"] for r in rows)
    maxoff = max(max(r["mac_offdiag"]) for r in rows)
    minratio = min(r["f_ratio_2_over_1"] for r in rows)
    out = {"rows": rows, "mac_min": mins, "mac_offdiag_max": maxoff,
           "min_f2_over_f1": minratio, "reference_h_um": href * 1e6,
           "mapping": "y=(h/href)*yref; dy,dxy DOFs multiplied by h/href"}
    with open(os.path.join(RESULTS, "mode_tracking.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    md = ["# Mode tracking across the thickness sweep", "",
          "Same 48x4 mesh topology at every thickness; bending configuration "
          "(poling y, through-thickness electrodes).", "",
          "| h (um) | f1 (kHz) | f2/f1 | MAC vs h=10 mode 1 | off-diagonal max |",
          "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['h_um']:.0f} | {r['f_kHz'][0]:.2f} | "
                  f"{r['f_ratio_2_over_1']:.2f} | "
                  f"{r['mac_mode1_vs_ref']:.6f} | {max(r['mac_offdiag']):.2e} |")
    md += ["", f"Minimum MAC: {mins:.6f}; largest off-diagonal MAC: "
              f"{maxoff:.2e}; smallest f2/f1: {minratio:.2f}.",
           "", "MAC uses a pullback to the reference thickness. These sampled shapes "
           "and spectral gaps support branch identification at the tested points; "
           "they do not prove absence of crossings between samples."]
    with open(os.path.join(RESULTS, "mode_tracking.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"  min MAC = {mins:.6f}, max off-diagonal = {maxoff:.2e}, "
          f"min f2/f1 = {minratio:.2f}")
    print("  -> results/mode_tracking.{md,json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
