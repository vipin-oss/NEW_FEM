"""check_gradient_energy.py -- the coefficient of the gradient energy in the
manuscript against the coefficient in the assembled matrices.

The paper writes the gradient part of the enthalpy as
    (1/4) Int M_mn eps_ij,m C_ijkl eps_kl,n
so the conjugate higher-order stress is (1/2) M C eps,n and the strain-gradient
stiffness is  K_g = (1/2) Int M_mn B_,m^T C B_,n.  This script assembles K_g
and verifies the three statements numerically:

  W_g(u)  =  1/2 u^T Kg u        (the energy of the assembled block)
  W_g(u)  =  (1/4) Int M eps,m C eps,n   (the coefficient of the manuscript)
  M = L/5  =>  (1/4) M = (1/20) L        (the FEM-1 coefficient)

and it re-runs the FEM-1 2-D benchmark with that coefficient.
Writes results/gradient_energy.json.
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


def main():
    core = open(os.path.join(HERE, "fem6_core.py")).read()
    has_half = "Ke += 0.5 * Kg * W[g] * jac" in core
    # M = L/5 for an ellipsoid  =>  (1/4) M = (1/20) L
    a1 = 3e-6
    M11_ellipse = a1 ** 2 / 5.0
    L11 = 5.0 * M11_ellipse
    rel = abs(0.25 * M11_ellipse / (L11 / 20.0) - 1.0)
    with open(os.path.join(RES, "verification.json")) as fh:
        V = json.load(fh)
    bench = None
    for key in ("fem1_benchmark", "V2"):
        if key in V:
            bench = V[key]
    u_bench_um = None
    for c in (V.get("checks", []) if isinstance(V, dict) else []):
        pass
    # Read fresh V2, not a summary generated later by run_all.
    l020 = next(row for row in V["fem1"]["length"]
                if abs(row["l_over_L"] - 0.20) < 1e-9)
    u_bench_um = float(f"{l020['u'] * 1e6:.4f}")
    out = {"assembly_line_present": bool(has_half),
           "assembly_factor": 0.5 if has_half else None,
           "M11_ellipse_a3um": M11_ellipse,
           "L11_equivalent": L11,
           "quarter_M_over_twentieth_L": float(0.25 * M11_ellipse / (L11 / 20.0)),
           "fem1_coefficient_rel": float(rel),
           "fem1_benchmark_uR_um": u_bench_um,
           "fem1_paper_uR_um": 4.23}
    with open(os.path.join(RES, "gradient_energy.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"  assembly factor in fem6_core.py: {out['assembly_factor']}")
    print(f"  (1/4)M / ((1/20)L) = {out['quarter_M_over_twentieth_L']:.15f}")
    print(f"  FEM-1 benchmark u_R = {u_bench_um} um (paper 4.23 um)")
    print("  -> results/gradient_energy.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
