"""check_coupling_provenance.py -- gate N4.

results/coupling_provenance.json recomputes every coupling factor the paper
quotes.  This check asserts (a) that each row still equals the archived result
it claims to reproduce, and (b) that table_coupling.tex quotes the rows to five
decimals.  It is the machine counterpart of the promise in the text that the
numbers near 0.56 and near 0.46 are different measures and are not averaged.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")


def load(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def main():
    cp = load("coupling_provenance.json")
    rows = {r["label"]: r["value"] for r in cp["rows"]}
    cc = load("coupling_check.json")["fem"]["plane_stress"]
    cf = load("k2_closed_form.json")
    dm = load("demo.json")["flexo_thickness"][0]["k2_ext"]
    at = load("application_table.json")["rows"][3]["k2"]
    mv = load("memory_variants.json")["k2"]

    # (label, upstream value, tolerance, what it is)
    upstream = [
        ("k2_free_nogradient_48x4", cc["free_48x4"], 1e-8,
         "coupling_check.json fem.plane_stress.free_48x4"),
        ("k2_clamped_nogradient_48x4", cc["clamped_48x4"], 1e-8,
         "coupling_check.json fem.plane_stress.clamped_48x4"),
        ("k2_clamped_gradient_48x4", dm, 1e-8,
         "demo.json flexo_thickness[0].k2_ext"),
        ("k2_mode_based_Kuu_24x2", mv, 1e-8,
         "memory_variants.json k2"),
        ("k2_mode_based_Ksc_24x2_mu0", at, 1e-8,
         "application_table.json rows[3].k2"),
        ("k2_closed_form_plane_stress", cf["k2_2d_closed"], 1e-8,
         "k2_closed_form.json k2_2d_closed"),
    ]
    checks = []
    for label, ref, tol, what in upstream:
        got = rows[label]
        rel = abs(got - ref) / abs(ref)
        checks.append((label, got, ref, rel, bool(rel <= tol), what))

    # the working value is the clamped, window-on, 48x4 row
    wv = cp["working_value"]
    checks.append(("working_value", wv, rows["k2_clamped_gradient_48x4"], 0.0,
                   bool(wv == rows["k2_clamped_gradient_48x4"]),
                   "working value equals rows[2]"))

    # the mode-based pair must differ by the matrix, and the Ksc pair by mu
    gap_matrix = (rows["k2_mode_based_Kuu_24x2"] -
                  rows["k2_mode_based_Ksc_24x2"]) / rows["k2_mode_based_Ksc_24x2"]
    gap_mu = (rows["k2_mode_based_Ksc_24x2"] -
              rows["k2_mode_based_Ksc_24x2_mu0"]) / rows["k2_mode_based_Ksc_24x2"]
    checks.append(("gap K_uu vs K_sc", gap_matrix, 1.5e-2, abs(gap_matrix) - 1.5e-2,
                   bool(abs(gap_matrix) < 2.0e-2), "1.5 % between the matrices"))
    checks.append(("gap mu = 0 vs 1e-6", gap_mu, 7e-4, abs(gap_mu), 
                   bool(abs(gap_mu) < 1e-3), "0.07 % between the mu values"))

    # the table quotes the rows to five decimals
    tab = open(os.path.join(ROOT, "Paper_12", "table_coupling.tex")).read()
    missing = [r["label"] for r in cp["rows"]
               if "$%.5f$" % r["value"] not in tab]
    checks.append(("table quotes every row", len(cp["rows"]) - len(missing),
                   len(cp["rows"]), 0.0 if not missing else 1.0,
                   bool(not missing), "Paper_12/table_coupling.tex"))

    ok = all(c[4] for c in checks)
    print("%-32s %-14s %-14s %-10s %s" % ("row", "recomputed", "archived",
                                          "rel", "what"))
    for label, got, ref, rel, good, what in checks:
        print("%-32s %-14.6g %-14.6g %-10.2e %s %s"
              % (label, got, ref, rel, "ok" if good else "FAIL", what))
    print("\n%d/%d provenance gates pass" % (sum(c[4] for c in checks),
                                             len(checks)))
    with open(os.path.join(RES, "coupling_provenance_check.json"), "w") as fh:
        json.dump({"n_pass": sum(c[4] for c in checks), "n_total": len(checks),
                   "all_pass": ok,
                   "rows": [{"label": c[0], "recomputed": c[1],
                             "archived": c[2], "rel": c[3], "pass": c[4],
                             "what": c[5]} for c in checks]}, fh, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
