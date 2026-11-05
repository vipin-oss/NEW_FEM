"""
run_paper_figures.py -- the figure set of Paper_12 (FEM-6 manuscript).

Every figure is drawn from a run of the solver in this file or from a JSON
written earlier in the same `run_all.py` invocation; each caption in the paper
says which.  Vector PDF is the deliverable, PNG is written alongside for
quick inspection.

House style
    * STIX (Times-like) for text and maths; on a machine with Times New Roman
      installed, set FIG_FONT = "Times New Roman" below.
    * perceptually uniform, colour-blind-safe maps only (viridis / cividis);
      categorical series use the Okabe-Ito palette.
    * no figure is drawn whose third dimension is not a real variable.

    python3 python/run_paper_figures.py        ~70 s
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D            # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fem6_core as f6          # noqa: E402
import materials as mt          # noqa: E402

FIG = os.path.join(ROOT, "results", "figures", "paper")
os.makedirs(FIG, exist_ok=True)

FIG_FONT = "STIXGeneral"        # Times-like; set to "Times New Roman" if present
plt.rcParams.update({
    "font.family": FIG_FONT,
    "mathtext.fontset": "stix",
    "font.size": 8.5,
    "axes.labelsize": 8.5,
    "axes.titlesize": 8.5,
    "legend.fontsize": 7,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.4,
    "lines.linewidth": 1.2,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,         # embed as TrueType: editable, prints cleanly
    "ps.fonttype": 42,
})

# Okabe-Ito colour-blind-safe categorical palette
OI = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9",
      "#F0E442", "#000000"]

LPLATE, HPLATE = 200e-6, 10e-6


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=300)
    plt.close(fig)
    print(f"    {name}.pdf")


# ---------------------------------------------------------------------------
# physics helpers
# ---------------------------------------------------------------------------
def static_k2(mats, Mg, pair, L=LPLATE, h=HPLATE, nx=24, ny=2):
    """Mode-free quasi-static coupling, K_uu = SHORT-circuit stiffness."""
    mesh = f6.mesh_rect(nx, ny, L, h)
    mdl = f6.assemble(mesh, mt.to_core(mats), Mg)
    Ksc, _, _, _ = f6.reduce(mdl, "short", pair=pair)
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    x = float((S * d) @ np.linalg.solve(Ksc * S[:, None] * S[None, :], S * d))
    return (x / beta) / (1.0 + x / beta)


def modal_k2(mats, Mg, pair, nmodes=6, L=LPLATE, h=HPLATE, nx=24, ny=2):
    """Mode-resolved k^2 from one short-circuit eigensolve (secular root)."""
    mesh = f6.mesh_rect(nx, ny, L, h)
    mdl = f6.assemble(mesh, mt.to_core(mats), Mg)
    Ksc, M, _, _ = f6.reduce(mdl, "short", pair=pair)
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    import scipy.linalg as sla
    w2, y = sla.eigh(Ksc * S[:, None] * S[None, :], M * S[:, None] * S[None, :])
    Phi = S[:, None] * y
    s = (Phi.T @ d) ** 2 / beta

    def f(yy):
        return 1.0 + float(np.sum(s / (w2 - yy)))

    out = []
    for j in range(nmodes):
        a, b = w2[j] * (1 + 1e-12), w2[j + 1] * (1 - 1e-12)
        for _ in range(200):
            m = 0.5 * (a + b)
            if f(m) > 0:
                b = m
            else:
                a = m
        out.append(0.5 * (a + b))
    r = np.array(out)
    return (r - w2[:nmodes]) / r, np.sqrt(w2[:nmodes]) / 2e3 / np.pi, Phi, M, w2


def polar_sweep():
    """f1 and k^2 of the extensional mode versus window angle, for three
    window aspect ratios, and the same for an ellipse of equal M."""
    thetas = np.deg2rad(np.arange(0, 360, 15))
    MAT = mt.Material(**{**mt.batio3("x", "plane_stress").__dict__, "mu": 0.0})
    rows = []
    for AR in (2.0, 3.0, 4.0, 5.0, 7.0, 10.0):
        ax_, ay_ = 3e-6, 3e-6 / AR
        for shape in ("cuboid", "ellipse"):
            if shape == "ellipse":
                if AR != 2.0:            # one ellipse family is enough
                    continue
                a_e = ax_ * np.sqrt(4.0 / 3.0)      # equal M to the cuboid
                b_e = ay_ * np.sqrt(4.0 / 3.0)
            for th in thetas:
                if shape == "cuboid":
                    Mg = f6.second_moment("cuboid", ax_, ay_, th)
                else:
                    Mg = f6.second_moment("ellipse", a_e, b_e, th)
                k2, fk, _, _, _ = modal_k2(MAT, Mg, ("left", "right"),
                                           nmodes=6)
                j = int(np.argmax(k2))
                rows.append({"AR": AR, "shape": shape,
                             "theta_deg": float(np.rad2deg(th)),
                             "f1_kHz": float(fk[0]),
                             "k2_axial": float(k2[j]),
                             "f_axial_kHz": float(fk[j]),
                             "Mg_xx": float(Mg[0, 0]), "Mg_yy": float(Mg[1, 1])})
    return rows




# ---------------------------------------------------------------------------
# P1  the two electrode configurations and the window
# ---------------------------------------------------------------------------
def fig_p1_geometry():
    fig, axs = plt.subplots(2, 1, figsize=(5.2, 2.7))
    L_, H_ = 1.0, 0.30
    for k, (ax, name, econf) in enumerate(zip(
            axs, ("(a) bending: through-thickness electrodes",
                  "(b) extensional: end electrodes"),
            ("tb", "lr"))):
        ax.add_patch(Rectangle((0, 0), L_, H_, fc="#eef3f8", ec="k", lw=0.9))
        ax.add_patch(Rectangle((-0.03, 0), 0.03, H_, fc="0.3", ec="k", lw=0.7))
        for yy in np.linspace(0.012, H_ - 0.012, 7):
            ax.plot([-0.03, 0.0], [yy, yy + 0.028], color="k", lw=0.45)
        if econf == "tb":
            ax.add_patch(Rectangle((0, -0.022), L_, 0.022, fc=OI[1],
                                   alpha=0.6, ec="none"))
            ax.add_patch(Rectangle((0, H_), L_, 0.022, fc=OI[1],
                                   alpha=0.6, ec="none"))
            ax.text(L_ / 2, -0.034, r"earthed, $V=0$", ha="center", va="top",
                    fontsize=6.5)
            ax.text(L_ / 2, H_ + 0.032, r"floating, $q=0$", ha="center",
                    va="bottom", fontsize=6.5)
        else:
            for xx in (0.0, L_):
                ax.add_patch(Rectangle((xx - (0.012 if xx == 0 else 0), 0),
                                        0.012, H_, fc=OI[1], alpha=0.6,
                                        ec="none"))
            ax.text(0.02, H_ / 2, r"$V=0$", fontsize=6.5, va="center")
            ax.text(L_ - 0.02, H_ / 2, r"$V$, $q=0$", fontsize=6.5,
                    va="center", ha="right")
        cx, cy = 0.52, H_ / 2
        ax.add_patch(Rectangle((cx - 0.10, cy - 0.035), 0.20, 0.07, fill=False,
                               ec=OI[0], lw=1.4))
        ax.add_patch(Ellipse((cx, cy), 0.20 * np.sqrt(3 / 4),
                             0.07 * np.sqrt(3 / 4), fill=False, ec=OI[2],
                             lw=1.4, ls="--"))
        ax.annotate(r"cuboid: $M_{ii}=a_i^2/3$", (cx + 0.085, cy + 0.033),
                    xytext=(cx + 0.14, cy + 0.085), fontsize=5.8,
                    arrowprops=dict(arrowstyle="-", lw=0.4, color="0.35"))
        ax.annotate(r"ellipse (equal $M$)", (cx - 0.09, cy - 0.028),
                    xytext=(cx - 0.30, cy - 0.095), fontsize=5.8,
                    arrowprops=dict(arrowstyle="-", lw=0.4, color="0.35"))
        ax.set_xlim(-0.07, L_ + 0.07)
        ax.set_ylim(-0.115, H_ + 0.075)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(name, fontsize=7.5, pad=1)
    fig.text(0.5, -0.02, r"$L=200\ \mu$m, thickness $h$; window half-widths "
             r"$a_1\times a_2$, $M_{ii}=a_i^2/3$ (cuboid), $a_i^2/4$ (ellipse)",
             ha="center", fontsize=6.5)
    save(fig, "P1_geometry")


# ---------------------------------------------------------------------------
# P2  petals
# ---------------------------------------------------------------------------
def fig_p2_petals(pol, ARS=(2.0, 5.0, 10.0)):
    th = np.deg2rad(np.arange(0, 360, 15))
    tt = np.r_[th, th[0]]

    def series(AR, key, shape="cuboid"):
        r = sorted([x for x in pol if x["AR"] == AR and x["shape"] == shape],
                   key=lambda z: z["theta_deg"])
        return np.r_[[z[key] for z in r], r[0][key]]

    fig = plt.figure(figsize=(6.8, 2.35))
    fig.subplots_adjust(wspace=0.42, left=0.02, right=0.90, bottom=0.14,
                        top=0.84)
    # (a) f1
    ax = fig.add_subplot(131, projection="polar")
    off = 145.0
    for i, AR in enumerate(ARS):
        v = series(AR, "f1_kHz") - off
        ax.plot(tt, v, color=OI[i], lw=1.3, label=f"AR = {AR:g}")
    ax.set_theta_zero_location("E")
    ax.set_rlabel_position(62)
    ax.set_rticks([5, 10])
    ax.set_yticklabels(["150", "155"], fontsize=5.5)
    ax.set_title(r"$f_1$ (kHz) $-\,145$", fontsize=7.5, pad=7)
    ax.tick_params(labelsize=5.5)
    ax.grid(alpha=0.3, lw=0.4)
    # (b) k2
    ax2 = fig.add_subplot(132, projection="polar")
    off2 = 0.355
    for i, AR in enumerate(ARS):
        v = series(AR, "k2_axial") - off2
        ax2.plot(tt, v, color=OI[i], lw=1.3)
    ax2.set_theta_zero_location("E")
    ax2.set_rlabel_position(62)
    ax2.set_rticks([0.02, 0.06, 0.10])
    ax2.set_yticklabels(["0.375", "0.415", "0.455"], fontsize=5.5)
    ax2.set_title(r"$k^2$ $-\,0.355$", fontsize=7.5, pad=7)
    ax2.tick_params(labelsize=5.5)
    ax2.grid(alpha=0.3, lw=0.4)
    # (c) cuboid vs ellipse at equal M
    ax3 = fig.add_subplot(133, projection="polar")
    for i, (shape, lab, ls) in enumerate((("cuboid", r"cuboid, $a_i^2/3$", "-"),
                                          ("ellipse", r"ellipse, equal $M$",
                                           "--"))):
        v = series(2.0, "k2_axial", shape) - off2
        ax3.plot(tt, v, ls, color=OI[0] if i == 0 else OI[2], lw=1.4,
                 label=lab)
    ax3.set_theta_zero_location("E")
    ax3.set_rlabel_position(62)
    ax3.set_rticks([0.02, 0.06, 0.10])
    ax3.set_yticklabels(["0.375", "0.415", "0.455"], fontsize=5.5)
    ax3.set_title(r"$k^2$: same $M$, two shapes", fontsize=7.5, pad=7)
    ax3.tick_params(labelsize=5.5)
    ax3.grid(alpha=0.3, lw=0.4)
    h, l = ax.get_legend_handles_labels()
    h2, l2 = ax3.get_legend_handles_labels()
    fig.legend(h + h2, l + l2, loc="center left", bbox_to_anchor=(0.905, 0.45),
               frameon=False, fontsize=6.5)
    save(fig, "P2_petals")


# ---------------------------------------------------------------------------
# P3  surface k^2(AR, theta)
# ---------------------------------------------------------------------------
def fig_p3_map(pol):
    """k^2 and f1 over the (window angle, aspect ratio) plane.

    Drawn as a filled contour map rather than a perspective surface: the
    quantity is a function of two variables, and a surface of a strongly
    one-dimensional function (it varies three times more with theta than with
    AR) reads as cliffs in perspective and hides the structure.  The dots are
    the 144 actual solver runs; the contours are a periodic spline through
    them.
    """
    from scipy.interpolate import RectBivariateSpline
    ARs = np.array([2.0, 3.0, 4.0, 5.0, 7.0, 10.0])
    ths = np.arange(0, 360, 15)
    Zk = np.zeros((len(ths), len(ARs)))
    Zf = np.zeros((len(ths), len(ARs)))
    for j, AR in enumerate(ARs):
        r = sorted([x for x in pol if x["AR"] == AR and x["shape"] == "cuboid"],
                   key=lambda z: z["theta_deg"])
        Zk[:, j] = [z["k2_axial"] for z in r]
        Zf[:, j] = [z["f1_kHz"] for z in r]
    lA = np.log10(ARs)
    the = np.r_[-45, -30, -15, ths, 360, 375, 390]

    def fine(Z):
        ext = np.vstack([Z[-3:], Z, Z[:3]])
        spl = RectBivariateSpline(the, lA, ext, kx=3, ky=3, s=0)
        tf = np.linspace(0, 360, 241)
        Af = np.linspace(lA[0], lA[-1], 81)
        return tf, Af, spl(tf, Af)

    fig, axs = plt.subplots(2, 1, figsize=(4.6, 3.6), sharex=True)
    TT, AA = np.meshgrid(ths, lA, indexing="ij")
    for ax, Z, lab, cm in ((axs[0], Zk, r"$k^2$", "viridis"),
                           (axs[1], Zf, r"$f_1$ (kHz)", "cividis")):
        tf, Af, Zg = fine(Z)
        T, A = np.meshgrid(tf, Af, indexing="ij")
        cf = ax.contourf(T, A, Zg, levels=18, cmap=cm)
        cs = ax.contour(T, A, Zg, levels=7, colors="k", linewidths=0.4)
        ax.clabel(cs, fontsize=5, fmt="%.3g" if Z is Zk else "%.0f")
        ax.scatter(TT.ravel(), AA.ravel(), s=1.5, c="w", alpha=0.65,
                   linewidths=0)
        ax.set_yticks(lA)
        ax.set_yticklabels(["2", "3", "4", "5", "7", "10"])
        ax.set_ylabel("aspect ratio")
        fig.colorbar(cf, ax=ax, pad=0.02, label=lab)
        ax.grid(False)
    axs[1].set_xlabel(r"window angle $\theta$ (deg)")
    axs[0].set_title(r"window anisotropy: 144 runs, periodic spline",
                     fontsize=7.5)
    save(fig, "P3_map_k2_AR_theta")


# ---------------------------------------------------------------------------
# P4  deformed mode, coloured by the open-circuit potential
# ---------------------------------------------------------------------------
def fig_p4_modeshape():
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    mesh = f6.mesh_rect(48, 4, LPLATE, HPLATE)
    mat = mt.batio3("y", "plane_stress")
    mdl = f6.assemble(mesh, mt.to_core(mat), Mg)
    Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=("bottom", "top"))
    Koc, _, _, (d, beta) = f6.reduce(mdl, "open", pair=("bottom", "top"))
    ws, Phi = f6.modes(Ksc, M, 3)
    phi_mode = Phi[:, 0].copy()
    # normalise the mode so that the peak transverse displacement is 10 nm
    vpeak = np.abs(phi_mode[[np.searchsorted(idx, mdl.mech_dof[n][4])
                             for n in range(mesh.nnode)]]).max()
    scale_nm = 10.0 / vpeak
    phi_mode *= scale_nm * 1e-9
    V = float(d @ phi_mode) / beta

    allp = np.arange(mdl.ndof_phi)
    bot, top = mdl.electrodes["bottom"], mdl.electrodes["top"]
    inter = np.setdiff1d(np.setdiff1d(allp, bot), top)
    u_full = np.zeros(mdl.ndof_mech)
    u_full[idx] = phi_mode
    b = mdl.B.T @ u_full
    Cin = mdl.Cphi[np.ix_(inter, inter)]
    Cif = mdl.Cphi[np.ix_(inter, np.r_[bot, top])]
    phi_f = np.r_[np.zeros(len(bot)), np.full(len(top), V)]
    phi = np.zeros(mdl.ndof_phi)
    phi[inter] = np.linalg.solve(Cin, b[inter] - Cif @ phi_f)
    phi[top] = V

    phin = 1e3 * np.array([phi[int(mdl.phi_dof[n])] if mdl.phi_dof[n] >= 0
                           else 0.0 for n in range(mesh.nnode)])
    v_disp = np.array([u_full[mdl.mech_dof[n][4]] for n in range(mesh.nnode)])
    X = mesh.nodes[:, 0] * 1e6
    Y = mesh.nodes[:, 1] * 1e6
    Zs = v_disp.reshape(5, 49)
    Ps = phin.reshape(5, 49)
    Xs = X.reshape(5, 49)
    Ys = Y.reshape(5, 49)
    magn = 1.0e9                            # 10 nm -> 10 um on the axis
    fig = plt.figure(figsize=(4.9, 3.1))
    ax = fig.add_subplot(111, projection="3d")
    cmap = plt.get_cmap("viridis")
    norm = matplotlib.colors.Normalize(vmin=0.0, vmax=Ps.max())
    ax.plot_surface(Xs, Ys, Zs * magn * 1e3, facecolors=cmap(norm(Ps)),
                    rstride=1, cstride=1, linewidth=0.15,
                    edgecolor=(0, 0, 0, 0.3), antialiased=True, shade=False)
    ax.set_xlabel(r"$x$ ($\mu$m)", labelpad=0)
    ax.set_ylabel(r"$y$ ($\mu$m)", labelpad=0)
    ax.set_zlabel(r"$v\times10^{9}$ ($\mu$m)", labelpad=4, fontsize=6.5)
    ax.view_init(elev=25, azim=-68)
    ax.set_box_aspect((3.3, 1.2, 1.45))
    ax.tick_params(labelsize=5.5, pad=0)
    ax.zaxis.set_tick_params(labelsize=5.5, pad=0)
    ax.set_yticks([0, 5, 10])
    ax.set_zticks([0, 4, 8, 12])
    ax.grid(True, lw=0.3, alpha=0.5)
    sm = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", shrink=0.62,
                      pad=0.015, aspect=34)
    cb.set_label(r"$\phi$ (mV), open circuit", fontsize=7)
    cb.ax.tick_params(labelsize=5.5, pad=1)
    save(fig, "P4_mode_shape_potential")
    return {"V_open_V": V, "magnification": float(magn * 1e3),
            "u_peak_nm": 10.0}


# ---------------------------------------------------------------------------
# P5  root locus
# ---------------------------------------------------------------------------
def fig_p5_rootlocus():
    from matplotlib.collections import LineCollection
    alphas = np.linspace(0.2, 1.0, 25)
    w0 = 2 * np.pi * 6.7273e6
    taus = [0.5e-9, 1e-9, 2e-9, 4e-9, 8e-9, 16e-9, 32e-9]
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    cmap = plt.get_cmap("viridis")
    for i, tau in enumerate(taus):
        s = []
        s0 = None
        for a in alphas:                      # continuation: keep the branch
            z = complex(f6.complex_frequency(w0, tau, a, s0=s0))
            s0 = z
            s.append(z)
        s = np.array(s)
        x = -s.real / w0
        y = np.abs(s.imag) / w0
        ok = x > 0
        pts = np.array([x[ok], y[ok]]).T.reshape(-1, 1, 2)
        segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
        lc = LineCollection(segs, cmap=cmap,
                            array=np.linspace(0.2, 1.0, len(segs)))
        lc.set_linewidth(1.5)
        ax.add_collection(lc)
        ax.plot(x[ok][-1], y[ok][-1], "o", ms=3.2, mfc="w", mec="0.2", mew=0.5)
        ax.annotate(rf"{tau*1e9:g} ns", (x[ok][-1], y[ok][-1]),
                    textcoords="offset points", xytext=(4, 2), fontsize=5.5)
    ax.set_xscale("log")
    ax.set_xlim(3e-3, 1.2)
    ax.set_ylim(0.85, 2.25)
    ax.axhline(1.0, color="0.6", lw=0.6, ls=":")
    ax.set_xlabel(r"$-\mathrm{Re}\,s/\omega_0$  (damping)")
    ax.set_ylabel(r"$|\mathrm{Im}\,s|/\omega_0$")
    sm = matplotlib.cm.ScalarMappable(
        cmap=cmap, norm=matplotlib.colors.Normalize(0.2, 1.0))
    fig.colorbar(sm, ax=ax, shrink=0.85, pad=0.03, label=r"$\alpha$")
    ax.set_title(r"open marker: $\alpha=1$; colour: $\alpha$", fontsize=6.8)
    save(fig, "P5_root_locus")


# ---------------------------------------------------------------------------
# P6  waterfall
# ---------------------------------------------------------------------------
def fig_p6_waterfall():
    """Ring-down for four Caputo orders.

    Drawn as coloured time traces rather than a 3-D waterfall: with four
    orders the perspective view is dominated by the overlapping of the traces
    and the alpha axis carries no more information than the colour does.
    """
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    mesh = f6.mesh_rect(24, 2, LPLATE, HPLATE)
    mdl = f6.assemble(mesh, mt.to_core(mt.batio3("x", "plane_stress")), Mg)
    Koc, M, idx, (d, beta) = f6.reduce(mdl, "open", pair=("left", "right"))
    ws, Phi = f6.modes(Koc, M, 8)
    k2, _, _, _, _ = modal_k2(mt.batio3("x", "plane_stress"), Mg,
                              ("left", "right"), nmodes=8)
    j = int(np.argmax(k2))
    tip = int(np.argmax(mesh.nodes[:, 0]))
    row = int(np.searchsorted(idx, mdl.mech_dof[tip][0]))
    x0 = Phi[:, j] * (10e-9 / abs(Phi[row, j]))
    tau = 3e-9
    alphas = [1.0, 0.9, 0.7, 0.5]
    T = 10 * 2 * np.pi / ws[j]
    N = 4000
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.5))
    cmap = plt.get_cmap("cividis")
    out = {"tau_s": tau, "mode_index": j + 1,
           "f_kHz": float(ws[j] / 2e3 / np.pi),
           "V0": float(abs(d @ x0) / beta)}
    for i, a in enumerate(alphas):
        t, x, y, v, acc = f6.transient(Koc, M, Koc, np.zeros(idx.size), a, tau,
                                       T / N, N, nmodes=8, x0=x0,
                                       v0=np.zeros(idx.size))
        u = (Phi[row, :] @ y) * 1e9
        V = (d @ Phi) @ y / beta
        c = cmap(i / (len(alphas) - 1))
        ax[0].plot(t * 1e6, u, color=c, lw=1.1, label=rf"$\alpha={a:g}$")
        ax[1].plot(t * 1e6, V, color=c, lw=1.1)
        # log-decrement estimate on the first two positive peaks
        pk = [n for n in range(1, len(u) - 1)
              if u[n] > u[n - 1] and u[n] > u[n + 1] and u[n] > 0]
        if len(pk) >= 2:
            out[f"zeta_{a}"] = float(np.log(u[pk[0]] / u[pk[1]]) / (2 * np.pi))
    ax[0].set_xlabel(r"$t$ ($\mu$s)")
    ax[0].set_ylabel(r"$u_{\rm tip}$ (nm)")
    ax[1].set_xlabel(r"$t$ ($\mu$s)")
    ax[1].set_ylabel(r"$V_{\rm oc}$ (V)")
    ax[0].legend(frameon=False, fontsize=6.5, ncol=2)
    ax[0].set_title("(a) tip displacement", fontsize=7.5)
    ax[1].set_title("(b) open-circuit voltage", fontsize=7.5)
    save(fig, "P6_ringdown")
    return out


# ---------------------------------------------------------------------------
# P7  thickness
# ---------------------------------------------------------------------------
def fig_p7_thickness(thick, closed_form):
    h = np.array([r["h_um"] for r in thick])
    kf = np.array([r["k2_flexo"] for r in thick])
    ke = np.array([r["k2_ext"] for r in thick])
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.6),
                           gridspec_kw={"width_ratios": [1.15, 1]})
    ax[0].loglog(h, kf, "o-", color=OI[0], label=r"flexo $k^2$ (48$\times$4)")
    ax[0].loglog([r["h_um"] for r in thick if "k2_flexo_96" in r],
                 [r["k2_flexo_96"] for r in thick if "k2_flexo_96" in r],
                 "s", mfc="none", ms=5.5, color=OI[1], label=r"96$\times$4")
    ax[0].loglog(h, kf[-1] * (h[-1] / h) ** 2, "k:", lw=0.8, alpha=0.6,
                 label=r"$h^{-2}$")
    for i in range(len(h) - 1):
        sl = ((np.log10(kf[i + 1]) - np.log10(kf[i])) /
              (np.log10(h[i + 1]) - np.log10(h[i])))
        xm = np.sqrt(h[i] * h[i + 1])
        ym = np.sqrt(kf[i] * kf[i + 1])
        ax[0].annotate(f"{sl:.2f}", (xm, ym), textcoords="offset points",
                       xytext=(4, -12), fontsize=6.5, color=OI[0])
    ax[0].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[0].set_ylabel(r"$k^2$ (bending)")
    ax[0].invert_xaxis()
    ax[0].legend(frameon=False, fontsize=6.5, loc="upper left")
    ax[0].set_title("(a) flexoelectric, local slope", fontsize=7.5)
    ax[1].semilogx(h, ke, "s-", color=OI[2], label=r"FEM, 48$\times$4")
    ax[1].semilogx(h, [r["k2_ext_24"] for r in thick], "s--", ms=4, lw=0.9,
                   alpha=0.7, color=OI[3], label=r"FEM, 24$\times$2")
    ax[1].axhline(closed_form, color="k", lw=0.9, ls=":",
                  label=r"$e^{\mathrm{T}}C^{-1}e/\kappa$")
    ax[1].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[1].set_ylabel(r"$k^2$ (quasi-static)")
    ax[1].invert_xaxis()
    ax[1].set_ylim(0.545, 0.575)
    ax[1].legend(frameon=False, fontsize=6.2, loc="lower left")
    ax[1].set_title("(b) piezoelectric, independent of $h$", fontsize=7.5)
    save(fig, "P7_thickness")


# ---------------------------------------------------------------------------
# P8  mode tracking
# ---------------------------------------------------------------------------
def fig_p8_mac(mt_data):
    rows = mt_data["rows"]
    hs = np.array([r["h_um"] for r in rows])
    macs = np.array([r["mac_mode1_vs_ref"] for r in rows])
    f1 = np.array([r["f_kHz"][0] for r in rows])
    fig, ax = plt.subplots(1, 2, figsize=(6.4, 2.4),
                           gridspec_kw={"width_ratios": [1.2, 1]})
    ax[0].bar(np.arange(len(hs)), 1.0 - macs, color=OI[0], width=0.55)
    ax[0].set_xticks(np.arange(len(hs)))
    ax[0].set_xticklabels([f"{x:.0f}" for x in hs])
    ax[0].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[0].set_ylabel(r"$1-$MAC  (defect from the $h$=10 $\mu$m shape)")
    ax[0].set_yscale("log")
    ax[0].set_ylim(1e-7, 3e-3)
    for i, m in enumerate(macs):
        ax[0].text(i, max(1.0 - m, 1.3e-7) * 1.35, f"{m:.5f}", ha="center",
                   fontsize=6)
    ax[0].set_title("(a) one shape at every thickness", fontsize=7.5)
    f2 = np.array([r["f_kHz"][1] for r in rows])
    rat = np.array([r["f_ratio_2_over_1"] for r in rows])
    ax[1].loglog(hs, f1, "o-", color=OI[1], ms=4, lw=1.1, label=r"$f_1$")
    ax[1].loglog(hs, f2, "s-", color=OI[0], ms=3.6, lw=1.1, label=r"$f_2$")
    ax[1].invert_xaxis()
    for i in range(hs.size):
        ax[1].annotate(rf"{rat[i]:.2f}", (hs[i], f1[i]),
                       textcoords="offset points", xytext=(3.5, -9),
                       fontsize=5.8, color=OI[1])
    ax[1].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[1].set_ylabel("frequency (kHz)")
    ax[1].legend(frameon=False, fontsize=6.2, loc="lower left")
    ax[1].set_title(r"(b) $f_2/f_1$ (labels) never approaches 1",
                    fontsize=7.5)
    save(fig, "P8_mode_tracking")


# ---------------------------------------------------------------------------
# P9  damping surface
# ---------------------------------------------------------------------------
def fig_p9_damping_surface():
    al = np.linspace(0.2, 1.0, 17)
    wt = np.logspace(-1.5, 1.5, 25)
    Z = np.zeros((len(al), len(wt)))
    for j, a in enumerate(al):
        s0 = None
        for i, x in enumerate(wt):
            s = complex(f6.complex_frequency(1.0, x, a, s0=s0))
            s0 = s
            Z[j, i] = -s.real / abs(s)
    A, W = np.meshgrid(al, wt, indexing="ij")
    fig = plt.figure(figsize=(4.4, 3.1))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(A, np.log10(W), Z, cmap="cividis", rstride=1,
                           cstride=1, linewidth=0.2, edgecolor="0.3",
                           alpha=0.96)
    ax.contour(A, np.log10(W), Z, zdir="z", offset=-0.06, levels=12,
               cmap="cividis", linewidths=0.7)
    ax.set_xlabel(r"$\alpha$", labelpad=1)
    ax.set_ylabel(r"$\log_{10}\omega\tau$", labelpad=1)
    ax.set_zlabel(r"$\zeta$", labelpad=1)
    ax.set_zlim(0.0, 1.02)
    ax.view_init(elev=32, azim=-118)
    ax.tick_params(labelsize=6, pad=-1)
    ax.set_zlim(-0.06, 1.02)
    # the validity window of the element: omega*tau <= 1 (Sec. limits)
    al_band = np.array([[0.2, 1.0], [0.2, 1.0]])
    ax.plot_surface(al_band, np.array([[-1.5, -1.5], [0.0, 0.0]]),
                    np.full((2, 2), -0.062), color="0.30", alpha=0.30,
                    linewidth=0, shade=False)
    ax.plot([0.2, 1.0], [0.0, 0.0], [-0.061, -0.061], ls="--", lw=1.1,
            color="k")
    ax.text2D(0.012, 0.995, "shaded floor: " r"$\omega\tau\leq1$, the band "
              "used here\n" r"unshaded: $\omega\tau>1$, not claimed",
              transform=ax.transAxes, fontsize=5.8, va="top", color="0.15",
              linespacing=1.35)
    fig.colorbar(surf, ax=ax, shrink=0.55, pad=0.06, label=r"$\zeta$")
    save(fig, "P9_damping_surface")


# ---------------------------------------------------------------------------
# P10 window size
# ---------------------------------------------------------------------------
def fig_p10_window():
    mesh = f6.mesh_rect(20, 4, 1.0, 0.2)
    mat = f6.isotropic_plane_strain(2e11, 0.3, 7850)

    def ur(Mg, grad):
        m = f6.assemble(mesh, mat, Mg, gradient=grad)
        K, Ms, idx, _ = f6.reduce(m, "short")
        f = m.edge_traction(tx=1e6)
        U = np.zeros(m.ndof_mech)
        U[idx] = np.linalg.solve(K, f[idx])
        right = [n for n, xy in enumerate(mesh.nodes) if abs(xy[0] - 1) < 1e-12]
        return float(np.mean([U[m.mech_dof[n][0]] for n in right]))

    u0 = ur(np.zeros((2, 2)), False)
    ls = np.linspace(0.01, 0.20, 12)
    y1 = np.array([ur(f6.second_moment("ellipsoid", l, l), True) / u0 for l in ls])
    y2 = np.array([ur(f6.second_moment("cuboid", l, l), True) / u0 for l in ls])
    y3 = np.array([ur(f6.second_moment("cuboid", l * np.sqrt(3 / 5),
                                       l * np.sqrt(3 / 5)), True) / u0
                   for l in ls])
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.plot(ls, y1, "-", color=OI[0], lw=1.6, label="ellipsoid, semi-axis $l$")
    ax.plot(ls, y2, "-", color=OI[1], lw=1.6, label="cuboid, half-width $l$")
    ax.plot(ls, y3, "--", color=OI[2], lw=1.5,
            label=r"cuboid, equal $M$ ($a=l\sqrt{3/5}$)")
    ax.annotate(f"{y1[-1]:.3f}", (ls[-1], y1[-1]), xytext=(-24, 4),
                textcoords="offset points", fontsize=6.5, color=OI[0])
    ax.annotate(f"{y2[-1]:.3f}", (ls[-1], y2[-1]), xytext=(-24, -10),
                textcoords="offset points", fontsize=6.5, color=OI[1])
    ax.annotate(f"{y3[-1]:.3f}", (ls[-1], y3[-1]), xytext=(-24, -2),
                textcoords="offset points", fontsize=6.5, color=OI[2])
    ax.set_xlabel(r"$l/L_x$")
    ax.set_ylabel(r"$u_R/u_{R,\rm classical}$")
    ax.legend(frameon=False, fontsize=6.5)
    save(fig, "P10_window_shape")


def main():
    import time
    t0 = time.time()
    only = [a for a in sys.argv[1:] if a.startswith("P")]
    if only:
        # redraw a subset from the stored sweep -- handy while polishing
        with open(os.path.join(ROOT, "results", "paper_figures_data.json")) as fh:
            pol = json.load(fh)["polar"]
        figs = {"P1": lambda p: fig_p1_geometry(), "P2": fig_p2_petals,
                "P3": fig_p3_map, "P4": lambda p: fig_p4_modeshape(),
                "P5": lambda p: fig_p5_rootlocus(),
                "P6": lambda p: fig_p6_waterfall(),
                "P9": lambda p: fig_p9_damping_surface(),
                "P10": lambda p: fig_p10_window()}
        for k in only:
            if k in figs:
                figs[k](pol)
                print(f"    {k} redrawn")
        return 0
    print("  polar sweep")
    pol = polar_sweep()
    print("  figures")
    fig_p1_geometry()
    fig_p2_petals(pol)
    fig_p3_map(pol)
    info = {"P4": fig_p4_modeshape()}
    fig_p5_rootlocus()
    info["P6"] = fig_p6_waterfall()
    with open(os.path.join(ROOT, "results", "demo.json")) as fh:
        demo = json.load(fh)
    with open(os.path.join(ROOT, "results", "coupling_check.json")) as fh:
        cc = json.load(fh)
    fig_p7_thickness(demo["flexo_thickness"], cc["closed_form"]["k2_2d_closed"])
    with open(os.path.join(ROOT, "results", "mode_tracking.json")) as fh:
        mtdata = json.load(fh)
    fig_p8_mac(mtdata)
    fig_p9_damping_surface()
    fig_p10_window()
    with open(os.path.join(ROOT, "results", "paper_figures_data.json"), "w") as fh:
        json.dump({"polar": pol, "notes": info}, fh, indent=1)
    print(f"  done in {time.time() - t0:.0f} s -> results/figures/paper/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
