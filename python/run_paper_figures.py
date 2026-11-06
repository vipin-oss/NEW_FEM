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
    """Write the vector PDF and a PNG preview, and keep the copy that the
    manuscript includes in Paper_12/figures."""
    import shutil
    for d in (FIG, os.path.join(ROOT, "Paper_12", "figures")):
        os.makedirs(d, exist_ok=True)
        fig.savefig(os.path.join(d, name + ".pdf"))
        fig.savefig(os.path.join(d, name + ".png"), dpi=220)
    plt.close(fig)
    print(f"    {name}.pdf")
    return os.path.join(FIG, name + ".pdf")

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


def _mode_free(MAT, Mg, pair=("left", "right")):
    """Coupling of the extensional mode and the frequencies of that mode and of
    the fundamental one."""
    k2, fk, _, _, _ = modal_k2(MAT, Mg, pair, nmodes=6)
    j = int(np.argmax(k2))
    return float(k2[j]), float(fk[j]), float(fk[0])


def polar_sweep():
    """f1 and k2 versus window angle on 0-90 deg in 5 deg steps.

    Only the first quadrant is computed.  The plate is invariant under
    theta -> theta + 180 (the second-moment tensor of a rectangle is
    unchanged, because R(theta + 180) = -R(theta)) and under theta -> -theta
    (the reflection y -> -y maps the plate onto itself and flips the sign of
    M12, which enters the energy quadratically).  Neither statement is
    assumed: both are checked below against the computed points at the two
    extreme aspect ratios, and the sizes of the deviations are stored with the
    data.
    """
    thetas = np.arange(0, 91, 5)
    ARS = (2.0, 3.0, 4.0, 5.0, 7.0, 10.0)
    MAT = mt.Material(**{**mt.batio3("x", "plane_stress").__dict__, "mu": 0.0})
    rows = []
    for AR in ARS:
        ax_, ay_ = 3e-6, 3e-6 / AR
        for shape in ("cuboid", "ellipse"):
            if shape == "ellipse" and AR != 2.0:
                continue
            if shape == "ellipse":
                a_e, b_e = ax_ * np.sqrt(4.0 / 3.0), ay_ * np.sqrt(4.0 / 3.0)
            for td in thetas:
                th = np.deg2rad(td)
                if shape == "cuboid":
                    Mg = f6.second_moment("cuboid", ax_, ay_, th)
                else:
                    Mg = f6.second_moment("ellipse", a_e, b_e, th)
                k2, fe, f1 = _mode_free(MAT, Mg)
                rows.append({"AR": AR, "shape": shape, "theta_deg": float(td),
                             "f1_kHz": f1, "k2_axial": k2, "f_ext_kHz": fe,
                             "Mg_xx": float(Mg[0, 0]), "Mg_yy": float(Mg[1, 1])})
    lookup = {(r["AR"], r["shape"], r["theta_deg"]): r for r in rows}
    sym = []
    for AR in (2.0, 10.0):
        ax_, ay_ = 3e-6, 3e-6 / AR
        for td in (15, 30, 45, 60, 75, 85):
            ref = lookup[(AR, "cuboid", float(td))]
            for ang, label in ((td + 180.0, "theta+180"), (-td, "-theta")):
                Mg = f6.second_moment("cuboid", ax_, ay_, np.deg2rad(ang))
                k2, fe, f1 = _mode_free(MAT, Mg)
                sym.append({"AR": AR, "theta_deg": float(td), "map": label,
                            "rel_k2": abs(k2 - ref["k2_axial"]) / ref["k2_axial"],
                            "rel_f": abs(fe - ref["f_ext_kHz"])
                            / ref["f_ext_kHz"]})
    worst = max(max(s["rel_k2"], s["rel_f"]) for s in sym)
    print(f"  symmetry: {len(sym)} mirrored solves, worst relative "
          f"deviation {worst:.2e}")
    return rows, sym

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
    save(fig, "F1_geometry")


# ---------------------------------------------------------------------------
# P2  petals
# ---------------------------------------------------------------------------
def _fold(rows, AR, key, shape="cuboid"):
    """Full circle from the first quadrant, using the two verified symmetries.

    Returns the computed angles and values on 0-90 deg, a dense 0-360 deg grid,
    the smoothed curve on that grid, and the mirror images of the computed
    points (which is where the markers go).
    """
    from scipy.interpolate import CubicSpline
    half = sorted([r for r in rows if r["AR"] == AR and r["shape"] == shape],
                  key=lambda z: z["theta_deg"])
    th = np.array([r["theta_deg"] for r in half], float)
    v = np.array([r[key] for r in half], float)
    th180 = np.r_[th, 180.0 - th[-2:0:-1]]
    v180 = np.r_[v, v[-2:0:-1]]
    cs = CubicSpline(np.r_[th180, 180.0], np.r_[v180, v[0]], bc_type="periodic")
    dense = np.linspace(0.0, 360.0, 1441)
    smooth = cs(np.mod(dense, 180.0))
    mk_t = np.r_[th, 180.0 - th, 180.0 + th, 360.0 - th]
    mk_v = np.r_[v, v, v, v]
    return th, v, dense, smooth, mk_t, mk_v


def _polarmap(rows, key, nar=61, nth=361):
    """Smooth map of key(theta, AR) on the full circle, from the quadrant."""
    from scipy.interpolate import CubicSpline
    ars = sorted({r["AR"] for r in rows})
    thf = np.linspace(0.0, 360.0, nth)
    Z = np.zeros((len(ars), nth))
    for i, AR in enumerate(ars):
        _, _, dense, smooth, _, _ = _fold(rows, AR, key)
        Z[i] = CubicSpline(dense, smooth)(thf)
    ar_f = np.geomspace(min(ars), max(ars), nar)
    Zf = np.zeros((nar, nth))
    for j in range(nth):
        Zf[:, j] = np.interp(np.log10(ar_f), np.log10(ars), Z[:, j])
    return thf, ar_f, Zf


def fig_orientation(pol):
    """Window orientation: normalised polar sections of f1 and k2, and their
    maps over the aspect ratio."""
    ARS = (2.0, 5.0, 10.0)
    fig = plt.figure(figsize=(6.9, 6.1))
    gs = fig.add_gridspec(2, 2, hspace=0.30, wspace=0.46,
                          left=0.075, right=0.955, top=0.95, bottom=0.075)
    cfg = (("f_ext_kHz", (0.945, 1.090), [0.95, 1.05], r"$f_{\rm ext}/f_{\rm ext}(0)$"),
           ("k2_axial", (0.74, 1.025), [0.8, 0.9], r"$k^2/k^2(0)$"))
    for k, (key, rlim, rticks, rlab) in enumerate(cfg):
        ax = fig.add_subplot(gs[0, k], projection="polar")
        ref = None
        for i, AR in enumerate(ARS):
            _, _, dense, smooth, mt_, mv = _fold(pol, AR, key)
            if AR == 2.0:
                ref = np.interp(0.0, dense, smooth)
            ax.plot(np.deg2rad(dense), smooth / ref, "-", color=OI[i], lw=1.2,
                    label=f"AR = {AR:g}", zorder=2)
            ax.plot(np.deg2rad(mt_), mv / ref, "o", ms=1.6, color=OI[i],
                    mfc="none", mew=0.45, zorder=3)
        if key == "k2_axial":
            _, _, dense, smooth, mt_e, mv_e = _fold(pol, 2.0, key, "ellipse")
            ax.plot(np.deg2rad(dense), smooth / ref, "--", color="0.15", lw=1.1,
                    label="ellipse, equal $M$", zorder=2)
            ax.plot(np.deg2rad(mt_e), mv_e / ref, "s", ms=1.5, color="0.15",
                    mfc="none", mew=0.45, zorder=3)
        ax.set_rlim(*rlim)
        ax.plot(np.linspace(0, 2 * np.pi, 361), np.ones(361), ":",
                color="0.55", lw=0.7, zorder=1)
        ax.set_rticks(rticks)
        ax.set_yticklabels([f"{v:g}" for v in rticks], fontsize=6.2)
        ax.set_theta_zero_location("E")
        ax.set_rlabel_position(118)
        ax.set_thetagrids(np.arange(0, 360, 45),
                          labels=["0", "45", "90", "135", "180", "225",
                                  "270", "315"], fontsize=6.2)
        ax.tick_params(pad=1)
        ax.grid(alpha=0.35, lw=0.4)
        ax.set_title(rlab, fontsize=8, pad=13)
        ax.text(0.02, 1.10, "(%s)" % "ab"[k], transform=ax.transAxes,
                fontsize=8.5, fontweight="bold")
        for lb in ax.get_yticklabels():
            lb.set_bbox(dict(fc="white", ec="none", alpha=0.9, pad=0.5))
        if k == 0:
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10),
                      frameon=False, fontsize=6.3, ncol=2, handlelength=1.3,
                      columnspacing=0.8)
    for k, (key, lab, cm, fmt) in enumerate((
            ("k2_axial", r"$k^2$", "viridis", "%.2f"),
            ("f_ext_kHz", r"$f_{\rm ext}$ (kHz)", "cividis", "%.0f"))):
        ax = fig.add_subplot(gs[1, k])
        thf, arf, Z = _polarmap(pol, key)
        m = thf <= 180.0
        T, A = np.meshgrid(thf[m], arf)
        cf = ax.contourf(T, A, Z[:, m], levels=16, cmap=cm)
        cs = ax.contour(T, A, Z[:, m], levels=4, colors="k", linewidths=0.4)
        ax.clabel(cs, fontsize=5.4, inline=True, inline_spacing=2, fmt=fmt)
        for AR in sorted({round(r["AR"], 3) for r in pol}):
            ax.plot([0, 180], [AR, AR], "o", ms=1.1, color="w", alpha=0.85)
        ax.set_xlim(0, 180)
        ax.set_xticks([0, 45, 90, 135, 180])
        ax.set_yscale("log")
        ax.set_yticks([2, 3, 5, 7, 10])
        ax.set_yticklabels(["2", "3", "5", "7", "10"])
        ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.set_xlabel(r"window angle $\theta$ (deg)", fontsize=7.5)
        ax.set_ylabel("aspect ratio", fontsize=7.5)
        ax.tick_params(labelsize=6.5)
        ax.grid(False)
        ax.text(0.03, 0.93, "(%s)" % "cd"[k], transform=ax.transAxes,
                fontsize=8.5, fontweight="bold", va="top",
                bbox=dict(fc="w", ec="none", alpha=0.8, pad=1.0))
        cb = fig.colorbar(cf, ax=ax, pad=0.015, fraction=0.05)
        cb.set_label(lab, fontsize=7.5)
        cb.ax.tick_params(labelsize=6.5)
    save(fig, "F4_orientation")


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
    save(fig, "FB2_modes")
    return {"V_open_V": V, "magnification": float(magn * 1e3),
            "u_peak_nm": 10.0}


# ---------------------------------------------------------------------------
# P5  root locus
# ---------------------------------------------------------------------------
def fig_damping():
    """The fractional element: where its poles go, and what it means for the
    damping ratio."""
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.75),
                            gridspec_kw={"wspace": 0.30, "left": 0.085,
                                         "right": 0.975, "bottom": 0.19,
                                         "top": 0.90})
    ax = axs[0]
    alphas = np.linspace(0.2, 1.0, 25)
    w0 = 2 * np.pi * 6.7273e6
    taus = [0.5e-9, 1e-9, 2e-9, 4e-9, 8e-9, 16e-9, 32e-9]
    cmap = plt.get_cmap("cividis")
    for i, tau in enumerate(taus):
        s0 = None
        xs, ys = [], []
        for a in alphas:
            z = complex(f6.complex_frequency(w0, tau, a, s0=s0))
            s0 = z
            xs.append(-z.real / w0)
            ys.append(abs(z.imag) / w0)
        xs, ys = np.array(xs), np.array(ys)
        col = cmap(0.12 + 0.76 * i / (len(taus) - 1))
        ax.plot(xs, ys, "-", color=col, lw=1.15, zorder=2)
        mk = [0, 6, 12, 18, 24]
        ax.plot(xs[mk], ys[mk], "o", ms=2.7, color=col, mfc="w", mew=0.55,
                zorder=3)
        if i in (0, len(taus) - 1):
            first = i == 0
            ax.annotate(rf"$\tau={tau*1e9:g}$ ns", (xs[0], ys[0]),
                        textcoords="offset points",
                        xytext=(-42, 0) if first else (5, 5),
                        ha="right" if first else "left", va="center",
                        fontsize=6.0, color="0.25")
    ax.set_xscale("log")
    ax.set_xlim(5e-3, 1.5)
    ax.set_ylim(0.955, 1.52)
    ax.axhline(1.0, color="0.55", lw=0.6, ls=":", zorder=1)
    ax.text(0.03, 0.94, r"markers: $\alpha=0.2,0.4,0.6,0.8,1$",
            transform=ax.transAxes, ha="left", va="top", fontsize=5.8)
    ax.set_xlabel(r"$-\mathrm{Re}\,s/\omega_0$")
    ax.set_ylabel(r"$|\mathrm{Im}\,s|/\omega_0$")
    ax.tick_params(labelsize=6.5)
    ax.set_title(r"(a) poles of the fractional mode", fontsize=7.8, loc="left")
    axb = axs[1]
    al = np.linspace(0.2, 1.0, 41)
    wt = np.logspace(-1.5, 1.5, 61)
    Z = np.zeros((al.size, wt.size))
    for j, a in enumerate(al):
        s0 = None
        for i, x in enumerate(wt):
            s = complex(f6.complex_frequency(1.0, x, a, s0=s0))
            s0 = s
            Z[j, i] = -s.real / abs(s)
    A, W = np.meshgrid(al, np.log10(wt), indexing="ij")
    cf = axb.contourf(A, W, Z, levels=16, cmap="cividis")
    cs = axb.contour(A, W, Z, levels=[0.05, 0.1, 0.2, 0.4, 0.7],
                     colors="k", linewidths=0.45)
    axb.clabel(cs, fontsize=5.6, inline=True, inline_spacing=2, fmt="%.2f")
    axb.set_xlabel(r"$\alpha$")
    axb.set_ylabel(r"$\log_{10}\omega\tau$")
    axb.tick_params(labelsize=6.5)
    axb.set_title(r"(b) damping ratio $\zeta(\alpha,\omega\tau)$",
                  fontsize=7.8, loc="left")
    cb = fig.colorbar(cf, ax=axb, pad=0.02, fraction=0.055)
    cb.set_label(r"$\zeta$", fontsize=7.5)
    cb.ax.tick_params(labelsize=6.5)
    save(fig, "F6_damping")

def fig_p6_waterfall():
    """Ring-down for eight Caputo orders.

    Drawn as coloured time traces rather than a 3-D waterfall: the
    perspective view is dominated by the overlapping of the traces and the
    alpha axis carries no more information than the colour does.
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
    alphas = [1.0, 0.95, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
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
        c = (OI + ["#8250A0"])[i % 9]
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
    save(fig, "F9_ringdown")
    return out


# ---------------------------------------------------------------------------
# P7  thickness
# ---------------------------------------------------------------------------


def fig_p7_thickness(thick, closed_form):
    """The two couplings against the plate thickness, and their ratio."""
    h = np.array([r["h_um"] for r in thick])
    kf = np.array([r["k2_flexo"] for r in thick])
    ke = np.array([r["k2_ext"] for r in thick])
    fig, ax = plt.subplots(1, 3, figsize=(6.9, 2.65),
                           gridspec_kw={"width_ratios": [1.1, 1.0, 0.95],
                                        "wspace": 0.42, "left": 0.075,
                                        "right": 0.985, "bottom": 0.18,
                                        "top": 0.90})
    ax[0].loglog(h, kf, "-", color=OI[0], lw=1.3,
                 label=r"FEM, 48$\times$4")
    ax[0].loglog(h, kf, "o", ms=3.4, color=OI[0], mfc="none", mew=0.6)
    h96 = [r["h_um"] for r in thick if "k2_flexo_96" in r]
    k96 = [r["k2_flexo_96"] for r in thick if "k2_flexo_96" in r]
    ax[0].loglog(h96, k96, "s", mfc="none", ms=5.0, mew=0.9, color=OI[1],
                 label=r"FEM, 96$\times$4")
    ax[0].loglog(h, kf[-1] * (h[-1] / h) ** 2, ":", lw=0.9, color="0.45",
                 label=r"$h^{-2}$ guide")
    slopes = []
    for i in range(len(h) - 1):
        slopes.append((np.log10(kf[i + 1]) - np.log10(kf[i])) /
                      (np.log10(h[i + 1]) - np.log10(h[i])))
    print("  flexo slopes:", ", ".join(f"{v:.2f}" for v in slopes))
    for i, dy in ((0, -13), (len(slopes) // 2, -12), (len(slopes) - 1, 8)):
        xm = np.sqrt(h[i] * h[i + 1])
        ym = np.sqrt(kf[i] * kf[i + 1])
        ax[0].annotate(f"{slopes[i]:.2f}", (xm, ym),
                       textcoords="offset points", xytext=(3, dy),
                       fontsize=6.2, color=OI[0])
    ax[0].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[0].set_ylabel(r"$k^2$ (bending)")
    ax[0].invert_xaxis()
    ax[0].set_ylim(1.2e-4, 1.1e-2)
    ax[0].tick_params(labelsize=6.5)
    ax[0].legend(frameon=False, fontsize=6.2, loc="upper left")
    ax[0].set_title("(a) flexoelectric", fontsize=7.8, loc="left")
    ax[1].semilogx(h, ke, "-", color=OI[2], lw=1.3, label=r"FEM, 48$\times$4")
    ax[1].semilogx(h, ke, "s", ms=3.4, color=OI[2], mfc="none", mew=0.6)
    ax[1].semilogx(h, [r["k2_ext_24"] for r in thick], "--", ms=4, lw=0.9,
                   alpha=0.8, color=OI[3], label=r"FEM, 24$\times$2")
    ax[1].axhline(closed_form, color="k", lw=0.9, ls=":",
                  label=r"$e^{\mathrm{T}}C^{-1}e/\kappa$")
    ax[1].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[1].set_ylabel(r"$k^2$ (quasi-static)")
    ax[1].invert_xaxis()
    ax[1].set_ylim(0.548, 0.570)
    ax[1].tick_params(labelsize=6.5)
    ax[1].legend(frameon=False, fontsize=6.0, loc="lower left")
    ax[1].set_title("(b) piezoelectric", fontsize=7.8, loc="left")
    ax[2].loglog(h, kf / ke, "-", color=OI[4], lw=1.3)
    ax[2].loglog(h, kf / ke, "o", ms=3.4, color=OI[4], mfc="none", mew=0.6)
    ax[2].axhline(1.0, color="0.45", lw=0.9, ls="--")
    ax[2].set_xlabel(r"thickness $h$ ($\mu$m)")
    ax[2].set_ylabel(r"ratio $k^2_{\rm flexo}/k^2_{\rm piezo}$")
    ax[2].invert_xaxis()
    ax[2].set_ylim(2.0e-4, 3.0)
    ax[2].tick_params(labelsize=6.5)
    ax[2].set_title("(c) the two together", fontsize=7.8, loc="left")
    save(fig, "F8_thickness")
    return {"n": int(h.size), "slope_thick": float(slopes[0]),
            "slope_thin": float(slopes[-1])}


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
    save(fig, "FB1_tracking")


# ---------------------------------------------------------------------------
# P9  damping surface
# ---------------------------------------------------------------------------


def main():
    import time
    t0 = time.time()
    only = [a for a in sys.argv[1:] if a.startswith("F")]
    if only:
        # redraw a subset from the stored sweep -- handy while polishing
        with open(os.path.join(ROOT, "results", "paper_figures_data.json")) as fh:
            pol = json.load(fh)["polar"]
        demo = json.load(open(os.path.join(ROOT, "results", "demo.json")))
        cc = json.load(open(os.path.join(ROOT, "results",
                                         "coupling_check.json")))
        figs = {"F1": lambda: fig_p1_geometry(),
                "F2": lambda: fig_p11_convergence(),
                "F3": lambda: fig_p12_fields(),
                "F4": lambda: fig_orientation(pol),
                "F5": lambda: fig_p14_design_space(pol),
                "F6": lambda: fig_damping(),
                "F7": lambda: fig_window(),
                "F8": lambda: fig_p7_thickness(demo["flexo_thickness"],
                                               cc["closed_form"]["k2_2d_closed"]),
                "F9": lambda: fig_p6_waterfall(),
                "FB1": lambda: fig_p8_mac(json.load(open(os.path.join(
                    ROOT, "results", "mode_tracking.json")))),
                "FB2": lambda: fig_p4_modeshape()}
        for k in only:
            if k in figs:
                print(figs[k]())
                print(f"    {k} redrawn")
        return 0
    print("  polar sweep")
    pol, sym = polar_sweep()
    print("  figures")
    fig_p1_geometry()
    fig_orientation(pol)
    info = {"P2_symmetry": sym, "P4": fig_p4_modeshape()}
    fig_damping()
    info["P6"] = fig_p6_waterfall()
    with open(os.path.join(ROOT, "results", "demo.json")) as fh:
        demo = json.load(fh)
    with open(os.path.join(ROOT, "results", "coupling_check.json")) as fh:
        cc = json.load(fh)
    fig_p7_thickness(demo["flexo_thickness"], cc["closed_form"]["k2_2d_closed"])
    with open(os.path.join(ROOT, "results", "mode_tracking.json")) as fh:
        mtdata = json.load(fh)
    fig_p8_mac(mtdata)
    print("  new panels")
    info.update(main_new_figures(pol))
    with open(os.path.join(ROOT, "results", "paper_figures_data.json"), "w") as fh:
        json.dump({"polar": pol, "symmetry": sym, "notes": info}, fh, indent=1)
    print(f"  done in {time.time() - t0:.0f} s -> results/figures/paper/")
    return 0




# ---------------------------------------------------------------------------
# P11  convergence of the discretisation
# ---------------------------------------------------------------------------
def fig_p11_convergence():
    """Convergence of the extensional coupling and of the frequency of the
    mode that carries it, against the mesh."""
    MAT = mt.Material(**{**mt.batio3("x", "plane_stress").__dict__, "mu": 0.0})
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    meshes = [(12, 2), (24, 2), (36, 2), (48, 4)]
    rec = []
    for nx, ny in meshes:
        mesh = f6.mesh_rect(nx, ny, LPLATE, HPLATE)
        mdl = f6.assemble(mesh, mt.to_core(MAT), Mg)
        Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=("left", "right"))
        _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=("left", "right"))
        w2, Phi = f6.modes(Ksc, M, 8)
        s = (Phi.T @ d) ** 2 / beta
        x = s / w2
        k2m = x / (1.0 + x)
        j = int(np.argmax(k2m))
        f1 = float(np.sqrt(w2[j]) / 2e3 / np.pi)
        k2 = float(static_k2(MAT, Mg, ("left", "right"), nx=nx, ny=ny))
        rec.append({"nx": nx, "ny": ny, "ndof": int(mdl.ndof_mech),
                    "f_coupled_kHz": f1, "k2_static": k2,
                    "k2_mode": float(k2m[j]), "mode_index": j})
    nd = np.array([r["ndof"] for r in rec], float)
    k2 = np.array([r["k2_static"] for r in rec], float)
    f1 = np.array([r["f_coupled_kHz"] for r in rec], float)
    ek = np.abs(k2 / k2[-1] - 1.0)
    ef = np.abs(f1 / f1[-1] - 1.0)

    fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.4), layout="constrained")
    ax = axs[0]
    ax.loglog(nd, np.maximum(ek, 1e-9), "o-", color="#0072B2", label=r"$k^2$")
    ax.loglog(nd, np.maximum(ef, 1e-9), "s-", color="#D55E00", label=r"$f$ of the mode")
    ax.loglog(nd, np.maximum(ek[0] * (nd[0] / nd) ** 2.0, 1e-9), "k--", lw=0.9,
              label=r"$\propto N^{-2}$")
    ax.axvline(nd[-1], color="0.55", ls="-.", lw=0.8)
    ax.set_xlabel("degrees of freedom"); ax.set_ylabel("relative error")
    ax.legend(frameon=False, loc="lower left"); ax.set_title("(a)", loc="left")
    ax = axs[1]
    ax.plot(nd, k2, "o-", color="#0072B2", label=r"$k^2$ (mode-free)")
    ax.axhline(k2[-1], color="k", ls=":", lw=0.8)
    ax.axvline(nd[-1], color="0.55", ls="-.", lw=0.8)
    ax.set_xlabel("degrees of freedom"); ax.set_ylabel(r"$k^2$", labelpad=2)
    ax2 = ax.twinx()
    ax2.plot(nd, f1, "s-", color="#D55E00", label=r"$f$ (kHz)")
    ax2.set_ylabel(r"$f$ (kHz)", color="#D55E00")
    ax2.tick_params(axis="y", colors="#D55E00")
    ax2.grid(False); ax2.spines["right"].set_visible(True)
    ax.set_title("(b)", loc="left")
    save(fig, "F2_convergence")
    return {"convergence": rec}


# ---------------------------------------------------------------------------
# P12  field panels of the coupled mode (open circuit)
# ---------------------------------------------------------------------------
def fig_p12_fields():
    """u_x, w, phi and |E| of the coupled bending mode, open circuit."""
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    mesh = f6.mesh_rect(48, 4, LPLATE, HPLATE)
    mat = mt.batio3("y", "plane_stress")
    mdl = f6.assemble(mesh, mt.to_core(mat), Mg)
    Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=("bottom", "top"))
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=("bottom", "top"))
    ws, Phi = f6.modes(Ksc, M, 3)
    mode = Phi[:, 0].copy()
    vpk = np.abs(mode[[np.searchsorted(idx, mdl.mech_dof[n][4])
                       for n in range(mesh.nnode)]]).max()
    mode *= 10.0e-9 / vpk
    V = float(d @ mode) / beta
    allp = np.arange(mdl.ndof_phi)
    bot, top = mdl.electrodes["bottom"], mdl.electrodes["top"]
    inter = np.setdiff1d(np.setdiff1d(allp, bot), top)
    u_full = np.zeros(mdl.ndof_mech)
    u_full[idx] = mode
    b = mdl.B.T @ u_full
    Cin = mdl.Cphi[np.ix_(inter, inter)]
    Cif = mdl.Cphi[np.ix_(inter, np.r_[bot, top])]
    phi_f = np.r_[np.zeros(len(bot)), np.full(len(top), V)]
    phi = np.zeros(mdl.ndof_phi)
    phi[inter] = np.linalg.solve(Cin, b[inter] - Cif @ phi_f)
    phi[top] = V

    nn = mesh.nnode
    phin = 1e3 * np.array([phi[int(mdl.phi_dof[n])] if mdl.phi_dof[n] >= 0
                           else 0.0 for n in range(nn)])
    ux = np.array([u_full[mdl.mech_dof[n][0]] for n in range(nn)])
    w = np.array([u_full[mdl.mech_dof[n][4]] for n in range(nn)])
    ph = phin.reshape(5, 49)
    Ey, Ex = np.gradient(ph, axis=0), np.gradient(ph, axis=1)
    Emag = np.sqrt(Ex ** 2 + Ey ** 2)

    X = (mesh.nodes[:, 0] * 1e6).reshape(5, 49)
    Y = (mesh.nodes[:, 1] * 1e6).reshape(5, 49)
    uxn = ux.reshape(5, 49) / np.abs(ux).max()
    wn = w.reshape(5, 49) / np.abs(w).max()
    fields = [(uxn, "(a)", r"$u_x/|u_x|_{\max}$"),
              (wn, "(b)", r"$w/|w|_{\max}$"),
              (ph, "(c)", r"$\phi$ (mV)"),
              (Emag, "(d)", r"$|\nabla\phi|$ (mV/$\mu$m)")]
    fig, axs = plt.subplots(2, 2, figsize=(6.4, 3.2), layout="constrained")
    for ax, (Z, tag, lab) in zip(axs.ravel(), fields):
        m = ax.pcolormesh(X, Y, Z, shading="gouraud", cmap="viridis")
        cb = fig.colorbar(m, ax=ax, pad=0.02, fraction=0.046)
        cb.set_label(lab, fontsize=7)
        cb.ax.tick_params(labelsize=6)
        ax.set_xlabel(r"$x$ ($\mu$m)"); ax.set_ylabel(r"$y$ ($\mu$m)")
        ax.set_title(tag, loc="left")
        ax.set_aspect("auto")
        ax.grid(False)
    save(fig, "F3_fields")
    return {"V_open_V": V, "u_peak_nm": 10.0}


# ---------------------------------------------------------------------------
# P13  boundary layer at the clamped edge versus a/L
# ---------------------------------------------------------------------------
def _static_w(Mg, nx=48, ny=4, L=LPLATE, h=HPLATE):
    mesh = f6.mesh_rect(nx, ny, L, h)
    mat = mt.batio3("y", "plane_stress")
    mdl = f6.assemble(mesh, mt.to_core(mat), Mg)
    Ksc, _, idx, _ = f6.reduce(mdl, "short", pair=("bottom", "top"))
    n = Ksc.shape[0]
    fixed = [np.searchsorted(idx, mdl.mech_dof[node][k])
             for node in range(mesh.nnode) if abs(mesh.nodes[node, 0]) < 1e-15
             for k in range(8)]
    load = [np.searchsorted(idx, mdl.mech_dof[node][4])
            for node in range(mesh.nnode) if abs(mesh.nodes[node, 0] - L) < 1e-12]
    free = np.setdiff1d(np.arange(n), np.array(fixed, int))
    f = np.zeros(n)
    f[np.array(load, int)] = 1.0 / len(load)
    u = np.zeros(n)
    u[free] = np.linalg.solve(Ksc[np.ix_(free, free)], f[free])
    w = np.array([u[np.searchsorted(idx, mdl.mech_dof[node][4])]
                  for node in range(mesh.nnode)])
    x = mesh.nodes[:, 0]
    return x, w


def fig_window():
    """What the window size does: the equal-M collapse and the profiles."""
    fig, axs = plt.subplots(1, 3, figsize=(6.9, 2.55),
                            gridspec_kw={"width_ratios": [1.1, 1.0, 1.0],
                                         "wspace": 0.34, "left": 0.075,
                                         "right": 0.985, "bottom": 0.19,
                                         "top": 0.90})
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
    y1 = np.array([ur(f6.second_moment("ellipsoid", l, l), True) / u0
                   for l in ls])
    y2 = np.array([ur(f6.second_moment("cuboid", l, l), True) / u0 for l in ls])
    y3 = np.array([ur(f6.second_moment("cuboid", l * np.sqrt(3 / 5),
                                       l * np.sqrt(3 / 5)), True) / u0
                   for l in ls])
    ax = axs[0]
    for y, lab, col, lsm, dy in (
            (y1, "ellipsoid, semi-axis $l$", OI[0], "-", 8),
            (y2, "cuboid, half-width $l$", OI[1], "-", -12),
            (y3, r"cuboid, equal $M$", OI[2], "--", None)):
        ax.plot(ls, y, lsm, color=col, lw=1.3, label=lab)
        ax.plot(ls, y, "o", ms=2.3, color=col, mfc="none", mew=0.5)
        if dy is not None:
            ax.annotate(f"{y[-1]:.3f}", (ls[-1], y[-1]), xytext=(2, dy),
                        textcoords="offset points", fontsize=6.0, color=col,
                        annotation_clip=False)
    ax.set_xlim(0.0, 0.215)
    ax.set_ylim(0.912, 1.004)
    ax.set_xlabel(r"$l/L_x$")
    ax.set_ylabel(r"$u_R/u_{R}^{\rm classical}$")
    ax.tick_params(labelsize=6.5)
    ax.set_title("(a) loaded edge", fontsize=7.8, loc="left")
    ax.legend(frameon=False, fontsize=6.0, loc="lower left")
    x0, w_el = _static_w(np.zeros((2, 2)))
    grid = x0.reshape(5, 49)[2]
    w_el = w_el.reshape(5, 49)[2]
    recs = []
    for ratio in (0.05, 0.1, 0.2):
        x, w = _static_w(f6.second_moment("cuboid", ratio * LPLATE, 1e-6, 0.0))
        recs.append((ratio, w.reshape(5, 49)[2]))
    axb = axs[1]
    axc = axs[2]
    for k, (ratio, pw) in enumerate(recs):
        axb.plot(grid / LPLATE, pw / pw[-1], "-", color=OI[k], lw=1.3,
                 label=rf"$a/L={ratio}$")
        axb.plot(grid[::8] / LPLATE, (pw / pw[-1])[::8], "o", ms=2.3,
                 color=OI[k], mfc="none", mew=0.5)
        d = np.abs(pw - w_el) / abs(w_el[-1])
        nz = d > 0
        axc.semilogy((grid / LPLATE)[nz], d[nz], "-", color=OI[k], lw=1.3)
        axc.semilogy((grid[::8] / LPLATE)[nz[::8]], d[::8][nz[::8]], "o",
                     ms=2.3, color=OI[k], mfc="none", mew=0.5)
    axb.set_xlabel(r"$x/L$")
    axb.set_ylabel(r"$w(x)/w(L)$")
    axb.tick_params(labelsize=6.5)
    axb.set_title("(b) clamped plate", fontsize=7.8, loc="left")
    axb.legend(frameon=False, fontsize=6.2, loc="upper left")
    axc.set_xlabel(r"$x/L$")
    axc.set_ylabel(r"$|w-w_{\rm cl}|/w_{\rm cl}(L)$")
    axc.tick_params(labelsize=6.5)
    axc.set_xlim(0, 1.0)
    axc.set_title("(c) departure from the classical", fontsize=7.8, loc="left")
    save(fig, "F7_window")


def fig_p14_design_space(pol):
    """The two quantities that are not already in the polar sections: the
    change of the coupling relative to the aligned window, and the anisotropy
    of the second-moment tensor that causes it."""
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.9),
                            gridspec_kw={"wspace": 0.26, "left": 0.10,
                                         "right": 0.975, "bottom": 0.19,
                                         "top": 0.90})
    ars = sorted({r["AR"] for r in pol})
    half = sorted([r for r in pol if r["AR"] == ars[0]
                   and r["shape"] == "cuboid"], key=lambda z: z["theta_deg"])
    th = np.array([r["theta_deg"] for r in half], float)
    M11 = np.array([r["Mg_xx"] for r in half])
    M22 = np.array([r["Mg_yy"] for r in half])
    an = (M11 - M22) / (M11 + M22)
    ax = axs[0]
    for i, AR in enumerate(ars):
        h = sorted([r for r in pol if r["AR"] == AR and r["shape"] == "cuboid"],
                   key=lambda z: z["theta_deg"])
        k2 = np.array([r["k2_axial"] for r in h])
        rel = 100.0 * (k2 / k2[0] - 1.0)
        ax.plot(th, rel, "-", color=OI[i], lw=1.15, label=f"AR = {AR:g}")
        ax.plot(th[::2], rel[::2], "o", ms=2.2, color=OI[i], mfc="none",
                mew=0.5)
        if i == 0:
            worst = (rel.min(), AR, th[np.argmin(rel)])
        if rel.min() < worst[0]:
            worst = (rel.min(), AR, th[np.argmin(rel)])
    ax.set_xlim(0, 90)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xlabel(r"window angle $\theta$ (deg)")
    ax.set_ylabel(r"$\Delta k^2/k^2(\theta{=}0)$ (%)")
    ax.tick_params(labelsize=6.5)
    ax.set_title("(a) coupling against alignment", fontsize=7.8, loc="left")
    ax.legend(frameon=False, fontsize=6.2, ncol=2, loc="lower left")
    axb = axs[1]
    axb.plot(th, an, "-", color=OI[3], lw=1.3)
    axb.plot(th, an, "o", ms=2.4, color=OI[3], mfc="none", mew=0.5)
    axb.axhline(0.0, color="0.55", lw=0.6, ls=":")
    axb.set_xlim(0, 90)
    axb.set_xticks([0, 15, 30, 45, 60, 75, 90])
    axb.set_xlabel(r"window angle $\theta$ (deg)")
    axb.set_ylabel(r"$(M_{11}-M_{22})/(M_{11}+M_{22})$")
    axb.tick_params(labelsize=6.5)
    axb.set_title(r"(b) anisotropy of $M$ (any aspect ratio)",
                  fontsize=7.8, loc="left")
    save(fig, "F5_design")
    print(f"  design: worst change {worst[0]:.1f} % (AR = {worst[1]:g}, "
          f"theta = {worst[2]:g} deg)")
    return {"n": int(len(pol)), "min_rel_pct": float(worst[0])}


def main_new_figures(pol):
    out = {}
    out["P11"] = fig_p11_convergence()
    out["P12"] = fig_p12_fields()
    out["P13"] = fig_window()
    out["P14"] = fig_p14_design_space(pol)
    return out


if __name__ == "__main__":
    sys.exit(main())
