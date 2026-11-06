"""
run_memory_variants.py -- two sensitivity studies for the memory term.

S1  WHERE the memory acts:  K_eff (baseline) vs K_uu (mechanical block only).
    With K_eff the modal system is proportional (Kd reduced = diagonal); with
    K_uu it is not, and the whole "one zeta per mode" picture breaks.
S2  KV vs fractional Zener: the fractional Kelvin-Voigt modulus grows without
    bound, |C*| ~ (w tau)^alpha; the Zener form saturates at C_inf.  Quantifies
    the error made by using KV at the device's w tau.

Run: python3 python/run_memory_variants.py -> results/memory_variants.{md,json}
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


def build(kin="plane_stress"):
    m = mt.batio3("x", kin)
    core = mt.to_core(m)
    mdl = f6.assemble(f6.mesh_rect(24, 2, L, H), core,
                      f6.second_moment("cuboid", 3e-6, 1e-6, 0.0), gradient=True)
    Koc, M, idx, (d, beta) = f6.reduce(mdl, "open", pair=("left", "right"))
    Ksc, _, _, _ = f6.reduce(mdl, "short", pair=("left", "right"))
    # K_uu: the same model with no electromechanical coupling has Keff = K_uu
    core0 = mt.to_core(m)
    core0.e[:] = 0.0
    core0.mu = 0.0
    mdl0 = f6.assemble(f6.mesh_rect(24, 2, L, H), core0,
                       f6.second_moment("cuboid", 3e-6, 1e-6, 0.0), gradient=True)
    Kuu, _, idx0, _ = f6.reduce(mdl0, "short", pair=("left", "right"))
    assert np.array_equal(idx, idx0)
    return mdl, core, Koc, Kuu, M, idx, d, beta


def ringdown(Kd, Koc, M, idx, d, beta, alpha, tau, j, x0, nm=8, nsteps=48000):
    wo = f6.modes(Koc, M, nm)[0]
    T = 20 * 2 * np.pi / wo[j]
    N = nsteps
    dt = T / N
    t, x, y, v, a = f6.transient(Koc, M, Kd, np.zeros(idx.size), alpha, tau,
                                 dt, N, nmodes=nm, x0=x0,
                                 v0=np.zeros(idx.size))
    u = (x[idx % 8 < 2]).max(axis=0) if False else None
    V = (d @ x) / beta
    return t, V


def peaks_of(t, s, w):
    """Local maxima of |s|, at least 0.7 period apart."""
    a = np.abs(s)
    per = int(len(t) / (t[-1] * w / (2 * np.pi)))          # samples per period
    cand = [i for i in range(1, len(a) - 1)
            if a[i] > a[i - 1] and a[i] >= a[i + 1]]
    keep = []
    for i in cand:
        if not keep or i - keep[-1] > 0.7 * per:
            keep.append(i)
    return a[np.array(keep)]


def zeta_eff(t, s, w):
    """Damping ratio from the successive-peak decrements.

    delta_k = ln(A_k/A_{k+1});  zeta = delta/sqrt(4 pi^2 + delta^2) exactly.
    `delta` is the mean over all successive pairs and `zeta_eff` the exact
    conversion of it; `zeta_small` = delta/(2 pi) is retained only to show how
    far the small-damping form is off. `zeta_first` is the first-period value,
    which is the only meaningful entry for alpha < 1, where the free decay of a
    fractional element is not exponential.
    """
    pk = peaks_of(t, s, w)
    if len(pk) < 3:
        return {}
    d = np.log(pk[:-1] / pk[1:])
    delta = float(d.mean())
    d1 = float(d[0])
    out = {"delta": delta,
           "peak_ratio": float(pk[0] / pk[1]),
           "zeta_eff": float(delta / np.sqrt(4 * np.pi ** 2 + delta ** 2)),
           "zeta_small": float(delta / (2 * np.pi)),
           "delta_spread": float(d.max() - d.min()),
           "first_delta": d1,
           "zeta_first": float(d1 / np.sqrt(4 * np.pi ** 2 + d1 ** 2)),
           "npeaks": int(len(pk))}
    out["zeta_eff"] = out["zeta_eff"]
    return out


def main():
    mdl, core, Koc, Kuu, M, idx, d, beta = build()
    wo, Phi = f6.modes(Koc, M, 8)
    ws, _ = f6.modes(Kuu, M, 8)
    k2 = (wo ** 2 - ws ** 2) / wo ** 2
    j = int(np.argmax(k2))
    f_j = wo[j] / 2 / np.pi
    tau = 0.3 / wo[j]
    tip = int(np.argmax(mdl.mesh.nodes[:, 0]))
    row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
    x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))

    out = {"mode": j, "f_Hz": float(f_j), "k2": float(k2[j]),
           "tau": float(tau), "omega_tau": 0.3, "S1": {}, "S2": []}

    print(f"S1  mode {j} at {f_j/1e3:.3f} kHz, k2 = {k2[j]:.4f}, "
          f"omega*tau = 0.3")
    for tag, Kd in (("Keff", Koc), ("Kuu", Kuu)):
        for alpha in (1.0, 0.7):
            t, V = ringdown(Kd, Koc, M, idx, d, beta, alpha, tau, j, x0)
            z = zeta_eff(t, V, wo[j])
            out["S1"][f"{tag}_alpha{alpha}"] = {"V0": float(abs(V[0])), **z}
            print(f"    Kd={tag:5s} alpha={alpha}: V(0)={abs(V[0]):8.4f} V, "
                  f"delta = {z['delta']:.6f}, zeta_eff = {z['zeta_eff']:.6f}, "
                  f"zeta_small = {z['zeta_small']:.6f}, "
                  f"zeta_first = {z['zeta_first']:.6f}, "
                  f"spread = {z['delta_spread']:.2e}")

    # ---- S2: KV vs fractional Zener modulus ----
    print("\nS2  |C*|/C0 : fractional Kelvin-Voigt vs fractional Zener")
    print(f"    {'w tau':>8} {'alpha':>5} {'KV':>10} {'Zener r=1.1':>12} "
          f"{'Zener r=2':>10} {'KV/Zener':>9}")
    for alpha in (1.0, 0.7, 0.5):
        for wtau in (0.01, 0.1, 0.3, 1.0, 10.0, 100.0):
            z = (1j * wtau) ** alpha
            kv = abs(1 + z)
            row_ = {"alpha": alpha, "omega_tau": wtau, "KV": float(kv)}
            zr = []
            for r in (1.1, 2.0):
                # C*/C0 = (1 + r z)/(1 + z),  r = C_inf/C_0
                v = abs((1 + r * z) / (1 + z))
                zr.append(float(v))
            row_["Zener_r1p1"], row_["Zener_r2"] = zr
            row_["ratio_KV_over_Zener"] = float(kv / zr[0])
            out["S2"].append(row_)
            print(f"    {wtau:8.2f} {alpha:5.1f} {kv:10.4f} {zr[0]:12.4f} "
                  f"{zr[1]:10.4f} {kv/zr[0]:9.3f}")

    # device operating point
    wtau_dev = 0.3
    for alpha in (1.0, 0.7):
        z = (1j * wtau_dev) ** alpha
        kv = float(abs(1 + z))
        ze = float(abs((1 + 1.1 * z) / (1 + z)))
        out.setdefault("device_point", {})[f"alpha{alpha}"] = {
            "KV_over_Zener": kv / ze, "KV": kv, "Zener": ze}
        print(f"\n    device point w tau = 0.3, alpha = {alpha}: "
              f"KV/Zener = {kv/ze:.4f} ({100*(kv/ze-1):+.1f} %)")

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "memory_variants.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    md = ["# Memory-term sensitivity", "",
          f"Mode {j} at {f_j/1e3:.3f} kHz, `k_eff^2 = {k2[j]:.4f}`, "
          f"`omega tau = 0.3` (underdamped).", "",
          "## S1 — where the memory acts", "",
          "| `K_d` | `alpha` | V(0) (V) | zeta_eff |", "|---|---|---|---|"]
    for k, v in out["S1"].items():
        tag, al = k.split("_alpha")
        md.append(f"| {tag} | {al} | {v['V0']:.4f} | {v['zeta_eff']:.5f} |")
    md += ["", "## S2 — fractional Kelvin-Voigt vs fractional Zener", "",
           "`|C*|/C_0`: KV `= |1+(i w tau)^a|` (unbounded), Zener "
           "`= |(1+r(i w tau)^a)/(1+(i w tau)^a)|` with `r = C_inf/C_0`.", "",
           "| `w tau` | `alpha` | KV | Zener r=1.1 | Zener r=2 | KV/Zener |",
           "|---|---|---|---|---|---|"]
    for r in out["S2"]:
        md.append(f"| {r['omega_tau']:.2f} | {r['alpha']:.1f} | {r['KV']:.4f} "
                  f"| {r['Zener_r1p1']:.4f} | {r['Zener_r2']:.4f} "
                  f"| {r['ratio_KV_over_Zener']:.3f} |")
    with open(os.path.join(ROOT, "results", "memory_variants.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n-> results/memory_variants.{md,json}")


if __name__ == "__main__":
    main()
