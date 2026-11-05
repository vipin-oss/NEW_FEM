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



def fig_flexo_thickness():
    """Size effect: the flexoelectric coupling vs plate thickness, against the
    thickness-independent piezoelectric extensional coupling."""
    import materials as mt
    rows = []
    hs = [10e-6, 5e-6, 2e-6, 1e-6]
    for h in hs:
        mesh = f6.mesh_rect(24, 2, L, h)
        Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
        # (a) bending, through-thickness electrodes, flexo on/off
        out = {}
        for tag, mu in (("mu0", 0.0), ("mu1", 1e-6)):
            core = mt.to_core(mt.Material(**{**mt.batio3("y", "plane_stress").__dict__,
                                             "mu": mu}))
            mdl = f6.assemble(mesh, core, Mg)
            Koc, M, idx, (d, beta) = f6.reduce(mdl, "open", pair=("bottom", "top"))
            Ksc, _, _, _ = f6.reduce(mdl, "short", pair=("bottom", "top"))
            wo, Phi = f6.modes(Koc, M, 4)
            ws, _ = f6.modes(Ksc, M, 4)
            k2 = (wo ** 2 - ws ** 2) / wo ** 2
            tip = int(np.argmax(mesh.nodes[:, 0]))
            row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
            x0 = Phi[:, 0] * (10e-9 / abs(Phi[row, 0]))
            V = float(abs(d @ x0)) / beta
            out[tag] = {"k2_1": float(k2[0]), "f1_kHz": float(wo[0] / 2e3 / np.pi),
                        "V": V}
        # (b) application case: length-extensional piezo
        core = mt.to_core(mt.batio3("x", "plane_stress"))
        mdl = f6.assemble(mesh, core, Mg)
        Koc, M, idx, (d, beta) = f6.reduce(mdl, "open",
                                           pair=("left", "right"))
        Ksc, _, _, _ = f6.reduce(mdl, "short", pair=("left", "right"))
        # thin plates put many bending modes below the extensional one, so ask
        # for more modes; the extensional mode is the one with the largest k^2
        wo, _ = f6.modes(Koc, M, 14)
        ws, _ = f6.modes(Ksc, M, 14)
        k2e = (wo ** 2 - ws ** 2) / wo ** 2
        rows.append({"h_um": h * 1e6,
                     "k2_flexo": out["mu1"]["k2_1"],
                     "k2_bending_piezo": out["mu0"]["k2_1"],
                     "f1_kHz": out["mu1"]["f1_kHz"],
                     "V_10nm": out["mu1"]["V"],
                     "k2_ext": float(np.max(k2e)),
                     "f_ext_kHz": float(wo[int(np.argmax(k2e))] / 2e3 / np.pi)})
        print(f"  h={h*1e6:4.1f} um: k2_flexo={rows[-1]['k2_flexo']:.3e}  "
              f"k2_bend_piezo={rows[-1]['k2_bending_piezo']:.2e}  "
              f"k2_ext={rows[-1]['k2_ext']:.4f}  f1={rows[-1]['f1_kHz']:.1f} kHz")

    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.7))
    h = np.array([r["h_um"] for r in rows])
    kf = np.array([r["k2_flexo"] for r in rows])
    ax[0].loglog(h, kf, "o-", label=r"flexo $k^2$ ($\mu=10^{-6}$ C/m)")
    ax[0].loglog(h, kf[0] * (h[0] / h) ** 2, "k--", lw=1,
                 label=r"slope $-2$ ($\propto h^{-2}$)")
    ax[0].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[0].set_ylabel(r"$k_{\rm eff}^2$ (bending)")
    ax[0].invert_xaxis()
    ax[0].legend(frameon=False, fontsize=7)
    ax[0].set_title("(a) flexoelectric size effect")
    ax[1].semilogx(h, [r["k2_ext"] for r in rows], "s-", label="length-extensional")
    ax[1].semilogx(h, [r["k2_bending_piezo"] for r in rows], "^-",
                   label="bending (piezo only)")
    ax[1].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[1].set_ylabel(r"$k_{\rm eff}^2$")
    ax[1].invert_xaxis()
    ax[1].legend(frameon=False, fontsize=7)
    ax[1].set_title("(b) piezoelectric coupling")
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
