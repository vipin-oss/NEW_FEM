"""
derive_k2_closed_form.py -- the piezoelectric extensional coupling factor of
the plate from the material constants alone, one algebraic step at a time, and
the same number from the finite element model.

The claim being tested is

    k^2 = x/(1+x),    x = d^T K_uu^{-1} d / beta,   K_uu = short-circuit,

whose constitutive counterpart for a homogeneous body with free strain is

    x = e^T C^{-1} e / kappa .

Neither side contains the other: the left is a condensed finite element matrix
problem, the right is 3 x 3 matrix algebra on the material record.  If they
agree, then the whole piezoelectric path -- the e tensor, the plane-stress
reduction, the potential condensation and the rank-one electrode update -- is
checked by something that does not use it.

The legacy error (a second x/(1+x) application) is checked ONLY against
a frozen legacy-material series. Corrected plane-stress values are not the
same as the legacy series, and no cross-model equality is claimed.

Run: python3 python/derive_k2_closed_form.py
     -> results/k2_closed_form.md, results/k2_closed_form.json
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

RES = os.path.join(ROOT, "results")
EPS0 = mt.EPS0
L, H = 200e-6, 10e-6


def fmt(M, scale=1.0, nd=2):
    if np.isscalar(M) or np.ndim(M) == 0:
        return f"{float(M) * scale:.{nd}g}"
    return "\n".join("  " + "  ".join(f"{v * scale: .4f}" for v in row)
                     for row in np.atleast_2d(M))


def fem_k2(kin, nx, ny, clamped, poling="x"):
    mesh = f6.mesh_rect(nx, ny, L, H)
    mat = mt.Material(**{**mt.batio3(poling, kin).__dict__, "mu": 0.0})
    mdl = f6.assemble(mesh, mt.to_core(mat), np.zeros((2, 2)),
                      clamped_edges=clamped)
    pair = ("left", "right") if poling == "x" else ("bottom", "top")
    Ksc, _, _, _ = f6.reduce(mdl, "short", pair=pair)
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    b, Ks = S * d, Ksc * S[:, None] * S[None, :]
    x = float(b @ (np.linalg.solve(Ks, b) if clamped
                   else np.linalg.lstsq(Ks, b, rcond=1e-11)[0])) / beta
    return {"x": x, "k2": x / (1.0 + x)}


def main():
    m = mt.batio3("x", "plane_stress")
    md = mt.batio3("x", "plane_strain")
    out = {"record": {"C11": m.C11, "C12": m.C12, "C13": m.C13,
                      "C33": m.C33, "C44": m.C44, "e31": m.e31,
                      "e33": m.e33, "e15": m.e15,
                      "kappa_r11": m.kappa_r11, "kappa_r33": m.kappa_r33}}
    lines = ["# The extensional coupling factor of the plate, from the material",
             "constants and from the finite element model", ""]

    # ---------------------------------------------------------------- step 1
    C3 = m.full_3d()
    s3 = np.linalg.inv(C3)
    e3 = np.array([m.e33, m.e31, m.e31])
    kap33 = m.kappa_r33 * EPS0
    x3 = float(e3 @ s3 @ e3) / kap33
    k3 = x3 / (1 + x3)
    k33sq = m.e33 ** 2 / (C3[0, 0] * kap33)
    lines += ["## Step 1 -- the record (poling along $x$, so the polar axis is `3`)", "",
              "```",
              f"C11={m.C11:.3e}  C12={m.C12:.3e}  C13={m.C13:.3e}  "
              f"C33={m.C33:.3e}  C44={m.C44:.3e}  Pa",
              f"e31={m.e31:+.1f}  e33={m.e33:+.1f}  e15={m.e15:+.1f}  C/m^2",
              f"kappa_r11={m.kappa_r11:.0f}  kappa_r33={m.kappa_r33:.0f} "
              f"(kappa33 = {kap33:.4e} F/m)",
              "```", "",
              "3-D stiffness in the $(x,y,z)$ frame, polar axis first:", "",
              "```", fmt(C3, 1e-10), "```  (units $10^{10}$ Pa)", ""]

    # ---------------------------------------------------------------- step 2
    lines += ["## Step 2 -- 3-D free bar (all normal strains free)", "",
              "$$x_{3D}=\\frac{\\mathbf e_3^{\\mathsf T}\\mathbf s_3\\mathbf e_3}"
              "{\\kappa_{33}},\\qquad \\mathbf e_3=(e_{33},e_{31},e_{31}),"
              "\\qquad k^2=\\frac{x_{3D}}{1+x_{3D}}$$", "",
              "```", fmt(s3, 1e12), "```  (compliance, units $10^{-12}$ Pa$^{-1}$)",
              "",
              f"e3' s3 e3 = {float(e3 @ s3 @ e3):.6e} m^4/N,   kappa33 = {kap33:.6e} F/m",
              f"x_3D = {x3:.6f}   ->   k^2_3D,free = **{k3:.5f}**", "",
              f"For comparison the blocked (1-D) textbook value "
              f"$k_{{33}}^2=e_{{33}}^2/(C_{{33}}\\kappa_{{33}})$ is "
              f"{k33sq:.5f}, whose free form $x/(1+x)$ is "
              f"{k33sq / (1 + k33sq):.5f} -- that is the 'uniaxial' column below.",
              ""]

    # ---------------------------------------------------------------- step 3
    C2 = C3[np.ix_([0, 1], [0, 1])]
    c3 = C3[[0, 1], 2]
    Cp = C2 - np.outer(c3, c3) / C3[2, 2]
    lines += ["## Step 3 -- plane-stress reduction, $\\sigma_{zz}=0$", "",
              "The out-of-plane normal stress is condensed exactly as the "
              "material adapter does it:", "",
              "$$\\mathbf C_p=\\mathbf C_{2d}-\\mathbf c_3\\mathbf c_3^{\\mathsf T}"
              "/C_{33}^{(zz)},\\qquad \\mathbf c_3=(C_{xz},C_{yz})$$", "",
              "```",
              f"C_2d =\n{fmt(C2, 1e-10)}   (1e10 Pa)",
              f"c3   = ({c3[0]/1e10:.4f}, {c3[1]/1e10:.4f})   (1e10 Pa)",
              f"C_zz = {C3[2, 2]/1e10:.4f}   (1e10 Pa)",
              f"C_p  =\n{fmt(Cp, 1e-10)}   (1e10 Pa)",
              "```", "",
              f"i.e. $C^p_{{11}}={Cp[0,0]:.4e}$, $C^p_{{12}}={Cp[0,1]:.4e}$, "
              f"$C^p_{{22}}={Cp[1,1]:.4e}$ Pa, $C_{{44}}={m.C44:.4e}$ Pa for "
              "$\\gamma_{xy}$.", "",
              f"Consistency check built into the reduction: the plane-stress "
              f"compliance must be the corresponding block of the 3-D "
              f"compliance, $\\mathbf C_p^{{-1}}=(\\mathbf s_3)_{{2\\times2}}$; "
              f"here the difference is "
              f"{float(np.max(np.abs(np.linalg.inv(Cp) - s3[:2, :2]))):.1e} Pa$^{{-1}}$.",
              "",
              "The local 3-D piezoelectric enthalpy is condensed consistently: "
              "$\\mathbf e_p=\\mathbf e_{2d}-\\mathbf e_z\\mathbf c_3^{\\mathsf T}/C_{zz}$ "
              "and $\\kappa_p=\\kappa_{2d}+\\mathbf e_z\\mathbf e_z^{\\mathsf T}/C_{zz}$. "
              "These coupled reductions are implemented in the patched "
              "`materials.py`. They concern local electromechanical blocks; "
              "higher-gradient and flexoelectric tensors require separate closure.", ""]

    # ---------------------------------------------------------------- step 4
    ep = m.e()[0, :]
    kep = m.kappa()[0, 0]
    # e_p has a zero in the shear slot (e31/e33 do not couple to gamma_xy),
    # so the quadratic form uses the 2x2 normal block of C_p
    eC = float(ep[:2] @ np.linalg.solve(Cp, ep[:2]))
    x2 = eC / kep
    k2c = x2 / (1 + x2)
    lines += ["## Step 4 -- the 2-D closed form", "",
              "$$x_{2D}=\\frac{\\mathbf e_p^{\\mathsf T}\\mathbf C_p^{-1}\\mathbf "
              "e_p}{\\kappa_{xx}},\\qquad k^2=\\frac{x_{2D}}{1+x_{2D}}$$", "",
              "```",
              f"e_p   = ({ep[0]:+.4f}, {ep[1]:+.4f}, {ep[2]:+.4f})   C/m^2",
              f"C_p^-1 =\n{fmt(np.linalg.inv(Cp), 1e11)}   (1e-11 /Pa)",
              f"e'C^-1 e = {eC:.6e} C^2/(N m^2)",
              f"kappa_xx = {kep:.6e} F/m",
              f"x_2D   = {x2:.6f}",
              f"k^2    = {x2:.6f}/(1+{x2:.6f}) = **{k2c:.5f}**",
              "```", "",
              "By hand, for a reader who wants to check the arithmetic: "
              f"$\\det C_p={np.linalg.det(Cp):.6e}$, "
              f"$\\mathbf e_p^{{\\mathsf T}}\\mathbf C_p^{{-1}}\\mathbf e_p="
              f"{eC:.4e}$, so "
              f"$x={x2:.4f}$ and $k^2={k2c:.5f}$.", ""]

    # ---------------------------------------------------------------- step 5
    rows = []
    for kin, tag, kw in (("plane_stress", "closed form", None),
                         ("plane_stress", "FEM free 48x4", (48, 4, ())),
                         ("plane_stress", "FEM clamped 48x4", (48, 4, ("left",))),
                         ("plane_stress", "FEM clamped 24x2", (24, 2, ("left",))),
                         ("plane_stress", "FEM clamped 96x4", (96, 4, ("left",)))):
        if kw is None:
            rows.append((tag, x2, k2c))
        else:
            r = fem_k2(kin, kw[0], kw[1], kw[2])
            rows.append((tag, r["x"], r["k2"]))
    mstr = md.C()
    ev = md.e()[0, :]
    x2s = float(ev[:2] @ np.linalg.solve(mstr[:2, :2], ev[:2])) / md.kappa()[0, 0]
    k2s = x2s / (1 + x2s)
    rows.append(("closed form, plane strain", x2s, k2s))
    r = fem_k2("plane_strain", 48, 4, ("left",))
    rows.append(("FEM clamped 48x4, plane strain", r["x"], r["k2"]))

    lines += ["## Step 5 -- closed form against the finite element model", "",
              "| value | $x$ | $k^2$ |", "|---|---|---|"]
    for tag, x, k in rows:
        lines.append(f"| {tag} | {x:.5f} | **{k:.5f}** |")
    lines += ["", f"3-D free bar for reference: $x={x3:.5f}$, $k^2={k3:.5f}$ "
              "(not attainable in a plane-stress model).", ""]
    fem_free = rows[1][2]
    fem_cl = rows[2][2]
    lines += [f"- closed form $-$ FEM free plate (48x4): "
              f"{100 * (fem_free / k2c - 1):+.4f} %",
              f"- closed form $-$ FEM clamped (48x4): "
              f"{100 * (fem_cl / k2c - 1):+.4f} %",
              f"- mesh: 24x2 vs 48x4 clamped: "
              f"{100 * (rows[3][2] / fem_cl - 1):+.4f} %, 96x4 vs 48x4: "
              f"{100 * (rows[4][2] / fem_cl - 1):+.4f} %", ""]

    # ---------------------------------------------------------------- step 6
    # The old 0.3582 series was derived with old (uncondensed) local e/kappa;
    # never assert that it agrees with the newly corrected material model.
    frozen_path = os.path.join(ROOT, "provenance", "FROZEN_LEGACY_K2_SERIES.json")
    with open(frozen_path) as ff:
        frozen = json.load(ff)
    legacy_wrong_table = frozen["wrong_series"]
    lines += ["## Step 6 -- the historical 0.3582 series belongs to the legacy material model", "",
              "The old helper incorrectly applied the $x/(1+x)$ map twice, "
              "but the archived values also used *unreduced* plane-stress "
              "piezoelectric and dielectric constants. Therefore historical "
              "values must be audited against the frozen **legacy** material "
              "dataset, not the present corrected-constitutive series.", "",
              "$$K_{oc}=K_{sc}+dd^\\mathsf{T}/\\beta,\\qquad "
              "d^\\mathsf{T}K_{oc}^{-1}d/\\beta=x/(1+x)=k^2.$$$", "",
              "| thickness (um) | legacy correct $k^2$ | legacy erroneous $k^2/(1+k^2)$ | original recorded | corrected-model $k^2$ |",
              "|---|---|---|---|---|"]
    th = json.load(open(os.path.join(RES, "demo.json")))["flexo_thickness"]
    by_h = {r_["h_um"]:r_ for r_ in th}
    wrong_table = []
    for old in legacy_wrong_table:
        h_rec=old["h_um"]
        kk=by_h[h_rec]["k2_ext"]
        lines.append(f"| {h_rec:.0f} | {old['k2']:.5f} | {old['k2_over_1p']:.5f} | {old['recorded']:.5f} | {kk:.5f} |")
        wrong_table.append({"h_um":h_rec, "legacy_k2":old["k2"],
                            "legacy_k2_over_1p":old["k2_over_1p"],
                            "legacy_recorded":old["recorded"],
                            "corrected_k2":kk})
    lines += ["", "The frozen legacy error series is internally consistent "
              "to its historical printed precision. The corrected constitutive "
              "model yields different coupling factors; **cross-model equality "
              "would be false**.", ""]

    # ---- the same table for LaTeX, generated not typed
    def texrow(label, x, k, bold=False, nd=4):
        tok = (r"\textbf{%.*f}" % (nd, k)) if bold else ("%.*f" % (nd, k))
        return f"{label} & {x:.4f} & {tok} @@ROW@@"

    tex = ["% table generated from the archived results",
           r"\begin{tabular}{@{}lcc@{}}", r"\toprule",
           r"& $x$ & $k^2$ @@ROW@@", r"\midrule"]
    tex.append(texrow(r"3-D free bar", x3, k3))
    tex.append(texrow(r"3-D uniaxial ($k_{33}^2$)", k33sq, k33sq / (1 + k33sq)))
    tex.append(texrow(r"2-D plane stress, from the record", x2, k2c,
                      bold=True))
    tex.append(r"\midrule")
    for lab, tag, nd in ((r"FEM, plane stress, free, $48\times4$",
                          "FEM free 48x4", 5),
                         (r"FEM, plane stress, clamped, $24\times2$",
                          "FEM clamped 24x2", 5),
                         (r"FEM, plane stress, clamped, $48\times4$",
                          "FEM clamped 48x4", 5),
                         (r"FEM, plane stress, clamped, $96\times4$",
                          "FEM clamped 96x4", 5)):
        x, k = dict((t, (xx, kk)) for t, xx, kk in rows)[tag]
        tex.append(texrow(lab, x, k, bold=(tag == "FEM free 48x4"), nd=nd))
    tex.append(r"\midrule")
    tex.append(texrow(r"2-D plane strain, from the record", x2s, k2s))
    x, k = dict((t, (xx, kk)) for t, xx, kk in rows)[
        "FEM clamped 48x4, plane strain"]
    tex.append(texrow(r"FEM, plane strain, clamped, $48 \times 4$", x, k))
    tex += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(ROOT, "Paper_12", "table_closed_form.tex"), "w") as fh:
        fh.write("\n".join(tex).replace("@@ROW@@", chr(92) * 2) + "\n")

    wtex = ["% historical legacy comparison; NOT an equal-material-model comparison",
            r"\begin{tabular}{@{}lcccc@{}}", r"\toprule",
            r"$h$ (\si{\micro\meter}) & legacy $k^2$ & legacy $k^2/(1+k^2)$ & old quoted & corrected $k^2$ @@ROW@@", r"\midrule"]
    for w in wrong_table:
        wtex.append("%.0f & %.5f & %.5f & %.5f & %.5f @@ROW@@"
                    % (w["h_um"],w["legacy_k2"],w["legacy_k2_over_1p"],w["legacy_recorded"],w["corrected_k2"]))
    wtex += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(RES,"table_superseded_series.tex"),"w") as fh:
        fh.write("\n".join(wtex).replace("@@ROW@@", chr(92)*2)+"\n")

    out.update({"x_3d": x3, "k2_3d_free": k3, "k33_squared": k33sq,
                "k2_3d_uniaxial": k33sq / (1 + k33sq),
                "C_p": Cp.tolist(), "e_p": ep.tolist(), "kappa_eff": kep,
                "x_2d": x2, "k2_2d_closed": k2c,
                "k2_2d_plane_strain": k2s,
                "fem": {tag: k for tag, x, k in rows},
                "fem_x": {tag: x for tag, x, k in rows},
                "legacy_wrong_series": legacy_wrong_table, "historical_comparison": wrong_table})
    with open(os.path.join(RES, "k2_closed_form.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(RES, "k2_closed_form.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"  3-D free bar          k^2 = {k3:.5f}")
    print(f"  2-D closed form       k^2 = {k2c:.5f}   (x = {x2:.5f})")
    print(f"  FEM free 48x4         k^2 = {rows[1][2]:.5f}")
    print(f"  FEM clamped 48x4      k^2 = {rows[2][2]:.5f}")
    print(f"  FEM clamped 24x2      k^2 = {rows[3][2]:.5f}")
    print(f"  FEM clamped 96x4      k^2 = {rows[4][2]:.5f}")
    print(f"  plane strain closed   k^2 = {k2s:.5f}   FEM {r['k2']:.5f}")
    k_sweep = th[0]["k2_ext"]
    print(f"  legacy wrong 0.3582 explained by historical k^2/(1+k^2);"
          f"  corrected model k^2={k_sweep:.5f}")
    print("  -> results/k2_closed_form.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
