"""coupling_provenance.py -- one row per coupling factor quoted in the paper.

    python3 python/coupling_provenance.py -> results/coupling_provenance.json

The paper quotes several numbers near 0.56 and near 0.46.  They are different
measures of the same tensors, and a reader cannot tell which is which from the
text alone, so every one of them is recomputed here with its provenance:
boundary condition, mesh, kinematics, poling/electrode pair, matrix, formula
and code key.
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

L, H = 200e-6, 10e-6
MG_WIN = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)   # 3 x 1 um window
MG_ZERO = np.zeros((2, 2))


def build(core, Mg, nx, ny, clamped):
    mdl = f6.assemble(f6.mesh_rect(nx, ny, L, H), core, Mg,
                      clamped_edges=(("left",) if clamped else ()))
    Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=("left", "right"))
    Koc, _, _, (d, beta) = f6.reduce(mdl, "open", pair=("left", "right"))
    return Ksc, Koc, M, d, beta


def static_k2(Ksc, d, beta, clamped=True):
    """Mode-free coupling on the diagonally scaled system (cond ~1e12)."""
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    b = S * d
    Ks = Ksc * S[:, None] * S[None, :]
    if clamped:
        x = float(b @ np.linalg.solve(Ks, b)) / beta
    else:                       # singular without a constraint: min-norm solve
        x = float(b @ np.linalg.lstsq(Ks, b, rcond=1e-11)[0]) / beta
    return x / (1.0 + x), x


def modal_k2(Koc, Ksc, M, nm=8):
    wo = f6.modes(Koc, M, nm)[0]
    ws = f6.modes(Ksc, M, nm)[0]
    k2 = (wo ** 2 - ws ** 2) / wo ** 2
    j = int(np.argmax(k2))
    return float(k2[j]), j + 1, float(wo[j] / 2e3 / np.pi)


def main():
    # three material states: full (mu = 1e-6 C/m), piezoelectric with mu = 0,
    # and purely elastic (e = 0, mu = 0) for the K_uu memory matrix
    core = mt.to_core(mt.batio3("x", "plane_stress"))
    core_p0 = mt.to_core(mt.batio3("x", "plane_stress"))
    core_p0.mu = 0.0
    core_np = mt.to_core(mt.batio3("x", "plane_stress"))
    core_np.e[:] = 0.0
    core_np.mu = 0.0
    rows = []

    def add(label, value, bc, mesh, matrix, formula, key, x=None, mode=None,
            f=None):
        rows.append(dict(label=label, value=float(value), x=x, bc=bc, mesh=mesh,
                         kin="plane stress",
                         poling="x, electrodes on the short faces",
                         matrix=matrix, formula=formula, key=key, mode=mode,
                         f_kHz=f))

    # 1-2. no gradient and no flexoelectricity: the homogeneous limit
    Ksc, _, _, d, beta = build(core_p0, MG_ZERO, 48, 4, False)
    add("k2_free_nogradient_48x4", static_k2(Ksc, d, beta, clamped=False)[0],
        "none (free, minimum-norm solve)", "48x4", "K_sc, mode-free",
        "x/(1+x)", "coupling_check.json fem.plane_stress.free_48x4")
    Ksc, _, _, d, beta = build(core_p0, MG_ZERO, 48, 4, True)
    add("k2_clamped_nogradient_48x4", static_k2(Ksc, d, beta)[0],
        "left edge clamped", "48x4", "K_sc, mode-free", "x/(1+x)",
        "coupling_check.json fem.plane_stress.clamped_48x4")

    # 3-4. window on, left edge clamped -- the value the paper works with
    Ksc, _, _, d, beta = build(core_p0, MG_WIN, 48, 4, True)
    k48 = static_k2(Ksc, d, beta)[0]
    add("k2_clamped_gradient_48x4", k48, "left edge clamped", "48x4",
        "K_sc, mode-free", "x/(1+x)", "demo.json flexo_thickness[0].k2_ext")
    Ksc24, Koc24, M24, d24, b24 = build(core_p0, MG_WIN, 24, 2, True)
    add("k2_clamped_gradient_24x2", static_k2(Ksc24, d24, b24)[0],
        "left edge clamped", "24x2", "K_sc, mode-free", "x/(1+x)",
        "run_demos._static_k2 on 24x2 (k2_ext_24)")

    # 5-7. mode-based factors of the extensional mode on the 24x2 build
    Ksc_f, Koc_f, M_f, _, _ = build(core, MG_WIN, 24, 2, True)      # mu = 1e-6
    Ksc_p, Koc_p, M_p, _, _ = build(core_p0, MG_WIN, 24, 2, True)   # mu = 0
    Ksc_u, Koc_u, M_u, _, _ = build(core_np, MG_WIN, 24, 2, True)   # e = 0
    k2, j, f = modal_k2(Koc_f, Ksc_u, M_f)
    add("k2_mode_based_Kuu_24x2", k2, "left edge clamped", "24x2",
        "K_oc vs K_uu (eigenvalues)", "(w_oc^2 - w_u^2)/w_oc^2",
        "memory_variants.json k2", mode=j, f=f)
    k2, j, f = modal_k2(Koc_f, Ksc_f, M_f)
    add("k2_mode_based_Ksc_24x2", k2, "left edge clamped", "24x2",
        "K_oc vs K_sc (eigenvalues)", "(w_oc^2 - w_sc^2)/w_oc^2, mu = 1e-6",
        "quoted as 0.4583 in the ring-down section", mode=j, f=f)
    k2, j, f = modal_k2(Koc_p, Ksc_p, M_p)
    add("k2_mode_based_Ksc_24x2_mu0", k2, "left edge clamped", "24x2",
        "K_oc vs K_sc (eigenvalues)", "(w_oc^2 - w_sc^2)/w_oc^2, mu = 0",
        "application_table.json rows[3].k2", mode=j, f=f)

    # 8. constitutive closed form
    cf = json.load(open(os.path.join(ROOT, "results", "coupling_check.json")))
    add("k2_closed_form_plane_stress", cf["closed_form"]["k2_2d_closed"], "--",
        "--", "e, C, kappa", "x/(1+x), x = e^T C^-1 e / kappa",
        "coupling_check.json closed_form.k2_2d_closed",
        x=cf["closed_form"]["x_2d_closed"])

    out = {"working_value": k48, "rows": rows}
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "coupling_provenance.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print("%-32s %-9s %-6s %s" % ("label", "value", "mesh", "matrix / formula"))
    for r in rows:
        print("%-32s %-9.5f %-6s %s | %s"
              % (r["label"], r["value"], r["mesh"], r["matrix"], r["formula"]))
    print("\nworking value (48x4, clamped, window on, mu = 0): %.5f" % k48)


if __name__ == "__main__":
    main()
