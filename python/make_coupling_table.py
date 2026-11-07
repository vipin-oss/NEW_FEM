"""make_coupling_table.py -- Paper_12/table_coupling.tex (tabular body only)
from results/coupling_provenance.json.

Every coupling factor the paper quotes appears once, with its boundary
condition, mesh, mu, the matrix and formula behind it, and the entry of the
JSON archive that reproduces it.  The table float and the caption live in
sec/07_results.tex, so that check_float_order.py sees the label.

Layout note: the table is set at \\small with short headers and two wrapping
p-columns, because the seven natural-width columns of the first version came to
about 540 pt against a \\textwidth of about 470 pt.  No value changed in that
reduction; the formulas are abbreviated to $x/(1+x)$ and $k^2_s$ and defined in
the caption.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "Paper_12")

BUILD = {
    "k2_free_nogradient_48x4": "free, no window",
    "k2_clamped_nogradient_48x4": "left edge clamped, no window",
    "k2_clamped_gradient_48x4": "left edge clamped, window on",
    "k2_clamped_gradient_24x2": "left edge clamped, window on",
    "k2_mode_based_Kuu_24x2": "left edge clamped, window on",
    "k2_mode_based_Ksc_24x2": "left edge clamped, window on",
    "k2_mode_based_Ksc_24x2_mu0": "left edge clamped, window on",
    "k2_closed_form_plane_stress": "none (constitutive tensors)",
}
MEASURE = {
    "k2_mode_based_Kuu_24x2": "$K_{oc}$/$K_{uu}$, $k^{2}_{u}$",
    "k2_mode_based_Ksc_24x2": "$K_{oc}$/$K_{sc}$, $k^{2}_{sc}$",
    "k2_mode_based_Ksc_24x2_mu0": "$K_{oc}$/$K_{sc}$, $k^{2}_{sc}$",
}
MU = {
    "k2_free_nogradient_48x4": "$0$",
    "k2_clamped_nogradient_48x4": "$0$",
    "k2_clamped_gradient_48x4": "$0$",
    "k2_clamped_gradient_24x2": "$0$",
    "k2_mode_based_Kuu_24x2": "$10^{-6}$",
    "k2_mode_based_Ksc_24x2": "$10^{-6}$",
    "k2_mode_based_Ksc_24x2_mu0": "$0$",
    "k2_closed_form_plane_stress": "---",
}


def main():
    d = json.load(open(os.path.join(ROOT, "results",
                                    "coupling_provenance.json")))
    body = []
    for r in d["rows"]:
        lab = r["label"]
        mesh = r["mesh"].replace("x", r"$\times$") if r["mesh"] != "--" else "---"
        body.append(" & ".join([
            "$%.5f$" % r["value"],
            BUILD[lab],
            mesh,
            MU[lab],
            MEASURE.get(lab, "$K_{sc}$, $x/(1+x)$"),
        ]) + r" \\")
    tex = "\n".join([
        "%% tabular body generated -- do not edit (see AUTHOR_TODO.md)",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}r p{0.22\textwidth} l l p{0.26\textwidth}@{}}",
        r"\toprule",
        r"$k^{2}$ & build & mesh & $\mu$ & measure \\",
        r"\midrule",
    ] + body + [
        r"\bottomrule",
        r"\end{tabular}",
        "",
    ])
    with open(os.path.join(OUT, "table_coupling.tex"), "w") as fh:
        fh.write(tex)
    print("  %d rows -> Paper_12/table_coupling.tex" % len(body))


if __name__ == "__main__":
    main()
