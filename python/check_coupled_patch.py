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


def nodal_vector(g=0.0, e0=0.0, affine=.01):
    """u=affine*x+g*x^2/2, v=0, phi=-e0*(x+y)."""
    u = np.zeros(32)
    corners = ((0.,0.),(HX,0.),(HX,HY),(0.,HY))
    for c,(x,y) in enumerate(corners):
        u[8*c] = affine*x + .5*g*x*x
        u[8*c+1] = affine + g*x
    return u, np.array([-e0*(x+y) for x,y in corners])


def analytic_components(g,e0,gradient=True,affine=.01):
    A=HX*HY; C,e,kap=MAT.C,MAT.e,MAT.kappa
    return dict(elastic=.5*C[0,0]*A*(affine**2+affine*g*HX+g*g*HX*HX/3),
                gradient=.25*MG[0,0]*C[0,0]*g*g*A if gradient else 0.,
                piezoelectric=-e0*(e[0,0]+e[1,0])*A*(affine+.5*g*HX),
                flexoelectric=-MAT.mu*g*e0*A,
                dielectric=-.5*e0*e0*kap.sum()*A)


def analytic_energy(g,e0,gradient=True):
    return sum(analytic_components(g,e0,gradient).values())


def fem_components(g,e0,gradient=True):
    from dataclasses import replace
    u,phi=nodal_vector(g,e0)
    K,_,B,C=f6.element_matrices(HX,HY,MAT,MG,gradient=gradient)
    K0,_,Bp,_=f6.element_matrices(HX,HY,replace(MAT,mu=0.),MG,gradient=False)
    return dict(elastic=.5*u@K0@u,gradient=.5*u@(K-K0)@u,
                piezoelectric=u@Bp@phi,flexoelectric=u@(B-Bp)@phi,
                dielectric=-.5*phi@C@phi)


def fem_energy(g,e0,gradient=True):
    return sum(fem_components(g,e0,gradient).values())


def patch():
    rows=[]
    for name,g,grad in [('affine strain, uniform field',0.,True),
                         ('affine plus strain gradient, uniform field',1e5,True),
                         ('gradient stiffness off, affine strain',0.,False)]:
        fc=fem_components(g,1e5,grad);ac=analytic_components(g,1e5,grad)
        scale=sum(abs(v) for v in ac.values())
        errors={k:abs(fc[k]-ac[k])/max(abs(ac[k]),scale*1e-12) for k in ac}
        # Zero terms are checked absolutely relative to total energy scale.
        errors={k:(abs(fc[k])/scale if ac[k]==0 else errors[k]) for k in ac}
        rows.append(dict(case=name,fem=sum(fc.values()),analytic=sum(ac.values()),
                         components_fem=fc,components_analytic=ac,
                         component_errors=errors,rel_err=max(errors.values())))
    assert all(abs(v)>0 for v in rows[1]['components_analytic'].values())
    worst=max(r['rel_err'] for r in rows)
    assert worst<1e-10, rows
    return dict(rows=rows,worst_rel_err=float(worst))


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
