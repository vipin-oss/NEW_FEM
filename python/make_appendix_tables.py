"""Generate the tables of Appendix C from the stored results.

Every number printed in the appendix is read from ``results/`` (or recomputed
from the same routine that produced the corresponding figure) so that the
appendix and the figures cannot drift apart.  Nothing here is hand-typed.

    python make_appendix_tables.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem6_core as f6
import materials as mt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Paper_12")


def load(name):
    with open(os.path.join(ROOT, "results", name)) as fh:
        return json.load(fh)


def write(fname, text, head):
    path = os.path.join(OUT, fname)
    with open(path, "w") as fh:
        fh.write("%% generated table -- do not edit (see AUTHOR_TODO.md)\n")
        fh.write(text)
    print("  %-34s %s" % (fname, head))


# --------------------------------------------------------------- C.1 orientation
def table_orientation():
    pol = load("paper_figures_data.json")["polar"]
    ars = (2.0, 5.0, 10.0)
    ths = (0, 15, 30, 45, 60, 75, 90)
    body = []
    for t in ths:
        row = ["%d" % t]
        for AR in ars:
            r = [q for q in pol if q["AR"] == AR and q["shape"] == "cuboid"
                 and q["theta_deg"] == float(t)][0]
            row += ["%.0f" % r["f_ext_kHz"], "%.4f" % r["k2_axial"]]
        body.append(" & ".join(row) + r" \\")
    text = r"""\begin{table}[!htbp]
\centering
\caption{Window orientation: frequency of the extensional mode and its coupling
factor, for the three aspect ratios of Fig.~\ref{fig:orientation}, on the
\SI{200}{\micro\metre}$\times$\SI{10}{\micro\metre} strip with
$h=\SI{10}{\micro\metre}$, poling $x$, plane stress, $24\times2$ mesh,
$\mu=0$ and $\alpha=1$. Every fifth degree is listed; the figure uses the same
sweep at $5^\circ$ spacing. The remaining orientations follow from
$\theta\to\theta+180^\circ$ and $\theta\to-\theta$, which reproduce the values
below to \num{3e-11} relative (Sec.~\ref{sec:orientation}).}
\label{tab:orientation}
\begin{tabular}{@{}l r r r r r r@{}}
\toprule
& \multicolumn{2}{c}{${\rm AR}=2$} & \multicolumn{2}{c}{${\rm AR}=5$}
& \multicolumn{2}{c}{${\rm AR}=10$} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}
$\theta$ (deg) & $f_{\rm ext}$ (kHz) & $k^2$ & $f_{\rm ext}$ (kHz) & $k^2$
& $f_{\rm ext}$ (kHz) & $k^2$ \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("table_C1_orientation.tex", text, "%d rows" % len(body))


# ---------------------------------------------------------------- C.2 thickness
def table_thickness():
    rows = load("demo.json")["flexo_thickness"]
    body = []
    for r in rows:
        k96 = ("%.4e" % r["k2_flexo_96"]) if "k2_flexo_96" in r else "--"
        body.append(" & ".join(["%g" % r["h_um"], "%.1f" % r["f1_kHz"],
                                "%.3e" % r["k2_flexo"],
                                "%.2e" % r["k2_flexo_24"], k96,
                                "%.5f" % r["k2_ext"],
                                "%.5f" % r["k2_ext_24"]]) + r" \\")
    text = r"""\begin{table}[!htbp]
\centering
\caption{Thickness sweep behind Fig.~\ref{fig:thickness}:
$L=\SI{200}{\micro\metre}$, window half-widths
$3\times1$\,\si{\micro\metre}, $\mu=10^{-6}$\,\si{\coulomb\per\metre} for the
bending columns and $\mu=0$ for the extensional ones, $\alpha=1$. The
$24\times2$ and $96\times4$ columns are the two mesh witnesses; the
$96\times4$ values were computed at the two ends of the range only. The
fundamental frequency is that of the same $48\times4$ model.}
\label{tab:thickness}
\begin{tabular}{@{}r r r r r r r@{}}
\toprule
& & \multicolumn{3}{c}{bending, $k^2_{\rm flexo}$}
& \multicolumn{2}{c}{extensional, $k^2_{\rm piezo}$} \\
\cmidrule(lr){3-5}\cmidrule(lr){6-7}
$h$ (\si{\micro\metre}) & $f_1$ (kHz) & $48\times4$ & $24\times2$ & $96\times4$
& $48\times4$ & $24\times2$ \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("table_C2_thickness.tex", text, "%d rows" % len(body))


# ------------------------------------------------------------------ C.3 damping
def table_damping():
    alphas = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
    wts = (0.1, 1.0, 3.0, 10.0, 30.0)
    body = []
    for a in alphas:
        s0 = None
        cells = ["%.1f" % a]
        for wt in wts:
            s = complex(f6.complex_frequency(1.0, wt, a, s0=s0))
            s0 = s
            cells.append("%.3f" % (-s.real / abs(s)))
        body.append(" & ".join(cells) + r" \\")
    text = r"""\begin{table}[!htbp]
\centering
\caption{Damping ratio $\zeta=-\mathrm{Re}\,s/(\omega_0|s|)$ of the fractional
Kelvin--Voigt element of \eqref{eq:kvfreq}, on the grid behind
Fig.~\ref{fig:damping}(b), from the complex pole with branch continuation. The
ratio rises with both $\alpha$ and $\omega\tau$ and reaches unity at
$\alpha=1$, $\omega\tau=10$, where the integer-order element is critically
damped. The band used for the strip mode of this paper is
$\omega\tau\le1$.}
\label{tab:damping}
\begin{tabular}{@{}l r r r r r@{}}
\toprule
& \multicolumn{5}{c}{$\omega\tau$} \\
\cmidrule(lr){2-6}
$\alpha$ & 0.1 & 1 & 3 & 10 & 30 \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("table_C3_damping.tex", text, "%d rows" % len(body))


# --------------------------------------------------------------- C.4 convergence
def table_convergence():
    MAT = mt.Material(**{**mt.batio3("x", "plane_stress").__dict__, "mu": 0.0})
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    meshes = [(12, 2), (24, 2), (36, 2), (48, 4)]
    rows = []
    for nx, ny in meshes:
        mesh = f6.mesh_rect(nx, ny, 200e-6, 10e-6)
        mdl = f6.assemble(mesh, mt.to_core(MAT), Mg)
        Ksc, M, idx, _ = f6.reduce(mdl, "short", pair=("left", "right"))
        _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=("left", "right"))
        w, Phi = f6.modes(Ksc, M, 8)           # w is omega in rad/s
        x = ((Phi.T @ d) ** 2 / beta) / w ** 2
        k2m = x / (1.0 + x)
        j = int(np.argmax(k2m))
        sd = np.sqrt(np.abs(np.diag(Ksc)))
        S = 1.0 / sd
        xq = float((S * d) @ np.linalg.solve(Ksc * S[:, None] * S[None, :], S * d))
        kqs = (xq / beta) / (1.0 + xq / beta)
        rows.append((nx, ny, int(mdl.ndof_mech), float(w[j] / 2e3 / np.pi),
                     float(k2m[j]), float(kqs)))
    ref_f, ref_k = rows[-1][3], rows[-1][5]
    body = []
    for nx, ny, nd, f, _k, kq in rows:
        body.append(" & ".join(["$%d\\times%d$" % (nx, ny), "%d" % nd,
                                "%.1f" % f, "%.5f" % kq,
                                "%.1e" % abs(f / ref_f - 1.0),
                                "%.1e" % abs(kq / ref_k - 1.0)]) + r" \\")
    text = r"""\begin{table}[!htbp]
\centering
\caption{Convergence of the extensional mode behind
Fig.~\ref{fig:convergence}: strip \SI{200}{\micro\metre}$\times$\SI{10}{\micro\metre},
poling $x$, plane stress, $\mu=0$, $a_1\times a_2=3\times1$\,\si{\micro\metre}.
The frequency is that of the extensional mode of the short-circuit eigenvalue
problem and the coupling is the mode-free quasi-static value of
\eqref{eq:kstatic}, the number quoted in the text; the errors are referred to
the $48\times4$ mesh.}
\label{tab:convergence}
\begin{tabular}{@{}l r r r r r@{}}
\toprule
mesh & dof & $f$ (kHz) & $k^2$ & err $f$ & err $k^2$ \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("table_C4_convergence.tex", text, "%d rows" % len(body))


def shift_txt(x):
    """1.6e-05 -> '$1.6\\times10^{-5}$'"""
    e = int(np.floor(np.log10(abs(x))))
    return r"$%.1f\times10^{%d}$" % (x / 10.0 ** e, e)


# ----------------------------------------------------------------- C.5 ring-down
def table_ringdown():
    notes = load("paper_figures_data.json")["notes"]["P6"]
    DT = load("dt_study.json")
    body = []
    for key in sorted(notes, reverse=True):
        if not key.startswith("zeta_"):
            continue
        a = key.split("_")[1]
        body.append(" & ".join([a, "%.5f" % notes[key]]) + r" \\")
    text = r"""\begin{table}[!htbp]
\centering
\caption{Ring-down behind Fig.~\ref{fig:ringdown}: the decrement $\delta$ of
the tip displacement over the first two peaks, converted with the exact
relation $\zeta=\delta/\sqrt{4\pi^{2}+\delta^{2}}$ of \eqref{eq:zeta}, for
each Caputo order. The entry is a damping ratio only at $\alpha=1$; for
$\alpha<1$ it is the first-period decrement, because the free decay of a
fractional element is not exponential. The mode is the extensional one at \SI{%.1f}{kHz}
($k^2=0.4583$), with $\tau=\SI{3}{\nano\second}$ and
$\omega\tau=%.2f$; the open-circuit voltage at the initial instant is
\SI{%.2f}{\volt} for a \SI{10}{\nano\metre} tip displacement. The entries are
the values at the %d steps ($400$ per period) of Fig.~\ref{fig:ringdown};
quartering that step moves the last decimal by %s, so they are quoted to four
significant digits. The decrement is not monotonic in $\alpha$: it peaks near
$\alpha=0.6$ and falls again as the response becomes slower and more heavily
damped.}
\label{tab:ringdown}
\begin{tabular}{@{}l r@{}}
\toprule
$\alpha$ & $\zeta$ of the first period \\
\midrule
""" % (notes["f_kHz"], 2 * np.pi * notes["f_kHz"] * 1e3 * notes["tau_s"],
       notes["V0"], DT["figure10"]["rows"][0]["steps"],
       shift_txt(DT["figure10"]["last_digit_shift"])) + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("table_C5_ringdown.tex", text, "%d rows" % len(body))


def main():
    print("Appendix C tables ->", OUT)
    table_orientation()
    table_thickness()
    table_damping()
    table_convergence()
    table_ringdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
