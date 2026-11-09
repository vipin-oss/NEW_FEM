"""
FEM-6 verification suite
========================
Runs the five verification cases of the blueprint plus the element-level and
solver-level checks, and writes results/verification.md and
results/verification.json.

Run:  python3 python/run_verification.py
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem6_core as f6  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results")
os.makedirs(OUT, exist_ok=True)
R = {}


def log(*a):
    print(*a, flush=True)


# ==========================================================================
# V1  element patch test (constant strain) and gradient consistency
# ==========================================================================
def v1_patch_test():
    mat = f6.isotropic_plane_strain(2e11, 0.3, 7850)
    hx, hy = 0.1, 0.05
    e0 = 1e-3
    Kh = hx / 2.0
    # u = e0 x, v = 0 exactly representable in BFS
    d = np.zeros(32)
    for c, (sx, sy) in enumerate(f6._CORNERS):
        x, y = (sx + 1) * hx / 2, (sy + 1) * hy / 2
        d[8 * c + 0] = e0 * x
        d[8 * c + 1] = e0
        d[8 * c + 4] = 0.0
    Ke, Me, _, _ = f6.element_matrices(hx, hy, mat, np.zeros((2, 2)),
                                       gradient=False)
    U = 0.5 * d @ Ke @ d
    Uex = 0.5 * mat.C[0, 0] * e0 ** 2 * hx * hy
    Kg = f6.element_matrices(hx, hy, mat, f6.second_moment("cuboid", 0.2, 0.2),
                             gradient=True)[0] - Ke
    Ug = 0.5 * d @ Kg @ d
    R["patch"] = {"U": U, "U_exact": Uex, "rel_err": abs(U / Uex - 1.0),
                  "grad_energy_const_strain": abs(Ug)}

    # element gradient operator == FEM-1 formula (l^2/10)(Kxx + Kyy)
    l = 0.2
    Kg_ell = f6.element_matrices(hx, hy, mat,
                                 f6.second_moment("ellipsoid", l, l),
                                 gradient=True)[0] - Ke
    xg, wg = f6.gauss_legendre(4)
    XI, ETA = np.meshgrid(xg, xg, indexing="ij")
    W = np.outer(wg, wg).ravel()
    N, Nx, Ny, Nxx, Nxy, Nyy = f6.bfs_scalar(XI.ravel(), ETA.ravel(), hx, hy)
    jac = 0.25 * hx * hy
    Kxx = np.zeros((32, 32))
    Kyy = np.zeros((32, 32))
    for g in range(16):
        Bx = np.zeros((3, 32))
        By = np.zeros((3, 32))
        for c in range(4):
            for dd in range(4):
                k = 4 * c + dd
                cu, cv = 8 * c + dd, 8 * c + 4 + dd
                Bx[0, cu], Bx[2, cu] = Nxx[g, k], Nxy[g, k]
                Bx[1, cv], Bx[2, cv] = Nxy[g, k], Nxx[g, k]
                By[0, cu], By[2, cu] = Nxy[g, k], Nyy[g, k]
                By[1, cv], By[2, cv] = Nyy[g, k], Nxy[g, k]
        Kxx += Bx.T @ mat.C @ Bx * W[g] * jac
        Kyy += By.T @ mat.C @ By * W[g] * jac
    ref = (l ** 2 / 10.0) * (Kxx + Kyy)
    R["patch"]["ellipsoid_vs_FEM1"] = float(
        np.max(np.abs(Kg_ell - ref)) / np.max(np.abs(Kg_ell)))

    # cuboid / ellipsoid at equal half-width = 5/3
    Kg_cub = f6.element_matrices(hx, hy, mat,
                                 f6.second_moment("cuboid", l, l),
                                 gradient=True)[0] - Ke
    R["patch"]["cuboid_over_ellipsoid_equal_halfwidth"] = float(
        np.max(np.abs(Kg_cub)) / np.max(np.abs(Kg_ell)))
    # equal second moment -> identical operators
    a_eq = l * np.sqrt(3.0 / 5.0)
    Kg_cub_eq = f6.element_matrices(hx, hy, mat,
                                    f6.second_moment("cuboid", a_eq, a_eq),
                                    gradient=True)[0] - Ke
    R["patch"]["cuboid_eq_moment_vs_ellipsoid"] = float(
        np.max(np.abs(Kg_cub_eq - Kg_ell)) / np.max(np.abs(Kg_ell)))


# ==========================================================================
# static cantilever / FEM-1 benchmark
# ==========================================================================
MAT_STEEL = f6.isotropic_plane_strain(2e11, 0.3, 7850)


def u_right(nx, ny, l=None, domain="ellipsoid", theta=0.0, mat=MAT_STEEL):
    mesh = f6.mesh_rect(nx, ny, 1.0, 0.2)
    Mg = f6.second_moment(domain, l, l, theta) if l else np.zeros((2, 2))
    m = f6.assemble(mesh, mat, Mg, gradient=l is not None)
    K, M, idx, _ = f6.reduce(m, "short")
    f = m.edge_traction(tx=1e6, side="right")
    U = np.zeros(m.ndof_mech)
    U[idx] = np.linalg.solve(K, f[idx])
    right = [n for n, xy in enumerate(mesh.nodes) if abs(xy[0] - 1.0) < 1e-12]
    return float(np.mean([U[m.mech_dof[n][0]] for n in right])), m, K, U


def v2_fem1_benchmark():
    u_ana = 1e6 * (1 - 0.3 ** 2) / 2e11
    R["fem1"] = {"u_analytic_plane_strain": u_ana, "meshes": [], "length": []}
    for nx, ny in [(5, 1), (10, 2), (20, 4), (40, 8)]:
        u, _, _, _ = u_right(nx, ny)
        R["fem1"]["meshes"].append({"nx": nx, "ny": ny,
                                    "ndof": 8 * f6.mesh_rect(nx, ny, 1, .2).nnode,
                                    "u": u})
        log(f"  classical {nx}x{ny}: u_R = {u*1e6:.4f} um")
    u0, _, _, _ = u_right(20, 4)
    for l in [0.02, 0.05, 0.10, 0.20]:
        u, _, _, _ = u_right(20, 4, l)
        R["fem1"]["length"].append({"l_over_L": l, "u": u, "ratio": u / u0})
        log(f"  ellipsoid l/L={l:.2f}: u_R = {u*1e6:.4f} um ratio {u/u0:.4f}")
    # FEM-1 published values (final_R2, Fig. 4 / 5): 4.50 um at l->0,
    # 4.23 um and ratio 0.94 at l/L=0.20 on a 20x4 mesh
    R["fem1"]["paper_u_classical_um"], R["fem1"]["paper_u_l020_um"] = 4.50, 4.23
    R["fem1"]["paper_ratio_l020"] = 0.94


def v3_mesh_convergence():
    ref, _, _, _ = u_right(60, 12)
    rows = []
    for nx, ny in [(5, 1), (10, 2), (20, 4), (40, 8)]:
        u, _, _, _ = u_right(nx, ny)
        rows.append({"nx": nx, "ny": ny, "u": u, "rel_err": abs(u / ref - 1)})
    # observed order by least squares on the last three points
    h = np.array([1.0 / r["nx"] for r in rows])
    e = np.array([r["rel_err"] for r in rows])
    order = np.polyfit(np.log(h[1:]), np.log(e[1:]), 1)[0]
    R["convergence"] = {"rows": rows, "ref": ref, "order": float(order)}
    u_g, _, _, _ = u_right(20, 4, 0.05)
    log(f"  gradient l/L=0.05 on 20x4: {u_g*1e6:.4f} um  "
        f"(paper 4.45 um, ratio 0.989)")


# ==========================================================================
# piezo checks
# ==========================================================================
def v4_piezo():
    mat = f6.batio3_plane_strain("y")
    mesh = f6.mesh_rect(20, 4, 200e-6, 10e-6)
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6)
    m = f6.assemble(mesh, mat, Mg)
    Ksc, M, idx, _ = f6.reduce(m, "short", pair=("bottom", "top"))
    Koc, M, idx, ex = f6.reduce(m, "open", pair=("bottom", "top"))
    d, beta = ex
    wsc, phisc = f6.modes(Ksc, M, 1)
    woc, phloc = f6.modes(Koc, M, 1)
    k2 = (woc ** 2 - wsc ** 2) / woc ** 2
    dK = Koc - Ksc
    eig_dK = np.linalg.eigvalsh(0.5 * (dK + dK.T))
    eig_sc = np.linalg.eigvalsh(0.5 * (Ksc + Ksc.T))
    R["piezo"] = {"f_sc": float(wsc[0] / 2 / np.pi),
                  "f_oc": float(woc[0] / 2 / np.pi),
                  "k2": float(np.ravel(k2)[0]), "beta": float(beta),
                  "min_eig_dK": float(eig_dK.min() / np.abs(eig_dK).max()),
                  "min_eig_Ksc": float(eig_sc.min() / np.abs(eig_sc).max()),
                  "mode1_charge": float(abs(d @ phloc[:, 0]))}
    k2v = float(np.ravel(k2)[0])
    log(f"  bending mode: f_sc={wsc[0]/2/np.pi:.2f} Hz, "
        f"f_oc={woc[0]/2/np.pi:.2f} Hz, k2={k2v:.3e}")

    # extensional configuration (poling along the axis, end electrodes)
    matx = f6.batio3_plane_strain("x")
    mx = f6.assemble(mesh, matx, Mg)
    Ksc2, M2, _, _ = f6.reduce(mx, "short", pair=("left", "right"))
    Koc2, M2, _, ex2 = f6.reduce(mx, "open", pair=("left", "right"))
    d2, beta2 = ex2
    ws, ps = f6.modes(Ksc2, M2, 6)
    wo, po = f6.modes(Koc2, M2, 6)
    k2s = (wo ** 2 - ws ** 2) / wo ** 2
    R["piezo"]["extensional"] = {
        "f_sc": (ws / 2 / np.pi).tolist(),
        "f_oc": (wo / 2 / np.pi).tolist(),
        "k2": k2s.tolist()}
    log("  extensional: k2 = " + ", ".join(f"{v:.3f}" for v in k2s))


# ==========================================================================
# memory: analytical limits
# ==========================================================================
def v5_memory():
    w0 = 2 * np.pi * 1000.0
    tau = 1e-4
    K = np.array([[w0 ** 2]])
    M = np.array([[1.0]])

    def ana(t, z=tau * w0 / 2):
        wd = w0 * np.sqrt(1 - z * z)
        return (1 / w0 ** 2) * (1 - np.exp(-z * w0 * t) *
                                (np.cos(wd * t) + (z * w0 / wd) * np.sin(wd * t)))

    rows, errs = [], []
    for Nt in [200, 400, 800, 1600]:
        T = 20 * tau
        dt = T / Nt
        t, x, *_ = f6.transient(K, M, K, np.array([1.0]), 1.0, tau, dt, Nt,
                                nmodes=1)
        e = float(np.max(np.abs(x[0] - ana(t))) / np.max(np.abs(ana(t))))
        errs.append(e)
        rows.append({"Nt": Nt, "dt": dt, "rel_err": e})
    order = float(np.polyfit(np.log([1 / r["Nt"] for r in rows]),
                             np.log(errs), 1)[0])
    R["memory_alpha1"] = {"rows": rows, "order": order,
                          "zeta_exact": float(f6.complex_frequency(w0, tau, 1.0).real)}
    log(f"  alpha=1 vs analytic KV: order {order:.2f}")

    # harmonic response vs analytic transfer function
    harm = []
    for a_ in [1.0, 0.7, 0.5]:
        for r_ in [0.5, 1.0, 2.0]:
            Om = r_ * w0
            T = 200 * 2 * np.pi / Om
            N = 60000
            dt = T / N
            f = lambda tt, Om=Om: np.array([np.sin(Om * tt)])
            t, x, *_ = f6.transient(K, M, K, f, a_, tau, dt, N, nmodes=1)
            sel = t > 0.8 * T
            tt, yy = t[sel], x[0, sel]
            c1 = 2 * np.mean(yy * np.sin(Om * tt))
            c2 = 2 * np.mean(yy * np.cos(Om * tt))
            amp = np.hypot(c1, c2)
            Ha = abs(1.0 / (-Om ** 2 + w0 ** 2 * (1 + (1j * Om * tau) ** a_)))
            harm.append({"alpha": a_, "Omega_over_w0": r_, "amp": amp,
                         "amp_analytic": Ha, "ratio": amp / Ha})
            log(f"  alpha={a_} Om/w0={r_}: |H| ratio {amp/Ha:.4f}")
    R["memory_harmonic"] = harm

    # tau -> 0 recovers the memory-free response
    t, x, *_ = f6.transient(K, M, K, np.array([1.0]), 1.0, 1e-40, 1e-5, 4000,
                            nmodes=1)
    R["memory_tau0"] = float(np.max(np.abs(x[0] -
                                           (1 - np.cos(w0 * t)) / w0 ** 2)))

    # the delivered L1 stencil, transcribed verbatim
    R["l1_scheme"] = l1_scheme_check()


def l1_delivered_stencil(w, f, tau, alpha, dt, Nt):
    """Verbatim transcription of modal_fractional() of
    FEM6_memory_piezo_SG_2D.m, 1-based indexing kept for fidelity.

        q(:,2) = 0.5*dt^2*f;
        dq(:,1) = q(:,2)-q(:,1);
        for n = 2:Nt
            Dq = c*(dq(:,n-1:-1:1)*b(1:n-1)');
            q(:,n+1) = 2*q(:,n) - q(:,n-1) + dt^2*(f - w.^2.*(q(:,n)+tau^alpha*Dq));
            dq(:,n) = q(:,n+1)-q(:,n);
        end
    """
    from math import gamma as _gamma
    q = np.zeros(Nt + 2)                     # MATLAB index i  <->  q[i]
    if alpha >= 1:
        b = np.zeros(Nt + 1); b[0] = 1.0; c = 1.0 / dt
    else:
        j = np.arange(Nt + 1)
        b = (j + 1) ** (1 - alpha) - j ** (1 - alpha)
        c = dt ** (-alpha) / _gamma(2 - alpha)
    fa = (np.full(Nt + 3, float(f)) if np.isscalar(f) else np.asarray(f, float))
    q[2] = 0.5 * dt ** 2 * fa[1]
    dq = np.zeros(Nt + 2); dq[1] = q[2] - q[1]
    for n in range(2, Nt + 1):
        js = np.arange(n - 1, 0, -1)         # MATLAB  n-1:-1:1
        Dq = c * np.dot(dq[js], b[0:n - 1])  # MATLAB  b(1:n-1)
        q[n + 1] = 2 * q[n] - q[n - 1] + dt ** 2 * (
            fa[n] - w ** 2 * (q[n] + tau ** alpha * Dq))
        dq[n] = q[n + 1] - q[n]
    return q[1:Nt + 1]


def _amp(qq, tt, Om):
    m = tt > tt[-1] - 4 * 2 * np.pi / Om
    M = np.vstack([np.sin(Om * tt[m]), np.cos(Om * tt[m])]).T
    ab, *_ = np.linalg.lstsq(M, qq[m], rcond=None)
    return float(np.hypot(*ab))


def l1_scheme_check():
    """Delivered L1 stencil against the analytic transfer function
    H(Om) = 1/(-Om^2 + w0^2 (1 + (i Om tau)^alpha)) -- the only test that
    actually exercises the memory discretisation."""
    w0 = 2 * np.pi * 1e4
    tau = 0.3 / w0
    rows = []
    for alpha in [1.0, 0.9, 0.7, 0.5, 0.3]:
        for r in [0.25, 0.5, 1.0, 1.5, 2.0]:
            Om = r * w0
            ppd, nper = 200, 40
            dt = (2 * np.pi / Om) / ppd
            Nt = nper * ppd
            tt = np.arange(1, Nt + 1) * dt
            fa = np.sin(Om * np.arange(Nt + 3) * dt)
            qq = l1_delivered_stencil(w0, fa, tau, alpha, dt, Nt)
            amp = _amp(qq, tt, Om)
            Ha = abs(1.0 / (-Om ** 2 + w0 ** 2 * (1 + (1j * Om * tau) ** alpha)))
            rows.append({"alpha": alpha, "Omega_over_w0": r, "amp": amp,
                         "amp_analytic": Ha, "ratio": amp / Ha})
    worst = max(abs(r["ratio"] - 1) for r in rows)
    conv = []
    Om = w0
    Ha = abs(1.0 / (-Om ** 2 + w0 ** 2 * (1 + (1j * Om * tau))))
    for ppd in [50, 100, 200, 400]:
        dt = (2 * np.pi / Om) / ppd
        Nt = 40 * ppd
        tt = np.arange(1, Nt + 1) * dt
        fa = np.sin(Om * np.arange(Nt + 3) * dt)
        amp = _amp(l1_delivered_stencil(w0, fa, tau, 1.0, dt, Nt), tt, Om)
        conv.append({"ppd": ppd, "dt": dt, "amp": amp,
                     "rel_err": abs(amp / Ha - 1)})
    errs = [c["rel_err"] for c in conv]
    order = float(np.log(errs[1] / errs[-1]) / np.log(4)) if errs[-1] > 0 else 0.0
    log(f"  delivered L1 stencil vs analytic |H|: worst error "
        f"{100*worst:.3f} % over alpha 1.0..0.3, Omega/w0 0.25..2")
    return {"rows": rows, "worst_ratio_error": worst, "convergence": conv,
            "observed_order": order, "pass": bool(worst < 0.01)}


def v6_modal_truncation():
    mat = MAT_STEEL
    mesh = f6.mesh_rect(20, 4, 1.0, 0.2)
    m = f6.assemble(mesh, mat, f6.second_moment("cuboid", 0.05, 0.02))
    K, M, idx, _ = f6.reduce(m, "short")
    f = m.edge_traction(tx=1e6)[idx]
    u = np.linalg.solve(K, f)
    right = [n for n, xy in enumerate(mesh.nodes) if abs(xy[0] - 1) < 1e-12]
    nodes = [m.mech_dof[n][0] for n in right]
    pos = np.searchsorted(idx, nodes)
    ud = np.mean(u[pos])
    rows = []
    for nm in [1, 2, 4, 8, 12, 16, 24]:
        w, Phi = f6.modes(K, M, nmodes=nm)
        um = Phi[np.ix_(pos, np.arange(len(w)))] @ (Phi.T @ f / w ** 2)
        rows.append({"nmodes": nm, "u_modal": float(np.mean(um)),
                     "rel_err": float(abs(np.mean(um) / ud - 1))})
    R["truncation"] = {"u_direct": float(ud), "rows": rows}
    log(f"  static modal truncation: direct {ud*1e6:.4f} um, "
        f"24 modes err {rows[-1]['rel_err']:.2e}")


def v7_domain_comparison():
    rows = []
    u0, _, _, _ = u_right(20, 4)
    for dom in ["ellipsoid", "cuboid"]:
        for l in [0.05, 0.10, 0.20]:
            u, _, _, _ = u_right(20, 4, l, dom)
            rows.append({"domain": dom, "l_over_L": l, "u": u,
                         "ratio": u / u0})
    # matched second moment (a = l sqrt(3/5))
    for l in [0.05, 0.10, 0.20]:
        a = l * np.sqrt(3.0 / 5.0)
        u, _, _, _ = u_right(20, 4, a, "cuboid")
        rows.append({"domain": "cuboid (equal M)", "l_over_L": l, "u": u,
                     "ratio": u / u0})
    R["domain"] = {"rows": rows, "u_classical": u0}
    for r in rows:
        log(f"  {r['domain']:>18s} l/L={r['l_over_L']:.2f}: {r['u']*1e6:.4f} um "
            f"ratio {r['ratio']:.4f}")


# ==========================================================================
def main():
    t0 = time.time()
    log("V1 patch test / element checks")
    v1_patch_test()
    log(f"  patch rel err {R['patch']['rel_err']:.2e}; "
        f"FEM-1 operator rel diff {R['patch']['ellipsoid_vs_FEM1']:.2e}; "
        f"cuboid/ellipsoid {R['patch']['cuboid_over_ellipsoid_equal_halfwidth']:.6f}")
    log("V2 FEM-1 2-D benchmark")
    v2_fem1_benchmark()
    log("V3 mesh convergence")
    v3_mesh_convergence()
    log("V4 piezoelectric checks")
    v4_piezo()
    log("V5 memory limits")
    v5_memory()
    log("V6 modal truncation")
    v6_modal_truncation()
    log("V7 domain comparison")
    v7_domain_comparison()
    R["runtime_s"] = time.time() - t0

    with open(os.path.join(OUT, "verification.json"), "w") as fh:
        json.dump(R, fh, indent=2)
    write_markdown(R)
    log(f"done in {R['runtime_s']:.1f} s -> results/verification.md")


def write_markdown(R):
    L = []
    A = L.append
    A("# FEM-6 verification report\n")
    A("Generated by `python/run_verification.py`. Every number below is "
      "produced by this run; no value is typed in by hand.\n")
    p = R["patch"]
    A("## V1 Element and operator checks\n")
    A("| check | value | reference |\n|---|---|---|")
    A(f"| constant-strain patch energy | {p['U']:.10e} | "
      f"{p['U_exact']:.10e} (rel. err {p['rel_err']:.1e}) |")
    A(f"| gradient energy for constant strain | {p['grad_energy_const_strain']:.2e} | 0 |")
    A(f"| ellipsoid K_g vs FEM-1 (l^2/10)(K_xx+K_yy) | {p['ellipsoid_vs_FEM1']:.1e} | 0 (rel.) |")
    A(f"| K_g(cuboid)/K_g(ellipsoid) at equal half-width | "
      f"{p['cuboid_over_ellipsoid_equal_halfwidth']:.6f} | 1.666667 (5/3) |")
    A(f"| cuboid vs ellipsoid at equal second moment | "
      f"{p['cuboid_eq_moment_vs_ellipsoid']:.1e} | 0 (rel.) |")

    A("\n## V2 FEM-1 2-D benchmark (e = 0)\n")
    B = R["fem1"]
    A(f"Plane-strain uniaxial reference: {B['u_analytic_plane_strain']*1e6:.3f} um. "
      f"FEM-1 reports {B['paper_u_classical_um']:.2f} um and "
      f"{B['paper_u_l020_um']:.2f} um (ratio {B['paper_ratio_l020']:.2f}) "
      "at l/L = 0.20 on a 20x4 mesh.\n")
    A("| mesh | dof | u_R (um) |\n|---|---|---|")
    for r in B["meshes"]:
        A(f"| {r['nx']}x{r['ny']} | {r['ndof']} | {r['u']*1e6:.4f} |")
    A("\n| l/L | u_R (um) | u/u(l=0) |\n|---|---|---|")
    for r in B["length"]:
        A(f"| {r['l_over_L']:.2f} | {r['u']*1e6:.4f} | {r['ratio']:.4f} |")

    A("\n## V3 Mesh convergence (l = 0)\n")
    A("| mesh | u_R (um) | rel. error vs 60x12 |\n|---|---|---|")
    for r in R["convergence"]["rows"]:
        A(f"| {r['nx']}x{r['ny']} | {r['u']*1e6:.4f} | {r['rel_err']:.2e} |")
    A(f"\nObserved order (last three meshes): {R['convergence']['order']:.2f}\n")

    A("\n## V4 Piezoelectric checks\n")
    P = R["piezo"]
    A(f"Through-thickness electrodes on a homogeneous BaTiO3 bridge:\n")
    A(f"* f_short = {P['f_sc']:.3f} Hz, f_open = {P['f_oc']:.3f} Hz, "
      f"k_eff^2 = {P['k2']:.3e}")
    A(f"* electrode capacitance beta = {P['beta']:.4e} F")
    A(f"* min eig(K_oc - K_sc) / max|eig| = {P['min_eig_dK']:.3e} (>= 0 required)")
    A(f"* min eig(K_sc) / max|eig| = {P['min_eig_Ksc']:.3e} (> 0 required)")
    A(f"* mode-1 electrode charge |d.phi| = {P['mode1_charge']:.3e}")
    A("\nLength-extensional configuration (poling along the axis):\n")
    A("| mode | f_short (Hz) | f_open (Hz) | k_eff^2 |\n|---|---|---|---|")
    for i, (fs, fo, k) in enumerate(zip(P["extensional"]["f_sc"],
                                        P["extensional"]["f_oc"],
                                        P["extensional"]["k2"])):
        A(f"| {i+1} | {fs:.2f} | {fo:.2f} | {k:.4f} |")

    A("\n## V5 Memory limits\n")
    M5 = R["memory_alpha1"]
    A("alpha = 1 against the closed-form Kelvin-Voigt modal solution "
      "(zeta = omega tau / 2):\n")
    A("| Nt | dt (s) | max rel. error |\n|---|---|---|")
    for r in M5["rows"]:
        A(f"| {r['Nt']} | {r['dt']:.3e} | {r['rel_err']:.3e} |")
    A(f"\nObserved order {M5['order']:.2f} (backward difference of the "
      "integer derivative is first order; the fractional L1 is O(dt^(2-alpha))).\n")
    A("\nSteady-state harmonic amplitude against the analytic transfer "
      "function 1/(-w^2 + w0^2(1+(i w tau)^alpha)):\n")
    A("| alpha | Omega/w0 | |H| numerical | |H| analytic | ratio |\n|---|---|---|---|---|")
    for r in R["memory_harmonic"]:
        A(f"| {r['alpha']:.1f} | {r['Omega_over_w0']:.1f} | {r['amp']:.5e} | "
          f"{r['amp_analytic']:.5e} | {r['ratio']:.4f} |")
    A(f"\ntau -> 0: max deviation from the undamped solution "
      f"{R['memory_tau0']:.2e}.\n")
    A("\nL1 indexing of the delivered `modal_fractional` (weights b_1..b_{n-1} "
      "instead of b_0..b_{n-1}):\n")
    A("| alpha | delivered late oscillation | adjusted late oscillation | ratio |\n|---|---|---|---|")
    l1 = R["l1_scheme"]
    A("\n### Delivered L1 stencil vs the analytic transfer function\n")
    A("Transcribed verbatim from `modal_fractional()`; `w0 tau = 0.3`.\n")
    A("| alpha | Omega/w0 | amplitude | analytic |H| | ratio |")
    A("|---|---|---|---|---|")
    for r in l1["rows"]:
        A(f"| {r['alpha']:.1f} | {r['Omega_over_w0']:.2f} | {r['amp']:.4e} | "
          f"{r['amp_analytic']:.4e} | {r['ratio']:.4f} |")
    A(f"\nWorst deviation {100*l1['worst_ratio_error']:.3f} % -> "
      f"{'PASS' if l1['pass'] else 'FAIL'}\n")
    A("Time-step refinement at Omega = w0, alpha = 1:\n")
    A("| pts/period | dt | rel. error |")
    A("|---|---|---|")
    for c in l1["convergence"]:
        A(f"| {c['ppd']} | {c['dt']:.3e} | {c['rel_err']:.2e} |")
    A(f"\nObserved order {l1['observed_order']:.2f}")

    A("\n## V6 Static modal truncation\n")
    A(f"Direct solution: {R['truncation']['u_direct']*1e6:.4f} um\n")
    A("| modes | u_modal (um) | rel. error |\n|---|---|---|")
    for r in R["truncation"]["rows"]:
        A(f"| {r['nmodes']} | {r['u_modal']*1e6:.4f} | {r['rel_err']:.2e} |")

    A("\n## V7 Domain comparison (20x4, l/L = 0.05, 0.10, 0.20)\n")
    A("| domain | l/L | u_R (um) | u/u_classical |\n|---|---|---|---|")
    for r in R["domain"]["rows"]:
        A(f"| {r['domain']} | {r['l_over_L']:.2f} | {r['u']*1e6:.4f} | "
          f"{r['ratio']:.4f} |")
    A(f"\nClassical u_R = {R['domain']['u_classical']*1e6:.4f} um.\n")

    open(os.path.join(OUT, "verification.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
