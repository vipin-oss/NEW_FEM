"""
run_independent_checks.py -- the headline numbers, each against a route that
does not use the finite element assembly that produced them.

    F1  the fundamental frequency of an elastic strip, e = mu = 0 and no
        gradient term, against clamped-clamped and clamped-free
        Euler-Bernoulli and Timoshenko closed forms, with the plane-stress
        beam modulus   E_b = 1/(C_p^{-1})_xx  (the free-edge modulus, not the
        plate modulus C_p[0,0], which is what a wide plate would use).

    F2  the damping ratio of the fractional Kelvin-Voigt element against the
        roots of a polynomial: for alpha = p/q the pole equation
        s^2 + w0^2 (1 + (tau s)^alpha) = 0 becomes a polynomial of degree 2q
        in w = s^(1/q), so the roots can be had with numpy.roots instead of
        the Newton iteration of fem6_core.complex_frequency.  At alpha = 1 the
        closed form is w0 tau/2.

    F3  the flexoelectric coupling in the uniform-curvature limit.  A plate
        carrying the exact pure-bending field (-kappa x y, kappa x^2/2) has a
        uniform strain gradient, so its 1-dof coupling follows from
        capacitance, charge and bending energy alone:

            x = 12 mu^2 / (E_b h^2 kappa33),      k^2 = x/(1+x),

        and the same x can be read off the finite element solution of that one
        prescribed field as x = beta V^2 / u^T K u.  This is a different
        statement from the constant-strain patch test (check F2 in run_all):
        the field here is quadratic in the displacement, not constant.

Writes results/independent_checks.{json,md}.
"""
from __future__ import annotations

import json
import os
import sys
from fractions import Fraction

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fem6_core as f6          # noqa: E402
import materials as mt          # noqa: E402

RES = os.path.join(ROOT, "results")
L, H = 200e-6, 10e-6


# ---------------------------------------------------------------------------
# F1  frequencies of the elastic strip
# ---------------------------------------------------------------------------
def eb_frequency(beta_l, E, rho, h, L):
    """Euler-Bernoulli: f = (betaL)^2/(2 pi L^2) sqrt(E I / (rho A))."""
    return beta_l ** 2 / (2 * np.pi * L ** 2) * np.sqrt(E * h ** 2 / (12 * rho))


def timoshenko_frequency(beta_l, E, G, rho, h, L, ks=5.0 / 6.0):
    """Timoshenko correction for a general boundary condition,
    f_T = f_EB / sqrt(1 + (betaL)^2 (I/A L^2)(1 + E/(ks G)))."""
    f_eb = eb_frequency(beta_l, E, rho, h, L)
    corr = 1.0 + beta_l ** 2 * (h ** 2 / (12 * L ** 2)) * (1.0 + E / (ks * G))
    return f_eb / np.sqrt(corr)


def fem_frequencies(clamped, nx, ny, h=H, nm=3):
    m = mt.batio3("x", "plane_stress")
    core = mt.to_core(m)
    core.mu = 0.0
    core.e[:] = 0.0                       # pure elastic
    mesh = f6.mesh_rect(nx, ny, L, h)
    mdl = f6.assemble(mesh, core, np.zeros((2, 2)), clamped_edges=clamped,
                      gradient=False)
    K, M, _, _ = f6.reduce(mdl, "short")
    w, _ = f6.modes(K, M, nm)
    return w / (2 * np.pi)


def check_frequencies():
    m = mt.batio3("x", "plane_stress")
    Cp = m.C()
    E_b = 1.0 / np.linalg.inv(Cp)[0, 0]        # beam modulus, sigma_yy = 0
    E_p = Cp[0, 0]                             # wide-plate modulus
    G = m.C44
    rho = m.rho
    out = {"E_beam": float(E_b), "E_plate": float(E_p), "G": float(G),
           "rho": float(rho), "cases": []}

    for name, clamped, bl in (("clamped-free", ("left",), 1.8751),
                              ("clamped-clamped", ("left", "right"), 4.7300)):
        f_eb = eb_frequency(bl, E_b, rho, H, L)
        f_ti = timoshenko_frequency(bl, E_b, G, rho, H, L)
        row = {"case": name, "betaL": bl, "f_EB_kHz": f_eb / 1e3,
               "f_Timoshenko_kHz": f_ti / 1e3, "mesh": []}
        for nx, ny in ((48, 4), (96, 4), (128, 4)):
            f = float(fem_frequencies(clamped, nx, ny)[0])
            row["mesh"].append({"nx": nx, "ny": ny, "f_FEM_kHz": f / 1e3,
                                "err_vs_EB_pct": 100 * (f / f_eb - 1),
                                "err_vs_Ti_pct": 100 * (f / f_ti - 1)})
        # what the plate modulus would have predicted, for contrast
        row["f_EB_plate_modulus_kHz"] = eb_frequency(bl, E_p, rho, H, L) / 1e3
        out["cases"].append(row)
    return out


# ---------------------------------------------------------------------------
# F2  the fractional pole from a polynomial, not from Newton
# ---------------------------------------------------------------------------
def pole_from_polynomial(omega0, tau, alpha):
    """Roots of s^2 + w0^2 (1 + (tau s)^alpha) = 0 for rational alpha = p/q.

    With s = w^q the equation is  w^(2q) + w0^2 tau^alpha w^p + w0^2 = 0,
    a polynomial of degree 2q.  Every root is a candidate; each one is then
    checked against the *original* equation with the principal branch of the
    complex power, because the substitution only respects that branch for some
    of them.
    """
    fr = Fraction(alpha).limit_denominator(20)
    p, q = fr.numerator, fr.denominator
    coef = np.zeros(2 * q + 1, dtype=complex)
    coef[0] = 1.0                                   # w^(2q)
    coef[2 * q - p] = omega0 ** 2 * tau ** alpha    # w^p
    coef[2 * q] = omega0 ** 2                       # w^0
    cands = np.roots(coef)
    best = None
    for w in cands:
        s = w ** q
        if abs(s.imag) < 1e-9 or s.real > 0:
            continue
        res = abs(s ** 2 + omega0 ** 2 * (1.0 + (tau * s) ** alpha))
        scale = abs(s) ** 2
        if res / scale > 1e-8:
            continue                                # wrong branch
        if best is None or s.imag > best.imag:
            best = s
    return best, (p, q), float(np.min(np.abs(cands)))


def check_damping():
    f_hz = 6.727321873203974e6                    # memory_variants mode 4
    w0 = 2 * np.pi * f_hz
    out = {"f_Hz": f_hz, "rows": []}
    for omt in (0.3, 1.0):
        tau = omt / w0
        s_cf = None
        for a in np.linspace(0.02, 1.0, 60):      # continue down to each alpha
            s_cf = f6.complex_frequency(w0, tau, float(a), s0=s_cf)
        for alpha in (1.0, 0.9, 0.7, 0.5, 0.3):
            s_newton = f6.complex_frequency(w0, tau, alpha,
                                            s0=f6.complex_frequency(
                                                w0, tau, 1.0))
            s_poly, pq, _ = pole_from_polynomial(w0, tau, alpha)
            z_newton = -s_newton.real / abs(s_newton)
            z_poly = -s_poly.real / abs(s_poly) if s_poly is not None else np.nan
            row = {"omega_tau": omt, "alpha": alpha,
                   "rational": f"{pq[0]}/{pq[1]}",
                   "s_newton": [s_newton.real, s_newton.imag],
                   "s_poly": None if s_poly is None else [s_poly.real,
                                                          s_poly.imag],
                   "zeta_newton": float(z_newton),
                   "zeta_poly": float(z_poly),
                   "rel_diff": float(abs(z_poly / z_newton - 1))
                   if s_poly is not None else None,
                   "zeta_kv_exact": omt / 2.0}
            out["rows"].append(row)
    return out


# ---------------------------------------------------------------------------
# F3  flexoelectric coupling in the uniform-curvature limit
# ---------------------------------------------------------------------------
def check_flexo_curvature(kappa=1.0):
    """Prescribe the pure-bending field and read the coupling two ways.

    Poling is along y (electrodes on the two long faces), so the field across
    the gap is E_y and the permittivity that enters is kappa_yy = kappa_33.
    The displacement field is the one of the patch test in run_flexo_check.py,
    u = kappa x y, v = -kappa x^2/2.  Its only non-zero strain is
    eps_xx = kappa y, so the neutral axis sits on the edge y = 0 and

        U = 1/2 C^p_11 kappa^2 L h^3/3,   q = mu kappa L,   C = kappa33 L/h,

    which gives x = 3 mu^2/(C^p_11 h^2 kappa33).  Two things this pins down
    that the constant-strain patch test cannot: the modulus that enters is the
    constrained one C^p_11 (the field has eps_yy = 0 exactly), not the beam
    modulus E_b; and the coupling really is the energy triple beta V^2/(u^T K u),
    not just a voltage.
    """
    m = mt.batio3("y", "plane_stress")
    core = mt.to_core(m)
    core.mu = 1.0e-6
    core.e[:] = 0.0                       # flexoelectric only
    Cp = m.C()
    E_b = 1.0 / np.linalg.inv(Cp)[0, 0]
    kap = float(m.kappa()[1, 1])
    x_an = 3.0 * core.mu ** 2 / (Cp[0, 0] * H ** 2 * kap)
    x_mid = 12.0 * core.mu ** 2 / (Cp[0, 0] * H ** 2 * kap)
    x_beam = 12.0 * core.mu ** 2 / (E_b * H ** 2 * kap)
    out = {"kappa_1_per_m": kappa, "E_beam": float(E_b),
           "C11_plane_stress": float(Cp[0, 0]), "kappa33": kap,
           "mu": 1.0e-6, "x_analytic": float(x_an),
           "x_midplane": float(x_mid), "x_beam_modulus": float(x_beam),
           "mesh": []}
    for nx, ny in ((8, 2), (24, 4), (48, 8), (96, 4)):
        mesh = f6.mesh_rect(nx, ny, L, H)
        mdl = f6.assemble(mesh, core, np.zeros((2, 2)), clamped_edges=(),
                          gradient=False)
        Ksc, _, idx, _ = f6.reduce(mdl, "short")
        _, _, _, (d, beta) = f6.reduce(mdl, "open")
        u_full = np.zeros(mdl.ndof_mech)
        for n, (x, y) in enumerate(mesh.nodes):
            g = mdl.mech_dof[n]
            u_full[g[0]] = kappa * x * y
            u_full[g[1]] = kappa * y
            u_full[g[2]] = kappa * x
            u_full[g[3]] = kappa
            u_full[g[4]] = -0.5 * kappa * x ** 2
            u_full[g[5]] = -kappa * x
            u_full[g[6]] = 0.0
            u_full[g[7]] = 0.0
        u = u_full[idx]
        V = float(d @ u) / beta
        U = 0.5 * float(u @ (Ksc @ u))
        x_fem = beta * V ** 2 / (2.0 * U) if U > 0 else float("nan")
        out["mesh"].append({"nx": nx, "ny": ny, "V": V,
                            "V_analytic": core.mu * kappa * H / kap,
                            "U": U,
                            "U_analytic": 0.5 * Cp[0, 0] * kappa ** 2
                            * L * H ** 3 / 3.0,
                            "x_fem": x_fem, "x_analytic": float(x_an),
                            "k2_fem": x_fem / (1 + x_fem),
                            "k2_analytic": x_an / (1 + x_an),
                            "rel_diff": abs(x_fem / x_an - 1)})
    return out


# ---------------------------------------------------------------------------
# F4  the second-moment factors of the three window shapes
# ---------------------------------------------------------------------------
def check_moments(a1=1.0, a2=0.6):
    """M_ii = a_i^2/3, a_i^2/4, a_i^2/5 from quadrature, not from the formula.

    The factors are asserted in the paper as the second moments of a cuboid,
    an ellipse and an ellipsoid.  Here each one is obtained by integrating
    r_i^2 over the shape and dividing by its measure: Gauss-Legendre for the
    cuboid and the ellipsoid, a dense trapezoid rule in the polar angle for
    the ellipse.
    """
    xg, wg = np.polynomial.legendre.leggauss(40)
    out = {"a1": a1, "a2": a2, "rows": []}

    # cuboid: mean of x_i^2 over [-a_i, a_i]
    m1 = 0.5 * float(np.sum(wg * (a1 * xg) ** 2))
    m2 = 0.5 * float(np.sum(wg * (a2 * xg) ** 2))
    out["rows"].append({"shape": "cuboid", "factor": 3.0,
                        "M11_num": m1, "M11_exact": a1 ** 2 / 3.0,
                        "M22_num": m2, "M22_exact": a2 ** 2 / 3.0})

    # ellipse (2-D): x = rho cos(theta), r(theta) = a1 a2 / sqrt(...)
    th = np.linspace(0, 2 * np.pi, 1000001)[:-1]
    r = a1 * a2 / np.sqrt((a2 * np.cos(th)) ** 2 + (a1 * np.sin(th)) ** 2)
    area = np.pi * a1 * a2
    e1 = float(np.trapezoid(r ** 4 * np.cos(th) ** 2, th) / (4 * area))
    e2 = float(np.trapezoid(r ** 4 * np.sin(th) ** 2, th) / (4 * area))
    out["rows"].append({"shape": "ellipse (2-D)", "factor": 4.0,
                        "M11_num": e1, "M11_exact": a1 ** 2 / 4.0,
                        "M22_num": e2, "M22_exact": a2 ** 2 / 4.0})

    # ellipsoid (3-D): the cross-section perpendicular to x_i is pi a_j a_k (1-t^2)
    def ell(a):
        num = float(np.sum(wg * xg ** 2 * (1 - xg ** 2)))
        den = float(np.sum(wg * (1 - xg ** 2)))
        return a ** 2 * num / den
    out["rows"].append({"shape": "ellipsoid (3-D)", "factor": 5.0,
                        "M11_num": ell(a1), "M11_exact": a1 ** 2 / 5.0,
                        "M22_num": ell(a2), "M22_exact": a2 ** 2 / 5.0})
    out["worst_rel"] = float(max(
        abs(r["M11_num"] / r["M11_exact"] - 1) for r in out["rows"])
        + max(abs(r["M22_num"] / r["M22_exact"] - 1) for r in out["rows"]))
    return out


def write_latex(F1, F2, F3, F4):
    """Paper_12/table_independent.tex, built from the values just computed."""
    ROW = chr(92) * 2
    BS = chr(92)
    L = ["% generated by python/run_independent_checks.py -- do not edit",
         "@@BS@@begin{tabular}{@{}lrrrr@{}}",
         "@@BS@@toprule",
         "boundary & Euler--Bernoulli & Timoshenko & FEM & error@@ROW@@",
         "& [kHz] & [kHz] & [kHz] & vs EB [@@BS@@%]@@ROW@@",
         "@@BS@@midrule",
         "@@BS@@multicolumn{5}{@{}l}{@@BS@@emph{(a) elastic strip, "
         "$e=\\mu=0$, no gradient term, $48\\times4$ mesh}}@@ROW@@"]
    for c in F1["cases"]:
        m0 = c["mesh"][0]
        nm = c["case"].replace("-", "@@BS@@textendash ")
        L.append(f"{nm} & {c['f_EB_kHz']:.1f} & {c['f_Timoshenko_kHz']:.1f} "
                 f"& {m0['f_FEM_kHz']:.1f} & {m0['err_vs_EB_pct']:+.2f}@@ROW@@")
    L += ["@@BS@@midrule",
          "@@BS@@multicolumn{5}{@{}l}{@@BS@@emph{(b) damping ratio: Newton "
          "pole of the pole equation against its polynomial roots}}@@ROW@@",
          "$@@BS@@omega@@BS@@tau$ & $@@BS@@alpha$ & "
          "@@BS@@multicolumn{2}{c}{$@@BS@@zeta$: Newton / polynomial} & "
          "$@@BS@@omega@@BS@@tau/2$@@ROW@@",
          "@@BS@@midrule"]
    for r in F2["rows"]:
        zp = "--" if r["zeta_poly"] is None else f"{r['zeta_poly']:.6f}"
        L.append(f"{r['omega_tau']:g} & {r['alpha']:g} & "
                 f"{r['zeta_newton']:.6f} & {zp} & "
                 f"{r['zeta_kv_exact']:.6f}@@ROW@@")
    L += ["@@BS@@midrule",
          "@@BS@@multicolumn{5}{@{}l}{@@BS@@emph{(c) flexoelectric coupling, "
          "uniform curvature: $x=3@@BS@@mu^2/(C^p_{11}h^2@@BS@@kappa_{33})$ "
          "against the finite element energy triple}}@@ROW@@",
          "mesh & @@BS@@multicolumn{2}{c}{$V_{oc}$ [V]: FEM / closed form} & "
          "$x$: FEM & $x$: closed form@@ROW@@",
          "@@BS@@midrule"]
    for r in F3["mesh"]:
        L.append(f"{r['nx']}$@@BS@@times${r['ny']} & @@BS@@multicolumn{{2}}{{c}}"
                 f"{{{r['V']:.6e} / {r['V_analytic']:.6e}}} & "
                 f"{r['x_fem']:.6e} & {r['x_analytic']:.6e}@@ROW@@")
    L += ["@@BS@@midrule",
          "@@BS@@multicolumn{5}{@{}l}{@@BS@@emph{(d) second moments of the "
          "window shapes: quadrature against the printed factor}}@@ROW@@",
          "shape & @@BS@@multicolumn{2}{c}{$M_{11}$} & "
          "@@BS@@multicolumn{2}{c}{$M_{22}$}@@ROW@@",
          "@@BS@@midrule"]
    for r in F4["rows"]:
        L.append(f"{r['shape']} & @@BS@@multicolumn{{2}}{{c}}"
                 f"{{{r['M11_num']:.10f} ($a_1^2/{r['factor']:g}$)}} & "
                 f"@@BS@@multicolumn{{2}}{{c}}"
                 f"{{{r['M22_num']:.10f} ($a_2^2/{r['factor']:g}$)}}@@ROW@@")
    L += ["@@BS@@bottomrule", "@@BS@@end{tabular}"]
    txt = "\n".join(L) + "\n"
    txt = txt.replace("@@BS@@", BS).replace("@@ROW@@", ROW)
    with open(os.path.join(ROOT, "Paper_12", "table_independent.tex"), "w") as fh:
        fh.write(txt)


def main():
    print("  F1 frequencies", flush=True)
    F1 = check_frequencies()
    print("  F2 damping", flush=True)
    F2 = check_damping()
    print("  F3 flexo curvature", flush=True)
    F3 = check_flexo_curvature()
    F4 = check_moments()
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "independent_checks.json"), "w") as fh:
        json.dump({"F1_frequencies": F1, "F2_damping": F2,
                   "F3_flexo_curvature": F3, "F4_window_moments": F4},
                  fh, indent=1)

    md = ["# Independent checks of the headline numbers", "",
          "Each row compares a number used in the paper with a value obtained "
          "along a route that does not share the code path that produced it.",
          ""]
    md += ["## F1 -- fundamental frequency of the elastic strip "
           "(e = mu = 0, no gradient term)", "",
           f"$L=\\SI{{200}}{{\\micro\\metre}}$, depth $h=\\SI{{10}}{{\\micro\\metre}}$, "
           f"$\\rho=\\SI{{{F1['rho']:.0f}}}{{\\kilo\\gram\\per\\cubic\\metre}}$ "
           "(unverified), beam modulus "
           f"$E_b=1/(\\bm C_p^{{-1}})_{{xx}}={F1['E_beam']:.4e}$ Pa "
           f"(a wide plate would use $C^p_{{11}}={F1['E_plate']:.4e}$ Pa).", "",
           "| boundary | closed form | value (kHz) | FEM 48x4 | 96x4 | 128x4 | err vs EB | err vs Timoshenko |",
           "|---|---|---|---|---|---|---|---|"]
    for c in F1["cases"]:
        mrows = c["mesh"]
        md.append(f"| {c['case']} | Euler-Bernoulli | {c['f_EB_kHz']:.1f} | "
                  f"{mrows[0]['f_FEM_kHz']:.1f} | {mrows[1]['f_FEM_kHz']:.1f} | "
                  f"{mrows[2]['f_FEM_kHz']:.1f} | "
                  f"{mrows[0]['err_vs_EB_pct']:+.3f} % | "
                  f"{mrows[0]['err_vs_Ti_pct']:+.3f} % |")
        md.append(f"| {c['case']} | Timoshenko | {c['f_Timoshenko_kHz']:.1f} | "
                  f"-- | -- | -- | (EB row) | -- |")
    md += ["", "## F2 -- damping ratio of the fractional Kelvin-Voigt element", "",
           "`zeta` from the Newton pole of `fem6_core.complex_frequency` "
           "against the roots of the same equation rewritten as a polynomial "
           "in $w=s^{1/q}$ for $\\alpha=p/q$ (`numpy.roots`).", "",
           "| $\\omega\\tau$ | $\\alpha$ | $p/q$ | $\\zeta$ (Newton) | "
           "$\\zeta$ (polynomial) | rel. diff | $\\omega\\tau/2$ |",
           "|---|---|---|---|---|---|---|"]
    for r in F2["rows"]:
        md.append(f"| {r['omega_tau']:g} | {r['alpha']:g} | {r['rational']} | "
                  f"{r['zeta_newton']:.6f} | "
                  f"{'--' if r['zeta_poly'] is None else format(r['zeta_poly'], '.6f')} | "
                  f"{'--' if r['rel_diff'] is None else format(r['rel_diff'], '.1e')} | "
                  f"{r['zeta_kv_exact']:.6f} |")
    md += ["", "## F3 -- flexoelectric coupling in the uniform-curvature limit", "",
           "A plate carrying the exact pure-bending field "
           "$u=\\kappa xy$, $v=-\\kappa x^2/2$ has $\\varepsilon_{xx}"
           "=\\kappa y$, $\\varepsilon_{yy}=0$, "
           "$\\gamma_{xy}=0$: a uniform strain gradient "
           "$\\partial\\varepsilon_{xx}/\\partial y=\\kappa$ and a "
           "neutral axis on the edge $y=0$.  Its one degree of freedom is fixed "
           "by three scalars -- charge $q=\\mu\\kappa L$, bending energy "
           "$U=\\tfrac12 C^p_{11}\\kappa^2Lh^3/3$ and capacitance "
           "$\\kappa_{33}L/h$ -- so", "",
           "$$x=\\frac{(\\mu L)^2}{(C^p_{11}h^3L/3)(\\kappa_{33}L/h)}"
           "=\\frac{3\\mu^2}{C^p_{11}h^2\\kappa_{33}}"
           "=" + f"{F3['x_analytic']:.6e}" + r"$$", "",
           f"The finite element value is read off the same prescribed field as "
           f"$x=\\beta V^2/(u^{{\\mathsf T}}Ku)$.  For contrast, the same "
           f"plate bent about its **mid-plane** would have "
           f"$U\\propto h^3/12$ and hence $x=12\\mu^2/(C^p_{{11}}h^2"
           f"\\kappa_{{33}})={F3['x_midplane']:.4e}$ -- exactly four times "
           f"larger, the factor being $\\int_0^h y^2dy=h^3/3$ against the "
           f"mid-plane $h^3/12$.  Using the beam modulus $E_b$ instead of the "
           f"constrained $C^p_{{11}}$ would give "
           f"${F3['x_beam_modulus']:.4e}$, which the finite element solution "
           f"rules out.", "",
           "| mesh | $V_{oc}$ FEM | $V=\\mu\\kappa h/\\kappa_{33}$ | "
           "$x$ FEM | $x$ analytic | rel. diff |", "|---|---|---|---|---|---|"]
    for r in F3["mesh"]:
        md.append(f"| {r['nx']}x{r['ny']} | {r['V']:.6e} | "
                  f"{r['V_analytic']:.6e} | {r['x_fem']:.6e} | "
                  f"{r['x_analytic']:.6e} | {r['rel_diff']:.1e} |")
    md += ["", "## F4 -- the second-moment factors of the three window shapes", "",
           "Integrated over each shape and divided by its measure, not taken "
           "from the formula in the code.", "",
           "| shape | $M_{ii}/a_i^2$ printed | quadrature, $a_1=1$ | "
           "quadrature, $a_2=0.6$ |", "|---|---|---|---|"]
    for r in F4["rows"]:
        md.append(f"| {r['shape']} | $1/{r['factor']:g}$ | "
                  f"{r['M11_num'] / F4['a1'] ** 2:.12f} vs "
                  f"{r['M11_exact'] / F4['a1'] ** 2:.12f} | "
                  f"{r['M22_num'] / F4['a2'] ** 2:.12f} vs "
                  f"{r['M22_exact'] / F4['a2'] ** 2:.12f} |")
    md += ["", f"Worst relative difference {F4['worst_rel']:.1e}.", ""]

    with open(os.path.join(RES, "independent_checks.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    write_latex(F1, F2, F3, F4)
    for c in F1["cases"]:
        m0 = c["mesh"][0]
        print(f"  F1 {c['case']:16s} EB {c['f_EB_kHz']:7.1f} kHz  "
              f"Ti {c['f_Timoshenko_kHz']:7.1f}  FEM {m0['f_FEM_kHz']:7.1f}  "
              f"({m0['err_vs_EB_pct']:+.2f} % vs EB)")
    for r in F2["rows"]:
        print(f"  F2 alpha={r['alpha']:4.2f}  zeta {r['zeta_newton']:.6f} vs "
              f"{'--' if r['zeta_poly'] is None else format(r['zeta_poly'], '.6f')}"
              f"  (w0 tau/2 = {r['zeta_kv_exact']:.6f})")
    for r in F3["mesh"]:
        print(f"  F3 {r['nx']}x{r['ny']:<3d}  x {r['x_fem']:.6e} vs "
              f"{r['x_analytic']:.6e}  ({r['rel_diff']:.1e})  "
              f"V {r['V']:.4e} vs {r['V_analytic']:.4e}")
    print("  -> results/independent_checks.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
