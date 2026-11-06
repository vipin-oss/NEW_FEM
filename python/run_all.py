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
    derive_k2_closed_form.py D1-D2 the coupling factor from the material
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
               "run_application_table.py", "derive_k2_closed_form.py",
               "run_independent_checks.py", "audit_abstract_claims.py",
               "run_config_table.py", "list_unverified.py",
               "run_sensitivity.py", "check_gradient_energy.py",
               os.path.join("..", "Paper_12", "check_refs.py")]
    if figs:
        scripts.append("run_demos.py")
        scripts.append("run_paper_figures.py")
        scripts.append("make_appendix_tables.py")
        scripts.append("coupling_provenance.py")
        scripts.append("make_coupling_table.py")
        scripts.append("check_coupling_provenance.py")
        scripts.append("worked_example.py")
        scripts.append("check_paper_numbers.py")
        scripts.append("check_paper_structure.py")
        scripts.append("check_float_order.py")
    ran = {s: run(s) for s in scripts}

    V = load("verification.json")
    F = load("flexo_check.json")
    Mc = load("material_comparison.json")
    Mv = load("memory_variants.json")
    Cc = load("coupling_check.json")
    Kt = load("mode_tracking.json")
    At = load("application_table.json")
    Ic = load("independent_checks.json")
    Ab = load("abstract_audit.json")
    Gc = load("config_table.json")
    Uv = load("unverified_numbers.json")
    Sn = load("sensitivity.json")
    Ge = load("gradient_energy.json")
    Cf = load("k2_closed_form.json")
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
    chk("C1", "FEM k^2 (unconstrained strip) vs 2-D closed form e^T C^-1 e/kappa",
        f"{Cc['fem']['plane_stress']['free_48x4']:.5f} vs {cf['k2_2d_closed']:.5f}",
        "rel. diff < 1e-3", Cc["rel_err_free"] < 1e-3)
    chk("C2", "2-D model vs 3-D free bar (plane-stress reduction)",
        f"{100 * Cc['rel_gap_2d_vs_3d']:.2f} %",
        "< 5 % (documented modelling gap)", Cc["rel_gap_2d_vs_3d"] < 0.05)
    chk("C3", "FEM k^2, clamped strip, 96x4 vs 48x4",
        f"{Cc['fem']['plane_stress']['clamped_96x4']:.5f} vs "
        f"{Cc['fem']['plane_stress']['clamped_48x4']:.5f}",
        "rel. diff < 1e-3", Cc["rel_mesh_96_vs_48"] < 1e-3)
    chk("C4", "FEM k^2, clamped strip, 24x2 vs 48x4",
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

    cf_err = abs(Cf["fem"]["FEM free 48x4"] / Cf["k2_2d_closed"] - 1.0)
    chk("D1", "closed form e'C^-1 e/kappa vs FEM coupling (free strip)",
        f"{Cf['k2_2d_closed']:.5f} vs {Cf['fem']['FEM free 48x4']:.5f}",
        "rel. diff < 1e-3", cf_err < 1e-3)
    wid = max(abs(w["k2_over_1p"] - w["recorded"]) for w in Cf["wrong_series"])
    chk("D2", "the superseded series is exactly k^2/(1+k^2) of the new one",
        f"{wid:.1e}", "< 1e-5 (same formula applied twice)", wid < 1e-5)

    # ---- independent routes (nothing here reuses the assembly path) ----
    e1 = {c["case"]: c for c in Ic["F1_frequencies"]["cases"]}
    co = e1["clamped-free"]["mesh"][0]
    cc = e1["clamped-clamped"]["mesh"][0]
    chk("I1", "clamped-free f1, FEM 48x4 vs Euler-Bernoulli closed form",
        f"{co['f_FEM_kHz']:.1f} vs {e1['clamped-free']['f_EB_kHz']:.1f} kHz",
        f"|err| < 1 % ({co['err_vs_EB_pct']:+.2f} %)",
        abs(co["err_vs_EB_pct"]) < 1.0)
    chk("I2", "clamped-clamped f1, FEM 48x4 vs Euler-Bernoulli closed form",
        f"{cc['f_FEM_kHz']:.1f} vs {e1['clamped-clamped']['f_EB_kHz']:.1f} kHz",
        f"|err| < 1 % ({cc['err_vs_EB_pct']:+.2f} %)",
        abs(cc["err_vs_EB_pct"]) < 1.0)
    chk("I3", "clamped-free f1 at 128x4 vs Euler-Bernoulli (mesh refinement)",
        f"{e1['clamped-free']['mesh'][2]['f_FEM_kHz']:.2f} kHz",
        f"|err| < 0.5 % ({e1['clamped-free']['mesh'][2]['err_vs_EB_pct']:+.2f} %)",
        abs(e1["clamped-free"]["mesh"][2]["err_vs_EB_pct"]) < 0.5)
    worst = max(r["rel_diff"] for r in Ic["F2_damping"]["rows"]
                if r["rel_diff"] is not None)
    chk("I4", "zeta from Newton pole vs polynomial roots (10 alpha, 2 omega*tau)",
        f"{worst:.1e}", "< 1e-8", worst < 1e-8)
    zerr = max(abs(r["zeta_newton"] - r["zeta_kv_exact"])
               for r in Ic["F2_damping"]["rows"] if r["alpha"] == 1.0)
    chk("I5", "zeta at alpha = 1 vs omega*tau/2 (both omega*tau)",
        f"{zerr:.1e}", "< 1e-9", zerr < 1e-9)
    fx = Ic["F3_flexo_curvature"]
    fx_worst = max(r["rel_diff"] for r in fx["mesh"])
    chk("I6", "flexo x, uniform curvature: FEM energy triple vs 3 mu^2/(C11 h^2 kappa33)",
        f"{fx['mesh'][0]['x_fem']:.6e} vs {fx['x_analytic']:.6e}",
        f"rel. diff < 1e-8 (worst {fx_worst:.1e})", fx_worst < 1e-8)
    v_worst = max(abs(r["V"] / r["V_analytic"] - 1) for r in fx["mesh"])
    chk("I7", "flexo Voc, uniform curvature: FEM vs mu*kappa*h/kappa33",
        f"{v_worst:.1e}", "< 1e-10", v_worst < 1e-10)
    chk("A2", "every number in the abstract has an independent-check verdict",
        f"{Ab['n_hua']} hua / {Ab['n_nahi_hua']} nahi hua / {Ab['n_input']} "
        f"inputs, {len(Ab['tokens'])} tokens",
        "0 uncovered, 0 stale",
        not Ab["missing"] and not Ab["stale"])
    gmax = max(r["piezo_share"] for r in Gc["rows"])
    chk("G1", "piezoelectric share of the bending device (poling y, long "
        "faces) at every thickness", f"{gmax:.1e}",
        "< 1e-5 (electrically silent bending mode)", gmax < 1e-5)
    chk("G2", "flexo growth with and without the piezoelectric terms",
        f"{Gc['growth_both']:.1f} vs {Gc['growth_flexo_only']:.1f}",
        "reported 24 (2 s.f.) uses the real crystal; 31 with e = 0, both "
        "graded at 1 %",
        abs(Gc["growth_both"] / 23.9 - 1) < 0.01
        and abs(Gc["growth_flexo_only"] / 31.1 - 1) < 0.01)
    cfg = {r["configuration"]: r for r in Ic["F5_configurations"]["rows"]}
    yb = cfg["poling y, electrodes top/bottom"]
    xb = cfg["poling x, electrodes top/bottom"]
    xl = cfg["poling x, electrodes left/right"]
    yl = cfg["poling y, electrodes left/right"]
    chk("I9", "the same bending field, four poling/electrode pairings: only "
        "the long faces collect it, and each pairing with its own permittivity",
        f"poled y {yb['x_fem']:.3e} vs {yb['x_analytic']:.3e}; poled x "
        f"{xb['x_fem']:.3e} vs {xb['x_analytic']:.3e}; short-face pairs "
        f"{max(abs(xl['V']), abs(yl['V'])):.1e} V",
        "rel. diff < 1e-6, short-face charge < 1e-12", 
        abs(yb["x_fem"] / yb["x_analytic"] - 1) < 1e-6
        and abs(xb["x_fem"] / xb["x_analytic"] - 1) < 1e-6
        and max(abs(xl["V"]), abs(yl["V"])) < 1e-12)
    mw = Ic["F4_window_moments"]["worst_rel"]
    chk("I8", "window second-moment factors 1/3, 1/4, 1/5 by quadrature",
        f"{mw:.1e}", "< 1e-5", mw < 1e-5)

    chk("U1", "h = 1 um flexo k^2 over four equivalent solver paths and "
        f"{Sn['n_stacks']} numeric stacks",
        f"spread {Sn['spread_h1_pct']:.3f} %, k^2 {Sn['k2_h1_min']:.4e}"
        f"..{Sn['k2_h1_max']:.4e}", "< 0.5 % (quoted to 2 s.f.)",
        Sn["spread_h1_pct"] < 0.5)
    chk("U2", "the same spread at h = 10 um", f"{Sn['spread_h10_pct']:.2e} %",
        "< 1e-3 %", Sn["spread_h10_pct"] < 1e-3)
    chk("U3", "truncating the secular sum to 12 modes is not an alternative",
        f"{Sn['truncated_max_dev_pct']:.0f} % off",
        "> 50 % (hence the sum runs over all modes)",
        Sn["truncated_max_dev_pct"] > 50)
    St = load("stale_tokens.json")
    chk("N3", "no quantity replaced in the round-16 audit has come back",
        f"{St['n_hits']} hits of {St['n_tokens']} forbidden tokens", "0 hits",
        St["n_hits"] == 0 and St["n_tokens"] >= 10)

    if figs:
        Cv = load("coupling_provenance_check.json")
        chk("N4", "every coupling factor is reproduced from the archive and "
            "quoted in one row of the coupling table",
            f"{Cv['n_pass']}/{Cv['n_total']}", "all, no averaging",
            Cv["all_pass"])

    chk("N2", "the list of unverified numbers cites only numbers still in the "
        "manuscript", f"{Uv['n']} entries, {len(Uv['stale'])} stale",
        "0 stale", not Uv["stale"] and Uv["n"] > 0)

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

    chk("W1", "gradient-energy coefficient: code vs manuscript",
        f"{Ge['assembly_factor']} x int, (1/4)M/((1/20)L)="
        f"{Ge['quarter_M_over_twentieth_L']:.12f}",
        "factor 1/2 in the assembly, (1/4)M = (1/20)L, FEM-1 u_R within 2 %",
        Ge["assembly_line_present"]
        and abs(Ge["quarter_M_over_twentieth_L"] - 1.0) < 1e-12
        and Ge["fem1_benchmark_uR_um"] is not None
        and abs(Ge["fem1_benchmark_uR_um"] / 4.23 - 1.0) < 0.02)

    if Pg is not None:
        pol = Pg["polar"]
        nfig = sum(1 for f in os.listdir(os.path.join(RESULTS, "figures",
                                                      "paper"))
                   if f.endswith(".pdf"))
        chk("P1", "paper figures: vector set written",
            f"{nfig} PDF", "= 11 (F1-F9, FB1-FB2)", nfig == 11)
        chk("P2", "orientation sweep rows / k^2 range",
            f"{len(pol)} rows, {min(r['k2_axial'] for r in pol):.4f}"
            f"-{max(r['k2_axial'] for r in pol):.4f}",
            "133 rows (114 cuboid + 19 ellipse), k^2 in (0.35, 0.50)",
            len(pol) == 133 and 0.35 < min(r["k2_axial"] for r in pol)
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
    # the verification table is built from summary.json, so it has to be
    # regenerated after the summary exists; the two text checks are then run
    # again on the final table, otherwise the stale-token gate would grade the
    # previous version of the table.
    if figs:
        ran["make_paper_table.py (second pass)"] = run("make_paper_table.py")
        run("check_paper_numbers.py")
        run("check_float_order.py")
        md_txt = open(os.path.join(RESULTS,
                                   "paper_number_audit.md")).read()
        m = _re.search(r"(\d+)/(\d+) claims agree", md_txt)
        nok, ntot = (int(m.group(1)), int(m.group(2))) if m else (0, 1)
        St2 = load("stale_tokens.json")
        for r in rows:
            if r["id"] == "N1":
                r["value"] = f"{nok}/{ntot}"
                r["pass"] = bool(nok == ntot and ntot > 20)
            elif r["id"] == "N3":
                r["value"] = (f"{St2['n_hits']} hits of "
                              f"{St2['n_tokens']} forbidden tokens")
                r["pass"] = bool(St2["n_hits"] == 0 and St2["n_tokens"] >= 10)
        npass = sum(r["pass"] for r in rows)
        allok = npass == len(rows) and all(ran.values())
        out.update({"checks": rows, "n_pass": npass, "scripts_ok": ran,
                    "all_pass": bool(allok)})
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
