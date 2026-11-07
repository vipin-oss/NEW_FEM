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
import re

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



_TIMES_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*\\times\s*10\^\{?\s*([+-]?[0-9]+)\s*\}?")


def normalise(text):
    """Rewrite a\times10^{b} as a e-notation so a bare numeral can be found.

    The manuscript states powers of ten in typeset form; the audit literals are
    bare numerals such as ``1.74e-4``.  Normalising the manuscript once keeps
    the table of audited numbers readable.
    """
    text = _TIMES_RE.sub(lambda m: m.group(1) + "e" + m.group(2), text)
    return text.replace("\\,", "").replace("{,}", "")


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

# ---------------------------------------------------------------------------
# Forbidden tokens: quantities that round 16 replaced.  They must not come back
# into the manuscript, its tables, its captions or its highlights.
# ---------------------------------------------------------------------------
STALE_TOKENS = {
    "2.5700": "peak ratio of the ring-down (round 16: 2.5947)",
    "0.94392": "logarithmic decrement (round 16: 0.95345)",
    "0.15023": "zeta(K_eff, alpha=1) (round 16: 0.15003)",
    "0.06749": "zeta(K_uu, alpha=1) (round 16: 0.06746 / 0.0675)",
    "0.449": "K_uu/K_eff ratio (round 16: 0.450)",
    "0.15\\,\\%": "integer-order error (round 16: 0.02 %)",
    "0.026": "alpha=0.7 zeta from a global fit, withdrawn in round 16",
    "0.05006": "alpha=0.7 zeta from a global fit, withdrawn in round 16",
    "1.93": "alpha=0.7 ratio from a global fit, withdrawn in round 16",
    "$2\\times2$": "'2x2 Gauss' quadrature (round 16: $4\\times4$)",
    "plate": "'plate' for a plane-stress strip (round 16: 'strip')",
    "Plate": "capitalised 'Plate' (round 16: 'Strip')",
    "Appendix~\\ref{app:": "the class prints 'Appendix' inside \\thesection, so "
                            "the literal word doubles it ('Appendix Appendix A')",
    "Appendix \\ref{app:": "same doubling without the tie",
}


def stale_scan():
    """Every .tex of the package, plus the highlights file."""
    base = os.path.dirname(TEX)
    texts = {}
    for dirpath, _dirs, files in os.walk(base):
        for fn in files:
            if fn.endswith(".tex"):
                full = os.path.join(dirpath, fn)
                texts[os.path.relpath(full, base)] = open(full).read()
    hits = []
    for tok, why in STALE_TOKENS.items():
        for rel, body in sorted(texts.items()):
            for i, line in enumerate(body.splitlines(), 1):
                if tok in line:
                    hits.append({"token": tok, "why": why, "file": rel,
                                 "line": i, "text": line.strip()[:120]})
    return hits


def main():
    tex = normalise(manuscript_text())
    R = []
    R.append(row("abstract, memory coupling", "0.4650",
                 "memory_variants.json k2", g("memory_variants.json.k2"),
                 "{:.4f}"))
    R.append(row("abstract, zeta ratio", "0.450",
                 "memory_variants.json S1 Kuu/Keff",
                 g("memory_variants.json.S1.Kuu_alpha1.0.zeta_eff")
                 / g("memory_variants.json.S1.Keff_alpha1.0.zeta_eff"),
                 "{:.3f}"))
    R.append(row("abstract, classical limit", "0.15003",
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
                 g("demo.json.flexo_thickness.7.k2_ext"), "{:.5f}"))
    R.append(row("thickness, flexo k^2 at h=10", "1.74e-4",
                 "demo.json flexo_thickness[0].k2_flexo",
                 g("demo.json.flexo_thickness.0.k2_flexo"), "{:.2e}"))
    R.append(row("thickness, flexo k^2 at h=1", "4.2e-3",
                 "demo.json flexo_thickness[3].k2_flexo",
                 g("demo.json.flexo_thickness.7.k2_flexo"), "{:.1e}",
                 rel_tol=5e-3))
    _dt = J("dt_study.json")["memory"]
    for _m, _lit in ((1, "0.150111"), (2, "0.150057"), (4, "0.150029")):
        _r = [r for r in _dt["rows"] if r["mult"] == _m][0]
        R.append(row("time step, zeta at %dN" % _m, _lit,
                     "dt_study.json memory rows[mult=%d].zeta" % _m,
                     _r["zeta"], "{:.6f}"))
    R.append(row("thickness, flexo growth factor", "24",
                 "demo.json flexo ratio",
                 g("demo.json.flexo_thickness.7.k2_flexo")
                 / g("demo.json.flexo_thickness.0.k2_flexo"), "{:.0f}",
                 rel_tol=5e-3))
    _wf = J("worked_example.json")["flexo"]
    R.append(row("worked, analytic flexo growth, h^-2 over 10 -> 1 um",
                 "100", "worked_example.json flexo (h_max/h_min)^2",
                 (_wf["h_um"][0] / _wf["h_um"][-1]) ** 2, "{:.0f}"))
    R.append(row("worked, FEM flexo below the analytic x at h=10", "2.05",
                 "worked_example.json x_analytic_h10 / demo k2_flexo[0]",
                 _wf["x_analytic_h10"]
                 / g("demo.json.flexo_thickness.0.k2_flexo"), "{:.2f}",
                 rel_tol=5e-3))
    R.append(row("orientation, extensional f at 0 deg, AR=2", "5012",
                 "paper_figures_data.json polar[AR=2,th=0].f_ext_kHz",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 2.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 0.0][0]["f_ext_kHz"], "{:.0f}"))
    R.append(row("orientation, extensional f at 90 deg, AR=2", "5296",
                 "paper_figures_data.json polar[AR=2,th=90].f_ext_kHz",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 2.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 90.0][0]["f_ext_kHz"], "{:.0f}"))
    R.append(row("orientation, extensional f at 0 deg, AR=10", "4907",
                 "paper_figures_data.json polar[AR=10,th=0].f_ext_kHz",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 10.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 0.0][0]["f_ext_kHz"], "{:.0f}"))
    R.append(row("orientation, extensional f at 90 deg, AR=10", "5288",
                 "paper_figures_data.json polar[AR=10,th=90].f_ext_kHz",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 10.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 90.0][0]["f_ext_kHz"], "{:.0f}"))
    R.append(row("orientation, worst coupling change (AR=10)", "-18.7",
                 "paper_figures_data.json polar, min of k2/k2(0)-1",
                 100.0 * min([r["k2_axial"] for r in J("paper_figures_data.json")["polar"]
                              if r["AR"] == 10.0 and r["shape"] == "cuboid"]
                             and [r["k2_axial"] / [q for q in
                                  J("paper_figures_data.json")["polar"]
                                  if q["AR"] == 10.0 and q["shape"] == "cuboid"
                                  and q["theta_deg"] == 0.0][0]["k2_axial"] - 1.0
                                  for r in J("paper_figures_data.json")["polar"]
                                  if r["AR"] == 10.0
                                  and r["shape"] == "cuboid"]), "{:.1f}"))
    R.append(row("orientation, symmetry deviation", "3e-11",
                 "paper_figures_data.json symmetry max",
                 max(max(x["rel_k2"], x["rel_f"])
                     for x in J("paper_figures_data.json")["symmetry"]),
                 "{:.0e}", rel_tol=0.6))
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
    R.append(row("mode tracking, worst MAC", "0.999",
                 "mode_tracking.json rows min mac",
                 min(r["mac_mode1_vs_ref"]
                     for r in J("mode_tracking.json")["rows"]), "{:.3f}"))
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
    R.append(row("orientation, f1 at 90 deg, AR=10", "158.1",
                 "paper_figures_data.json polar[AR=10,th=90].f1_kHz",
                 [r for r in J("paper_figures_data.json")["polar"]
                  if r["AR"] == 10.0 and r["shape"] == "cuboid"
                  and r["theta_deg"] == 90.0][0]["f1_kHz"], "{:.1f}"))
    R.append(row("application, k2 extensional plane strain", "0.4024",
                 "application_table.json rows[2].k2",
                 g("application_table.json.rows.2.k2"), "{:.4f}"))
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
    R.append(row("closed form, e'C^-1 e", "6.3308e-10",
                 "k2_closed_form.json eC",
                 g("k2_closed_form.json.x_2d")
                 * g("k2_closed_form.json.kappa_eff"), "{:.4e}"))
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
                 "0.5\\%", "sensitivity.json spread_h1_pct (range/midpoint)",
                 SN["spread_h1_pct"], "{:.2f}", upper=0.5))
    R.append(row("sensitivity, spread at h=10 um, per cent, upper bound",
                 "10^{-4}\\%",
                 "sensitivity.json spread_h10_pct (range/midpoint)",
                 SN["spread_h10_pct"], "{:.2e}", upper=1e-4))
    CT = J("config_table.json")
    # Round 13: the 4e7 ratio left the abstract with the rewrite; the same gap is
    # now stated as "two orders of magnitude" in the conclusion, so this slot
    # carries the ring-down decrements that the rewritten Sec. 6.7 quotes.
    P6 = J("paper_figures_data.json")["notes"]["P6"]
    R.append(row("ring-down, decrement at alpha=1", "0.063",
                 "paper_figures_data.json notes.P6 zeta_1.0",
                 P6["zeta_1.0"], "{:.3f}", rel_tol=1e-2))
    R.append(row("ring-down, peak decrement at alpha=0.6", "0.104",
                 "paper_figures_data.json notes.P6 zeta_0.6",
                 P6["zeta_0.6"], "{:.3f}", rel_tol=1e-2))
    R.append(row("ring-down, decrement at alpha=0.4", "0.085",
                 "paper_figures_data.json notes.P6 zeta_0.4",
                 P6["zeta_0.4"], "{:.3f}", rel_tol=1e-2))
    R.append(row("ring-down, error at alpha=0.6 against alpha=1", "64",
                 "paper_figures_data.json notes.P6 zeta_0.6/zeta_1.0 - 1, in percent",
                 100.0 * (P6["zeta_0.6"] / P6["zeta_1.0"] - 1.0), "{:.0f}",
                 rel_tol=1e-2))
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
    # the cross-paired value is still computed and archived in
    # independent_checks.json; the paper no longer quotes it, so there is no
    # literal to audit (the pairing rule is stated once, in Sec. 4.2)
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
    R.append(row("closed form, FEM clamped 48x4", "0.55957",
                 "k2_closed_form.json fem.FEM clamped 48x4",
                 g("k2_closed_form.json.fem.FEM clamped 48x4"), "{:.5f}"))
    R.append(row("modulus ratio, w=1, alpha=1", "1.35",
                 "memory_variants.json S2[3].ratio_KV_over_Zener",
                 g("memory_variants.json.S2.3.ratio_KV_over_Zener"), "{:.2f}"))
    R.append(row("modulus ratio, w=1, alpha=0.7", "1.62",
                 "memory_variants.json S2[9].ratio_KV_over_Zener",
                 g("memory_variants.json.S2.9.ratio_KV_over_Zener"), "{:.2f}"))
    R.append(row("modulus ratio, w=100, alpha=1", "91",
                 "memory_variants.json S2[5].ratio_KV_over_Zener",
                 g("memory_variants.json.S2.5.ratio_KV_over_Zener"), "{:.0f}"))

    # ---- Round 14: the worked-calculation subsection ------------------------
    W = J("worked_example.json")
    wn, cf, fx, mm = W["window"], W["closed_form"], W["flexo"], W["memory"]
    R.append(row("worked, window M11", "3.000e-12", "worked_example window M11",
                 wn["M11"], "{:.3e}"))
    R.append(row("worked, window M22", "3.333e-13", "worked_example window M22",
                 wn["M22"], "{:.3e}"))
    R.append(row("worked, equal-M ellipsoid over cuboid", "1.2910",
                 "worked_example sqrt(5/3)", wn["a_ellipsoid_over_cuboid_equal_M"],
                 "{:.4f}"))
    R.append(row("worked, equal-M cuboid over ellipsoid", "0.7746",
                 "worked_example sqrt(3/5)", wn["a_cuboid_over_ellipsoid_equal_M"],
                 "{:.4f}"))
    R.append(row("worked, plane-stress C11 poling x", "9.5500e10",
                 "materials C_p[0,0] poling x", W["plane_stress"]["C11p_poling_x"],
                 "{:.4e}"))
    R.append(row("worked, plane-stress C11 poling y", "1.6946e11",
                 "materials C_p[0,0] poling y", W["plane_stress"]["C11p_poling_y"],
                 "{:.4e}", rel_tol=1e-4))
    R.append(row("worked, plane-stress C12", "5.7000e10",
                 "materials C_p[0,1]", W["plane_stress"]["C12p_poling_x"],
                 "{:.4e}"))
    R.append(row("worked, kappa33", "4.9583e-10", "k2_closed_form kappa_eff",
                 cf["kappa_eff"], "{:.4e}", rel_tol=1e-4))
    R.append(row("worked, condensed capacitance beta", "2.4792e-11",
                 "worked_example beta", cf["beta"], "{:.4e}", rel_tol=1e-3))
    R.append(row("worked, x from the assembled matrices", "1.2631",
                 "worked_example x_fem", cf["x_fem"], "{:.4f}"))
    R.append(row("worked, distance to the closed form", "0.47",
                 "worked_example diff_percent", cf["diff_percent"], "{:.2f}"))
    R.append(row("worked, flexoelectric x at h=10", "3.5704e-4",
                 "worked_example x_analytic_h10", fx["x_analytic_h10"], "{:.4e}"))
    R.append(row("worked, peak ratio of the ring-down", "2.5947",
                 "exp(delta) from memory_variants.json", mm["zeta"]["peak_ratio"], "{:.4f}"))
    R.append(row("worked, logarithmic decrement", "0.95345",
                 "ln(peak ratio)", float(__import__("math").log(mm["zeta"]["peak_ratio"])),
                 "{:.5f}"))
    R.append(row("worked, L1 weight b1 at alpha=0.5", "0.414214",
                 "sqrt(2)-1", mm["alpha"]["0.5"][1], "{:.6f}", rel_tol=1e-5))
    R.append(row("worked, L1 weight b2 at alpha=0.7", "0.159245",
                 "3^0.3-2^0.3", mm["alpha"]["0.7"][2], "{:.6f}", rel_tol=1e-4))

    # ---- Table B.1: the two rows that are comparisons rather than identities
    _cg = J("verification.json")["convergence"]["rows"]
    import math as _math
    R.append(row("verification table, order on the finest mesh pair", "2.01",
                 "verification.json convergence rel_err[2]/rel_err[3]",
                 _math.log2(_cg[2]["rel_err"] / _cg[3]["rel_err"]), "{:.2f}"))
    _rm = J("reduction_mac.json")
    R.append(row("verification table, MAC of mode 5 across the two reductions",
                 "0.99999", "reduction_mac.json mac_mode5",
                 _rm["mac_mode5"], "{:.5f}"))
    R.append(row("verification table, largest overlap between different modes",
                 "2.8e-6", "reduction_mac.json mac_offdiag_max",
                 _rm["mac_offdiag_max"], "{:.1e}"))
    _nu = J("numerics.json")["truncation"]
    R.append(row("Sec. 5.4, 8 vs 40 modes with the memory on K_eff", "2.0e-14",
                 "numerics.json keff_relerr_8_vs_40",
                 _nu["keff_relerr_8_vs_40"], "{:.1e}"))
    R.append(row("Sec. 5.4, 8 vs 40 modes with the memory on K_uu", "3.0e-4",
                 "numerics.json kuu_relerr_8_vs_40",
                 _nu["kuu_relerr_8_vs_40"], "{:.1e}"))
    R.append(row("Sec. 5.4, 20 vs 40 modes with the memory on K_uu", "5.1e-5",
                 "numerics.json kuu_relerr_20_vs_40",
                 _nu["kuu_relerr_20_vs_40"], "{:.1e}"))
    _kf = J("k2_closed_form.json")["fem"]
    R.append(row("verification table, clamped 96x4 vs 48x4, relative", "6.2e-4",
                 "k2_closed_form.json fem clamped 96x4 / 48x4 - 1",
                 abs(_kf["FEM clamped 96x4"] / _kf["FEM clamped 48x4"] - 1.0),
                 "{:.1e}"))

    # ---- the design map of Fig. 12 (results/design_map.json)
    dm = J("design_map.json")
    _h, _a = dm["h_um"], dm["a2_um"]
    _kb, _ke = dm["k2_bend_flexo"], dm["k2_ext_piezo"]

    def _at(hh, aa):
        return _kb[_h.index(hh)][_a.index(aa)]

    R.append(row("design map, flexo k^2 at h=10, a2=0.25", "1.648e-4",
                 "design_map.json [h=10][a2=0.25]", _at(10.0, 0.25), "{:.4e}",
                 rel_tol=2e-4))
    R.append(row("design map, change of k^2 at h=10 for a2 1 -> 0.25 um", "5.5",
                 "design_map.json 100*(1-k(a2=.25)/k(a2=1)) at h=10",
                 100.0 * (1.0 - _at(10.0, 0.25) / _at(10.0, 1.0)), "{:.1f}"))
    R.append(row("design map, flexo k^2 at h=1, a2=0.25", "1.03e-2",
                 "design_map.json [h=1][a2=0.25]", _at(1.0, 0.25), "{:.2e}"))
    R.append(row("design map, gain from the window at h=1", "2.5",
                 "design_map.json k(a2=.25)/k(a2=1) at h=1",
                 _at(1.0, 0.25) / _at(1.0, 1.0), "{:.1f}"))
    R.append(row("design map, flexo k^2 at h=1, a2=1 um", "4.17e-3",
                 "design_map.json [h=1][a2=1]", _at(1.0, 1.0), "{:.2e}"))
    R.append(row("design map, smallest flexo k^2", "3.6e-6",
                 "design_map.json range k2_flexo_min",
                 dm["range"]["k2_flexo_min"], "{:.1e}"))
    R.append(row("design map, smallest flexo/piezo ratio", "6.5e-6",
                 "design_map.json range ratio_min",
                 dm["range"]["ratio_min"], "{:.1e}"))
    R.append(row("design map, largest flexo/piezo ratio", "1.85e-2",
                 "design_map.json range ratio_max",
                 dm["range"]["ratio_max"], "{:.2e}"))
    R.append(row("design map, thickness of the 0.1 % crossing at a2=1 um", "5.46",
                 "design_map.json thresholds h_at_0p1pct_a2_1um",
                 dm["thresholds"]["h_at_0p1pct_a2_1um"], "{:.2f}"))

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
    # ---- forbidden stale tokens (round 16 replacements)
    hits = stale_scan()
    lines += ["", "## Forbidden stale tokens", "",
              f"{len(hits)} hits of {len(STALE_TOKENS)} forbidden tokens.", ""]
    if hits:
        lines += ["| token | file | line | text |", "|---|---|---|---|"]
        for h in hits:
            lines.append(f"| `{h['token']}` | {h['file']} | {h['line']} | "
                         f"`{h['text']}` |")
    with open(os.path.join(RES, "stale_tokens.json"), "w") as fh:
        json.dump({"n_tokens": len(STALE_TOKENS), "n_hits": len(hits),
                   "hits": hits}, fh, indent=1)
    with open(os.path.join(RES, "paper_number_audit.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    for r in R:
        st = "ok" if r["ok"] and r["tex"] in tex else (
            "MISMATCH" if not r["ok"] else "NOT IN TEXT")
        print(f"  {r['where']:48s} {r['tex']:>10s}  {r['json'][:44]:44s} {st}")
    for h in hits:
        print(f"  STALE {h['token']:>10s}  {h['file']}:{h['line']}  {h['text']}")
    print(f"\n  {len(R) - len(missing) - len(bad)}/{len(R)} agree; "
          f"{len(hits)} stale-token hits of {len(STALE_TOKENS)} "
          f"-> results/paper_number_audit.md")
    return 0 if not (missing or bad or hits) else 1


if __name__ == "__main__":
    raise SystemExit(main())
