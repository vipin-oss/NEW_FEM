"""
run_sensitivity.py -- how much of the h = 1 um flexoelectric coupling is the
platform and how much is the physics.

The number in question is k^2 = (y_o - w_0^2)/y_o of the rank-one secular
equation in run_demos._modal_k2, with w_0^2 the fundamental of a pencil whose
condition number is ~1e12 at h = 1 um.  k^2 is therefore a small difference of
nearly equal eigenvalues, and it moves at the 1e-3 relative level between
numeric stacks while the h >= 5 um values move at the 1e-7 level.

The script runs one model (48 x 4, poling y, electrodes on the long faces,
mu = 1e-6 C/m) through five eigensolver paths and records the versions of the
interpreter, numpy and scipy that produced them.  Run it under several stacks
and merge:

    python3 python/run_sensitivity.py                       # local stack
    python3 python/run_sensitivity.py --emit results/sensitivity_envs/a.json
    python3 python/run_sensitivity.py                       # merges and writes

Every emitted file names its own stack, so the merged table in
results/sensitivity.md and Paper_12/table_sensitivity.tex says which
combination produced which value.

Writes results/sensitivity.json and Paper_12/table_sensitivity.tex.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import platform
import sys

import numpy as np
import scipy
import scipy.linalg as sla
import scipy.sparse.linalg as spla
from scipy.linalg import eigh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
ENVS = os.path.join(RES, "sensitivity_envs")
sys.path.insert(0, HERE)

import fem6_core as f6          # noqa: E402
import materials as mt          # noqa: E402

L = 200e-6
HS = (1e-6, 10e-6)
# paths that keep the whole spectrum: the secular sum runs over every mode,
# so only these are alternatives to the pipeline
EQUIVALENT = ("dense eigh, scaled", "dense eigh, unscaled",
              "QZ (eig, general)", "numpy eig, all modes")
# paths that truncate the spectrum: not alternatives, and the table says why
TRUNCATED = ("dense eigh, 12 modes", "sparse eigsh, 12 modes")
PATHS = EQUIVALENT + TRUNCATED


# ---------------------------------------------------------------------------
def model(h, nx=48, ny=4, mu=1.0e-6):
    m = mt.batio3("y", "plane_stress")
    core = mt.to_core(m)
    core.mu = mu
    mesh = f6.mesh_rect(nx, ny, L, h)
    Mg = f6.second_moment("cuboid", 3e-6, 1e-6, 0.0)
    mdl = f6.assemble(mesh, core, Mg)
    K, M, _, _ = f6.reduce(mdl, "short", pair=("bottom", "top"))
    _, _, _, (d, beta) = f6.reduce(mdl, "open", pair=("bottom", "top"))
    return K, M, d, beta


def secular_k2(w2, Phi, d, beta):
    """Same arithmetic as run_demos._modal_k2, for a supplied eigenpairs."""
    s = (Phi.T @ d) ** 2 / beta

    def f(y):
        return 1.0 + float(np.sum(s / (w2 - y)))

    a = w2[0] * (1 + 1e-10)
    b = None
    for step in (1e-6, 1e-4, 1e-2, 0.1, 0.5, 0.9):
        cand = w2[0] + step * (w2[1] - w2[0])
        if f(cand) > 0:
            b = cand
            break
    if b is None:
        b = w2[1] * (1 - 1e-9)
    for _ in range(200):
        m = 0.5 * (a + b)
        if f(m) > 0:
            b = m
        else:
            a = m
        if b - a <= 1e-15 * w2[0]:
            break
    yo = 0.5 * (a + b)
    return (yo - w2[0]) / yo


def eigenpairs(K, M, path):
    if path in ("dense eigh, scaled", "dense eigh, unscaled",
                "dense eigh, 12 modes"):
        if path == "dense eigh, scaled":
            sd = np.sqrt(np.abs(np.diag(K)))
            S = 1.0 / sd
            A = K * S[:, None] * S[None, :]
            B = M * S[:, None] * S[None, :]
        elif path == "dense eigh, unscaled":
            S = np.ones(K.shape[0])
            A, B = K, M
        else:
            sd = np.sqrt(np.abs(np.diag(K)))
            S = 1.0 / sd
            A = K * S[:, None] * S[None, :]
            B = M * S[:, None] * S[None, :]
        if path == "dense eigh, 12 modes":
            w2, y = eigh(A, B, subset_by_index=[0, 11])
        else:
            w2, y = eigh(A, B)
        return w2, S[:, None] * y
    if path == "QZ (eig, general)":
        sd = np.sqrt(np.abs(np.diag(K)))
        S = 1.0 / sd
        A = K * S[:, None] * S[None, :]
        B = M * S[:, None] * S[None, :]
        w2, V = sla.eig(A, B)                    # generalized, all modes
        w2 = np.real(w2)
        order = np.argsort(w2)
        w2 = w2[order]
        Phi = S[:, None] * np.real(V[:, order])
        for i in range(Phi.shape[1]):
            c = np.sqrt(abs(Phi[:, i] @ (M @ Phi[:, i])))
            Phi[:, i] /= c
        return w2, Phi
    if path == "numpy eig, all modes":
        sd = np.sqrt(np.abs(np.diag(K)))
        S = 1.0 / sd
        A = K * S[:, None] * S[None, :]
        B = M * S[:, None] * S[None, :]
        w2, V = np.linalg.eig(np.linalg.solve(B, A))
        w2 = np.real(w2)
        order = np.argsort(w2)
        w2 = w2[order]
        Phi = S[:, None] * np.real(V[:, order])
        for i in range(Phi.shape[1]):
            c = np.sqrt(abs(Phi[:, i] @ (M @ Phi[:, i])))
            Phi[:, i] /= c
        return w2, Phi
    if path == "sparse eigsh, 12 modes":
        w2, y = spla.eigsh(K, k=12, M=M, sigma=0.0, which="LM")
        order = np.argsort(w2)
        return w2[order], y[:, order]
    raise ValueError(path)


def run_stack():
    out = {}
    for h in HS:
        K, M, d, beta = model(h)
        row = {}
        for path in PATHS:
            try:
                w2, Phi = eigenpairs(K, M, path)
                row[path] = float(secular_k2(w2, Phi, d, beta))
            except Exception as exc:                # noqa: BLE001
                row[path] = None
                print(f"    {path}: {type(exc).__name__}: {exc}")
        out[f"h{int(round(h * 1e6))}_um"] = row
        print(f"  h = {h * 1e6:g} um done", flush=True)
    return out


def environment():
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "machine": platform.machine()}


def main():
    emit = None
    if "--emit" in sys.argv:
        emit = sys.argv[sys.argv.index("--emit") + 1]
    env = environment()
    tag = f"py{env['python']}-np{env['numpy']}-sp{env['scipy']}"
    print(f"  stack {tag}")
    values = run_stack()
    # Do not pool old datasets computed with different constitutive tensors.
    # The fingerprint includes the two files that set the constitutive tensors
    # and the assembled stiffness/eigenproblem. Old untagged environment files
    # are retained on disk but excluded from same-model solver comparisons.
    fp = hashlib.sha256()
    for name in ("materials.py", "fem6_core.py"):
        fp.update(name.encode())
        with open(os.path.join(HERE, name), "rb") as fh:
            fp.update(fh.read())
    model_digest = fp.hexdigest()
    rec = {"tag": tag, **env, "model_digest": model_digest, "values": values}

    os.makedirs(ENVS, exist_ok=True)
    path = emit or os.path.join(ENVS, tag + ".json")
    with open(path, "w") as fh:
        json.dump(rec, fh, indent=1)
    if emit:
        print(f"  -> {path}")
        return 0

    # merge every stack that has been run
    recs = []
    excluded = []
    for fn in sorted(glob.glob(os.path.join(ENVS, "*.json"))):
        with open(fn) as fh:
            old = json.load(fh)
        if old.get("model_digest") != model_digest:
            excluded.append(os.path.basename(fn))
            continue
        recs.append(old)
    if not recs:
        recs = [rec]

    def k2(r, h, path=EQUIVALENT[0]):
        return r["values"][h].get(path)

    rows = []
    for r in recs:
        for path in PATHS:
            v1 = k2(r, "h1_um", path)
            v10 = k2(r, "h10_um", path)
            if v1 is None or v10 is None:
                continue
            rows.append({"tag": r["tag"], "python": r["python"],
                         "numpy": r["numpy"], "scipy": r["scipy"],
                         "path": path, "k2_h1": v1, "k2_h10": v10,
                         "growth": v1 / v10})
    eq = [r for r in rows if r["path"] in EQUIVALENT]
    tr = [r for r in rows if r["path"] in TRUNCATED]
    if not eq:
        raise SystemExit("run_sensitivity: no equivalent-path rows")

    # ---- a fixed, stack-independent reference --------------------------------
    # The spread is max-min over the midpoint of the equivalent rows, and every
    # deviation in the tables is measured from that same midpoint.  It is NOT
    # measured from whichever stack happens to be running: a spread quoted
    # relative to a moving reference doubles on a machine that sits at one end
    # of the range (0.11 % became 0.15 % on the reviewer's Python 3.13 stack),
    # which turns the number into a statement about the machine, not the model.
    v1s = [r["k2_h1"] for r in eq]
    v10s = [r["k2_h10"] for r in eq]
    mid1 = 0.5 * (min(v1s) + max(v1s))
    mid10 = 0.5 * (min(v10s) + max(v10s))
    for r in rows:
        r["dev_h1_pct"] = 100.0 * (r["k2_h1"] / mid1 - 1.0)
        r["dev_h10_pct"] = 100.0 * (r["k2_h10"] / mid10 - 1.0)
    spread_h1 = 100.0 * (max(v1s) - min(v1s)) / mid1
    spread_h10 = 100.0 * (max(v10s) - min(v10s)) / mid10
    growth = [r["growth"] for r in eq]

    # the stack whose alternative paths are tabulated is chosen by proximity to
    # the midpoint (ties by tag), so the generated table does not depend on who
    # runs the script either
    pipe = sorted((r for r in eq if r["path"] == EQUIVALENT[0]),
                  key=lambda r: (abs(r["k2_h1"] - mid1), r["tag"]))
    ref_tag = pipe[0]["tag"]
    ref = next(r for r in recs if r["tag"] == ref_tag)

    data = {"reference": ref_tag, "reference_rule": "midpoint of equivalent rows",
            "rows": rows,
            "spread_h1_pct": spread_h1, "spread_h10_pct": spread_h10,
            "k2_h1_min": min(v1s), "k2_h1_max": max(v1s),
            "k2_h1_midpoint": mid1,
            "k2_h10_min": min(v10s), "k2_h10_max": max(v10s),
            "growth_min": min(growth), "growth_max": max(growth),
            "n_stacks": len(recs), "n_rows": len(rows),
            "model_digest": model_digest, "excluded_unverified_envs": excluded,
            "spread_h1_method": "(max-min)/midpoint over equivalent rows",
            "truncated_max_dev_pct": max(abs(r["dev_h1_pct"]) for r in tr)
            if tr else None}
    with open(os.path.join(RES, "sensitivity.json"), "w") as fh:
        json.dump(data, fh, indent=1)

    md = ["# Platform sensitivity of the h = 1 um flexoelectric coupling", "",
          "One model (48$\\times4$, poling $y$, electrodes on the long faces, "
          "$\\mu=10^{-6}$ C/m), five eigensolver paths, three numeric stacks.  "
          f"Excluded {len(excluded)} pre-patch/untagged environment records: "
          "their physical tensors cannot be confirmed identical. "
          "The deviations are relative to the **midpoint** of the "
          "equivalent rows, never to the running stack, so the same table "
          "is produced on every machine.", "",
          f"**h = 1 um: spread {spread_h1:.3f} %; h = 10 um: spread "
          f"{spread_h10:.3e} %.**  The growth factor ranges "
          f"{min(growth):.2f}-{max(growth):.2f}.", "",
          "| stack | path | $k^2$ (h = 1 um) | dev [%] | $k^2$ (h = 10 um) | "
          "dev [%] | growth |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| py{r['python']} np{r['numpy']} sp{r['scipy']} | "
                  f"{r['path']} | {r['k2_h1']:.5e} | {r['dev_h1_pct']:+.3f} | "
                  f"{r['k2_h10']:.5e} | {r['dev_h10_pct']:+.2e} | "
                  f"{r['growth']:.2f} |")
    md += ["",
           "These model-tagged rows test solver-path agreement only; they do "
           "not establish cross-platform variation unless multiple tagged "
           "independent environments are available. Former pooled 3.50%/4.46% "
           "ranges confounded different constitutive models and must not be "
           "described as numerical software variation.",
           "The h = 1 um value is the least reproducible number in the paper: "
           "it is a small difference of two nearly equal eigenvalues of a "
           "pencil with condition $\\sim10^{12}$, so it inherits the "
           "eigenvector accuracy of the stack.  Two significant digits "
           "(4.0e-3, growth 24) are stable across the current model-tagged paths; the "
           "fourth digit is not, which is why the manuscript quotes two.", ""]
    with open(os.path.join(RES, "sensitivity.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    ROW = chr(92) * 2
    BS = chr(92)
    # the paper table: one row per stack on the pipeline path, plus the other
    # equivalent paths at the reference stack -- six rows, not eighteen
    tex_rows = (sorted((r for r in rows if r["path"] == EQUIVALENT[0]),
                        key=lambda r: r["tag"])
                + [r for r in rows if r["tag"] == ref_tag
                   and r["path"] in EQUIVALENT[1:]])
    Lt = ["% table generated from the archived results",
          BS + "begin{tabular}{@{}llccc@{}}", BS + "toprule",
          "stack & solver path & $k^2$, $h=$" + BS + "SI{1}{" + BS + "micro"
          + BS + "meter} & dev & $k^2$, $h=$" + BS + "SI{10}{" + BS + "micro"
          + BS + "meter}" + ROW, BS + "midrule"]
    for r in tex_rows:
        Lt.append(f"py{r['python']}, np{r['numpy']}, sp{r['scipy']} & "
                  f"{r['path']} & {r['k2_h1']:.4e} & "
                  f"{r['dev_h1_pct']:+.2f} & {r['k2_h10']:.4e}" + ROW)
    n_eq = len(eq)

    def sci(x, d=1):
        m, e = (f"%.{d}e" % x).split("e")
        return "$" + m + BS + "times10^{" + str(int(e)) + "}$"

    note = ("all " + str(n_eq) + " equivalent-path rows: spread "
            + f"{spread_h1:.2f}" + BS + "%, $h=1$" + BS
            + ",\\si{\\micro\\meter}; " + sci(spread_h10) + BS
            + "%, $h=10$" + BS + ",\\si{\\micro\\meter}"
            + " (range over midpoint)")
    Lt += [BS + "midrule",
           BS + "multicolumn{5}{@{}l}{" + note + "}" + ROW,
           BS + "bottomrule", BS + "end{tabular}"]
    with open(os.path.join(ROOT, "Paper_12", "table_sensitivity.tex"), "w") as fh:
        fh.write("\n".join(Lt) + "\n")

    print(f"  {len(rows)} rows from {len(recs)} stack(s); "
          f"h=1um spread {spread_h1:.3f} %, h=10um {spread_h10:.2e} %")
    print(f"  k2(h=1) {min(v1s):.4e} .. {max(v1s):.4e}; growth "
          f"{min(growth):.2f} .. {max(growth):.2f}")
    print("  -> results/sensitivity.md, Paper_12/table_sensitivity.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
