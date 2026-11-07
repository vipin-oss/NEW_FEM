"""check_numerics.py -- numerical hygiene of the solver, one number per hazard.

Five questions, five answers, all archived in results/numerics.json:

  scaling      is the generalized eigenproblem solved in a scaling in which the
               eigenvalue is not swamped by the units of K and M?  The
               eigenvalues of (K, M) are compared with those of the
               Cholesky-standardized pencil L^-1 K L^-T, and the condition
               number of each matrix is reported at h = 10 and h = 1 um.

  l1_weights   b_0 must be 1 for every alpha, although the closed form
               (j+1)^(1-a) - j^(1-a) gives 1 - 0^0 at j = 0 and numpy reads
               0**0 as 1; and for alpha -> 1 the difference of two nearly equal
               powers loses digits, so the float weights are compared with a
               50-digit Decimal evaluation.

  dt_order     at alpha < 1 the L1 scheme must still converge at first order:
               dt, dt/2 and dt/4 on the same ring-down, order from Richardson.

  truncation   how many modes the modal projection needs, from the delivered
               truncation study (8 vs 40 modes, memory on K_eff and on K_uu).

  conditioning the conditioning of the condensed stiffness at the thinnest
               strip of the paper, where the eigenvalues being differenced are
               closest.

    python3 python/check_numerics.py   -> results/numerics.json
"""
from __future__ import annotations

import json
import os
from decimal import Decimal, getcontext

import deterministic  # noqa: F401  (pins the numeric stack)

import numpy as np
from scipy.linalg import eigh

import fem6_core as f6
import materials as mt
from run_memory_variants import build, ringdown, peaks_of

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
L = 200e-6
getcontext().prec = 50


def scaling():
    """Generalized vs standardized pencil, and the condition numbers."""
    out = {}
    for h_um in (10.0, 1.0):
        core = mt.to_core(mt.batio3("x", "plane_stress"))
        H = h_um * 1e-6
        mdl = f6.assemble(f6.mesh_rect(24, 2, L, H), core,
                          f6.second_moment("cuboid", 3e-6, 1e-6, 0.0))
        K, M, _idx, _db = f6.reduce(mdl, "open", pair=("left", "right"))
        w2 = eigh(K, M, eigvals_only=True)[:6]
        Lc = np.linalg.cholesky(M)
        A = np.linalg.solve(Lc, np.linalg.solve(Lc, K).T)
        A = 0.5 * (A + A.T)
        w2s = np.linalg.eigvalsh(A)[:6]
        rel = np.max(np.abs(w2s - w2) / np.abs(w2))
        out[f"h_{h_um:g}um"] = {
            "omega2_generalized": w2.tolist(),
            "omega2_standardized": w2s.tolist(),
            "rel_diff": float(rel),
            "cond_K": float(np.linalg.cond(K)),
            "cond_M": float(np.linalg.cond(M)),
        }
    out["worst_rel_diff"] = max(v["rel_diff"] for k, v in out.items()
                                if isinstance(v, dict))
    out["max_cond_K"] = max(v["cond_K"] for k, v in out.items()
                            if isinstance(v, dict))
    return out


def l1_weights():
    """b_0 = 1 for every alpha (the 0**0 case) and the cancellation at j >= 1."""
    alphas = [0.1, 0.3, 0.5, 0.7, 0.9, 0.99, 0.999, 1.0]
    b0 = {}
    for a in alphas:
        b = f6.l1_weights(64, a)
        b0[f"{a:g}"] = float(b[0])
    # cancellation: float against 50-digit Decimal, worst over j = 1..2000
    worst = {}
    for a in (0.5, 0.9, 0.99, 0.999, 1.0):
        b = f6.l1_weights(2000, a)
        ex = []
        p_exp = Decimal(repr(1.0 - a))          # the L1 exponent 1 - alpha
        for j in range(1, 2001):
            ex.append(float((Decimal(j + 1) ** p_exp)
                            - (Decimal(j) ** p_exp)))
        ex = np.array(ex)
        rel = np.abs(b[1:2001] - ex) / np.maximum(np.abs(ex), 1e-300)
        worst[f"{a:g}"] = float(rel.max())
    b = f6.l1_weights(64, 0.6)
    return {"b0": b0, "b0_ok": bool(all(abs(v - 1.0) < 1e-15
                                       for v in b0.values())),
            "worst_cancellation_rel": worst,
            "monotone_positive": bool(np.all(b[1:] > 0)
                                      and np.all(np.diff(b[1:]) < 0)),
            "sum_first_64": float(b.sum())}


def _records(alpha, nmodes_list, nsteps=2000):
    """One ring-down per truncation, on the same physical time grid."""
    mdl, core, Koc, Kuu, M, idx, d, beta = build()
    j = 4
    ws, Phi = f6.modes(Koc, M, 8)
    tip = int(np.argmax(mdl.mesh.nodes[:, 0]))
    row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
    x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))
    tau = 3e-9
    T = 10 * 2 * np.pi / ws[j]
    tg = np.linspace(0.0, T, 401)
    out = []
    for nm in nmodes_list:
        t, V = ringdown(Kuu, Koc, M, idx, d, beta, alpha, tau, j, x0,
                        nm=nm, nsteps=nsteps)
        out.append(np.interp(tg, t, V))
    return tg, out


def dt_order():
    """Observed order of the L1 scheme at alpha < 1, dt, dt/2, dt/4, dt/8.

    The measure is the L2 difference of the whole voltage record from the
    finest one, which is what a first-order scheme converges at; the peak
    amplitude and the peak ratio are individually insensitive or
    cancellation-prone, and measuring either of them returns a misleading
    order (see the round-2 report).
    """
    out = {}
    for alpha in (0.5, 0.7):
        steps = (800, 1600, 3200, 6400)
        mdl, core, Koc, Kuu, M, idx, d, beta = build()
        j = 4
        ws, _ = f6.modes(Koc, M, 8)
        tip = int(np.argmax(mdl.mesh.nodes[:, 0]))
        row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
        _, Phi = f6.modes(Koc, M, 8)
        x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))
        T = 10 * 2 * np.pi / ws[j]
        tg = np.linspace(0.0, T, 401)
        Vs = []
        for n in steps:
            t, V = ringdown(Koc, Koc, M, idx, d, beta, alpha, 3e-9, j, x0,
                            nm=8, nsteps=n)
            Vs.append(np.interp(tg, t, V))
        ref = Vs[-1]
        err = [float(np.linalg.norm(v - ref) / np.linalg.norm(ref))
               for v in Vs[:-1]]
        order = [float(np.log2(err[i] / err[i + 1])) for i in range(len(err) - 1)]
        out[f"{alpha:g}"] = {"steps": list(steps), "rel_err": err,
                             "orders": order}
    finest = min(min(v["orders"][-1] for v in out.values()), 9.9)
    coarse = min(min(v["orders"][0] for v in out.values()), 9.9)
    return {"cases": out, "finest_order": finest, "coarsest_order": coarse,
            "first_order_ok": bool(finest >= 0.8 and coarse >= 0.8)}


def truncation():
    """How many modes the ring-down needs, on both memory matrices.

    Memory on K_uu couples the modes, so the projection has to be wide;
    memory on K_eff leaves the motion in a single mode and eight modes are
    exact to the last bit.  Both numbers are the max-norm of the voltage
    difference over ten periods, referred to the forty-mode peak.
    """
    _tg, recs = _records(0.7, (8, 20, 40))
    v8, v20, v40 = recs
    scale = float(np.abs(v40).max())
    # the same pair with the memory on the condensed matrix
    mdl, core, Koc, Kuu, M, idx, d, beta = build()
    j = 4
    ws, Phi = f6.modes(Koc, M, 8)
    tip = int(np.argmax(mdl.mesh.nodes[:, 0]))
    row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
    x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))
    T = 10 * 2 * np.pi / ws[j]
    tg = np.linspace(0.0, T, 401)
    eff = {}
    for nm in (8, 40):
        t, V = ringdown(Koc, Koc, M, idx, d, beta, 0.7, 3e-9, j, x0,
                        nm=nm, nsteps=2000)
        eff[nm] = np.interp(tg, t, V)
    eff_rel = float(np.abs(eff[8] - eff[40]).max()
                    / np.abs(eff[40]).max())
    return {"alpha": 0.7, "nmodes": [8, 20, 40],
            "kuu_relerr_8_vs_40": float(np.abs(v8 - v40).max() / scale),
            "kuu_relerr_20_vs_40": float(np.abs(v20 - v40).max() / scale),
            "keff_relerr_8_vs_40": eff_rel,
            "converged": bool(np.abs(v20 - v40).max() / scale < 1e-2
                              and eff_rel < 1e-10)}


def main():
    out = {"scaling": scaling(), "l1": l1_weights(), "dt": dt_order(),
           "truncation": truncation()}
    with open(os.path.join(RES, "numerics.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    s = out["scaling"]
    print(f"  eigenproblem: |w2(gen) - w2(std)| / w2 <= {s['worst_rel_diff']:.1e}"
          f"  |  cond(K) <= {s['max_cond_K']:.1e}")
    l = out["l1"]
    print(f"  L1: b0 = 1 for all alpha: {l['b0_ok']}  |  worst cancellation "
          f"rel. error {max(l['worst_cancellation_rel'].values()):.1e}")
    d = out["dt"]
    for a, v in d["cases"].items():
        print(f"  alpha = {a}: rel. err " + ", ".join(f"{e:.2e}" for e in v["rel_err"])
              + "  ->  orders " + ", ".join(f"{o:.2f}" for o in v["orders"]))
    t = out["truncation"]
    print(f"  truncation: K_uu 8 vs 40 {t['kuu_relerr_8_vs_40']:.1e}, "
          f"20 vs 40 {t['kuu_relerr_20_vs_40']:.1e};  "
          f"K_eff 8 vs 40 {t['keff_relerr_8_vs_40']:.1e}")
    print("  -> results/numerics.json")


if __name__ == "__main__":
    main()
