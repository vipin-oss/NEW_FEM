"""
FEM-6 core library
==================
C1 Bogner-Fox-Schmit (BFS) plane-strain finite element framework for
piezoelectric solids with

  * an anisotropic strain-gradient (nonlocal) energy derived from the second
    moment of a rectangular (2-D) / cuboid (3-D) averaging domain, and
  * fractional Kelvin-Voigt memory of Caputo order alpha on the condensed
    electromechanical stiffness.

Conventions (identical to FEM-1 and FEM-5 manuscripts in this project)
----------------------------------------------------------------------
Plane strain in the x-z plane.  The beam/microbridge axis is x, the thickness
direction is z (here called y internally to keep the 2-D code simple; the
manuscript symbol is z).  Poling is along the thickness direction.

Strain vector            eps = [eps_xx, eps_zz, gamma_xz]^T
Electric field           E = -grad(phi)
Constitutive relations   sigma = C eps - e^T E ,   D = e eps + kappa E
Enthalpy density         H = 1/2 eps'C eps - E'e eps - 1/2 E'kappa E
                               + (1/4) M_mn (C eps)_,m . (eps)_,n

Gradient energy coefficient
---------------------------
The strain-gradient (double-stress) stiffness assembled here is

    K_g = (1/2) * int  M_mn  B_,m^T C B_,n  dOmega ,

so that the energy is  (1/4) M_mn (C eps)_,m . (eps)_,n  and the double stress
is  q = (1/2) M_mn (C eps)_,n .  The factor 1/2 is the Taylor factor of the
uniform-kernel average and is *dimension independent*: only the second-moment
tensor M changes with the shape of the averaging domain.

    ellipsoid (3-D, semi-axes l)   M = diag(l_x^2/5, l_y^2/5, l_z^2/5)
    rectangle (2-D, half-widths a) M = diag(a_x^2/3, a_y^2/3)
    cuboid    (3-D, half-widths a) M = diag(a_x^2/3, a_y^2/3, a_z^2/3)

FEM-1 uses the equivalent "L-form"  K_g = (1/10) L_mn B_,m^T C B_,n  with
L = diag(l^2) = 5 M.  Writing 1/20 * M (i.e. copying the ellipsoid number
while swapping L -> M) is wrong by a factor of five.  See
docs/FEM6_cuboid_coefficient.md.

Author: FEM-6 (HSRF 2026) -- reference implementation.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from scipy.linalg import eigh, cho_factor, cho_solve
from math import gamma

# --------------------------------------------------------------------------
# Gauss-Legendre rules on [-1, 1]
# --------------------------------------------------------------------------


def gauss_legendre(n: int):
    x, w = np.polynomial.legendre.leggauss(n)
    return x, w


# --------------------------------------------------------------------------
# 1-D cubic Hermite functions (FEM-5 convention)
# --------------------------------------------------------------------------


def hermite(s):
    """H0, H1 and their first two derivatives (s may be an array)."""
    s = np.asarray(s, dtype=float)
    H0 = 0.25 * (2.0 - 3.0 * s + s ** 3)
    H1 = 0.25 * (1.0 - s - s ** 2 + s ** 3)
    dH0 = 0.25 * (-3.0 + 3.0 * s ** 2)
    dH1 = 0.25 * (-1.0 - 2.0 * s + 3.0 * s ** 2)
    ddH0 = 0.25 * (6.0 * s)
    ddH1 = 0.25 * (-2.0 + 6.0 * s)
    return H0, H1, dH0, dH1, ddH0, ddH1


# corner coordinates in the reference element, counter-clockwise
_CORNERS = ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))


def bfs_scalar(xi, eta, hx, hy):
    """Bicubic Hermite (BFS) scalar basis.

    Returns
    -------
    N, Nx, Ny, Nxx, Nxy, Nyy : (npts, 16) arrays
        Basis functions and their first/second derivatives at (xi, eta).
        Local ordering: for each of the 4 corners,
        [value, d/dx, d/dy, d2/dxdy].
    """
    xi = np.atleast_1d(np.asarray(xi, float))
    eta = np.atleast_1d(np.asarray(eta, float))
    n = xi.size
    N = np.zeros((n, 16))
    Nx = np.zeros((n, 16))
    Ny = np.zeros((n, 16))
    Nxx = np.zeros((n, 16))
    Nxy = np.zeros((n, 16))
    Nyy = np.zeros((n, 16))

    for a, b in _CORNERS:
        k = 4 * _CORNERS.index((a, b))
        s = -a * xi
        t = -b * eta
        H0s, H1s, dH0s, dH1s, ddH0s, ddH1s = hermite(s)
        H0t, H1t, dH0t, dH1t, ddH0t, ddH1t = hermite(t)

        # 1-D factors in xi (value family A and derivative family C)
        A = H0s
        dA = -a * dH0s
        ddA = a ** 2 * ddH0s
        C = 0.5 * hx * (-a) * H1s
        dC = 0.5 * hx * a ** 2 * dH1s
        ddC = 0.5 * hx * (-a ** 3) * ddH1s
        # 1-D factors in eta
        B = H0t
        dB = -b * dH0t
        ddB = b ** 2 * ddH0t
        D = 0.5 * hy * (-b) * H1t
        dD = 0.5 * hy * b ** 2 * dH1t
        ddD = 0.5 * hy * (-b ** 3) * ddH1t

        # value / value
        N[:, k + 0] = A * B
        Nx[:, k + 0] = (2.0 / hx) * dA * B
        Ny[:, k + 0] = (2.0 / hy) * A * dB
        Nxx[:, k + 0] = (2.0 / hx) ** 2 * ddA * B
        Nxy[:, k + 0] = (4.0 / (hx * hy)) * dA * dB
        Nyy[:, k + 0] = (2.0 / hy) ** 2 * A * ddB

        # d/dx
        N[:, k + 1] = C * B
        Nx[:, k + 1] = (2.0 / hx) * dC * B
        Ny[:, k + 1] = (2.0 / hy) * C * dB
        Nxx[:, k + 1] = (2.0 / hx) ** 2 * ddC * B
        Nxy[:, k + 1] = (4.0 / (hx * hy)) * dC * dB
        Nyy[:, k + 1] = (2.0 / hy) ** 2 * C * ddB

        # d/dy
        N[:, k + 2] = A * D
        Nx[:, k + 2] = (2.0 / hx) * dA * D
        Ny[:, k + 2] = (2.0 / hy) * A * dD
        Nxx[:, k + 2] = (2.0 / hx) ** 2 * ddA * D
        Nxy[:, k + 2] = (4.0 / (hx * hy)) * dA * dD
        Nyy[:, k + 2] = (2.0 / hy) ** 2 * A * ddD

        # d2/dxdy
        N[:, k + 3] = C * D
        Nx[:, k + 3] = (2.0 / hx) * dC * D
        Ny[:, k + 3] = (2.0 / hy) * C * dD
        Nxx[:, k + 3] = (2.0 / hx) ** 2 * ddC * D
        Nxy[:, k + 3] = (4.0 / (hx * hy)) * dC * dD
        Nyy[:, k + 3] = (2.0 / hy) ** 2 * C * ddD

    return N, Nx, Ny, Nxx, Nxy, Nyy


def bilinear(xi, eta):
    """Four-node bilinear basis and derivatives in (xi, eta)."""
    xi = np.atleast_1d(np.asarray(xi, float))
    eta = np.atleast_1d(np.asarray(eta, float))
    n = xi.size
    N = np.zeros((n, 4))
    Nx = np.zeros((n, 4))
    Ny = np.zeros((n, 4))
    for k, (a, b) in enumerate(_CORNERS):
        N[:, k] = 0.25 * (1.0 + a * xi) * (1.0 + b * eta)
        Nx[:, k] = 0.25 * a * (1.0 + b * eta)
        Ny[:, k] = 0.25 * b * (1.0 + a * xi)
    return N, Nx, Ny


# --------------------------------------------------------------------------
# Material models
# --------------------------------------------------------------------------


@dataclass
class Material:
    """Plane-strain (x-z) material data.

    C     : 3x3 stiffness for [eps_xx, eps_zz, gamma_xz]
    e     : 2x3 piezoelectric matrix, rows = (E_x, E_z), cols = (xx, zz, xz)
    kappa : 2x2 permittivity
    rho   : mass density
    """

    C: np.ndarray
    e: np.ndarray
    kappa: np.ndarray
    rho: float
    name: str = "material"
    mu: float = 0.0          # flexoelectric constant, C/m (single-constant,
                             # shear-free: D = e eps + mu grad(tr eps) + kappa E)


def isotropic_plane_strain(E: float, nu: float, rho: float) -> Material:
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    mu = E / (2.0 * (1.0 + nu))
    C = np.array([[lam + 2 * mu, lam, 0.0],
                  [lam, lam + 2 * mu, 0.0],
                  [0.0, 0.0, mu]])
    return Material(C=C, e=np.zeros((2, 3)), kappa=np.eye(2) * 1e-11,
                    rho=rho, name=f"isotropic E={E:.3g}")


# --------------------------------------------------------------------------
# 3-D tensors and plane-strain reduction
# --------------------------------------------------------------------------

_VOIGT_PAIRS = ((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1))


def _C_to_tensor(C):
    T = np.zeros((3, 3, 3, 3))
    for A, (i, j) in enumerate(_VOIGT_PAIRS):
        for B, (k, l) in enumerate(_VOIGT_PAIRS):
            T[i, j, k, l] = C[A, B]
            T[j, i, k, l] = C[A, B]
            T[i, j, l, k] = C[A, B]
            T[j, i, l, k] = C[A, B]
    return T


def _e_to_tensor(e):
    """Voigt e (engineering shear strain) -> third-order tensor.

    The Voigt shear entries multiply the engineering shear strain
    gamma = 2 eps, so the tensor components carry a factor 1/2.
    """
    T = np.zeros((3, 3, 3))
    for A, (j, k) in enumerate(_VOIGT_PAIRS):
        f = 0.5 if A >= 3 else 1.0
        T[:, j, k] = f * e[:, A]
        T[:, k, j] = f * e[:, A]
    return T


def _tensor_to_2d(C3, e3, k3, Q=None):
    """Rotate the 3-D tensors and return the plane-strain (x-y) blocks."""
    if Q is None:
        Q = np.eye(3)
    C4 = np.einsum("ip,jq,kr,ls,pqrs->ijkl", Q, Q, Q, Q, C3)
    e3 = np.einsum("ip,jq,kr,pqr->ijk", Q, Q, Q, e3)
    k3 = Q @ k3 @ Q.T
    C = np.array([[C4[0, 0, 0, 0], C4[0, 0, 1, 1], C4[0, 0, 0, 1]],
                  [C4[1, 1, 0, 0], C4[1, 1, 1, 1], C4[1, 1, 0, 1]],
                  [C4[0, 1, 0, 0], C4[0, 1, 1, 1], C4[0, 1, 0, 1]]])
    e = np.array([[e3[0, 0, 0], e3[0, 1, 1], 2 * e3[0, 0, 1]],
                  [e3[1, 0, 0], e3[1, 1, 1], 2 * e3[1, 0, 1]]])
    kap = np.array([[k3[0, 0], k3[0, 1]], [k3[1, 0], k3[1, 1]]])
    return C, e, kap


def batio3_3d():
    """Tetragonal 4mm BaTiO3 poled along z (FEM-5 data set)."""
    C11, C12, C13, C33, C44 = 2.22e11, 1.08e11, 1.11e11, 1.51e11, 6.10e10
    e15, e31, e33 = 34.2, -0.7, 6.7
    k11, k33 = 1.9479e-8, 4.9583e-10
    C = np.array([[C11, C12, C13, 0, 0, 0],
                  [C12, C11, C13, 0, 0, 0],
                  [C13, C13, C33, 0, 0, 0],
                  [0, 0, 0, C44, 0, 0],
                  [0, 0, 0, 0, C44, 0],
                  [0, 0, 0, 0, 0, C44]])
    e = np.array([[0, 0, 0, 0, e15, 0],
                  [0, 0, 0, e15, 0, 0],
                  [e31, e31, e33, 0, 0, 0]])
    k = np.diag([k11, k11, k33])
    return _C_to_tensor(C), _e_to_tensor(e), k


def batio3_plane_strain(poling="z", rho=6020.0):
    """Plane-strain BaTiO3 with the poling axis inside the model plane.

    poling='z' : poling along the thickness direction (model y)
    poling='x' : poling along the beam axis (length-extensional mode)
    """
    C3, e3, k3 = batio3_3d()
    p = poling.lower()
    if p in ("y", "thickness"):
        # poling along the model y axis (through-thickness electrodes):
        # swap y and z so that the poling axis of the 4mm data becomes y
        Q = np.array([[1.0, 0.0, 0.0],
                      [0.0, 0.0, 1.0],
                      [0.0, 1.0, 0.0]])
    elif p in ("x", "axis"):
        # poling along the beam axis (length-extensional mode): z -> x
        Q = np.array([[0.0, 0.0, 1.0],
                      [0.0, 1.0, 0.0],
                      [-1.0, 0.0, 0.0]])
    else:
        raise ValueError("poling must be 'y' (thickness) or 'x' (axis)")
    C, e, kap = _tensor_to_2d(C3, e3, k3, Q)
    return Material(C=C, e=e, kappa=kap, rho=rho,
                    name=f"BaTiO3 (4mm, poled {poling})")


# --------------------------------------------------------------------------
# Nonlocal (strain-gradient) characteristic-length tensor
# --------------------------------------------------------------------------


def second_moment(domain: str, a1: float, a2: float, theta: float = 0.0):
    """In-plane second-moment tensor M of the averaging domain.

    domain : 'cuboid' | 'rectangle'  -> a_i are half-widths, M_ii = a_i^2/3
             'ellipsoid' | 'ellipse' -> a_i are semi-axes, M_ii = a_i^2/5 (3-D)
                                        or a_i^2/4 (2-D ellipse)
    theta  : rotation of the domain about the out-of-plane axis [rad]
    """
    d = domain.lower()
    if d in ("cuboid", "rectangle", "rect"):
        m = np.array([a1 ** 2 / 3.0, a2 ** 2 / 3.0])
    elif d in ("ellipsoid", "ellipsoid3d", "ellipsoid_3d"):
        m = np.array([a1 ** 2 / 5.0, a2 ** 2 / 5.0])
    elif d in ("ellipse", "ellipse2d", "ellipse_2d"):
        m = np.array([a1 ** 2 / 4.0, a2 ** 2 / 4.0])
    else:
        raise ValueError(f"unknown domain {domain!r}")
    c, s = np.cos(theta), np.sin(theta)
    R = np.array([[c, -s], [s, c]])
    return R @ np.diag(m) @ R.T


# --------------------------------------------------------------------------
# Mesh
# --------------------------------------------------------------------------


@dataclass
class Mesh:
    nx: int
    ny: int
    Lx: float
    Ly: float
    nodes: np.ndarray          # (N, 2)
    elems: np.ndarray          # (ne, 4) node ids, corner order as _CORNERS
    hx: float
    hy: float

    @property
    def nnode(self):
        return self.nodes.shape[0]


def mesh_rect(nx: int, ny: int, Lx: float, Ly: float) -> Mesh:
    xs = np.linspace(0.0, Lx, nx + 1)
    ys = np.linspace(0.0, Ly, ny + 1)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    nodes = np.column_stack([X.ravel(order="F"), Y.ravel(order="F")])
    # node id = i + (nx+1)*j  with i the x index, j the y index
    elems = []
    for j in range(ny):
        for i in range(nx):
            n0 = i + (nx + 1) * j
            n1 = (i + 1) + (nx + 1) * j
            n2 = (i + 1) + (nx + 1) * (j + 1)
            n3 = i + (nx + 1) * (j + 1)
            elems.append([n0, n1, n2, n3])
    return Mesh(nx=nx, ny=ny, Lx=Lx, Ly=Ly, nodes=nodes,
                elems=np.array(elems, dtype=int), hx=Lx / nx, hy=Ly / ny)


# --------------------------------------------------------------------------
# Element matrices
# --------------------------------------------------------------------------


def element_matrices(hx, hy, mat: Material, Mg: np.ndarray,
                     ngauss: int = 4, gradient: bool = True):
    """Return Ke (32x32), Me (32x32), Kuphi (32x4), Kphiphi (4x4)."""
    xg, wg = gauss_legendre(ngauss)
    XI, ETA = np.meshgrid(xg, xg, indexing="ij")
    W = np.outer(wg, wg).ravel()
    xi = XI.ravel()
    eta = ETA.ravel()

    N, Nx, Ny, Nxx, Nxy, Nyy = bfs_scalar(xi, eta, hx, hy)
    Np, Npxi, Npeta = bilinear(xi, eta)

    # strain-displacement matrices.  The element has 32 dof ordered like the
    # global numbering: [u, ux, uy, uxy, v, vx, vy, vxy] at each of the four
    # corners.
    npt = xi.size
    B = np.zeros((npt, 3, 32))
    Bx = np.zeros((npt, 3, 32))
    By = np.zeros((npt, 3, 32))
    Nmat = np.zeros((npt, 2, 32))
    for c in range(4):
        for d in range(4):
            k = 4 * c + d
            cu = 8 * c + d          # u dof column
            cv = 8 * c + 4 + d      # v dof column
            B[:, 0, cu] = Nx[:, k]
            B[:, 2, cu] = Ny[:, k]
            B[:, 1, cv] = Ny[:, k]
            B[:, 2, cv] = Nx[:, k]
            Bx[:, 0, cu] = Nxx[:, k]
            Bx[:, 2, cu] = Nxy[:, k]
            Bx[:, 1, cv] = Nxy[:, k]
            Bx[:, 2, cv] = Nxx[:, k]
            By[:, 0, cu] = Nxy[:, k]
            By[:, 2, cu] = Nyy[:, k]
            By[:, 1, cv] = Nyy[:, k]
            By[:, 2, cv] = Nxy[:, k]
            Nmat[:, 0, cu] = N[:, k]
            Nmat[:, 1, cv] = N[:, k]

    # electric-field operator: E = -Bphi phi, Bphi = grad(Nphi)
    Bp = np.zeros((npt, 2, 4))
    Bp[:, 0, :] = (2.0 / hx) * Npxi
    Bp[:, 1, :] = (2.0 / hy) * Npeta

    C, e, kap = mat.C, mat.e, mat.kappa
    jac = 0.25 * hx * hy  # constant Jacobian on a rectangle

    Ke = np.zeros((32, 32))
    Me = np.zeros((32, 32))
    Kuphi = np.zeros((32, 4))
    Kpp = np.zeros((4, 4))

    for g in range(npt):
        Bg, Bxg, Byg = B[g], Bx[g], By[g]
        Ke += (Bg.T @ C @ Bg) * W[g] * jac
        if gradient:
            Kg = (Mg[0, 0] * (Bxg.T @ C @ Bxg)
                  + Mg[0, 1] * (Bxg.T @ C @ Byg)
                  + Mg[1, 0] * (Byg.T @ C @ Bxg)
                  + Mg[1, 1] * (Byg.T @ C @ Byg))
            Ke += 0.5 * Kg * W[g] * jac
        Me += mat.rho * (Nmat[g].T @ Nmat[g]) * W[g] * jac
        Kuphi += (Bg.T @ e.T @ Bp[g]) * W[g] * jac
        if mat.mu:
            # strain-gradient operator, rows
            #   (eps_xx,x, eps_xx,y, eps_yy,x, eps_yy,y, gamma_xy,x, gamma_xy,y)
            Beta = np.stack([Bxg[0], Byg[0], Bxg[1], Byg[1],
                             Bxg[2], Byg[2]], axis=0)          # 6 x 32
            # shear-free single-constant coupling: D = mu * grad(eps_xx + eps_yy)
            # (rows: D_x, D_y; the shear-gradient columns are identically zero)
            muV = mat.mu * np.array([[1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                                     [0.0, 1.0, 0.0, 1.0, 0.0, 0.0]])
            Kuphi += (Beta.T @ muV.T @ Bp[g]) * W[g] * jac
        Kpp += (Bp[g].T @ kap @ Bp[g]) * W[g] * jac

    return Ke, Me, Kuphi, Kpp


# --------------------------------------------------------------------------
# Global model
# --------------------------------------------------------------------------


@dataclass
class Model:
    mesh: Mesh
    mat: Material
    Mg: np.ndarray
    K: np.ndarray              # mechanical 8N x 8N (cl + gradient)
    M: np.ndarray
    B: np.ndarray              # 8N x Nphi coupling
    Cphi: np.ndarray           # Nphi x Nphi (positive definite)
    phi_dof: np.ndarray        # global phi dof index of each node (or -1)
    mech_dof: np.ndarray       # 8N x 8 mapping node -> dofs
    constrained: np.ndarray    # mechanical dofs fixed (clamped edge)
    electrodes: dict           # {'bottom': node ids, 'top': node ids}
    ndof_mech: int = 0
    ndof_phi: int = 0

    # -- convenience -------------------------------------------------------
    def force_tip(self, Fx=0.0, Fy=0.0, side="right", at_y=None):
        """Consistent nodal load for a point force at an edge node."""
        n = self.mesh
        i = n.nx if side == "right" else 0
        if at_y is None:
            j = n.ny // 2
        else:
            j = int(round(at_y / n.hy))
        node = i + (n.nx + 1) * j
        f = np.zeros(self.ndof_mech)
        d = self.mech_dof[node]
        f[d[0]] += Fx
        f[d[4]] += Fy
        return f

    def edge_traction(self, tx=0.0, ty=0.0, side="right"):
        """Consistent nodal load of a uniform traction on a vertical edge."""
        n = self.mesh
        xg, wg = gauss_legendre(4)
        f = np.zeros(self.ndof_mech)
        iel = n.nx - 1 if side == "right" else 0
        a = 1.0 if side == "right" else -1.0
        corners = (1, 2) if side == "right" else (0, 3)
        for j in range(n.ny):
            base = iel + (n.nx + 1) * j
            nloc = (base, base + 1, base + 1 + (n.nx + 1), base + (n.nx + 1))
            N, *_ = bfs_scalar(np.full(4, a), xg, n.hx, n.hy)
            for g in range(4):
                w = wg[g] * (n.hy / 2.0)
                for c in corners:
                    node = nloc[c]
                    # on the edge the value (d=0) and the tangential
                    # derivative (d=2) basis functions are non-zero;
                    # d=1 and d=3 carry a H1(-a*xi) factor and vanish.
                    for d in (0, 2):
                        k = 4 * c + d
                        f[self.mech_dof[node][0 + d]] += w * N[g, k] * tx
                        f[self.mech_dof[node][4 + d]] += w * N[g, k] * ty
        return f


def assemble(mesh: Mesh, mat: Material, Mg: np.ndarray,
             clamped_edges=("left",), gradient=True, phi_bilinear=True):
    """Assemble the global system."""
    nnode = mesh.nnode
    ndm = 8 * nnode
    ndp = nnode
    K = np.zeros((ndm, ndm))
    M = np.zeros((ndm, ndm))
    B = np.zeros((ndm, ndp))
    Cphi = np.zeros((ndp, ndp))

    mech_dof = -np.ones((nnode, 8), dtype=int)
    for n in range(nnode):
        mech_dof[n] = 8 * n + np.arange(8)

    for el in mesh.elems:
        Ke, Me, Kuphi, Kpp = element_matrices(mesh.hx, mesh.hy, mat, Mg,
                                              gradient=gradient)
        idx = np.concatenate([mech_dof[n] for n in el])
        K[np.ix_(idx, idx)] += Ke
        M[np.ix_(idx, idx)] += Me
        B[np.ix_(idx, el)] += Kuphi
        Cphi[np.ix_(el, el)] += Kpp

    # clamped mechanical dofs (value and derivative dofs on the edge)
    constrained = []
    for edge in clamped_edges:
        for n, xy in enumerate(mesh.nodes):
            if (edge == "left" and abs(xy[0]) < 1e-12) or \
               (edge == "right" and abs(xy[0] - mesh.Lx) < 1e-12) or \
               (edge == "bottom" and abs(xy[1]) < 1e-12) or \
               (edge == "top" and abs(xy[1] - mesh.Ly) < 1e-12):
                constrained.extend(mech_dof[n])
    constrained = np.array(sorted(set(constrained)), dtype=int)

    bottom = [n for n, xy in enumerate(mesh.nodes) if abs(xy[1]) < 1e-12]
    top = [n for n, xy in enumerate(mesh.nodes) if abs(xy[1] - mesh.Ly) < 1e-12]
    left = [n for n, xy in enumerate(mesh.nodes) if abs(xy[0]) < 1e-12]
    right = [n for n, xy in enumerate(mesh.nodes) if abs(xy[0] - mesh.Lx) < 1e-12]

    return Model(mesh=mesh, mat=mat, Mg=Mg, K=K, M=M, B=B, Cphi=Cphi,
                 phi_dof=np.arange(nnode), mech_dof=mech_dof,
                 constrained=constrained,
                 electrodes={"bottom": np.array(bottom), "top": np.array(top),
                             "left": np.array(left), "right": np.array(right)},
                 ndof_mech=ndm, ndof_phi=ndp)


# --------------------------------------------------------------------------
# Reduction: mechanical Dirichlet + potential condensation
# --------------------------------------------------------------------------


def _sub(A, rows, cols):
    return A[np.ix_(rows, cols)]


def reduce(model: Model, circuit="short", pair=("bottom", "top")):
    """Return (Kred, dof_map) for the mechanical system.

    circuit 'short' : both electrodes grounded, internal potential condensed
    circuit 'open'  : bottom electrode grounded, top electrode floating at a
                      single uniform potential (zero net charge)
    """
    free = np.setdiff1d(np.arange(model.ndof_mech), model.constrained)
    mech_idx = free
    Kmm = _sub(model.K, free, free)
    Mmm = _sub(model.M, free, free)
    if not np.any(model.B):                 # purely elastic problem
        if circuit == "open":
            return Kmm, Mmm, mech_idx, (np.zeros(free.size), 1.0)
        return Kmm, Mmm, mech_idx, None
    Bf = _sub(model.B, free, np.arange(model.ndof_phi))

    bot = model.electrodes[pair[0]]
    top = model.electrodes[pair[1]]

    if circuit == "short":
        fixed_phi = np.union1d(bot, top)
        Kred = _condense_phi(Kmm, Bf, model.Cphi, fixed_phi, None)
        return Kred, Mmm, mech_idx, None

    # open circuit
    fixed_phi = bot
    float_phi = top
    Kred, d, beta = _condense_phi(Kmm, Bf, model.Cphi, fixed_phi, float_phi,
                                  return_float=True)
    return Kred, Mmm, mech_idx, (d, beta)


def _condense_phi(Kmm, Bf, C, fixed, floating, return_float=False):
    """Eliminate potential dofs from the indefinite coupled tangent

        [[ Kmm,  Bf ],
         [ Bf^T, -C  ]]                     (FEM-5 sign convention).

    Potential dofs in ``fixed`` are grounded (phi = 0).  If ``floating`` is
    given, those dofs share a single unknown electrode voltage V with zero net
    charge.  Returns

        K* = Kmm + Bf_i C_ii^{-1} Bf_i^T + (d g)(d g)^T / (g^T C1 g)

    with  d = Bf_f - Bf_i C_ii^{-1} C_if,  C1 = C_ff - C_fi C_ii^{-1} C_if.
    """
    m = C.shape[0]
    allp = np.arange(m)
    fixed = np.asarray(fixed, int) if len(fixed) else np.array([], int)
    float_idx = (np.asarray(floating, int) if floating is not None
                 else np.array([], int))
    interior = np.setdiff1d(np.setdiff1d(allp, fixed), float_idx)

    n = Kmm.shape[0]
    if interior.size:
        Cii = C[np.ix_(interior, interior)]
        cf = cho_factor(Cii, lower=True)
        Bfi = Bf[:, interior]
        Kmm = Kmm + Bfi @ cho_solve(cf, Bfi.T)
        if float_idx.size:
            Cif = C[np.ix_(interior, float_idx)]
            X = cho_solve(cf, Cif)                       # C_ii^{-1} C_if
            d = Bf[:, float_idx] - Bfi @ X
            C1 = C[np.ix_(float_idx, float_idx)] - \
                C[np.ix_(float_idx, interior)] @ X
        else:
            d = np.zeros((n, 0))
            C1 = np.zeros((0, 0))
    else:
        d = Bf[:, float_idx]
        C1 = C[np.ix_(float_idx, float_idx)]

    if float_idx.size == 0:
        return (Kmm, None, None) if return_float else Kmm

    g = np.ones(float_idx.size)
    dg = d @ g
    beta = float(g @ C1 @ g)
    if beta <= 0.0:
        raise RuntimeError("floating-electrode capacitance must be positive")
    Kmm = Kmm + np.outer(dg, dg) / beta
    if return_float:
        return Kmm, dg, beta
    return Kmm


# --------------------------------------------------------------------------
# Eigen-solver with diagonal scaling (FEM-1 corrected formulation)
# --------------------------------------------------------------------------


def modes(K, M, nmodes=6, dense_limit=2600):
    """Solve K x = w^2 M x with diagonal scaling S = diag(1/sqrt(K_ii))."""
    n = K.shape[0]
    d = np.sqrt(np.abs(np.diag(K)))
    S = 1.0 / d
    Ks = K * S[:, None] * S[None, :]
    Ms = M * S[:, None] * S[None, :]
    if n <= dense_limit:
        w2, y = eigh(Ks, Ms)
    else:
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import eigsh
        w2, y = eigsh(csr_matrix(Ks), k=nmodes, M=csr_matrix(Ms), sigma=0.0,
                      which="LM")
        order = np.argsort(w2)
        w2, y = w2[order], y[:, order]
    nmodes = min(nmodes, n)
    w2 = w2[:nmodes]
    y = y[:, :nmodes]
    x = S[:, None] * y
    # mass-normalise
    for k in range(x.shape[1]):
        x[:, k] /= np.sqrt(x[:, k] @ M @ x[:, k])
    return np.sqrt(np.maximum(w2, 0.0)), x


# --------------------------------------------------------------------------
# Memory: fractional Kelvin-Voigt, L1 + Newmark
# --------------------------------------------------------------------------


def l1_weights(nsteps, alpha):
    """L1 weights b_j = (j+1)^(1-a) - j^(1-a), j = 0..nsteps.

    Only b_0 is used for the newest increment, and only j >= 1 for the
    history.  At alpha = 1 the closed form gives b_0 = 1 - 0^0 = 0 because
    numpy evaluates 0**0 as 1, so b_0 is set explicitly here: the newest
    weight of the L1 stencil is 1 for every alpha, and the transient already
    applies it implicitly (it never reads b[0]).
    """
    k = np.arange(nsteps + 1)
    b = (k + 1.0) ** (1.0 - alpha) - k ** (1.0 - alpha)
    b[0] = 1.0
    return b


def transient(K, M, Kd, f_hat, alpha, tau, dt, nsteps, nmodes=12,
              beta=0.25, gam=0.5, x0=None, v0=None):
    """Time integration of

        M x'' + K x + tau^alpha Kd D^alpha x = f(t)

    in a mass-normalised modal basis of (K, M).  Returns t, x, y, v, a.

    Kd is the matrix receiving the memory (K for 'full Keff', or K_uu for the
    mechanical-only variant).  When Kd == K the system is proportional and the
    modal equations decouple; otherwise the projected memory matrix is dense.
    """
    omega, Phi = modes(K, M, nmodes=nmodes)
    w2 = omega ** 2
    r = Phi.shape[1]
    Kd_red = Phi.T @ Kd @ Phi
    c = tau ** alpha / (gamma(2.0 - alpha) * dt ** alpha)

    f_time = f_hat if callable(f_hat) else None
    p0 = None if f_time is not None else Phi.T @ np.asarray(f_hat, float)

    y = np.zeros((r, nsteps + 1))
    v = np.zeros((r, nsteps + 1))
    a = np.zeros((r, nsteps + 1))
    if x0 is not None:
        y[:, 0] = Phi.T @ M @ x0
    if v0 is not None:
        v[:, 0] = Phi.T @ M @ v0
    # initial acceleration: M a0 = f0 - K x0 (memory term vanishes at t=0+)
    p = p0 if p0 is not None else Phi.T @ f_time(0.0)
    a[:, 0] = p - w2 * y[:, 0]

    Om2 = np.diag(w2)
    A = np.eye(r) + beta * dt ** 2 * (Om2 + c * Kd_red)
    cf = cho_factor(A, lower=True)

    hist = np.zeros((r, nsteps + 1))        # Delta y at each step index
    b = l1_weights(nsteps, alpha)

    x = np.zeros((Phi.shape[0], nsteps + 1))
    x[:, 0] = Phi @ y[:, 0]
    for n in range(1, nsteps + 1):
        if f_time is not None:
            p = Phi.T @ f_time(n * dt)
        yhat = y[:, n - 1] + dt * v[:, n - 1] + dt ** 2 * (0.5 - beta) * a[:, n - 1]
        # S_n = sum_{k=1}^{n-1} b_k (y_{n-k} - y_{n-k-1})
        S = np.zeros(r)
        if n >= 2:
            S = hist[:, 1:n] @ b[1:n][::-1]
        rhs = p - (Om2 + c * Kd_red) @ yhat + c * Kd_red @ (y[:, n - 1] - S)
        an = cho_solve(cf, rhs)
        yn = yhat + beta * dt ** 2 * an
        vn = v[:, n - 1] + dt * ((1 - gam) * a[:, n - 1] + gam * an)
        y[:, n] = yn
        v[:, n] = vn
        a[:, n] = an
        hist[:, n] = yn - y[:, n - 1]
        x[:, n] = Phi @ yn
    return np.arange(nsteps + 1) * dt, x, y, v, a


def damping_ratio(omega, tau, alpha):
    """Small-damping modal ratio of fractional Kelvin-Voigt.

    zeta = (1/2) (omega tau)^alpha sin(pi alpha / 2)
    (exact in the limit of small damping; alpha = 1 gives zeta = omega tau / 2).
    """
    return 0.5 * (omega * tau) ** alpha * np.sin(0.5 * np.pi * alpha)


def complex_frequency(omega0, tau, alpha, iters=200, s0=None):
    """Fundamental pole of  s^2 + omega0^2 (1 + (tau s)^alpha) = 0.

    Damped Newton iteration on the principal branch (as in the MATLAB
    helper cplx_root, but with a convergence check on the residual).

    ``s0`` warm-starts the iteration.  The pole equation has several roots and
    for alpha < 1 and omega*tau >~ 4 the plain iteration can jump to a
    different one (it was observed to land on a root with a positive real
    part); sweeping omega*tau with the previous root as s0 keeps the branch
    continuous, which is what a damping map needs.
    """
    s = omega0 * (-0.05 + 1.0j) if s0 is None else complex(s0)
    for _ in range(iters):
        fv = s ** 2 + omega0 ** 2 * (1.0 + (tau * s) ** alpha)
        dfv = 2.0 * s + omega0 ** 2 * alpha * tau ** alpha * s ** (alpha - 1.0)
        ds = fv / dfv
        s -= ds
        if abs(ds) < 1e-14 * abs(s):
            break
    return s
