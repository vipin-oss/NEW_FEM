"""
make_paper_table.py -- the full criterion table behind the manuscript.

    python3 python/make_paper_table.py

writes
    results/paper_table.md   every criterion of the suite, one row each

This is the archive copy.  The table typeset in the appendix is a hand-curated,
compact selection of the same benchmarks (Paper_12/table_verification.tex): a
manuscript table summarizes the evidence, it is not the evidence, so this
script no longer writes it.
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "Paper_12")

# which JSON file each criterion id is graded from
SOURCE = {
    "V": "verification.json", "F": "flexo_check.json",
    "M": "material_comparison.json", "S": "memory_variants.json",
    "C": "coupling_check.json", "K": "mode_tracking.json",
    "T": "demo.json", "P": "paper_figures_data.json",
}

TEX_WHAT = {
    "V1a": r"patch test, relative energy error", "V1b": r"gradient energy at constant strain",
    "V1c": r"$K_g$(ellipsoid) vs FEM-1 closed form", "V1d": r"$K_g$(cuboid)/$K_g$(ellipsoid), equal half-width",
    "V1e": r"equal-$M$ cuboid vs ellipsoid", "V2": r"tip displacement, length-scale sweep",
    "V3": r"observed order of convergence", "V4a": r"$C_\phi$ smallest eigenvalue",
    "V4b": r"piezo extensional $k^2$ (poling $x$)", "V5a": r"L1, $\alpha=1$, observed order",
    "V5b": r"L1 stencil error", "V5c": r"harmonic amplitude, $\alpha=1$",
    "V5d": r"harmonic amplitude, $\alpha=0.5$", "V6a": r"modal truncation, 24 modes",
    "V6b": r"truncation error monotone in $N_{\rm modes}$",
    "V7": r"equal-$M$ cuboid vs ellipsoid, max rel.\ diff",
    "F1": r"flexo patch test, $\mu=0$", "F2": r"flexo patch test, $\mu\neq0$",
    "F3": r"linearity of the flexo response in $\mu$",
    "F4": r"bending $k^2$ with $\mu=10^{-6}$\,\si{\coulomb\per\meter}",
    "M1": r"$\kappa_{11}/\kappa_{33}$ of the material record",
    "S1a": r"$\zeta_{\rm eff}(K_{\rm eff},\alpha{=}1)$ vs $\omega\tau/2$",
    "S1b": r"$\zeta(K_{uu})/\zeta(K_{\rm eff})$, $\alpha=1$",
    "S2": r"KV/Zener modulus, $\omega\tau=1$, $\alpha=1$",
    "C1": r"FEM $k^2$ (free strip) vs 2-D closed form $e^{\rm T}C^{-1}e/\kappa$",
    "C2": r"2-D model vs 3-D free bar (plane-stress reduction)",
    "C3": r"FEM $k^2$, clamped, $96\times4$ vs $48\times4$",
    "C4": r"FEM $k^2$, clamped, $24\times2$ vs $48\times4$",
    "K1": r"lowest MAC of mode 1, $h=10\to1$\,\si{\micro\meter}",
    "K2": r"worst MAC off-diagonal / $f_2/f_1$",
    "T1": r"piezo $k^2$ (mode-free), max/min over $h$",
    "T2": r"piezo $k^2$, $24\times2$ vs $48\times4$",
    "T3": r"flexo $k^2$ vs $h$", "T4": r"flexo $k^2$, $48\times4$ vs $96\times4$ witness",
    "T5": r"flexo $k^2$ at $\mu=0$, residual / value",
    "P1": r"paper figure set, vector files written",
    "P2": r"orientation sweep, rows / $k^2$ range",
}


def texify(s):
    out = []
    for ch in str(s):
        out.append({"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#",
                    "~": r"\textasciitilde{}",
                    "^": r"\^{}"}.get(ch, ch))
    return "".join(out)


UNIT = {"um": r"\,\si{\micro\meter}", "kHz": r"\,\si{\kilo\hertz}",
        "MPa": r"\,\si{\mega\pascal}", " s ": r"\,\si{\second} "}


def pretty(s):
    """1.06e-12 -> $1.06\\times10^{-12}$;  um -> microns;  % -> \%."""
    s = s.replace("graded at", "within").replace("graded to", "within")
    s = texify(s)
    out = []
    i = 0
    while i < len(s):
        m = re.match(r"(-?\d+(?:\.\d+)?)e([+-]?\d+)", s[i:])
        if m:
            out.append(r"$%s\times10^{%d}$" % (m.group(1), int(m.group(2))))
            i += m.end()
        else:
            out.append(s[i])
            i += 1
    s = "".join(out)
    for k, v in UNIT.items():
        if k == "um":
            # only a length written after a number, never the "um" of a word
            s = re.sub(r"(?<=[0-9])\s*um\b", lambda m, v=v: v, s)
        else:
            s = s.replace(k, v)
    return s


def main():
    with open(os.path.join(RES, "summary.json")) as fh:
        S = json.load(fh)
    rows = S["checks"]
    body, md = [], ["# The full criterion table (archive copy)", "",
                    f"{S['n_pass']}/{S['n_total']} checks pass.", "",
                    "| quantity | value obtained | requirement | source |",
                    "|---|---|---|---|"]
    for r in rows:
        what = TEX_WHAT.get(r["id"], texify(r["what"]))
        what = re.sub(r"(?<=[0-9])\s*um\b", lambda m: r"\,\si{\micro\meter}", what)
        src = SOURCE.get(r["id"].rstrip("ab")[0], "?")
        body.append(f"{what} & {pretty(r['value'])} & "
                    f"{pretty(r['criterion'])} \\\\")
        md.append(f"| {r['what']} | {r['value']} | {r['criterion']} | "
                  f"`results/{src}` |")
    with open(os.path.join(RES, "paper_table.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"  {S['n_pass']}/{S['n_total']} criteria -> results/paper_table.md (the typeset table is hand-curated)")
    return 0


def application_table():
    """The four polarization/kinematics combinations of the worked strip."""
    import json
    with open(os.path.join(RES, "application_table.json")) as fh:
        A = json.load(fh)["rows"]
    tex = ["% table generated from the archived results",
           r"\begin{tabular}{@{}llcccc@{}}", r"\toprule",
           r"poling & kinematics & mode & $f$ (kHz) & $k^2$ & $V$ at \SI{10}{\nano\meter} (V) \\",
           r"\midrule"]
    for r in A:
        tex.append(f"{r['poling']} & {r['kinematics'].replace('_', ' ')} & "
                   f"{r['mode']} ({r['mode_index']}) & {r['f_kHz']:.1f} & "
                   f"{r['k2']:.4f} & {r['V0_V']:.2f} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(OUT, "table_application.tex"), "w") as fh:
        fh.write("\n".join(tex) + "\n")
    print(f"  {len(A)} rows -> Paper_12/table_application.tex")
    return 0


if __name__ == "__main__":
    application_table()
    raise SystemExit(main())
