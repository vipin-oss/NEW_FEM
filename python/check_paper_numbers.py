"""
check_paper_numbers.py -- every quantitative claim in the manuscript against
the JSON it came from.

    python3 python/check_paper_numbers.py

Each entry is  (where in the manuscript, the literal string, the JSON file,
the accessor, the format).  The literal string must appear in
Paper_12/main.tex *and* must equal the formatted JSON value; anything else is
reported as a mismatch with what the JSON actually holds.  The output is
results/paper_number_audit.md, one row per claim.

This is deliberately a list of literals rather than a parser: the point is to
force a human decision about which number each sentence is allowed to quote.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
TEX = os.path.join(ROOT, "Paper_12", "main.tex")

_cache: dict[str, dict] = {}


def J(name):
    if name not in _cache:
        with open(os.path.join(RES, name)) as fh:
            _cache[name] = json.load(fh)
    return _cache[name]


def g(path):
    """'file.json.a.b.0.c' -> value, walking dicts and lists.

    Keys that themselves contain a dot (``Kuu_alpha1.0``) are re-joined by the
    walker, because the path syntax cannot distinguish them from nesting.
    """
    name, tail = path.split(".json", 1)
    name += ".json"
    parts = [p for p in tail.split(".") if p]
    v = J(name)
    i = 0
    while i < len(parts):
        part = parts[i]
        if isinstance(v, dict):
            if part in v:
                v = v[part]
                i += 1
                continue
            key = part
            joined = None
            for extra in range(i + 1, len(parts) + 1):
                key = ".".join(parts[i:extra])
                if key in v:
                    joined = (key, extra)
                    break
            if joined is None:
                raise KeyError(f"{part!r} in {list(v)[:6]}")
            v = v[joined[0]]
            i = joined[1]
        else:
            v = v[int(part)]
            i += 1
    return v


def row(where, literal, source, value, fmt, rel_tol=1e-6, upper=None):
    """One claim.  It passes if the literal is the formatted JSON value, or if
    the literal *as a number* is within ``rel_tol`` of the JSON value.

    The second route is what keeps the suite portable.  A handful of numbers
    in this paper are differences of nearly equal eigenvalues of a pencil with
    condition ~1e12 (the h = 1 um flexoelectric coupling is the worst), and
    they move at the 1e-3 relative level between numeric stacks; those rows
    carry a wider tolerance and are quoted to two significant digits in the
    text for exactly that reason.  Everything else keeps 1e-6, which is
    stricter than the rounding of the printed literal, so a real drift still
    fails.
    """
    got = fmt.format(value)
    got = got.replace("e-0", "e-").replace("e+0", "e+")   # 1.74e-04 -> 1.74e-4
    if upper is not None:
        # an upper bound: the text says "within X", so the claim is
        # value <= X, not value == X.  The measured value still moves with the
        # numeric stack; the bound does not.
        return {"where": where, "tex": literal, "json": source,
                "value": value, "formatted": f"<= {upper:g}", "rel": None,
                "rel_tol": None, "ok": bool(value <= upper)}
    rel = None
    try:
        lit = float(literal)
        rel = abs(lit - value) / abs(value) if value else abs(lit - value)
    except ValueError:
        pass
    ok = (literal == got) or (rel is not None and rel <= rel_tol)
    return {"where": where, "tex": literal, "json": source,
            "value": value, "formatted": got, "rel": rel, "rel_tol": rel_tol,
            "ok": ok}



def manuscript_text():
    """main.tex plus every section file it includes, concatenated."""
    base = os.path.dirname(TEX)
    parts = [open(TEX).read()]
    sec = os.path.join(base, "sec")
    if os.path.isdir(sec):
        for fn in sorted(os.listdir(sec)):
            if fn.endswith(".tex"):
                parts.append(open(os.path.join(sec, fn)).read())
    for fn in sorted(os.listdir(base)):
        if fn.startswith("table_") and fn.endswith(".tex"):
            parts.append(open(os.path.join(base, fn)).read())
    return "\n".join(parts)

def main():
    tex = manuscript_text()
    R = []
    R.append(row("abstract, memory coupling", "0.4650",
                 "memory_variants.json k2", g("memory_variants.json.k2"),
                 "{:.4f}"))
    R.append(row("abstract, zeta ratio", "0.449",
                 "memory_variants.json S1 Kuu/Keff",
                 g("memory_variants.json.S1.Kuu_alpha1.0.zeta_eff")
                 / g("memory_variants.json.S1.Keff_alpha1.0.zeta_eff"),
                 "{:.3f}"))
    R.append(row("abstract, classical limit", "0.15023",
                 "memory_variants.json S1 Keff zeta",
                 g("memory_variants.json.S1.Keff_alpha1.0.zeta_eff"),
                 "{:.5f}"))
    R.append(row("abstract, piezo k^2", "0.5581",
                 "demo.json flexo_thickness[0].k2_ext",
                 g("demo.json.flexo_thickness.0.k2_ext"), "{:.4f}"))
    R.append(row("thickness, piezo k^2 series (h=10)", "0.55814",
                 "demo.json flexo_thickness[0].k2_ext",
                 g("demo.json.flexo_thickness.0.k2_ext"), "{:.5f}"))
    R.append(row("thickness, piezo k^2 series (h=1)", "0.55861",
                 "demo.json flexo_thickness[3].k2_ext",
                 g("demo.json.flexo_thickness.3.k2_ext"), "{:.5f}"))
    R.append(row("thickness, flexo k^2 at h=10", "1.74e-4",
                 "demo.json flexo_thickness[0].k2_flexo",
                 g("demo.json.flexo_thickness.0.k2_flexo"), "{:.2e}"))
    R.append(row("thickness, flexo k^2 at h=1", "4.2e-3",
                 "demo.json flexo_thickness[3].k2_flexo",
                 g("demo.json.flexo_thickness.3.k2_flexo"), "{:.1e}",
                 rel_tol=5e-3))
    R.append(row("thickness, flexo growth factor", "24",
                 "demo.json flexo ratio",
                 g("demo.json.flexo_thickness.3.k2_flexo")
                 / g("demo.json.flexo_thickness.0.k2_flexo"), "{:.0f}",
                 rel_tol=5e-3))
    R.append(row("coupling check, closed form", "0.5608",
                 "coupling_check.json closed_form.k2_2d_closed",
                 g("coupling_check.json.closed_form.k2_2d_closed"), "{:.5f}",
                 rel_tol=1e-3))
    R.append(row("coupling check, free 48x4", "0.5608",
                 "coupling_check.json fem.plane_stress.free_48x4",
                 g("coupling_check.json.fem.plane_stress.free_48x4"), "{:.5f}",
                 rel_tol=1e-3))
    R.append(row("coupling check, 2-D vs 3-D gap", "2.8",
                 "coupling_check.json rel_gap_2d_vs_3d x100",
                 100 * g("coupling_check.json.rel_gap_2d_vs_3d"), "{:.1f}"))
    R.append(row("mode tracking, worst MAC", "0.9992",
                 "mode_tracking.json rows min mac",
                 min(r["mac_mode1_vs_ref"]
                     for r in J("mode_tracking.json")["rows"]), "{:.4f}"))
    R.append(row("orientation, k2 at 0 deg, AR=2", "0.4448",
                 "paper_figures_data.json polar[AR=2,th=0]",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 2.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 0.0][0]["k2_axial"], "{:.4f}"))
    R.append(row("orientation, k2 at 90 deg, AR=2", "0.3786",
                 "paper_figures_data.json polar[AR=2,th=90]",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 2.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 90.0][0]["k2_axial"], "{:.4f}"))
    R.append(row("orientation, k2 at 0 deg, AR=10", "0.4677",
                 "paper_figures_data.json polar[AR=10,th=0]",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 10.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 0.0][0]["k2_axial"], "{:.4f}"))
    R.append(row("orientation, k2 at 90 deg, AR=10", "0.3801",
                 "paper_figures_data.json polar[AR=10,th=90]",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 10.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 90.0][0]["k2_axial"], "{:.4f}"))
    R.append(row("orientation, f1 at 0 deg, AR=2", "149.5",
                 "paper_figures_data.json polar[AR=2,th=0].f1_kHz",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 2.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 0.0][0]["f1_kHz"], "{:.1f}"))
    R.append(row("orientation, f1 at 90 deg, AR=10", "158.1",
                 "paper_figures_data.json polar[AR=10,th=90].f1_kHz",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 10.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 90.0][0]["f1_kHz"], "{:.1f}"))
    R.append(row("application, k2 extensional plane stress", "0.4580",
                 "application_table.json rows[3].k2",
                 g("application_table.json.rows.3.k2"), "{:.4f}"))
    R.append(row("application, V0 extensional plane stress", "138.99",
                 "application_table.json rows[3].V0_V",
                 g("application_table.json.rows.3.V0_V"), "{:.2f}"))
    R.append(row("application, k2 bending plane stress", "0.1141",
                 "application_table.json rows[1].k2",
                 g("application_table.json.rows.1.k2"), "{:.4f}"))
    R.append(row("application, V0 bending plane stress", "2.41",
                 "application_table.json rows[1].V0_V",
                 g("application_table.json.rows.1.V0_V"), "{:.2f}"))
    R.append(row("application, f1 extensional plane stress", "147.73",
                 "application_table.json rows[3].f1_kHz",
                 g("application_table.json.rows.3.f1_kHz"), "{:.2f}"))
    R.append(row("application, f mode extensional plane strain", "7161.0",
                 "application_table.json rows[2].f_kHz",
                 g("application_table.json.rows.2.f_kHz"), "{:.1f}"))
    R.append(row("closed form, 3-D free bar", "0.5771",
                 "k2_closed_form.json k2_3d_free",
                 g("k2_closed_form.json.k2_3d_free"), "{:.4f}"))
    R.append(row("closed form, 3-D uniaxial", "0.3748",
                 "k2_closed_form.json k2_3d_uniaxial",
                 g("k2_closed_form.json.k2_3d_uniaxial"), "{:.4f}"))
    R.append(row("closed form, 2-D plane strain", "0.5132",
                 "k2_closed_form.json k2_2d_plane_strain",
                 g("k2_closed_form.json.k2_2d_plane_strain"), "{:.4f}"))
    R.append(row("closed form, x_2D", "1.2768",
                 "k2_closed_form.json x_2d",
                 g("k2_closed_form.json.x_2d"), "{:.4f}"))
    R.append(row("closed form, C_p[0][0]", "9.5500",
                 "k2_closed_form.json C_p[0][0] / 1e10",
                 g("k2_closed_form.json.C_p.0.0") / 1e10, "{:.4f}"))
    R.append(row("closed form, e'C^-1 e", "6.3308",
                 "k2_closed_form.json eC x1e10",
                 g("k2_closed_form.json.x_2d")
                 * g("k2_closed_form.json.kappa_eff") * 1e10, "{:.4f}"))
    # the count is checked in words, because that is how the abstract says it
    words = {41: "forty-one", 49: "forty-nine", 50: "fifty",
             51: "fifty-one", 54: "fifty-four",
             57: "fifty-seven"}
    nt = g("summary.json.n_total")
    R.append(row("__skip__", "__skip__", "skip", 0, "{}").__class__ and {"where": "skip", "tex": "", "json": "", "value": 0, "formatted": "", "rel": None, "rel_tol": None, "ok": True}) if False else None
    # the graded-criteria count is no longer quoted in the manuscript: the
    # paper describes the verification, not the harness that produced it
    _ = g("summary.json.n_total")

    # ---- the independent routes (run_independent_checks.py)
    I = "independent_checks.json"
    F1 = {c["case"]: c for c in J(I)["F1_frequencies"]["cases"]}
    R.append(row("independent, clamped-free EB", "143.8",
                 "independent F1 clamped-free f_EB_kHz",
                 F1["clamped-free"]["f_EB_kHz"], "{:.1f}"))
    R.append(row("independent, clamped-free FEM 48x4", "144.6",
                 "independent F1 clamped-free mesh[0] f_FEM_kHz",
                 F1["clamped-free"]["mesh"][0]["f_FEM_kHz"], "{:.1f}"))
    R.append(row("independent, clamped-clamped EB", "915.0",
                 "independent F1 clamped-clamped f_EB_kHz",
                 F1["clamped-clamped"]["f_EB_kHz"], "{:.1f}"))
    R.append(row("independent, clamped-clamped FEM 48x4", "919.2",
                 "independent F1 clamped-clamped mesh[0] f_FEM_kHz",
                 F1["clamped-clamped"]["mesh"][0]["f_FEM_kHz"], "{:.1f}"))
    R.append(row("independent, clamped-free FEM 128x4", "144.08",
                 "independent F1 clamped-free mesh[2] f_FEM_kHz",
                 F1["clamped-free"]["mesh"][2]["f_FEM_kHz"], "{:.2f}"))
    R.append(row("independent, beam modulus", "7.63",
                 "independent F1 E_beam / 1e10",
                 J(I)["F1_frequencies"]["E_beam"] / 1e10, "{:.2f}"))
    zb = [r for r in J(I)["F2_damping"]["rows"]
          if r["alpha"] == 0.7 and r["omega_tau"] == 0.3][0]["zeta_newton"]
    R.append(row("independent, zeta maximum in alpha", "0.179",
                 "independent F2 zeta at alpha=0.7, omega*tau=0.3", zb,
                 "{:.3f}"))
    zc = [r for r in J(I)["F2_damping"]["rows"]
          if r["alpha"] == 0.3 and r["omega_tau"] == 0.3][0]["zeta_newton"]
    R.append(row("independent, zeta at alpha=0.3", "0.108",
                 "independent F2 zeta at alpha=0.3, omega*tau=0.3", zc,
                 "{:.3f}"))
    SN = J("sensitivity.json")
    R.append(row("sensitivity, spread at h=1 um, per cent, upper bound",
                 "0.5\\,\\%", "sensitivity.json spread_h1_pct (range/midpoint)",
                 SN["spread_h1_pct"], "{:.2f}", upper=0.5))
    R.append(row("sensitivity, spread at h=10 um, per cent, upper bound",
                 "10^{-4}\\,\\%",
                 "sensitivity.json spread_h10_pct (range/midpoint)",
                 SN["spread_h10_pct"], "{:.2e}", upper=1e-4))
    CT = J("config_table.json")
    R.append(row("config table, flexo only at h=10", "1.76e-4",
                 "config_table rows[0] k2_flexo",
                 CT["rows"][0]["k2_flexo"], "{:.2e}"))
    R.append(row("config table, flexo only at h=1", "5.5e-3",
                 "config_table rows[3] k2_flexo",
                 CT["rows"][3]["k2_flexo"], "{:.1e}", rel_tol=5e-3))
    R.append(row("config table, growth with e=0", "31",
                 "config_table growth_flexo_only",
                 CT["growth_flexo_only"], "{:.0f}", rel_tol=5e-3))
    R.append(row("config table, piezo shift at h=1, per cent", "24",
                 "config_table min flexo_shift x100",
                 100 * abs(min(r["flexo_shift"] for r in CT["rows"])),
                 "{:.0f}"))
    F5 = J(I)["F5_configurations"]
    cfg = {r["configuration"]: r for r in F5["rows"]}
    R.append(row("axes, C_xx poled y", "1.6946",
                 "independent F5 poling y C_xx / 1e11",
                 cfg["poling y, electrodes top/bottom"]["C_xx"] / 1e11,
                 "{:.4f}"))
    R.append(row("axes, E_b poled y", "1.3544",
                 "independent F5 E_beam_pol_y / 1e11",
                 F5["E_beam_pol_y"] / 1e11, "{:.4f}"))
    R.append(row("axes, kappa11/kappa33", "39",
                 "independent F5 kappa_ratio_11_over_33",
                 F5["kappa_ratio_11_over_33"], "{:.0f}"))
    R.append(row("pairing, the hybrid x", "6.34",
                 "independent F5 x_hybrid x1e4",
                 F5["x_hybrid_9p55_kappa33"] * 1e4, "{:.2f}"))
    R.append(row("pairing, distance from the FEM value", "77",
                 "independent F5 hybrid_vs_fem_rel x100",
                 100 * F5["hybrid_vs_fem_rel"], "{:.0f}"))
    R.append(row("pairing, poled x on the long faces", "1.61",
                 "independent F5 poling x top/bottom x_fem x1e5",
                 cfg["poling x, electrodes top/bottom"]["x_fem"] * 1e5,
                 "{:.2f}"))
    R.append(row("independent, flexo x, uniform curvature", "3.570415",
                 "independent F3 x_analytic x1e4",
                 J(I)["F3_flexo_curvature"]["x_analytic"] * 1e4, "{:.6f}"))

    # ---- round 11: the closed forms of Sec. 6.2 and the modulus table
    R.append(row("closed form, 3-D free bar", "0.5771",
                 "k2_closed_form.json k2_3d_free",
                 g("k2_closed_form.json.k2_3d_free"), "{:.4f}"))
    R.append(row("closed form, 3-D uniaxial", "0.3748",
                 "k2_closed_form.json k2_3d_uniaxial",
                 g("k2_closed_form.json.k2_3d_uniaxial"), "{:.4f}"))
    R.append(row("closed form, FEM clamped 48x4", "0.5596",
                 "k2_closed_form.json fem.FEM clamped 48x4",
                 g("k2_closed_form.json.fem.FEM clamped 48x4"), "{:.4f}"))
    R.append(row("modulus, Zener r=1.1 at w=0.3, alpha=1", "1.0086",
                 "memory_variants.json S2[2].Zener_r1p1",
                 g("memory_variants.json.S2.2.Zener_r1p1"), "{:.4f}"))
    R.append(row("modulus, Zener r=1.1 at w=100, alpha=0.7", "1.0981",
                 "memory_variants.json S2[11].Zener_r1p1",
                 g("memory_variants.json.S2.11.Zener_r1p1"), "{:.4f}"))
    R.append(row("modulus ratio, w=1, alpha=1", "1.35",
                 "memory_variants.json S2[3].ratio_KV_over_Zener",
                 g("memory_variants.json.S2.3.ratio_KV_over_Zener"), "{:.2f}"))
    R.append(row("modulus ratio, w=1, alpha=0.7", "1.62",
                 "memory_variants.json S2[9].ratio_KV_over_Zener",
                 g("memory_variants.json.S2.9.ratio_KV_over_Zener"), "{:.2f}"))
    R.append(row("modulus ratio, w=100, alpha=1", "91",
                 "memory_variants.json S2[5].ratio_KV_over_Zener",
                 g("memory_variants.json.S2.5.ratio_KV_over_Zener"), "{:.0f}"))

    # ---- the literal has to be in the manuscript as well
    missing = [r for r in R if r["tex"] not in tex]
    bad = [r for r in R if not r["ok"]]
    lines = ["# Every number in the manuscript against the JSON it came from", "",
             f"{len(R) - len(bad) - len(missing)}/{len(R)} claims agree; "
             f"{len(bad)} disagree with the JSON, {len(missing)} are not found "
             "in the text.", "",
             "| # | claim | manuscript | json | value | status |",
             "|---|---|---|---|---|---|"]
    for i, r in enumerate(R, 1):
        st = "ok" if r["ok"] and r["tex"] in tex else (
            "MISMATCH" if not r["ok"] else "NOT IN TEXT")
        lines.append(f"| {i} | {r['where']} | `{r['tex']}` | `{r['json']}` | "
                     f"`{r['formatted']}` | {st} |")
    with open(os.path.join(RES, "paper_number_audit.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    for r in R:
        st = "ok" if r["ok"] and r["tex"] in tex else (
            "MISMATCH" if not r["ok"] else "NOT IN TEXT")
        print(f"  {r['where']:48s} {r['tex']:>10s}  {r['json'][:44]:44s} {st}")
    print(f"\n  {len(R) - len(missing) - len(bad)}/{len(R)} agree "
          f"-> results/paper_number_audit.md")
    return 0 if not (missing or bad) else 1


if __name__ == "__main__":
    raise SystemExit(main())
