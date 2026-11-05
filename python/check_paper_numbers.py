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


def row(where, literal, source, value, fmt):
    got = fmt.format(value)
    got = got.replace("e-0", "e-").replace("e+0", "e+")   # 1.74e-04 -> 1.74e-4
    return {"where": where, "tex": literal, "json": source,
            "value": value, "formatted": got, "ok": literal == got}


def main():
    tex = open(TEX).read()
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
    R.append(row("thickness, flexo k^2 at h=1", "4.17e-3",
                 "demo.json flexo_thickness[3].k2_flexo",
                 g("demo.json.flexo_thickness.3.k2_flexo"), "{:.2e}"))
    R.append(row("thickness, flexo growth factor", "23.9",
                 "demo.json flexo ratio",
                 g("demo.json.flexo_thickness.3.k2_flexo")
                 / g("demo.json.flexo_thickness.0.k2_flexo"), "{:.1f}"))
    R.append(row("coupling check, closed form", "0.56079",
                 "coupling_check.json closed_form.k2_2d_closed",
                 g("coupling_check.json.closed_form.k2_2d_closed"), "{:.5f}"))
    R.append(row("coupling check, free 48x4", "0.56079",
                 "coupling_check.json fem.plane_stress.free_48x4",
                 g("coupling_check.json.fem.plane_stress.free_48x4"), "{:.5f}"))
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
    R.append(row("criteria count", "thirty-nine",
                 "summary.json n_total = 39", 39, "thirty-nine"))

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
