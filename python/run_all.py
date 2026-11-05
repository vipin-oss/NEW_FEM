"""
run_all.py -- one command, whole suite, one pass/fail table.

    python3 python/run_all.py              # everything (~2 min)
    python3 python/run_all.py --no-figs    # skip the figures

Runs, in order:
    run_verification.py    V1-V7 + the delivered L1 stencil check
    run_flexo_check.py     F1-F5 flexoelectric
    run_material_check.py  plane strain vs plane stress, dielectric anisotropy
    run_memory_variants.py S1 memory matrix, S2 KV vs Zener
    run_coupling_check.py  C1-C4 piezo k^2 against the closed form
    run_mode_tracking.py   K1-K2 the same mode shape at every thickness
    run_application_table.py A1 the four polarisation/kinematics cases
    run_demos.py           the thickness sweep (optional)
    run_paper_figures.py   the paper figure set (optional)
    check_paper_numbers.py N1 every number in the manuscript (optional)
    check_paper_structure.py   manuscript structure, no TeX available (opt.)
then applies the pass/fail criteria below to the generated JSON and writes
results/SUMMARY.md and results/summary.json.

Every criterion is stated here, in one place, with its tolerance -- nothing is
graded inside the individual scripts (the single exception is the L1 stencil
check, which carries its own flag).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")


def load(name):
    with open(os.path.join(RESULTS, name)) as fh:
        return json.load(fh)


def run(script):
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       capture_output=True, text=True)
    ok = p.returncode == 0
    if not ok:
        print(p.stdout[-3000:])
        print(p.stderr[-3000:])
    print(f"  {script:26s} {'ok' if ok else 'FAILED'}  ({time.time()-t0:.1f} s)")
    return ok


def main():
    figs = "--no-figs" not in sys.argv
    print("running the suite")
    scripts = ["run_verification.py", "run_flexo_check.py",
               "run_material_check.py", "run_memory_variants.py",
               "run_coupling_check.py", "run_mode_tracking.py",
               "run_application_table.py"]
    if figs:
        scripts.append("run_demos.py")
        scripts.append("run_paper_figures.py")
        scripts.append("make_paper_table.py")
        scripts.append("check_paper_numbers.py")
        scripts.append("check_paper_structure.py")
    ran = {s: run(s) for s in scripts}

    V = load("verification.json")
    F = load("flexo_check.json")
    Mc = load("material_comparison.json")
    Mv = load("memory_variants.json")
    Cc = load("coupling_check.json")
    Kt = load("mode_tracking.json")
    At = load("application_table.json")
    D = load("demo.json") if figs else None
    Pg = load("paper_figures_data.json") if figs else None

    rows = []          # (id, what, value, criterion, ok)

    def chk(cid, what, value, crit, ok):
        rows.append({"id": cid, "what": what, "value": value,
                     "criterion": crit, "pass": bool(ok)})

    P = V["patch"]
    chk("V1a", "patch energy, rel. error", f"{P['rel_err']:.2e}",
        "< 1e-12", P["rel_err"] < 1e-12)
    chk("V1b", "gradient energy under constant strain",
        f"{P['grad_energy_const_strain']:.2e}", "< 1e-9",
        P["grad_energy_const_strain"] < 1e-9)
    chk("V1c", "K_g(ellipsoid) vs FEM-1 (l^2/10)", f"{P['ellipsoid_vs_FEM1']:.2e}",
        "< 1e-12", P["ellipsoid_vs_FEM1"] < 1e-12)
    chk("V1d", "K_g(cuboid)/K_g(ellipsoid), equal a",
        f"{P['cuboid_over_ellipsoid_equal_halfwidth']:.6f}", "= 5/3 = 1.666667",
        abs(P["cuboid_over_ellipsoid_equal_halfwidth"] - 5 / 3) < 1e-6)
    chk("V1e", "cuboid vs ellipsoid at equal M",
        f"{P['cuboid_eq_moment_vs_ellipsoid']:.2e}", "= 0 (< 1e-12)",
        abs(P["cuboid_eq_moment_vs_ellipsoid"]) < 1e-12)

    l020 = [r for r in V["fem1"]["length"] if abs(r["l_over_L"] - 0.20) < 1e-9][0]
    chk("V2", "FEM-1 benchmark, u_R at l/L = 0.20",
        f"{l020['u']*1e6:.4f} um", "within 2 % of 4.23 um (paper)",
        abs(l020["u"] * 1e6 / 4.23 - 1) < 0.02)

    chk("V3", "observed mesh order", f"{V['convergence']['order']:.2f}",
        "> 1.5", V["convergence"]["order"] > 1.5)

    Pe = V["piezo"]
    chk("V4a", "bending mode k_eff^2 (piezo only)", f"{Pe['k2']:.2e}",
        "< 1e-6 (no net charge in bending)", Pe["k2"] < 1e-6)
    chk("V4b", "length-extensional max k_eff^2",
        f"{max(Pe['extensional']['k2']):.4f}", "> 0.35",
        max(Pe["extensional"]["k2"]) > 0.35)

    chk("V5a", "alpha = 1 vs closed-form KV, order",
        f"{V['memory_alpha1']['order']:.2f}", "> 0.9",
        V["memory_alpha1"]["order"] > 0.9)
    worst_h = max(abs(r["ratio"] - 1) for r in V["memory_harmonic"])
    chk("V5b", "harmonic |H|, worst deviation", f"{100*worst_h:.2f} %",
        "< 2 %", worst_h < 0.02)
    chk("V5c", "tau -> 0 residual", f"{V['memory_tau0']:.2e}", "< 1e-6",
        V["memory_tau0"] < 1e-6)
    L = V["l1_scheme"]
    chk("V5d", "delivered L1 stencil vs analytic |H|",
        f"{100*L['worst_ratio_error']:.2f} %", "< 1 %", L["pass"])

    tr = V["truncation"]["rows"]
    chk("V6a", "static truncation, 24 modes",
        f"{tr[-1]['rel_err']:.2e}", "< 5e-2", tr[-1]["rel_err"] < 5e-2)
    chk("V6b", "static truncation, monotone decreasing",
        "yes" if all(tr[i + 1]["rel_err"] <= tr[i]["rel_err"] + 1e-12
                     for i in range(len(tr) - 1)) else "no",
        "monotone",
        all(tr[i + 1]["rel_err"] <= tr[i]["rel_err"] + 1e-12
            for i in range(len(tr) - 1)))

    dom = V["domain"]["rows"]
    eqm = [r["u"] for r in dom if r["domain"].startswith("cuboid (equal")] 
    ell = [r["u"] for r in dom if r["domain"] == "ellipsoid"]
    dmax = max(abs(a - b) / b for a, b in zip(eqm, ell)) if eqm else 1.0
    chk("V7", "equal-M cuboid vs ellipsoid, max rel. diff",
        f"{dmax:.2e}", "< 1e-12", dmax < 1e-12)

    chk("F1", "flexo patch test, mu = 0", f"{F['F1_patch_mu0']:.2e} V", "= 0",
        abs(F["F1_patch_mu0"]) < 1e-18)
    chk("F2", "flexo patch test vs mu*kappa*h/kappa33",
        f"{F['F2_patch']['ratio']:.10f}", "= 1 (1e-10)",
        abs(F["F2_patch"]["ratio"] - 1) < 1e-10)
    chk("F3", "flexo linearity V(2mu)/V(mu)", f"{F['F3_linearity']:.10f}", "= 2",
        abs(F["F3_linearity"] - 2) < 1e-10)
    chk("F4", "bending k_eff^2 with flexo (mu=1e-6)",
        f"{F['F4_cantilever']['mu1']['k2_1']:.2e}", "> 1e-5",
        F["F4_cantilever"]["mu1"]["k2_1"] > 1e-5)

    chk("M1", "kappa11/kappa33", f"{Mc['kappa_ratio_11_over_33']:.1f}",
        "> 30 (real crystal, was 1.2)", Mc["kappa_ratio_11_over_33"] > 30)
    z1 = Mv["S1"]["Keff_alpha1.0"]["zeta_eff"]
    chk("S1a", "zeta(K_eff, alpha=1) vs omega*tau/2",
        f"{z1:.5f} vs 0.15000", "within 2 %", abs(z1 / 0.15 - 1) < 0.02)
    r1 = Mv["S1"]["Kuu_alpha1.0"]["zeta_eff"] / z1
    chk("S1b", "zeta(K_uu)/zeta(K_eff) at alpha=1", f"{r1:.3f}",
        "in (0, 1) -- the choice matters", 0 < r1 < 1)
    kv = [r for r in Mv["S2"] if abs(r["omega_tau"] - 1.0) < 1e-9
          and r["alpha"] == 1.0][0]
    chk("S2", "KV/Zener modulus at omega*tau = 1, alpha = 1",
        f"{kv['ratio_KV_over_Zener']:.3f}", "> 1.3 (KV unbounded)",
        kv["ratio_KV_over_Zener"] > 1.3)

    cf = Cc["closed_form"]
    chk("C1", "FEM k^2 (unconstrained plate) vs 2-D closed form e^T C^-1 e/kappa",
        f"{Cc['fem']['plane_stress']['free_48x4']:.5f} vs {cf['k2_2d_closed']:.5f}",
        "rel. diff < 1e-3", Cc["rel_err_free"] < 1e-3)
    chk("C2", "2-D model vs 3-D free bar (plane-stress reduction)",
        f"{100 * Cc['rel_gap_2d_vs_3d']:.2f} %",
        "< 5 % (documented modelling gap)", Cc["rel_gap_2d_vs_3d"] < 0.05)
    chk("C3", "FEM k^2, clamped plate, 96x4 vs 48x4",
        f"{Cc['fem']['plane_stress']['clamped_96x4']:.5f} vs "
        f"{Cc['fem']['plane_stress']['clamped_48x4']:.5f}",
        "rel. diff < 1e-3", Cc["rel_mesh_96_vs_48"] < 1e-3)
    chk("C4", "FEM k^2, clamped plate, 24x2 vs 48x4",
        f"{100 * abs(Cc['fem']['plane_stress']['clamped_24x2'] / Cc['fem']['plane_stress']['clamped_48x4'] - 1):.2f} %",
        "< 0.5 % (coarse mesh)", abs(
            Cc["fem"]["plane_stress"]["clamped_24x2"] /
            Cc["fem"]["plane_stress"]["clamped_48x4"] - 1) < 5e-3)

    kmac = min(r["mac_mode1_vs_ref"] for r in Kt["rows"])
    koff = max(max(r["mac_offdiag"]) for r in Kt["rows"])
    chk("K1", "lowest MAC of mode 1 vs the h = 10 um shape (4 thicknesses)",
        f"{kmac:.5f}", "> 0.999", kmac > 0.999)
    krat = min(r["f_ratio_2_over_1"] for r in Kt["rows"])
    chk("K2", "worst f2/f1 over the thickness sweep (mode off-diagonal)",
        f"{koff:.1e}, f2/f1 >= {krat:.2f}", "off-diag < 1e-5, ratio > 6",
        koff < 1e-5 and krat > 6.0)

    ak2 = [r["k2"] for r in At["rows"]]
    chk("A1", "application table: extensional plane stress is the strongest "
        "coupling of the four", f"{max(ak2):.4f}",
        "= 0.4580, largest, > 0.4",
        abs(max(ak2) - 0.45797) < 1e-4 and ak2.index(max(ak2)) == 3
        and max(ak2) > 0.4)

    if D is not None:
        # thickness sweep -- the panel that used to be a mode-selection
        # artefact, now graded on the properties that make it admissible:
        # no mode is picked by argmax, the piezo column is mode-free, and the
        # flexo column is monotone and carries a finer-mesh witness.
        TH = D["flexo_thickness"]
        ext = np.array([r["k2_ext"] for r in TH])
        ratio = float(ext.max() / ext.min())
        chk("T1", "piezo k^2 (mode-free) over h = 10 -> 1 um, max/min",
            f"{ratio:.4f}", "< 1.005 (thickness independent)", ratio < 1.005)
        mesh = max(abs(r["k2_ext"] / r["k2_ext_24"] - 1.0) for r in TH)
        chk("T2", "piezo k^2, 24x2 vs 48x4, max rel. diff", f"{mesh:.1e}",
            "< 1e-3", mesh < 1e-3)
        kf = np.array([r["k2_flexo"] for r in TH])
        chk("T3", "flexo k^2, 48x4 (monotone in h)",
            f"{kf[0]:.2e} -> {kf[-1]:.2e}",
            "strictly increasing as h falls", bool(np.all(np.diff(kf) > 0)))
        wit = max(abs(r["k2_flexo_96"] / r["k2_flexo"] - 1.0)
                  for r in TH if "k2_flexo_96" in r)
        chk("T4", "flexo k^2, 48x4 vs 96x4 witness", f"{wit:.1e}",
            "< 0.02", wit < 0.02)
        fl = max(abs(r["k2_floor"]) / r["k2_flexo"] for r in TH)
        chk("T5", "flexo k^2 at mu = 0 / value (residual)", f"{fl:.0e}",
            "< 1e-5", fl < 1e-5)

    if Pg is not None:
        pol = Pg["polar"]
        nfig = sum(1 for f in os.listdir(os.path.join(RESULTS, "figures",
                                                      "paper"))
                   if f.endswith(".pdf"))
        chk("P1", "paper figures: vector set written",
            f"{nfig} PDF", "= 10 (P1-P10)", nfig == 10)
        chk("P2", "orientation sweep rows / k^2 range",
            f"{len(pol)} rows, {min(r['k2_axial'] for r in pol):.4f}"
            f"-{max(r['k2_axial'] for r in pol):.4f}",
            "168 rows (144 cuboid + 24 ellipse), k^2 in (0.35, 0.50)",
            len(pol) == 168 and 0.35 < min(r["k2_axial"] for r in pol)
            and max(r["k2_axial"] for r in pol) < 0.50)

        import re as _re
        with open(os.path.join(RESULTS, "paper_number_audit.md")) as fh:
            head = fh.readline()
        with open(os.path.join(RESULTS, "paper_number_audit.md")) as fh:
            txt = fh.read()
        m = _re.search(r"(\d+)/(\d+) claims agree", txt)
        nok, ntot = (int(m.group(1)), int(m.group(2))) if m else (0, 1)
        chk("N1", "manuscript numbers vs the JSON they came from",
            f"{nok}/{ntot}", "all agree", nok == ntot and ntot > 20)

    npass = sum(r["pass"] for r in rows)
    allok = npass == len(rows) and all(ran.values())
    out = {"checks": rows, "n_pass": npass, "n_total": len(rows),
           "scripts_ok": ran, "figures": figs, "all_pass": bool(allok),
           "runtime_note": "run_verification ~45 s, run_demos ~~55 s of the total"}

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "summary.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    w = max(len(r["id"]) for r in rows)
    md = ["# FEM-6 verification summary", "",
          f"Generated by `python3 python/run_all.py`. "
          f"**{npass}/{len(rows)} checks pass.**", "",
          "| id | check | value | criterion | |",
          "|---|---|---|---|---|"]
    print()
    for r in rows:
        mark = "PASS" if r["pass"] else "**FAIL**"
        print(f"  {r['id']:<{w}}  {r['value']:<26s} {mark}")
        md.append(f"| {r['id']} | {r['what']} | {r['value']} | "
                  f"{r['criterion']} | {mark} |")
    md += ["", "| script | ran |", "|---|---|"]
    md += [f"| `{k}` | {'ok' if v else 'FAILED'} |" for k, v in ran.items()]
    md += ["", "Overall: **" + ("PASS" if allok else "FAIL") + "**"]
    with open(os.path.join(RESULTS, "SUMMARY.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"\n  {npass}/{len(rows)} checks pass -> "
          f"{'PASS' if allok else 'FAIL'}")
    print("  -> results/SUMMARY.md, results/summary.json")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
