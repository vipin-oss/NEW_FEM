"""
run_coupling_check.py -- is the piezoelectric coupling factor of the plate the
one the material constants predict?

The quasi-static coupling factor of an electrode pair is

    x = d^T K_uu^{-1} d / beta,      k^2 = x/(1+x),

with K_uu the SHORT-CIRCUIT mechanical stiffness.  For a homogeneous body
whose strain is free, the same number follows from the constitutive tensors
alone, because the mechanical energy released by the polarisation is
1/2 e^T C^{-1} e E^2 per unit volume against 1/2 kappa E^2 of electrical
energy:

    x = e^T C^{-1} e / kappa,        k^2 = x/(1+x).

That closed form contains no geometry, no mesh and no eigenvalue, so comparing
it with the finite element value of the same plate is an independent check of
the whole piezoelectric path (e tensor, C reduction, potential condensation,
floating-electrode update).

Three closed forms are reported, because the answer depends on how much the
body is allowed to relax:

  * 3-D, free bar        -- eps_xx, eps_yy, eps_zz all free (all stresses zero)
  * 3-D, laterally blocked -- only eps_xx free  (the "uniaxial" textbook value)
  * 2-D plane stress     -- what this plate model actually implements

and the finite element value is compared with the last one, which is the model
the code solves.  The 2-D-to-3-D gap is reported separately, as a modelling
deviation rather than an implementation error.

Writes results/coupling_check.json and .md.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fem6_core as f6          # noqa: E402
import materials as mt          # noqa: E402

RESULTS = os.path.join(ROOT, "results")
EPS0 = 8.854187817e-12
L, H = 200e-6, 10e-6


def closed_forms(kin="plane_stress", poling="x"):
    """Analytic coupling factors from the constitutive record."""
    m = mt.batio3(poling, kin)
    out = {}

    # --- 3-D, free bar: all three normal strains free, field along the polar
    # axis.  e_11j for j in (x, y, z) with 3 = x.
    C3 = m.full_3d()
    s3 = np.linalg.inv(C3)
    e3 = np.array([m.e33, m.e31, m.e31])
    kap = m.kappa_r33 * EPS0
    x = float(e3 @ s3 @ e3) / kap
    out["k2_3d_free"] = x / (1.0 + x)
    out["x_3d_free"] = x

    # --- 3-D, laterally blocked: only eps_xx free
    x = m.e33 ** 2 / (C3[0, 0] * kap)
    out["k2_3d_uniaxial"] = x / (1.0 + x)

    # --- the 2-D model that the code implements
    C = m.C()
    ev = m.e()[0, :]                     # field along x
    k = m.kappa()[0, 0]
    x = float(ev @ np.linalg.solve(C, ev)) / k
    out["k2_2d_closed"] = x / (1.0 + x)
    out["x_2d_closed"] = x
    return out


def fem_k2(kin="plane_stress", poling="x", nx=48, ny=4, h=H,
           clamped=("left",)):
    """Quasi-static coupling of the finite element plate.

    K_uu is the SHORT-circuit stiffness: the mechanical energy that the
    electrodes can pick up is measured against the stiff (grounded) state.
    """
    mesh = f6.mesh_rect(nx, ny, L, h)
    mat = mt.Material(**{**mt.batio3(poling, kin).__dict__, "mu": 0.0})
    mdl = f6.assemble(mesh, mt.to_core(mat), np.zeros((2, 2)),
                      clamped_edges=clamped)
    pair = ("left", "right") if poling == "x" else ("bottom", "top")
    Ksc, _, _, _ = f6.reduce(mdl, "short", pair=pair)
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=pair)
    sd = np.sqrt(np.abs(np.diag(Ksc)))
    S = 1.0 / sd
    b = S * d
    Ks = Ksc * S[:, None] * S[None, :]
    if clamped:
        x = float(b @ np.linalg.solve(Ks, b)) / beta
    else:
        x = float(b @ np.linalg.lstsq(Ks, b, rcond=1e-11)[0]) / beta
    return x / (1.0 + x)


def main():
    out = {"closed_form": closed_forms("plane_stress"),
           "closed_form_plane_strain": closed_forms("plane_strain"),
           "fem": {}}
    for kin in ("plane_stress", "plane_strain"):
        out["fem"][kin] = {}
        for tag, kw in (("free_48x4", dict(clamped=())),
                        ("clamped_48x4", dict(clamped=("left",))),
                        ("clamped_24x2", dict(nx=24, ny=2)),
                        ("clamped_96x4", dict(nx=96, ny=4))):
            v = fem_k2(kin, **kw)
            out["fem"][kin][tag] = v
            print(f"  {kin:12s} {tag:12s} k2 = {v:.5f}")

    cf = out["closed_form"]
    fem = out["fem"]["plane_stress"]
    out["rel_err_free"] = abs(fem["free_48x4"] / cf["k2_2d_closed"] - 1.0)
    out["rel_err_clamped"] = abs(fem["clamped_48x4"] / cf["k2_2d_closed"] - 1.0)
    out["rel_gap_2d_vs_3d"] = abs(cf["k2_2d_closed"] / cf["k2_3d_free"] - 1.0)
    out["rel_mesh_96_vs_48"] = abs(
        fem["clamped_96x4"] / fem["clamped_48x4"] - 1.0)

    print()
    print(f"  closed form, 3-D free bar          k2 = {cf['k2_3d_free']:.5f}")
    print(f"  closed form, 3-D uniaxial          k2 = {cf['k2_3d_uniaxial']:.5f}")
    print(f"  closed form, 2-D plane stress      k2 = {cf['k2_2d_closed']:.5f}")
    print(f"  FEM, unconstrained plate 48x4      k2 = {fem['free_48x4']:.5f}"
          f"   ({100*out['rel_err_free']:.3f} % from the 2-D closed form)")
    print(f"  FEM, clamped plate 48x4            k2 = {fem['clamped_48x4']:.5f}"
          f"   ({100*out['rel_err_clamped']:.3f} %)")

    with open(os.path.join(RESULTS, "coupling_check.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    cfp = out["closed_form_plane_strain"]
    md = ["# Piezoelectric coupling: closed form versus finite element", "",
          "| quantity | plane stress | plane strain |",
          "|---|---|---|",
          f"| 3-D closed form, free bar | {cf['k2_3d_free']:.5f} | "
          f"{cfp['k2_3d_free']:.5f} |",
          f"| 3-D closed form, uniaxial | {cf['k2_3d_uniaxial']:.5f} | "
          f"{cfp['k2_3d_uniaxial']:.5f} |",
          f"| 2-D closed form, $e^TC^{-1}e/\\kappa$ | {cf['k2_2d_closed']:.5f} | "
          f"{cfp['k2_2d_closed']:.5f} |",
          f"| FEM, unconstrained plate 48x4 | {fem['free_48x4']:.5f} | "
          f"{out['fem']['plane_strain']['free_48x4']:.5f} |",
          f"| FEM, clamped plate 48x4 | {fem['clamped_48x4']:.5f} | "
          f"{out['fem']['plane_strain']['clamped_48x4']:.5f} |",
          f"| FEM, clamped plate 24x2 | {fem['clamped_24x2']:.5f} | "
          f"{out['fem']['plane_strain']['clamped_24x2']:.5f} |", "",
          f"FEM versus the 2-D closed form: {100*out['rel_err_free']:.3f} % "
          f"(free), {100*out['rel_err_clamped']:.3f} % (clamped).",
          f"2-D model versus the 3-D free bar: {100*out['rel_gap_2d_vs_3d']:.2f} % "
          "-- the plane-stress reduction drops the $e_{31}\\varepsilon_{zz}$ "
          "term, which is the price of the 2-D idealisation, not an error of "
          "the implementation."]
    with open(os.path.join(RESULTS, "coupling_check.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    print("  -> results/coupling_check.{md,json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
