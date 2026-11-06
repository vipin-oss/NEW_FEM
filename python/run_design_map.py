"""Design map: flexoelectric bending coupling and piezoelectric extensional
coupling of the same strip over (thickness, window half-thickness).

The two couplings of Sec. 6 answer different questions -- one is a size effect
that grows as the strip is thinned, the other is a material property that does
not depend on thickness -- so a designer needs both at once.  This script
resolves them on a grid and writes

    results/design_map.json      every point, plus the thresholds quoted in the
                                 text
    results/figures/paper/F11_designmap.pdf  the two-panel map

The couplings are the ones used everywhere else in the paper: the bending
column is the mode-free flexoelectric coupling of the poled-$y$ configuration
with $\\mu = 10^{-6}$ C/m (48x4 BFS, electrodes on the long faces), the
extensional column the mode-free piezoelectric coupling of the poled-$x$
configuration with $\\mu = 0$ (48x4 BFS, electrodes on the short faces).

    python run_design_map.py [--quick]
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem6_core as f6      # noqa: E402
import materials as mt      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(RES, "figures", "paper")

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix",
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 8.5,
    "legend.fontsize": 7, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.4,
    "figure.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
})

L = 200e-6
HS = [10.0, 7.0, 5.0, 3.5, 2.5, 1.8, 1.3, 1.0]        # um
A2S = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]      # um, half-thickness
A1 = 3e-6                                              # um, in-plane half-width


def static_k2(mesh, mat, Mg, pair):
    """Mode-free quasi-static coupling of an electrode pair (short circuit).

    This is the measure used for the piezoelectric column: no eigenvector, so
    the same number is returned for every mode and it can be compared across
    thicknesses (Sec. 4.2, Eq. 37).
    """
    mdl = f6.assemble(mesh, mt.to_core(mat), Mg)
    Ksc, _, _, _ = f6.reduce(mdl, "short", pair=pair)
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    x = float((S * d) @ np.linalg.solve(Ksc * S[:, None] * S[None, :], S * d))
    x /= beta
    return x / (1.0 + x)


def modal_k2(mesh, mat, Mg, pair):
    """Mode-resolved coupling of the fundamental mode from ONE eigensolve.

    This is the measure used for the flexoelectric bending column, because the
    bending electrode pair senses the strain *gradient* of the fundamental
    mode: its mode-free static coupling is dominated by the in-plane response
    and is not the flexoelectric number.  Secant root of the rank-one secular
    equation as in Sec. 6.5.
    """
    mdl = f6.assemble(mesh, mt.to_core(mat), Mg)
    Ksc, M, _, _ = f6.reduce(mdl, "short", pair=pair)
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    w2, y = scipy.linalg.eigh(Ksc * S[:, None] * S[None, :],
                              M * S[:, None] * S[None, :])
    Phi = S[:, None] * y
    s = (Phi.T @ d) ** 2 / beta

    def f(yy):
        return 1.0 + float(np.sum(s / (w2 - yy)))

    a = w2[0] * (1 + 1e-10)
    b = None
    for step in (1e-6, 1e-4, 1e-2, 0.1, 0.5, 0.9):
        cand = w2[0] + step * (w2[1] - w2[0])
        if f(cand) > 0:
            b = cand
            break
    if b is None:
        b = w2[1] * (1 - 1e-9)
    for _ in range(200):
        m = 0.5 * (a + b)
        if f(m) > 0:
            b = m
        else:
            a = m
        if b - a <= 1e-15 * w2[0]:
            break
    yo = 0.5 * (a + b)
    return (yo - w2[0]) / yo


def flexo_k2(mesh, Mg, pair):
    """Flexoelectric bending coupling: mode-resolved, as in Fig. 9(a)."""
    return modal_k2(mesh, mt.batio3("y", "plane_stress"), Mg, pair)


def draw(H, A, KB, KE):
    """Two-panel design map."""
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.6))
    XX, YY = np.meshgrid(H, A, indexing="ij")
    for ax, Z, title, cbl, levels in (
            (axs[0], np.log10(KB), "(a) flexoelectric bending $k^2$",
             r"$\log_{10}k^2$", None),
            (axs[1], np.log10(KB / KE),
             "(b) $k^2_{\\rm flexo}/k^2_{\\rm piezo}$",
             r"$\log_{10}$ of the ratio",
             [np.log10(x) for x in (1e-4, 1e-3, 1e-2)])):
        cs = ax.contourf(XX, YY, Z, levels=18, cmap="viridis")
        cb = fig.colorbar(cs, ax=ax, pad=0.02, fraction=0.05)
        cb.set_label(cbl, fontsize=7)
        cb.ax.tick_params(labelsize=6)
        cb.locator = matplotlib.ticker.MaxNLocator(nbins=4)
        cb.update_ticks()
        if levels:
            cl = ax.contour(XX, YY, Z, levels=levels, colors="w",
                            linewidths=0.9, linestyles=["--", "-", "-."])
            ax.clabel(cl, fmt={levels[0]: "0.01 %", levels[1]: "0.1 %",
                               levels[2]: "1 %"}, fontsize=6)
        ax.plot(H, H, ":", color="w", lw=1.1)
        ax.text(1.05, 4.2, r"$a_2=h$", color="w", fontsize=6.5)
        ax.set_ylim(A.min(), 45.0)
        ax.axhline(0.2 * 200.0, color="w", lw=1.0, alpha=0.9)
        ax.text(1.05, 34.0, r"$a_2/L=0.2$", color="w", fontsize=6.2)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlim(H.min(), H.max()); ax.set_ylim(A.min(), A.max())
        ax.set_xlabel(r"strip thickness $h$ ($\mu$m)")
        ax.set_ylabel(r"window half-thickness $a_2$ ($\mu$m)")
        ax.set_title(title)
        ax.grid(False)
    fig.tight_layout()
    for d in (FIG, os.path.join(ROOT, "Paper_12", "figures")):
        os.makedirs(d, exist_ok=True)
        fig.savefig(os.path.join(d, "F11_designmap.pdf"))
        fig.savefig(os.path.join(d, "F11_designmap.png"), dpi=220)
    plt.close(fig)


def replot(summary):
    """Redraw F11 from a stored results/design_map.json (no recompute)."""
    H = np.array(summary["h_um"]); A = np.array(summary["a2_um"])
    KB = np.array(summary["k2_bend_flexo"]); KE = np.array(summary["k2_ext_piezo"])
    return H, A, KB, KE


def main():
    quick = "--quick" in sys.argv
    hs = HS[::2] + [HS[-1]] if quick else HS
    a2s = A2S[::2] + [A2S[-1]] if quick else A2S
    if "--replot" in sys.argv:
        summary = json.load(open(os.path.join(RES, "design_map.json")))
        H, A, KB, KE = replot(summary)
        draw(H, A, KB, KE)
        return 0
    mup_y = mt.batio3("y", "plane_stress")
    mue_x = mt.Material(**{**mt.batio3("x", "plane_stress").__dict__, "mu": 0.0})
    rows = []
    for h_um in hs:
        for a2_um in a2s:
            Mg = f6.second_moment("cuboid", A1, a2_um * 1e-6, 0.0)
            mesh = f6.mesh_rect(48, 4, L, h_um * 1e-6)
            kb = flexo_k2(mesh, Mg, ("bottom", "top"))
            ke = static_k2(mesh, mue_x, Mg, ("left", "right"))
            rows.append({"h_um": h_um, "a2_um": a2_um, "a2_over_L": a2_um / 200.0,
                         "k2_bend_flexo": kb, "k2_ext_piezo": ke,
                         "ratio": kb / ke})
            print(f"  h={h_um:5.1f} um  a2={a2_um:5.2f} um  "
                  f"k2_flexo={kb:.3e}  k2_ext={ke:.5f}  ratio={kb/ke:.2e}",
                  flush=True)

    H = np.array(sorted({r["h_um"] for r in rows}))
    A = np.array(sorted({r["a2_um"] for r in rows}))
    KB = np.array([[next(r["k2_bend_flexo"] for r in rows
                         if r["h_um"] == h and r["a2_um"] == a) for a in A]
                   for h in H])
    KE = np.array([[next(r["k2_ext_piezo"] for r in rows
                         if r["h_um"] == h and r["a2_um"] == a) for a in A]
                   for h in H])

    # thresholds quoted in the text
    def crossing(level, a2=1.0):
        """Thickness at which ratio crosses ``level`` for window a2 (log-log)."""
        j = int(np.argmin(abs(A - a2)))
        r = KB[:, j] / KE[:, j]
        lr, lh = np.log(r), np.log(H)
        for i in range(len(H) - 1):
            if (lr[i] - np.log(level)) * (lr[i + 1] - np.log(level)) <= 0:
                t = (np.log(level) - lr[i]) / (lr[i + 1] - lr[i])
                return float(np.exp(lh[i] + t * (lh[i + 1] - lh[i])))
        return None

    summary = {
        "L_um": 200.0, "a1_um": 3.0, "mu_C_per_m": 1e-6,
        "mesh": "48x4", "measure": "mode-free static, K_uu short circuit",
        "h_um": H.tolist(), "a2_um": A.tolist(),
        "k2_bend_flexo": KB.tolist(), "k2_ext_piezo": KE.tolist(),
        "ratio": (KB / KE).tolist(),
        "range": {"k2_flexo_min": float(KB.min()), "k2_flexo_max": float(KB.max()),
                  "k2_ext_min": float(KE.min()), "k2_ext_max": float(KE.max()),
                  "ratio_min": float((KB / KE).min()),
                  "ratio_max": float((KB / KE).max())},
        "thresholds": {"h_at_0p1pct_a2_1um": crossing(1e-3),
                       "h_at_0p1pct_a2_4um": crossing(1e-3, 4.0),
                       "h_at_1pct_a2_025um": crossing(1e-2, 0.25)},
        "band": {"a2_over_L_max": 0.2},
    }

    with open(os.path.join(RES, "design_map.json"), "w") as fh:
        json.dump(summary, fh, indent=1)

    draw(H, A, KB, KE)

    r = summary["range"]
    print(f"\n  flexo  {r['k2_flexo_min']:.2e} .. {r['k2_flexo_max']:.2e}"
          f"\n  piezo  {r['k2_ext_min']:.5f} .. {r['k2_ext_max']:.5f}"
          f"\n  ratio  {r['ratio_min']:.2e} .. {r['ratio_max']:.2e}")
    for k, v in summary["thresholds"].items():
        print(f"  {k}: {v}")
    print("  -> results/design_map.json, F11_designmap.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
