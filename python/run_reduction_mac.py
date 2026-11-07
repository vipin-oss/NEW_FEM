"""
run_reduction_mac.py -- do the two 2-D reductions select the same mode?

The paper compares the extensional coupling of one mode in plane strain with
that of one mode in plane stress (Table B.1).  The two models share the mesh,
the electrode pair and the mass matrix, so the two eigenvectors live in the
same space and their overlap can be measured:

    MAC(a,b) = |phi_a^T M phi_b|^2 / ((phi_a^T M phi_a)(phi_b^T M phi_b)),

which is 1 for the same shape and 0 for orthogonal ones.  Both vectors are
M-normalised by the eigensolver, so the denominator is 1 in practice.

    python3 python/run_reduction_mac.py  ->  results/reduction_mac.json

Reported: the mode index selected in each reduction (the argmax of k^2 over
six modes, the rule of Table 6), the MAC between the two selected shapes, the
largest off-diagonal MAC between the two six-mode sets (a check that the modes
are not merely reordered), and the two frequencies.
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
NMODE = 6


def reduced(poling, kin):
    """Short- and open-circuit reductions of one model; returns the shorts."""
    m = mt.batio3(poling, kin)
    core = mt.to_core(m)
    core.mu = 0.0
    mesh = f6.mesh_rect(24, 2, L, H)
    mdl = f6.assemble(mesh, core, f6.second_moment("cuboid", 3e-6, 1e-6, 0.0),
                      gradient=True)
    pair = ("bottom", "top") if poling == "y" else ("left", "right")
    Ksc, M, _idx, _ = f6.reduce(mdl, "short", pair=pair)
    Koc, _, _, _ = f6.reduce(mdl, "open", pair=pair)
    ws, phi = f6.modes(Ksc, M, NMODE)
    wo, _ = f6.modes(Koc, M, NMODE)
    k2 = (wo ** 2 - ws ** 2) / wo ** 2
    return {"phi": phi, "M": M, "f_sc_kHz": ws / 2e3 / np.pi,
            "f_oc_kHz": wo / 2e3 / np.pi, "k2": k2}


def mac(phi_a, phi_b, M):
    a, b = phi_a, phi_b
    return float(abs(a @ M @ b) ** 2 / ((a @ M @ a) * (b @ M @ b)))


def main():
    strain = reduced("x", "plane_strain")
    stress = reduced("x", "plane_stress")

    j_s = int(np.argmax(strain["k2"]))
    j_t = int(np.argmax(stress["k2"]))
    value = mac(strain["phi"][:, j_s], stress["phi"][:, j_t], strain["M"])

    # the full 6x6 overlap, and the largest true off-diagonal entry: if the two
    # reductions merely reordered the modes, the selected shape would still
    # overlap more strongly with some other member of the other set
    table = [[mac(strain["phi"][:, i], stress["phi"][:, j], strain["M"])
              for j in range(NMODE)] for i in range(NMODE)]
    off = max(table[i][j] for i in range(NMODE) for j in range(NMODE)
              if i != j)

    out = {
        "case": "poling x, end electrodes, 24x2 mesh, mu = 0",
        "mode_index_strain": j_s + 1,
        "mode_index_stress": j_t + 1,
        "mac_mode5": value,
        "mac_offdiag_max": float(off),
        "f_sc_kHz": {"plane_strain": float(strain["f_sc_kHz"][j_s]),
                     "plane_stress": float(stress["f_sc_kHz"][j_t])},
        "f_oc_kHz": {"plane_strain": float(strain["f_oc_kHz"][j_s]),
                     "plane_stress": float(stress["f_oc_kHz"][j_t])},
        "k2": {"plane_strain": float(strain["k2"][j_s]),
               "plane_stress": float(stress["k2"][j_t])},
        "mac_table": table,
        "note": "MAC = |phi_a^T M phi_b|^2 with M-normalised eigenvectors of "
                "the short-circuit problem; 1 means the same shape",
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "reduction_mac.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"  mode {j_s + 1} (strain) vs mode {j_t + 1} (stress): "
          f"MAC = {value:.4f}, largest off-diagonal {off:.3f}")
    print(f"  f_sc {out['f_sc_kHz']['plane_strain']:.1f} vs "
          f"{out['f_sc_kHz']['plane_stress']:.1f} kHz; "
          f"k2 {out['k2']['plane_strain']:.4f} vs {out['k2']['plane_stress']:.4f}")
    print("  -> results/reduction_mac.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
