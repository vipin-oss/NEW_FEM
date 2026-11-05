"""
run_flexo_check.py -- verification of the flexoelectric coupling.

F1  mu = 0 and e = 0            -> V = 0 exactly
F2  pure-bending patch test     -> V = mu * kappa * h / kappa33 (exact,
                                   independent of the mesh)
F3  linearity in mu             -> V(2 mu) = 2 V(mu), exactly
F4  cantilever, piezo + flexo   -> bending mode acquires k_eff^2 > 0 and a
                                   finite open-circuit voltage
F5  k_eff^2 vs mu               -> quadratic scaling of the coupling

The cantilever voltage is NOT mu*h*theta_tip/(kappa33*L): in a cantilever the
curvature varies along x and eps_yy = -nu' eps_xx, so that closed form only
holds for uniform curvature.  F2 is the exact statement.

Run: python3 python/run_flexo_check.py   -> results/flexo_check.md / .json
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
F_TIP = 1e-3


def model(mu, kin="plane_stress", mesh=(24, 2), kill_e=False, poling="y"):
    m0 = mt.batio3(poling, kin)
    m = mt.Material(**{**m0.__dict__, "mu": mu})
    core = mt.to_core(m)
    if kill_e:
        core.e[:] = 0.0
    mdl = f6.assemble(f6.mesh_rect(mesh[0], mesh[1], L, H), core,
                      f6.second_moment("cuboid", 3e-6, 1e-6, 0.0), gradient=True)
    pair = ("bottom", "top") if poling == "y" else ("left", "right")
    Koc, M, idx, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    Ksc, _, _, _ = f6.reduce(mdl, "short", pair=pair)
    return mdl, core, Koc, Ksc, M, idx, d, beta


def patch_test(mu, kappa=1.0, mesh=(24, 2), kin="plane_stress"):
    """Impose u = kappa*x*y, v = -kappa*x^2/2 (uniform curvature) and read V."""
    mdl, core, Koc, _Ksc, M, idx, d, beta = model(mu, kin, mesh, kill_e=True)
    U = np.zeros(mdl.ndof_mech)
    for n, (x, y) in enumerate(mdl.mesh.nodes):
        vals = [kappa * x * y, kappa * y, kappa * x, kappa,
                -0.5 * kappa * x * x, -kappa * x, 0.0, 0.0]
        for j, v in enumerate(vals):
            U[mdl.mech_dof[n][j]] = v
    V = float(d @ U[idx]) / beta
    ana = mu * kappa * H / core.kappa[1, 1]
    return V, ana


def cantilever(mu):
    mdl, core, Koc, Ksc, M, idx, d, beta = model(mu)
    f = mdl.force_tip(Fy=-F_TIP)
    U = np.zeros(mdl.ndof_mech)
    U[idx] = np.linalg.solve(Koc, f[idx])
    V = float(d @ U[idx]) / beta
    wo, _ = f6.modes(Koc, M, 4)
    ws, _ = f6.modes(Ksc, M, 4)
    k2 = (wo ** 2 - ws ** 2) / wo ** 2
    return {"V": V, "k2_1": float(k2[0]), "f1_kHz": float(wo[0] / 2e3 / np.pi),
            "beta": beta}


def main():
    mu = 1e-6
    out = {"mu_nominal": mu, "kinematics": "plane_stress"}

    V0 = patch_test(0.0)[0]
    V1, A1 = patch_test(mu)
    V2, A2 = patch_test(2 * mu)
    V1b, _ = patch_test(mu, mesh=(8, 2))
    V1c, _ = patch_test(mu, mesh=(4, 1))
    out["F1_patch_mu0"] = V0
    out["F2_patch"] = {"V": V1, "analytic": A1, "ratio": V1 / A1,
                       "mesh_8x2": V1b, "mesh_4x1": V1c}
    out["F3_linearity"] = V2 / V1

    c0 = cantilever(0.0)
    c1 = cantilever(mu)
    out["F4_cantilever"] = {"mu0": c0, "mu1": c1}

    sweep = []
    for m_ in [0.0, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5]:
        c = cantilever(m_)
        sweep.append({"mu": m_, "k2_1": c["k2_1"], "V": c["V"],
                      "f1_kHz": c["f1_kHz"]})
    out["F5_sweep"] = sweep
    out["pass"] = bool(abs(V0) < 1e-18
                       and abs(V1 / A1 - 1) < 1e-10
                       and abs(V1b / V1 - 1) < 1e-10
                       and abs(V1c / V1 - 1) < 1e-10
                       and abs(V2 / V1 - 2) < 1e-10
                       and c1["k2_1"] > 1e-5)

    print(f"F1  patch, mu=0            V = {V0:+.3e} V        (must be 0)")
    print(f"F2  patch, mu=1e-6         V = {V1:+.6e} V, analytic {A1:+.6e} V, "
          f"ratio {V1/A1:.10f}")
    print(f"    mesh 8x2 / 24x2 / 4x1  {V1b:+.6e} / {V1:+.6e} / {V1c:+.6e}")
    print(f"F3  V(2mu)/V(mu)           = {V2/V1:.10f}       (must be 2)")
    print(f"F4  cantilever k2(mode1)   mu=0: {c0['k2_1']:+.3e} -> "
          f"mu=1e-6: {c1['k2_1']:+.3e}")
    print(f"    cantilever V           mu=0: {c0['V']:+.3e} V -> "
          f"mu=1e-6: {c1['V']:+.3e} V")
    for s in sweep:
        print(f"F5  mu={s['mu']:.0e}: k2_1 = {s['k2_1']:+.3e}, V = {s['V']:+.3e} V")
    print(f"    overall: {'PASS' if out['pass'] else 'FAIL'}")

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "flexo_check.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    md = ["# Flexoelectric verification", "",
          f"mu = {mu:.1e} C/m (parametric, FEM-5 sensitivity value, not source "
          "controlled); plane stress; 200x10 um bridge.", "",
          "| check | result | expected |", "|---|---|---|",
          f"| F1 patch test, mu = 0 | {V0:+.3e} V | 0 |",
          f"| F2 patch test, mu = 1e-6 | {V1:+.6e} V vs analytic "
          f"{A1:+.6e} V | ratio 1, got {V1/A1:.10f} |",
          f"| F2 mesh independence | 4x1: {V1c:+.6e}, 8x2: {V1b:+.6e}, "
          f"24x2: {V1:+.6e} V | identical |",
          f"| F3 linearity | V(2mu)/V(mu) = {V2/V1:.10f} | 2 |",
          f"| F4 bending k_eff^2, no flexo | {c0['k2_1']:+.3e} | ~0 |",
          f"| F4 bending k_eff^2, mu = 1e-6 | {c1['k2_1']:+.3e} | > 1e-5 |",
          "", "Analytic identity used in F2 (uniform curvature kappa):",
          "`V = mu * kappa * h / kappa33`", "",
          "| mu (C/m) | k_eff^2 (mode 1) | V at 1 mN tip load (V) | f1 (kHz) |",
          "|---|---|---|---|"]
    for s in sweep:
        md.append(f"| {s['mu']:.0e} | {s['k2_1']:+.3e} | {s['V']:+.3e} | "
                  f"{s['f1_kHz']:.3f} |")
    md += ["", f"Overall: **{'PASS' if out['pass'] else 'FAIL'}**"]
    with open(os.path.join(ROOT, "results", "flexo_check.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
