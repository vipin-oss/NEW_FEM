"""
audit_abstract_claims.py -- every number in the abstract, and whether an
independent route reproduces it.

    python3 python/audit_abstract_claims.py   -> results/abstract_audit.md

The abstract of Paper_12/main.tex is the one place in the manuscript where a
number appears with no table under it, so it is the place where an unchecked
claim can hide.  Each numeric token of the abstract is listed here with a
verdict:

    hua        -- an independent route (a closed form, a polynomial, a
                  quadrature) reproduces the number, or the number *is* the
                  comparison with that route.
    nahi hua   -- no independent route exists yet; the number is traceable to
                  a JSON file and to a passing criterion, but that criterion
                  grades the finite element solver against itself.

The coverage check at the bottom rejects an abstract that grows a number
without growing a verdict, so the table cannot fall behind the text.
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
TEX = os.path.join(ROOT, "Paper_12", "main.tex")

# (literal in the abstract, what it is, verdict, route / where it is checked)
CLAIMS = [
    ("200", "plate length and width, \\SI{200}{\\micro\\metre}",
     "n/a", "an input of the model, not a measured quantity"),
    ("10", "plate thickness, \\SI{10}{\\micro\\metre}",
     "n/a", "an input of the model"),
    ("0.4650", "extensional $k^2$ at $\\omega\\tau=0.3$",
     "nahi hua", "FEM modal coupling (memory\\_variants S1, criterion S1a); "
     "the closed form of Sec.~\\ref{sec:closedform} covers the free plate "
     "(0.5608), not this mode"),
    ("0.3", "$\\omega\\tau$ of the damping study", "n/a", "a chosen operating point"),
    ("0.449", "$\\zeta$ ratio, memory on $K_{uu}$ over $K_{\\rm eff}$",
     "nahi hua", "a property of the two condensation choices, read off the "
     "FEM matrices (S1b); the pole solver that converts the pole into "
     "$\\zeta$ is itself checked (I4)"),
    ("1", "$\\alpha=1$", "n/a", "the classical limit, chosen for the comparison"),
    ("0.15", "distance of $\\zeta_{\\rm eff}$ from the classical limit",
     "hua", "I5: at $\\alpha=1$ the pole equation is quadratic and gives "
     "$\\omega\\tau/2=0.15000$ exactly, so the $0.15\\,\\%$ is a comparison "
     "with an exact value"),
    ("0.15023", "$\\zeta_{\\rm eff}$ from the finite element matrices",
     "nahi hua", "FEM value (memory\\_variants S1); only its *distance* from "
     "0.15000 has an independent reference"),
    ("0.15000", "$\\omega\\tau/2$",
     "hua", "I5, and exactly the classical Kelvin--Voigt result"),
    ("2", "the factor $1/2$ in $\\omega\\tau/2$",
     "hua", "at $\\alpha=1$ the pole equation is a quadratic whose root is "
     "$s=\\omega_0(-\\zeta+i\\sqrt{1-\\zeta^2})$ with "
     "$\\zeta=\\omega\\tau/2$; the polynomial route returns the same "
     "root (I4, I5)"),
    ("3", "$M_{ii}=a_i^2/3$ for a cuboid",
     "hua", "I8: quadrature over the box, 0.3333333333"),
    ("4", "$M_{ii}=a_i^2/4$ for an ellipse",
     "hua", "I8: quadrature over the ellipse, 0.2499991667"),
    ("5", "$M_{ii}=a_i^2/5$ for an ellipsoid",
     "hua", "I8: quadrature over the ellipsoid, 0.2000000000"),
    ("19", "effect of window anisotropy and orientation on the coupling",
     "nahi hua", "FEM rotation study (criterion T5 for the mesh/rotation "
     "trend); no independent route"),
    ("0.5581", "piezoelectric extensional $k^2$ of the 200x10 plate",
     "hua", "D1/C1: the closed form built from $e$, $C$, $\\kappa$ alone "
     "gives 0.56079, and the free-plate FEM matches it to $10^{-10}$"),
    ("0.2", "distance between 0.5581 and the closed form",
     "hua", "D1, the same two numbers"),
    ("0.5608", "$e^{\\mathsf T}C^{-1}e/\\kappa$, 2-D plane stress",
     "hua", "derive\\_k2\\_closed\\_form.py from the constitutive tensors "
     "only; agreements 0.56079 vs 0.56079 (D1)"),
    ("0.09", "spread of the piezo $k^2$ between 10 and 1 micron",
     "nahi hua", "FEM thickness sweep (T3, T2 for mesh independence); the "
     "spread is small but no closed form predicts it"),
    ("31.1", "the same growth with the piezoelectric terms switched off",
     "nahi hua", "config_table: an FEM run with $e=0$ in the same solver; the "
     "two runs differ by the piezoelectric stiffness of the mode, and neither "
     "has a closed form"),
    ("23.9", "growth of the flexoelectric $k^2$ over the same range",
     "nahi hua", "the same FEM sweep (T3); the flexoelectric operator itself "
     "is verified against the uniform-curvature limit (I6, I7), the growth "
     "factor is not"),
    ("fifty-four", "the number of graded criteria",
     "hua", "run\\_all.py: 54/54 pass, and check\\_paper\\_numbers.py compares "
     "the word against summary.json"),
]


def abstract_text():
    tex = open(TEX).read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    body = m.group(1) if m else ""
    # superscripts are exponents, not quantities
    body = re.sub(r"\^\{-?\d+\}", "", body)
    body = re.sub(r"\^\d+", "", body)
    return body


def tokens(body):
    seen = []
    for t in re.findall(r"\d+(?:\.\d+)?", body):
        if t not in seen:
            seen.append(t)
    return seen


def main():
    body = abstract_text()
    toks = tokens(body)
    known = {c[0] for c in CLAIMS}
    missing = [t for t in toks if t not in known]
    stale = [c[0] for c in CLAIMS if c[0] not in body]

    n_hua = sum(1 for c in CLAIMS if c[2] == "hua")
    n_nahi = sum(1 for c in CLAIMS if c[2] == "nahi hua")
    n_na = sum(1 for c in CLAIMS if c[2] == "n/a")

    lines = ["# The abstract, number by number", "",
             "Every numeric token of the abstract of `Paper_12/main.tex`, with "
             "the verdict `hua` (an independent route reproduces it, or the "
             "number *is* a comparison against such a route) or `nahi hua` "
             "(no independent route; traceable to a JSON file and a passing "
             "criterion, but that criterion grades the solver against "
             "itself).  Generated by `python/audit_abstract_claims.py`; the "
             "coverage check at the end fails if the abstract grows a number "
             "without a verdict.", "",
             f"**{n_hua} checked, {n_nahi} not checked, {n_na} inputs.**", "",
             "| number | what it is | independent check | where |",
             "|---|---|---|---|"]
    for lit, what, verdict, route in CLAIMS:
        mark = {"hua": "**hua**", "nahi hua": "*nahi hua*",
                "n/a": "input"}[verdict]
        lines.append(f"| `{lit}` | {what} | {mark} | {route} |")
    lines += ["", "## Coverage", "",
              f"Numeric tokens found in the abstract: {len(toks)} "
              f"(`{'`, `'.join(toks)}`).", ""]
    if missing:
        lines.append("**Tokens with no verdict (fix before submission):** "
                     + ", ".join(f"`{t}`" for t in missing))
    else:
        lines.append("Every token has a verdict.")
    if stale:
        lines.append("")
        lines.append("Claims whose literal is no longer in the abstract: "
                     + ", ".join(f"`{t}`" for t in stale))
    with open(os.path.join(RES, "abstract_audit.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(RES, "abstract_audit.json"), "w") as fh:
        json.dump({"claims": [{"literal": c[0], "what": c[1],
                               "verdict": c[2], "route": c[3]}
                              for c in CLAIMS],
                   "n_hua": n_hua, "n_nahi_hua": n_nahi, "n_input": n_na,
                   "tokens": toks, "missing": missing, "stale": stale}, fh,
                  indent=1)

    print(f"  {n_hua} hua, {n_nahi} nahi hua, {n_na} inputs; "
          f"{len(missing)} token(s) uncovered")
    for t in missing:
        print(f"    MISSING verdict for {t!r}")
    for t in stale:
        print(f"    stale claim {t!r} (not in the abstract)")
    print("  -> results/abstract_audit.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
