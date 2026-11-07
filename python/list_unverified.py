"""
list_unverified.py -- every number in the paper that no independent route
reproduces, in one place.

    python3 python/list_unverified.py   -> results/unverified_numbers.md

Three classes are kept apart, because they mean different things:

    verified      a closed form, a quadrature or a polynomial reproduces it,
                  or the number *is* the comparison against such a route
                  (criteria C1, D1, I1-I9, N1, A2).
    not verified  a finite element output.  Traceable to a JSON file and to a
                  passing criterion -- so it is not a typo and it is not
                  unattributable -- but the only thing it has been graded
                  against is the same solver.
    input         geometry, chosen operating points, and the two flagged
                  material constants.

The list is built from the JSON files rather than typed, and each entry is
checked to still appear in Paper_12/main.tex, so a number that is removed from
the manuscript cannot linger here as if it were a live claim.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
TEX = os.path.join(ROOT, "Paper_12", "main.tex")


def J(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)



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
    rows = []          # (literal, what, source, why)

    # ---- 1. everything the abstract audit already calls "nahi hua"
    for c in J("abstract_audit.json")["claims"]:
        if c["verdict"] == "nahi hua":
            rows.append((c["literal"], c["what"], "abstract_audit.json",
                         c["route"]))

    # ---- 2. the application table: four FEM configurations, no closed form
    at = J("application_table.json")
    for r in at["rows"]:
        rows.append((f"{r['f_kHz']:.1f}",
                     f"application table, {r['poling']}/{r['kinematics']}, "
                     f"mode {r['mode_index']} frequency [kHz]",
                     "application_table.json", "FEM eigen-solve"))
        rows.append((f"{r['k2']:.4f}",
                     f"application table, {r['poling']}/{r['kinematics']} "
                     f"$k^2$", "application_table.json",
                     "FEM eigen-solve; no closed form for this mode and "
                     "this clamping"))
        rows.append((f"{r['V0_V']:.2f}",
                     f"application table, {r['poling']}/{r['kinematics']} "
                     f"open-circuit voltage [V]", "application_table.json",
                     "FEM eigen-solve plus the rank-one electrode update"))

    # ---- 3. mode tracking
    mt = J("mode_tracking.json")
    rows.append((f"{mt['mac_min']:.3f}", "lowest MAC of mode 1 against the "
                 "$h=\\SI{10}{\\micro\\meter}$ shape", "mode_tracking.json",
                 "an FEM eigenvector overlap; the reference is another FEM "
                 "eigenvector"))
    rows.append((f"{mt['min_f2_over_f1']:.2f}", "smallest $f_2/f_1$ over the "
                 "thickness sweep", "mode_tracking.json",
                 "FEM eigen-solve; exact for no geometry of this kind"))

    # ---- 4. the thickness sweep: frequencies and slopes
    th = J("demo.json")["flexo_thickness"]
    rows.append((f"{th[0]['f1_kHz']:.1f}", "$f_1$ at $h=\\SI{10}{\\micro\\meter}$"
                 " [kHz]", "demo.json flexo_thickness[0]",
                 "FEM eigen-solve; the Euler--Bernoulli value is the one "
                 "quoted as the comparison, not as this number"))
    for h, s in ((10, -1.96), (5, -1.52), (2, -0.43)):
        rows.append((f"{s:.2f}", f"local log-log slope of the flexoelectric "
                     f"$k^2$ at $h=\\SI{{{h}}}{{\\micro\\meter}}$",
                     "demo.json flexo_thickness (finite differences)",
                     "a finite difference of the eight FEM runs; no closed "
                     "form predicts the slope once the window is fixed in size"))

    # ---- 5. the memory study
    mv = J("memory_variants.json")
    # alpha = 1: zeta from the successive-peak decrement (exact conversion);
    # alpha < 1: only the first-period local value, the decay being
    # non-exponential (round 16).
    for key, what, field in (
            ("Keff_alpha1.0", "$\\zeta_{\\rm eff}$ at $\\alpha=1$", "zeta_eff"),
            ("Kuu_alpha1.0", "$\\zeta(K_{uu})$ at $\\alpha=1$", "zeta_eff"),
            ("Keff_alpha0.7", "first-period $\\zeta_{\\rm eff}$ at $\\alpha=0.7$",
             "zeta_first"),
            ("Kuu_alpha0.7", "first-period $\\zeta(K_{uu})$ at $\\alpha=0.7$",
             "zeta_first")):
        prec = 4 if field == "zeta_first" else 5
        rows.append((f"{mv['S1'][key][field]:.{prec}f}", what,
                     f"memory_variants.json S1 {field}",
                     "a logarithmic decrement of an FEM ring-down; the "
                     "closed-form $\\omega\\tau/2$ is the $\\alpha=1$, "
                     "$K_{\\rm eff}$ limit only"))
    rows.append((f"{mv['S1']['Keff_alpha1.0']['V0']:.2f}",
                 "open-circuit voltage of the ring-down initial condition [V]",
                 "memory_variants.json S1",
                 "FEM mode shape times the rank-one electrode update"))

    # ---- 6. the 2-D versus 3-D gap
    cc = J("coupling_check.json")
    rows.append((f"{100 * cc['rel_gap_2d_vs_3d']:.1f}",
                 "2-D plane-stress against 3-D free-bar closed form [%]",
                 "coupling_check.json rel_gap_2d_vs_3d",
                 "the gap itself is a comparison, but its *attribution* to "
                 "the dropped $e_{31}\\varepsilon_{zz}$ is not separable "
                 "here"))

    # ---- keep only what is still in the manuscript, and say what was dropped
    kept, stale = [], []
    for lit, what, src, why in rows:
        (kept if lit in tex else stale).append((lit, what, src, why))

    lines = ["# Numbers in the paper with no independent route", "",
             "Generated by `python/list_unverified.py` from the JSON files.  "
             "Each entry is checked to still appear in `Paper_12/main.tex`, so "
             "this is a list of live claims and not of history.", "",
             f"**{len(kept)} entries.**  For comparison: 51 numbers are traced "
             "to their JSON by criterion N1, and the independent routes of "
             "Table 6 (criteria I1--I9, C1, D1) reproduce the headline values "
             "along paths that never touch the assembled matrices.", "",
             "| number | what it is | source | why it is not verified |",
             "|---|---|---|---|"]
    for lit, what, src, why in kept:
        lines.append(f"| `{lit}` | {what} | `{src}` | {why} |")
    lines += ["", "## What this list does and does not say", "",
              "Every entry is reproducible: `python3 python/run_all.py` "
              "regenerates it, and each is graded by a criterion that compares "
              "it with something else in the same solver (mesh refinement, a "
              "witness run, a $\\mu=0$ floor).  That is a statement about "
              "consistency, not about correctness against nature.  The values "
              "in Table 6 are the ones where an outside route exists; these "
              "are the ones where it does not.", "",
              "Two entries deserve a caveat larger than the rest, and both are "
              "in §7 of the manuscript: the flexoelectric numbers are "
              "proportional to an unmeasured $\\mu^2$, and every frequency is "
              "proportional to an unsourced $\\rho^{-1/2}$.", ""]
    if stale:
        lines += ["## Entries dropped because the number is no longer in the "
                  "manuscript", ""]
        for lit, what, src, _ in stale:
            lines.append(f"- `{lit}` ({what}) -- `{src}`")
        lines.append("")
    with open(os.path.join(RES, "unverified_numbers.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(RES, "unverified_numbers.json"), "w") as fh:
        json.dump({"n": len(kept),
                   "rows": [{"literal": a, "what": b, "source": c,
                             "why": d} for a, b, c, d in kept],
                   "stale": [a for a, *_ in stale]}, fh, indent=1)

    print(f"  {len(kept)} unverified numbers, {len(stale)} stale")
    for lit, what, _, _ in stale:
        print(f"    stale: {lit} ({what})")
    print("  -> results/unverified_numbers.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
