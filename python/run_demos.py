"""
FEM-6 demonstration runs and figures.

Produces results/figures/*.png and results/demo.json:

  fig1_k2_orientation.png   f1 and k_eff^2 versus orientation for the cuboid
  fig2_memory_response.png  u_tip(t) and open-circuit V(t) for three alpha
  fig3_damping_ratio.png    zeta versus alpha (small-damping and exact pole)
  fig4_domain_comparison.png u/u_classical versus l/L for ellipsoid and cuboid

Run:  python3 python/run_demos.py
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
import fem6_core as f6  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({"font.size": 9, "figure.dpi": 200,
                     "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})


# --------------------------------------------------------------------------
# application model: length-extensional BaTiO3 bar (poled along x)
# --------------------------------------------------------------------------
L, H = 200e-6, 10e-6
import materials as mt
MAT_X = mt.to_core(mt.batio3("x", "plane_stress"))
MESH = f6.mesh_rect(24, 2, L, H)


def build(domain="cuboid", ax=3e-6, ay=1e-6, theta=0.0):
    Mg = f6.second_moment(domain, ax, ay, theta)
    m = f6.assemble(MESH, MAT_X, Mg)
    Ksc, M, idx, _ = f6.reduce(m, "short", pair=("left", "right"))
    Koc, M, idx, ex = f6.reduce(m, "open", pair=("left", "right"))
    d, beta = ex
    return m, Ksc, Koc, M, idx, d, beta


def oriented_sweep():
    rows = []
    for AR in [2.0, 5.0, 10.0]:
        for th in np.deg2rad([0, 15, 30, 45, 60, 75, 90]):
            ax = 3e-6
            ay = ax / AR
            m, Ksc, Koc, M, idx, d, beta = build("cuboid", ax, ay, th)
            ws, _ = f6.modes(Ksc, M, 6)
            wo, phio = f6.modes(Koc, M, 6)
            k2 = (wo ** 2 - ws ** 2) / wo ** 2
            # axial mode = the one with the largest coupling
            j = int(np.argmax(k2))
            rows.append({"AR": AR, "theta_deg": float(np.rad2deg(th)),
                         "f1_kHz": float(ws[0] / 2e3 / np.pi),
                         "k2_mode1": float(k2[0]),
                         "k2_axial": float(k2[j]),
                         "f_axial_kHz": float(ws[j] / 2e3 / np.pi)})
    return rows


def fig_orientation(rows):
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.7))
    for AR in [2.0, 5.0, 10.0]:
        r = [x for x in rows if x["AR"] == AR]
        th = [x["theta_deg"] for x in r]
        ax[0].plot(th, [x["f1_kHz"] for x in r], "o-", ms=3, label=f"AR={AR:g}")
        ax[1].plot(th, [x["k2_axial"] for x in r], "o-", ms=3, label=f"AR={AR:g}")
    ax[0].set_xlabel(r"orientation $\theta$ (deg)")
    ax[0].set_ylabel(r"$f_1$ (kHz)")
    ax[0].set_title("(a) fundamental frequency")
    ax[1].set_xlabel(r"orientation $\theta$ (deg)")
    ax[1].set_ylabel(r"$k_{\rm eff}^2$ (axial mode)")
    ax[1].set_title("(b) electromechanical coupling")
    ax[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_k2_orientation.png"))
    plt.close(fig)


def fig_memory():
    """Ring-down of the axial mode after an initial displacement."""
    m, Ksc, Koc, M, idx, d, beta = build("cuboid", 3e-6, 1e-6, 0.0)
    wo, Phi = f6.modes(Koc, M, 8)
    k2 = (wo ** 2 - (f6.modes(Ksc, M, 8)[0]) ** 2) / wo ** 2
    j = int(np.argmax(k2))                      # length-extensional mode
    tip_node = int(np.argmax(MESH.nodes[:, 0]))
    tip_row = int(np.searchsorted(idx, m.mech_dof[tip_node][0]))
    x0 = Phi[:, j].copy()
    x0 *= 10e-9 / abs(x0[tip_row])              # 10 nm tip amplitude
    tau = 3e-9          # omega*tau = 0.13 at this mode (underdamped)
    f_zero = np.zeros(idx.size)
    out = {"mode_index": j + 1, "f_axial_kHz": float(wo[j] / 2e3 / np.pi),
           "k2_axial": float(k2[j])}
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.7))
    for alpha in [1.0, 0.9, 0.7]:
        T = 20 * 2 * np.pi / wo[j]
        N = 12000
        dt = T / N
        t, x, y, v, a = f6.transient(Koc, M, Koc, f_zero, alpha, tau, dt, N,
                                     nmodes=8, x0=x0, v0=np.zeros(idx.size))
        u_tip = Phi[tip_row, :] @ y
        V = (d @ Phi) @ y / beta
        ax[0].plot(t * 1e6, u_tip * 1e9, lw=1.2, label=fr"$\alpha={alpha}$")
        ax[1].plot(t * 1e6, V, lw=1.2, label=fr"$\alpha={alpha}$")
        out[str(alpha)] = {"u_tip_nm": float(np.max(np.abs(u_tip)) * 1e9),
                           "V_at_t0_V": float(abs(V[0]))}
    ax[0].set_xlabel(r"$t$ ($\mu$s)")
    ax[0].set_ylabel(r"$u_{\rm tip}$ (nm)")
    ax[1].set_xlabel(r"$t$ ($\mu$s)")
    ax[1].set_ylabel(r"$V_{\rm oc}$ (V)")
    ax[1].legend(frameon=False, fontsize=8)
    ax[0].set_title("(a) tip displacement")
    ax[1].set_title("(b) open-circuit voltage")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_memory_response.png"))
    plt.close(fig)
    return out


def fig_damping():
    a = np.linspace(0.05, 1.0, 40)
    w0 = 2 * np.pi * 200e3
    tau = 3e-9          # omega*tau = 0.13 at this mode (underdamped)
    ze = []
    for x in a:
        s = f6.complex_frequency(w0, tau, x)
        ze.append(-s.real / abs(s))
    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    ax.plot(a, f6.damping_ratio(w0, tau, a), "--", lw=1.2,
            label="small-damping formula")
    ax.plot(a, ze, "-", lw=1.6, label="exact complex pole")
    ax.set_xlabel(r"Caputo order $\alpha$")
    ax.set_ylabel(r"modal damping ratio $\zeta_1$")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_damping_ratio.png"))
    plt.close(fig)
    return {"alpha": a.tolist(), "zeta_small": f6.damping_ratio(w0, tau, a).tolist(),
            "zeta_exact": ze}


def fig_domain():
    mesh = f6.mesh_rect(20, 4, 1.0, 0.2)
    mat = f6.isotropic_plane_strain(2e11, 0.3, 7850)

    def ur(Mg, grad):
        m = f6.assemble(mesh, mat, Mg, gradient=grad)
        K, M, idx, _ = f6.reduce(m, "short")
        f = m.edge_traction(tx=1e6)
        U = np.zeros(m.ndof_mech)
        U[idx] = np.linalg.solve(K, f[idx])
        right = [n for n, xy in enumerate(mesh.nodes) if abs(xy[0] - 1) < 1e-12]
        return float(np.mean([U[m.mech_dof[n][0]] for n in right]))

    u0 = ur(np.zeros((2, 2)), False)
    ls = np.linspace(0.01, 0.20, 12)
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    ax.plot(ls, [ur(f6.second_moment("ellipsoid", l, l), True) / u0 for l in ls],
            "-", lw=1.6, label="ellipsoid, semi-axis $l$")
    ax.plot(ls, [ur(f6.second_moment("cuboid", l, l), True) / u0 for l in ls],
            "-", lw=1.6, label="cuboid, half-width $l$")
    ax.plot(ls, [ur(f6.second_moment("cuboid", l * np.sqrt(3 / 5),
                                     l * np.sqrt(3 / 5)), True) / u0
                 for l in ls], "--", lw=1.2,
            label=r"cuboid, equal $M$ ($a=l\sqrt{3/5}$)")
    ax.set_xlabel(r"$l/L_x$")
    ax.set_ylabel(r"$u_R/u_{R,\rm classical}$")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_domain_comparison.png"))
    plt.close(fig)
    return {"l_over_L": ls.tolist()}



def _static_k2(mesh, mats, Mg, pair):
    """Mode-free (quasi-static, single-port) coupling factor.

    x = d^T K_uu^{-1} d / beta is the ratio of the energy the electrodes can
    pick up to the electrical energy of the electrode pair, so k^2 = x/(1+x).
    It uses no eigenvector and therefore cannot jump to a different mode at a
    different thickness.  The solve is done on the diagonally scaled system
    (cond ~ 1e12 instead of 1e27) and agrees with the unscaled solve to 6
    digits.
    """
    mdl = f6.assemble(mesh, mt.to_core(mats), Mg)
    Koc, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    sd = np.sqrt(np.abs(np.diag(Koc)))
    S = 1.0 / sd
    x = float((S * d) @ np.linalg.solve(Koc * S[:, None] * S[None, :], S * d))
    x /= beta
    return x / (1.0 + x)


def _modal_k2(mesh, mats, Mg, pair, dense_limit=4200):
    """Mode-resolved k^2 from ONE short-circuit eigensolve.

    The obvious route -- solve the open- and the short-circuit problems and
    take (wo^2 - ws^2)/wo^2 -- needs the *difference* of two nearly equal
    eigenvalues of a pencil with cond(K) ~ 1e12.  Its noise is the same size
    as the flexoelectric k^2 itself: at h = 1 um it gave 3.94e-3 / 4.47e-3 /
    3.30e-3 on 24x2 / 48x4 / 96x4 and even a *negative* value for mu = 0.

    The open-circuit matrix is a rank-one update of the short-circuit one,
    K_open = K_sc + d d^T / beta, so the open-circuit fundamental frequency is
    the root in (w_0^2, w_1^2) of the secular equation

        1 + sum_i s_i / (w_i^2 - y) = 0,     s_i = (d . phi_i)^2 / beta,

    with (w_i, phi_i) the mass-normalised short-circuit modes.  One eigensolve,
    no difference of close eigenvalues, and the mu = 0 residual drops to 1e-10
    (i.e. to round-off).  The eigenvector sign cancels inside s_i.
    """
    mdl = f6.assemble(mesh, mt.to_core(mats), Mg)
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
    for _ in range(200):                      # bisection; f is monotone here
        m = 0.5 * (a + b)
        if f(m) > 0:
            b = m
        else:
            a = m
        if b - a <= 1e-15 * w2[0]:
            break
    yo = 0.5 * (a + b)
    f1 = float(np.sqrt(w2[0])) / 2e3 / np.pi
    return (yo - w2[0]) / yo, f1


def fig_flexo_thickness():
    """Size effect: flexoelectric bending coupling vs plate thickness, against
    the thickness-independent piezoelectric coupling of the same plate.

    Why the sweep is built the way it is (docs/FEM6_thickness_sweep.md):

    * Panel (b) used to read the piezo k^2 as argmax over the first 14 modes.
      That returns a different mode at every thickness (index 4 -> 5 -> 7 -> 9)
      and gave the non-monotone 0.458 / 0.452 / 0.313 / 0.362.  It is replaced
      by the mode-free static coupling, which uses no eigenvector at all.
    * Panel (a) used to take the difference of two eigensolves, which is noise
      dominated once the plate is thin; see _modal_k2.  The tabulated build is
      the same plate at every h (L = 200 um, window half-widths 3 x 1 um), 48x4
      with a 96x4 witness at the two ends of the range.
    """
    rows = []
    hs = [10e-6, 5e-6, 2e-6, 1e-6]
    Lb = 200e-6                                        # fixed plate length
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)   # half-widths 3 x 1 um
    # NB: materials.batio3() already carries mu = 1e-6, so the piezo-only
    # columns have to ask for mu = 0 explicitly.
    MUP = mt.batio3("y", "plane_stress")               # poling y -> bending
    MUP0 = mt.Material(**{**MUP.__dict__, "mu": 0.0})
    MUE = mt.Material(**{**mt.batio3("x", "plane_stress").__dict__,
                         "mu": 0.0})                   # poling x -> extensional
    for h in hs:
        row = {"h_um": h * 1e6, "L_um": Lb * 1e6}
        row["k2_flexo"], row["f1_kHz"] = _modal_k2(          # 48 x 4
            f6.mesh_rect(48, 4, Lb, h), MUP, Mg, ("bottom", "top"))
        row["k2_flexo_24"], _ = _modal_k2(                   # 24 x 2
            f6.mesh_rect(24, 2, Lb, h), MUP, Mg, ("bottom", "top"))
        row["k2_floor"], _ = _modal_k2(                      # mu = 0
            f6.mesh_rect(48, 4, Lb, h), MUP0, Mg, ("bottom", "top"))
        if h in (hs[0], hs[-1]):                             # 96 x 4 witness
            row["k2_flexo_96"], _ = _modal_k2(
                f6.mesh_rect(96, 4, Lb, h), MUP, Mg, ("bottom", "top"))
        # panel (b): same 200 um plate, mode-free quasi-static coupling
        row["k2_ext"] = _static_k2(f6.mesh_rect(48, 4, Lb, h), MUE, Mg,
                                   ("left", "right"))
        row["k2_ext_24"] = _static_k2(f6.mesh_rect(24, 2, Lb, h), MUE, Mg,
                                      ("left", "right"))
        rows.append(row)
        wit = (f"  (96x4 {row['k2_flexo_96']:.3e})" if "k2_flexo_96" in row
               else "")
        print(f"  h={h*1e6:4.1f} um: k2_flexo={row['k2_flexo']:.4e}{wit}"
              f"  24x2 {row['k2_flexo_24']:.2e}  floor {row['k2_floor']:+.1e}"
              f"  k2_ext={row['k2_ext']:.5f} (24x2 {row['k2_ext_24']:.5f})"
              f"  f1={row['f1_kHz']:.1f} kHz")

    h = np.array([r["h_um"] for r in rows])
    kf = np.array([r["k2_flexo"] for r in rows])
    print("  local log-log slopes: "
          + ", ".join(f"{(np.log10(kf[i + 1]) - np.log10(kf[i])) / (np.log10(h[i + 1]) - np.log10(h[i])):.2f}"
                      for i in range(len(h) - 1)))
    print(f"  growth over 10 -> 1 um: x{kf[-1]/kf[0]:.1f}"
          f"   (max |k2(mu=0)| = {max(abs(r['k2_floor']) for r in rows):.0e})")

    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.7))
    ax[0].loglog(h, kf, "o-", label=r"$\mu=10^{-6}$ C/m, 48$\times$4")
    ax[0].loglog([r["h_um"] for r in rows if "k2_flexo_96" in r],
                 [r["k2_flexo_96"] for r in rows if "k2_flexo_96" in r],
                 "s", mfc="none", label=r"96$\times$4 witness")
    ax[0].loglog(h, kf[-1] * (h[-1] / h) ** 2, "k-", lw=0.8, alpha=0.45,
                 label=r"slope $-2$ guide")
    ax[0].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[0].set_ylabel(r"$k^2$ (bending)")
    ax[0].invert_xaxis()
    ax[0].legend(frameon=False, fontsize=6.5)
    ax[0].set_title("(a) flexoelectric size effect", fontsize=9.5)

    ke = np.array([r["k2_ext"] for r in rows])
    ax[1].semilogx(h, ke, "s-", label="48$\\times$4")
    ax[1].semilogx(h, [r["k2_ext_24"] for r in rows], "s--", ms=4, lw=0.9,
                   alpha=0.6, label="24$\\times$2")
    ax[1].set_ylim(0.30, 0.40)
    ax[1].text(0.03, 0.05,
               f"{min(ke):.4f} $\\to$ {max(ke):.4f}"
               f"  ({100 * (max(ke) / min(ke) - 1):.2f} % over $10\\to1$ $\\mu$m)",
               transform=ax[1].transAxes, fontsize=6.5)
    ax[1].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[1].set_ylabel(r"$k^2$ (quasi-static, mode-free)")
    ax[1].invert_xaxis()
    ax[1].legend(frameon=False, fontsize=7)
    ax[1].set_title("(b) piezoelectric ($h$-independent)", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_flexo_thickness.png"))
    plt.close(fig)
    return rows


def main():
    print("orientation sweep ...", flush=True)
    rows = oriented_sweep()
    fig_orientation(rows)
    print("memory response ...", flush=True)
    mem = fig_memory()
    print("flexo thickness sweep ...")
    thick = fig_flexo_thickness()
    print("damping ratio ...", flush=True)
    dam = fig_damping()
    print("domain comparison ...", flush=True)
    dom = fig_domain()
    with open(os.path.join(ROOT, "results", "demo.json"), "w") as fh:
        json.dump({"orientation": rows, "memory": mem, "domain": dom,
                   "damping": dam, "flexo_thickness": thick},
                  fh, indent=2)
    print("figures written to results/figures/")


if __name__ == "__main__":
    main()
