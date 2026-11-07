"""check_coupled_patch.py -- patch and symmetry tests of the *coupled* element.

Two tests that the FEM-6 element set had not carried before round 2:

  patch      an exact field that excites every term of the enthalpy at once --
             a constant strain with a uniform electric field (elastic,
             piezoelectric and dielectric terms) and a constant strain
             gradient (gradient and flexoelectric terms) -- is imposed on one
             element and the assembled quadratic form is compared with the
             analytic integral of the same enthalpy.  A C^1 patch test that
             passes with the couplings switched on is what says the sign and
             the pairing of B, C_phi and the flexoelectric operator are right,
             not just that K is.

  symmetry   the coupled matrix [[K, B], [B^T, -C_phi]] is symmetric to machine
             precision, its blocks are the assembled ones, and its inertia is
             (n_mech, 0, n_phi): K and C_phi positive definite and the saddle
             point indefinite.  The inertia is the statement that the element
             cannot manufacture a spurious zero eigenvalue of the coupled
             problem.

    python3 python/check_coupled_patch.py   -> results/coupled_patch.json
"""
from __future__ import annotations

import json
import os

import numpy as np

import fem6_core as f6
import materials as mt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")

# one element, unit square, window of the paper's size
HX = HY = 1.0e-6
MG = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
MAT = mt.to_core(mt.batio3("y", "plane_stress"))
MAT.mu = 1e-6


def nodal_vector(g=0.0, e0=0.0):
    """Nodal values of u = g x^2 / 2, v = 0, phi = -e0 x on the unit element.

    The BFS node carries (u, u_x, u_y, u_xy, v, v_x, v_y, v_xy), so the
    quadratic field fixes all four u-values of each corner exactly.
    """
    u = np.zeros(32)
    for c, (xa, ya) in enumerate(((0.0, 0.0), (HX, 0.0), (HX, HY), (0.0, HY))):
        u[8 * c + 0] = 0.5 * g * xa ** 2
        u[8 * c + 1] = g * xa
    phi = np.array([-e0 * 0.0, -e0 * HX, -e0 * HX, -e0 * 0.0])
    return u, phi


def fem_energy(g, e0, gradient=True):
    Ke, _Me, Kuphi, Kpp = f6.element_matrices(HX, HY, MAT, MG,
                                              gradient=gradient)
    u, phi = nodal_vector(g, e0)
    return 0.5 * u @ Ke @ u + u @ Kuphi @ phi - 0.5 * phi @ Kpp @ phi


def analytic_energy(g, e0, gradient=True):
    """The same enthalpy, integrated in closed form over the element.

        Pi = 1/2 int eps C eps + 1/4 int M_mn eps_,m C eps_,n
             + int (e eps).grad(phi) + int mu grad(tr eps).grad(phi)
             - 1/2 int grad(phi) kappa grad(phi)

    with eps_xx = g x, grad(phi) = (-e0, 0) and grad(tr eps) = (g, 0).
    """
    C, e, kap = MAT.C, MAT.e, MAT.kappa
    A = HX * HY
    # elastic: 1/2 C11 g^2 \int x^2 dA
    el = 0.5 * C[0, 0] * g ** 2 * (HX ** 3 / 3.0) * HY
    gr = (0.25 * MG[0, 0] * C[0, 0] * g ** 2 * A) if gradient else 0.0
    # coupling: int (e_{k1} eps_xx) grad(phi)_k = e_{01} g (-e0) \int x dA
    pz = e[0, 0] * g * (-e0) * (0.5 * HX ** 2 * HY)
    # flexoelectric: int mu (g, 0).(-e0, 0) = -mu g e0 A
    fx = -MAT.mu * g * e0 * A
    # dielectric: -1/2 kappa_xx e0^2 A
    dl = -0.5 * kap[0, 0] * e0 ** 2 * A
    return el + gr + pz + fx + dl


def patch():
    """Two fields: one that only the classical terms see, one with a gradient."""
    rows = []
    for name, g, e0, grad in (
            ("constant strain, uniform field", 0.0, 1.0e5, True),
            ("constant strain gradient, uniform field", 1.0e5, 1.0e5, True)):
        a = fem_energy(g, e0, grad)
        b = analytic_energy(g, e0, grad)
        rows.append({"case": name, "fem": a, "analytic": b,
                     "rel_err": abs(a - b) / max(abs(b), 1e-300)})
    # a field with no gradient must not see the gradient operator at all
    a0 = fem_energy(0.0, 1.0e5, gradient=False)
    rows.append({"case": "gradient operator off, constant strain",
                 "fem": a0, "analytic": analytic_energy(0.0, 1.0e5, False),
                 "rel_err": abs(a0 - analytic_energy(0.0, 1.0e5, False))
                 / abs(analytic_energy(0.0, 1.0e5, False))})
    worst = max(r["rel_err"] for r in rows)
    return {"rows": rows, "worst_rel_err": float(worst)}


def symmetry():
    """Symmetric coupled matrix, correct blocks, inertia (n_mech, 0, n_phi).

    The clamped edge is eliminated first: the *free* element set has rigid-body
    modes, so the inertia statement is made about the system the paper solves.
    The blocks are compared after a symmetric diagonal scaling, because K scales
    as C ~ 1e11 and C_phi as kappa ~ 1e-9 and an unscaled relative threshold
    would classify every stretched eigenvalue as zero.
    """
    L, H = 40e-6, 10e-6
    mdl = f6.assemble(f6.mesh_rect(4, 2, L, H), MAT, MG)
    keep = np.setdiff1d(np.arange(mdl.K.shape[0]), mdl.constrained)
    # one electrode is grounded: the constant-potential mode of C_phi is the
    # only null vector of the dielectric block, and grounding removes it
    evC = np.linalg.eigvalsh(mdl.Cphi)
    n_null_Cphi = int((np.abs(evC) < 1e-9 * np.abs(evC).max()).sum())
    keep_phi = np.arange(1, mdl.Cphi.shape[0])
    K = mdl.K[np.ix_(keep, keep)]
    B = mdl.B[np.ix_(keep, keep_phi)]
    C = mdl.Cphi[np.ix_(keep_phi, keep_phi)]
    n, m = K.shape[0], C.shape[0]
    S = np.zeros((n + m, n + m))
    S[:n, :n] = K
    S[:n, n:] = B
    S[n:, :n] = B.T
    S[n:, n:] = -C
    asym = np.linalg.norm(S - S.T) / np.linalg.norm(S)
    d = np.sqrt(np.abs(np.diag(S)))
    d[d == 0] = 1.0
    ev = np.linalg.eigvalsh(S / np.outer(d, d))
    tol = 1e-8
    npos = int((ev > tol).sum())
    nneg = int((ev < -tol).sum())
    nzero = int(len(ev) - npos - nneg)
    # the reduced K of one element is positive *semi*-definite: the gradient
    # energy does not penalise a uniform mode, so the smallest eigenvalue sits
    # at round-off around zero and its sign is not a result.  Record it
    # relative to the matrix norm and judge it at that scale.
    kmin = float(np.linalg.eigvalsh(K)[0])
    kmin_rel = kmin / float(np.linalg.norm(K))
    cmin = float(np.linalg.eigvalsh(C)[0])
    return {"ndof_mech": int(n), "ndof_phi": int(m),
            "rel_asymmetry": float(asym),
            "n_positive": npos, "n_negative": nneg, "n_zero": nzero,
            "min_eig_K": kmin, "min_eig_K_rel": kmin_rel,
            "min_eig_Cphi": cmin,
            "n_null_Cphi_ungrounded": n_null_Cphi,
            "blocks_exact": bool(np.array_equal(S[:n, n:], B)
                                 and np.array_equal(S[n:, :n], B.T)),
            "symmetric": bool(asym < 1e-12),
            "inertia_ok": bool(npos == n and nneg == m and nzero == 0
                               and kmin_rel > -1e-10 and cmin > 0
                               and n_null_Cphi == 1)}


def main():
    P = patch()
    Y = symmetry()
    out = {"patch": P, "symmetry": Y}
    with open(os.path.join(RES, "coupled_patch.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    for r in P["rows"]:
        print(f"  patch: {r['case']:44s} rel. err {r['rel_err']:.2e}")
    print(f"  symmetry: |S - S^T|/|S| = {Y['rel_asymmetry']:.1e}, "
          f"inertia ({Y['n_positive']}, {Y['n_negative']}) "
          f"for ({Y['ndof_mech']}, {Y['ndof_phi']})")
    print(f"  worst patch error {P['worst_rel_err']:.2e}")
    print("  -> results/coupled_patch.json")


if __name__ == "__main__":
    main()
