"""
worked_example.py -- the intermediate quantities behind the headline numbers.

    python3 python/worked_example.py  -> results/worked_example.json

Every number quoted in the worked-calculation subsection of the manuscript is
computed here from the same code that produces the results, so that the text
shows the route and not only the answer.  Nothing is typed in by hand: the
window moments, the plane-stress moduli, the closed-form coupling, the assembled
sizes and the condensed pair, the flexoelectric smallness parameter, the first
L1 weights and the damping ratios all come out of fem6_core/materials or out of
the archived JSON of the other scripts.
"""
from __future__ import annotations

import json
import os

import numpy as np

import fem6_core as f6
import materials as mt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
L, H = 200e-6, 10e-6


def J(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def window():
    """a. second moments of the 3 x 1 um window and the equal-M shapes."""
    M = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    Me = f6.second_moment("ellipsoid", 3e-6, 1e-6, 0.0)
    out = {
        "a1_um": 3.0, "a2_um": 1.0,
        "M11": float(M[0, 0]), "M22": float(M[1, 1]),
        "M11_over_a1sq": float(M[0, 0] / 3e-6 ** 2),
        "M22_over_a2sq": float(M[1, 1] / 1e-6 ** 2),
        "M11_ellipsoid": float(Me[0, 0]),
        # equal M: a_ell^2/5 = a_cub^2/3
        "a_ellipsoid_over_cuboid_equal_M": float(np.sqrt(5.0 / 3.0)),
        "a_cuboid_over_ellipsoid_equal_M": float(np.sqrt(3.0 / 5.0)),
    }
    # the same relation by direct quadrature over the two shapes
    a_cub = 3e-6
    a_ell = a_cub * np.sqrt(5.0 / 3.0)
    out["check_M_cuboid"] = float(f6.second_moment("cuboid", a_cub, a_cub / 3.0, 0.0)[0, 0])
    out["check_M_ellipsoid"] = float(f6.second_moment("ellipsoid", a_ell, a_ell / 3.0, 0.0)[0, 0])
    return out


def plane_stress():
    """b. the reduced moduli, the piezoelectric constants and the permittivities."""
    mx, my = mt.batio3("x", "plane_stress"), mt.batio3("y", "plane_stress")
    Cx, Cy = mx.C(), my.C()
    return {
        "C11p_poling_x": float(Cx[0, 0]), "C22p_poling_x": float(Cx[1, 1]),
        "C11p_poling_y": float(Cy[0, 0]), "C22p_poling_y": float(Cy[1, 1]),
        "C12p_poling_x": float(Cx[0, 1]),
        "e31": float(mx.e31), "e33": float(mx.e33), "e15": float(mx.e15),
        "kappa_xx_poling_x": float(mx.kappa()[0, 0]),
        "kappa_yy_poling_x": float(mx.kappa()[1, 1]),
        "kappa_yy_poling_y": float(my.kappa()[1, 1]),
    }


def closed_form():
    """c. x = e^T C^-1 e / kappa, and the assembled route to the same quantity."""
    cf = J("k2_closed_form.json")
    mat = mt.batio3("x", "plane_stress")
    core = mt.to_core(mat)
    core.mu = 0.0                      # the mode-free number is quoted with mu = 0
    mdl = f6.assemble(f6.mesh_rect(48, 4, L, H), core,
                      f6.second_moment("cuboid", 3e-6, 1e-6, 0.0))
    Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=("left", "right"))
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=("left", "right"))
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    x_fem = float((S * d) @ np.linalg.solve(Ksc * S[:, None] * S[None, :], S * d) / beta)
    k2_fem = x_fem / (1.0 + x_fem)
    return {
        "x_closed_form": float(cf["x_2d"]),
        "k2_closed_form": float(cf["k2_2d_closed"]),
        "C_p": [[float(v) for v in r] for r in cf["C_p"]],
        "e_p": [float(v) for v in cf["e_p"]],
        "kappa_eff": float(cf["kappa_eff"]),
        "nodes": int(mdl.mesh.nnode), "ndof_mech": int(mdl.ndof_mech),
        "ndof_phi": int(mdl.ndof_phi), "n_condensed_pairs": 1,
        "beta": float(beta), "d_norm": float(np.linalg.norm(d)),
        "x_fem": x_fem, "k2_fem": k2_fem,
        "k2_fem_to_4dp": round(k2_fem, 4),
        "fem_clamped_48x4_json": float(cf["fem"]["FEM clamped 48x4"]),
        "diff_percent": 100.0 * abs(k2_fem - float(cf["k2_2d_closed"])) / float(cf["k2_2d_closed"]),
    }


def flexo():
    """d. the smallness parameter and its finite element counterpart."""
    ps = plane_stress()
    x_an = 3.0 * 1e-6 ** 2 / (ps["C11p_poling_y"] * H ** 2 * ps["kappa_yy_poling_y"])
    rows = J("demo.json")["flexo_thickness"]
    hs = [r["h_um"] for r in rows]
    ks = [r["k2_flexo"] for r in rows]
    slopes = []
    for i in range(len(hs) - 1):
        slopes.append(float(np.log(ks[i + 1] / ks[i]) / np.log(hs[i + 1] / hs[i])))
    return {
        "x_analytic_h10": float(x_an),
        "h_um": hs, "k2_flexo": ks, "local_slope": slopes,
        "growth": float(ks[-1] / ks[0]),
        "slope_first": slopes[0], "slope_last": slopes[-1],
    }


def memory():
    """e. the first L1 weights and the damping extraction."""
    out = {"alpha": {}, "zeta": {}, "ratio": {}}
    for a in (0.5, 0.7):
        b = [(k + 1.0) ** (1 - a) - k ** (1 - a) for k in range(3)]
        out["alpha"]["%.1f" % a] = [round(x, 6) for x in b]
    mv = J("memory_variants.json")
    s1 = mv["S1"]
    keff = s1["Keff_alpha1.0"]["zeta_eff"]
    kuu = s1["Kuu_alpha1.0"]["zeta_eff"]
    exact = mv["omega_tau"] / 2.0
    delta = s1["Keff_alpha1.0"]["delta"]
    out["zeta"] = {"Keff_alpha1": keff, "Kuu_alpha1": kuu, "exact": exact,
                   "error_percent": 100.0 * abs(keff - exact) / exact,
                   "delta": delta,
                   "peak_ratio": float(np.exp(delta)),
                   "zeta_small": float(delta / (2 * np.pi))}
    out["ratio"] = {"Kuu_over_Keff": kuu / keff,
                    "naive_1_minus_k2": 1.0 - mv["k2"]}
    out["tau_s"] = mv["tau"]
    out["omega_tau"] = mv["omega_tau"]
    out["k2_memory"] = mv["k2"]
    return out


def main():
    out = {"window": window(), "plane_stress": plane_stress(),
           "closed_form": closed_form(), "flexo": flexo(), "memory": memory()}
    with open(os.path.join(RES, "worked_example.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    w, c, f, m = out["window"], out["closed_form"], out["flexo"], out["memory"]
    print("worked example -> results/worked_example.json")
    print("  window   M11 %.4e  M22 %.4e  (a_ell/a_cub = %.4f)"
          % (w["M11"], w["M22"], w["a_ellipsoid_over_cuboid_equal_M"]))
    print("  closed   x_cf %.4f -> k2 %.5f | FEM x %.4f -> k2 %.5f (%.2f %%)"
          % (c["x_closed_form"], c["k2_closed_form"], c["x_fem"], c["k2_fem"],
             c["diff_percent"]))
    print("  flexo    x %.4e at h=10 um, slopes %s"
          % (f["x_analytic_h10"], ["%.2f" % s for s in f["local_slope"]]))
    print("  memory   b(0.5) %s  b(0.7) %s  zeta %.5f vs %.5f, ratio %.3f"
          % (m["alpha"]["0.5"], m["alpha"]["0.7"], m["zeta"]["Keff_alpha1"],
             m["zeta"]["exact"], m["ratio"]["Kuu_over_Keff"]))


if __name__ == "__main__":
    main()
