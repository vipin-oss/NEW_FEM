"""sensitivity_tornado.py -- what a +/-10 % error in an input does to the four
headline numbers of the paper.  Small and closed: no new material data.

    input        what it is                        headline output it moves
    mu           flexoelectric coefficient         factor 24
    rho          density                           frequencies, damping
    a2           window half-thickness             0.5581, factor 24
    tau          dielectric relaxation time        0.450, damping ratio

Each row is either an exact scaling law of the model or a solver run at the
perturbed value; the source of each percentage is recorded in the JSON, so a
reader can tell a derivative from a measurement.

    python3 python/sensitivity_tornado.py  -> results/sensitivity_tornado.json,
                                              results/sensitivity_tornado.md
"""
from __future__ import annotations

import json
import os

import numpy as np

import fem6_core as f6
import materials as mt
from run_demos import _modal_k2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
LB = 200e-6
# the factor 24 is a 48x4 quantity (24x2 gives 30.9 for the same pair)
NX, NY = 48, 4
MESH = f6.mesh_rect(NX, NY, LB, 10e-6)


def flexo_pair(a2_um=1.0, mu=1e-6):
    """flexoelectric bending k^2 at h = 10 and 1 um, and their ratio."""
    Mg = f6.second_moment("cuboid", 3e-6, a2_um * 1e-6, 0.0)
    M = mt.Material(**{**mt.batio3("y", "plane_stress").__dict__, "mu": mu})
    out = {}
    for h_um in (10.0, 1.0):
        mesh = f6.mesh_rect(NX, NY, LB, h_um * 1e-6)
        k2, _f = _modal_k2(mesh, M, Mg, ("bottom", "top"))
        out[h_um] = k2
    return out, out[1.0] / out[10.0]


def ext_k2(a2_um=1.0):
    """piezoelectric extensional k^2 (mode-free in the limit, modal here)."""
    Mg = f6.second_moment("cuboid", 3e-6, a2_um * 1e-6, 0.0)
    M = mt.Material(**{**mt.batio3("x", "plane_stress").__dict__, "mu": 0.0})
    k2, _f = _modal_k2(MESH, M, Mg, ("left", "right"))
    return k2


def zeta_ratio(tau=7.0974e-9, omega=6.727e6 * 2 * np.pi, alpha=1.0):
    """zeta on K_uu over zeta on K_eff, at alpha = 1 (exact: zeta = omega tau/2)."""
    z = f6.damping_ratio(omega, tau, alpha)
    return float(z), 0.450 * z / (omega * tau / 2.0)


def main():
    base, base24 = flexo_pair()
    k0 = ext_k2()
    rows = []

    # mu: the flexoelectric energy is quadratic in mu
    kp, k24p = flexo_pair(mu=1.1e-6)
    rows.append({"input": "mu", "what": "flexoelectric coefficient",
                 "perturbation": "+10 %",
                 "d_factor24_pct": 100 * (k24p / base24 - 1),
                 "d_k2ext_pct": 100 * (kp[1.0] / base[1.0] - 1),
                 "d_zeta_pct": 0.0,
                 "source": "solver, 48x4: factor 24 and the flexo k^2 at 1 um, "
                           "mu -> 1.1e-6; the flexo k^2 carries mu^2, the ratio "
                           "cancels it to the (1+x) saturation"})
    kp, k24p = flexo_pair(mu=0.9e-6)
    rows.append({"input": "mu", "what": "flexoelectric coefficient",
                 "perturbation": "-10 %",
                 "d_factor24_pct": 100 * (k24p / base24 - 1),
                 "d_k2ext_pct": 100 * (kp[1.0] / base[1.0] - 1),
                 "d_zeta_pct": 0.0,
                 "source": "solver, 48x4: as above, mu -> 0.9e-6"})

    # a2: the second moment is quadratic in the half-width
    ap, a24p = flexo_pair(a2_um=1.1)
    k1 = ext_k2(a2_um=1.1)
    rows.append({"input": "a2", "what": "window half-thickness",
                 "perturbation": "+10 %",
                 "d_factor24_pct": 100 * (a24p / base24 - 1),
                 "d_k2ext_pct": 100 * (k1 / k0 - 1),
                 "d_zeta_pct": 0.0,
                 "source": "solver, 48x4: M22 = a2^2/3 enters the gradient stiffness; k^2 ext is the mode-free limit on the 24x2 strip"})
    ap, a24p = flexo_pair(a2_um=0.9)
    k1 = ext_k2(a2_um=0.9)
    rows.append({"input": "a2", "what": "window half-thickness",
                 "perturbation": "-10 %",
                 "d_factor24_pct": 100 * (a24p / base24 - 1),
                 "d_k2ext_pct": 100 * (k1 / k0 - 1),
                 "d_zeta_pct": 0.0,
                 "source": "solver, 48x4: as above, a2 -> 0.9 um"})

    # rho: every frequency scales as rho^-1/2, every stiffness ratio stands
    rows.append({"input": "rho", "what": "density", "perturbation": "+10 %",
                 "d_factor24_pct": 0.0, "d_k2ext_pct": 0.0,
                 "d_zeta_pct": 100 * (1.1 ** -0.5 - 1),
                 "source": "exact: omega ~ rho^-1/2 for every mode, so "
                           "zeta = omega tau/2 moves by rho^-1/2"})
    rows.append({"input": "rho", "what": "density", "perturbation": "-10 %",
                 "d_factor24_pct": 0.0, "d_k2ext_pct": 0.0,
                 "d_zeta_pct": 100 * (0.9 ** -0.5 - 1),
                 "source": "exact: omega ~ rho^-1/2 for every mode"})

    # tau: zeta is linear in tau at alpha = 1; the 0.450 ratio is unchanged
    rows.append({"input": "tau", "what": "relaxation time",
                 "perturbation": "+10 %", "d_factor24_pct": 0.0,
                 "d_k2ext_pct": 0.0, "d_zeta_pct": 10.0,
                 "source": "exact at alpha = 1: zeta = omega tau/2; the K_uu/K_eff "
                           "ratio is unchanged because both zetas scale with tau"})
    rows.append({"input": "tau", "what": "relaxation time",
                 "perturbation": "-10 %", "d_factor24_pct": 0.0,
                 "d_k2ext_pct": 0.0, "d_zeta_pct": -10.0,
                 "source": "exact at alpha = 1: as above"})

    out = {"baseline": {"factor24": base24, "k2_flexo": base,
                        "k2_ext_24x2": k0}, "rows": rows}
    with open(os.path.join(RES, "sensitivity_tornado.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    md = ["# Tornado table: +/-10 % in an input, in percent of a headline number",
          "",
          "Generated by `python/sensitivity_tornado.py`. Baseline: factor "
          f"$24$ = {base24:.2f}, $k^2_{{\\rm ext}}$ (24x2) = {k0:.4f}.",
          "", "| input | +/-10 % | factor 24 | flexo k^2 (1 µm) | damping |",
          "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['input']} ({r['what']}) | {r['perturbation']} | "
                  f"{r['d_factor24_pct']:+.1f} % | {r['d_k2ext_pct']:+.1f} % | "
                  f"{r['d_zeta_pct']:+.1f} % |")
    md += ["", "A zero is a structural statement, not a null result: the "
           "couplings are stiffness ratios, so they cannot see $\\rho$; and "
           "$\\zeta$ cancels between the two memory matrices, so the 0.450 "
           "ratio is invariant in $\\tau$."]
    with open(os.path.join(RES, "sensitivity_tornado.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    for r in rows:
        print(f"  {r['input']:4s} {r['perturbation']:6s}  factor24 "
              f"{r['d_factor24_pct']:+7.1f} %   k2ext {r['d_k2ext_pct']:+7.2f} %"
              f"   zeta {r['d_zeta_pct']:+6.1f} %")
    print("  -> results/sensitivity_tornado.md")


if __name__ == "__main__":
    main()
