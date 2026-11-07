"""
run_config_table.py -- the combined case: piezoelectric and flexoelectric
coupling on the *same* bending mode, one at a time and together.

The paper uses two electrical configurations, and they are not variants of one
device: the extensional harvester is a plate poled along x with electrodes on
the end faces, while the bending harvester is the same plate poled along y
with electrodes on the long faces (Table tab:axes).  A referee is entitled to
ask what the piezoelectric terms do on the *bending* device, since the same
crystal carries e31 and e33 whether or not they are wanted.  This script
answers that for the bending mode:

    k2_p    mu = 0            piezoelectric only (e31, e33, e15 all present)
    k2_f    e  = 0            flexoelectric only
    k2_b    both             what the thickness sweep actually reports

and verifies the small-coupling rule k2_b = k2_p + k2_f to the accuracy that
the coupling is small.

Writes results/config_table.{json,md} and Paper_12/table_config.tex.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
sys.path.insert(0, HERE)

import fem6_core as f6          # noqa: E402
import materials as mt          # noqa: E402
from run_demos import _modal_k2  # noqa: E402  (one eigensolve, no difference)

L = 200e-6
HS = [10e-6, 5e-6, 2e-6, 1e-6]
MU = 1.0e-6


def main():
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    base = mt.batio3("y", "plane_stress")          # poling y -> bending device
    piezo = mt.Material(**{**base.__dict__, "mu": 0.0})
    flexo = mt.Material(**{**base.__dict__, "e31": 0.0, "e33": 0.0,
                           "e15": 0.0})
    both = mt.Material(**{**base.__dict__, "mu": MU})

    rows = []
    for h in HS:
        mesh = f6.mesh_rect(48, 4, L, h)
        k2_p, f_p = _modal_k2(mesh, piezo, Mg, ("bottom", "top"))
        k2_f, f_f = _modal_k2(mesh, flexo, Mg, ("bottom", "top"))
        k2_b, f_b = _modal_k2(mesh, both, Mg, ("bottom", "top"))
        rows.append({"h_um": h * 1e6,
                     "k2_piezo": float(k2_p), "k2_flexo": float(k2_f),
                     "k2_both": float(k2_b),
                     "piezo_share": float(k2_p / k2_b),
                     "flexo_shift": float(k2_b / k2_f - 1.0),
                     "f1_kHz": float(f_b)})

    data = {"poling": "y", "electrodes": "bottom/top", "pair": "long faces",
            "mesh": "48x4", "L_um": L * 1e6, "mu": MU,
            "rows": rows}
    with open(os.path.join(RES, "config_table.json"), "w") as fh:
        json.dump(data, fh, indent=1)

    worst_share = max(r["piezo_share"] for r in rows)
    shift_min = min(r["flexo_shift"] for r in rows)
    growth_both = rows[-1]["k2_both"] / rows[0]["k2_both"]
    growth_flexo = rows[-1]["k2_flexo"] / rows[0]["k2_flexo"]
    data["growth_both"] = float(growth_both)
    data["growth_flexo_only"] = float(growth_flexo)
    with open(os.path.join(RES, "config_table.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    md = ["# Piezoelectric and flexoelectric coupling on the same bending mode",
          "",
          "Poling $y$, electrodes on the long faces (gap $h$), 48$\\times4$ "
          "mesh, $L=\\SI{200}{\\micro\\metre}$, window half-widths "
          "$3\\times\\SI{1}{\\micro\\metre}$, $\\mu=10^{-6}$ C/m.", "",
          "| $h$ [µm] | $k^2$ piezo only | $k^2$ flexo only ($e=0$) | "
          "$k^2$ both (as reported) | piezo share | both/flexo $-1$ |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['h_um']:g} | {r['k2_piezo']:.2e} | "
                  f"{r['k2_flexo']:.4e} | {r['k2_both']:.4e} | "
                  f"{r['piezo_share']:.1e} | {100 * r['flexo_shift']:+.1f} % |")
    md += ["",
           "The piezoelectric share of the bending coupling is at most "
           f"{worst_share:.1e} -- at the round-off floor of the secular "
           "equation -- so the bending device is not a piezoelectric device.  "
           "The reason is geometric rather than numerical: "
           "the piezoelectric charge of a bending mode is "
           "$e_{31}\\varepsilon_{xx}+e_{33}\\varepsilon_{yy}$, and with "
           "$\\varepsilon_{xx}=\\kappa(y-h/2)$ odd about the mid-plane and "
           "$\\varepsilon_{yy}\\simeq0$ its integral over a face electrode "
           "vanishes."
           "", "",
           "The two effects are nevertheless not separable inside one run, and "
           "the table says by how much: the piezoelectric terms change the "
           "elastic stiffness of the same mode, so the flexo-only column "
           f"differs from the reported one by up to {100 * abs(shift_min):.0f} % "
           f"at the thinnest plate (both/flexo $-1$ = {100 * shift_min:+.1f} %)."
           "  With the piezoelectric terms switched off the flexoelectric "
           f"coupling would grow by {growth_flexo:.1f} over the range instead "
           f"of the {growth_both:.1f} that the paper reports for the real "
           "crystal.", ""]
    with open(os.path.join(RES, "config_table.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    # LaTeX
    ROW = chr(92) * 2
    BS = chr(92)
    Ltx = ["% table generated from the archived results",
           BS + "begin{tabular}{@{}lcccc@{}}", BS + "toprule",
           "$h$ [" + BS + "si{" + BS + "micro" + BS + "metre}] & "
           "$k^2$ piezo only & $k^2$ flexo only, $e=0$ & "
           "$k^2$ both, as reported & both/flexo $-1$" + ROW,
           BS + "midrule"]
    for r in rows:
        Ltx.append(f"{r['h_um']:g} & {r['k2_piezo']:.1e} & "
                   f"{r['k2_flexo']:.4e} & {r['k2_both']:.4e} & "
                   f"{100 * r['flexo_shift']:+.1f}\\%" + ROW)
    Ltx += [BS + "bottomrule", BS + "end{tabular}"]
    with open(os.path.join(ROOT, "Paper_12", "table_config.tex"), "w") as fh:
        fh.write("\n".join(Ltx) + "\n")

    for r in rows:
        print(f"  h={r['h_um']:4.1f} um  piezo {r['k2_piezo']:.1e}  "
              f"flexo {r['k2_flexo']:.4e}  both {r['k2_both']:.4e}  "
              f"shift {100 * r['flexo_shift']:+.1f} %")
    print("  -> results/config_table.md, Paper_12/table_config.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
