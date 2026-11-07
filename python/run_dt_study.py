"""run_dt_study.py -- the step-refinement statement of Sec. 6.2.

Two runs, both archived in results/dt_study.json:

  memory      the ring-down of Table 5 (K_eff, alpha = 1, omega*tau = 0.3,
              twenty periods) at N, 2N and 4N steps, N = 12000.  The damping
              ratio is extracted from successive peaks with the exact relation
              of eq:zeta, so the sequence measures the order of the L1 scheme
              at alpha = 1 against the exact omega*tau/2 = 0.150000.

  figure10    the first-period decrement of the alpha = 1 curve of Fig. 10
              (tau = 3 ns, omega*tau = 0.13) at 4000 steps over ten periods --
              the step that figure uses -- and at four times that step, which
              measures how far the last quoted digit of Table C.5 moves.
"""
from __future__ import annotations

import json
import os

import numpy as np

import fem6_core as f6
import materials as mt
from run_memory_variants import build, ringdown, zeta_eff

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
L, H = 200e-6, 10e-6


def figure10_step(nsteps, nmodes=8):
    """first-period decrement of the alpha = 1 curve of Fig. 10"""
    mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    mdl = f6.assemble(f6.mesh_rect(24, 2, L, H),
                      mt.to_core(mt.batio3("x", "plane_stress")), mg)
    Koc, M, idx, (d, beta) = f6.reduce(mdl, "open", pair=("left", "right"))
    ws, Phi = f6.modes(Koc, M, nmodes)
    j = 4
    tip = int(np.argmax(mdl.mesh.nodes[:, 0]))
    row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
    x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))
    tau = 3e-9
    T = 10 * 2 * np.pi / ws[j]
    t, x, y, v, a = f6.transient(Koc, M, Koc, np.zeros(idx.size), 1.0, tau,
                                 T / nsteps, nsteps, nmodes=nmodes, x0=x0,
                                 v0=np.zeros(idx.size))
    u = (Phi[row, :] @ y) * 1e9
    pk = [n for n in range(1, len(u) - 1)
          if u[n] > u[n - 1] and u[n] > u[n + 1] and u[n] > 0]
    dl = float(np.log(u[pk[0]] / u[pk[1]]))
    return {"steps": nsteps, "periods": 10,
            "steps_per_period": nsteps / 10.0,
            "delta": dl, "zeta": float(dl / np.sqrt(4 * np.pi ** 2 + dl ** 2)),
            "omega_tau": float(ws[j] * tau)}


def main():
    mdl, core, Koc, Kuu, M, idx, d, beta = build()
    wo, Phi = f6.modes(Koc, M, 8)
    j = 4
    tau = 0.3 / wo[j]
    tip = int(np.argmax(mdl.mesh.nodes[:, 0]))
    row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
    x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))

    rowsm = []
    for mult in (1, 2, 4):
        n = 12000 * mult
        t, V = ringdown(Koc, Koc, M, idx, d, beta, 1.0, tau, j, x0, nsteps=n)
        z = zeta_eff(t, V, wo[j])
        rowsm.append({"mult": mult, "steps": n, "periods": 20,
                      "steps_per_period": n / 20.0,
                      "zeta": float(z["zeta_eff"])})
        print("  memory  N=%6d  zeta = %.6f" % (mult, z["zeta_eff"]))
    exact = 0.3 / 2
    err = [abs(r["zeta"] - exact) for r in rowsm]
    order = float(np.log(err[0] / err[-1]) / np.log(4.0))

    f10 = []
    for n in (4000, 16000):
        r = figure10_step(n)
        f10.append(r)
        print("  fig.10  N=%6d (%.0f steps/period)  zeta = %.8f"
              % (n, r["steps_per_period"], r["zeta"]))
    shift = abs(f10[0]["zeta"] - f10[1]["zeta"])

    out = {
        "memory": {"K": "K_eff", "alpha": 1.0, "omega_tau": 0.3,
                   "exact": exact, "N": 12000, "rows": rowsm,
                   "err_vs_exact": err, "order": order},
        "figure10": {"alpha": 1.0, "rows": f10, "last_digit_shift": shift},
    }
    with open(os.path.join(RES, "dt_study.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n  exact omega*tau/2 = %.6f, observed order %.2f" % (exact, order))
    print("  Fig. 10: the last quoted digit moves by %.1e when the step is "
          "quartered" % shift)


if __name__ == "__main__":
    main()
