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
    ("200", "plate length, \\SI{200}{\\micro\\metre}",
     "n/a", "an input of the model, not a measured quantity"),
    ("10", "plate thickness, \\SI{10}{\\micro\\metre}",
     "n/a", "an input of the model"),
    ("1", "$\\alpha=1$ and the one L1 history",
     "n/a", "the classical limit, chosen for the comparison"),
    ("0.5581", "piezoelectric extensional $k^2$ of the 200x10 plate",
     "hua", "D1/C1: the closed form built from $e$, $C$, $\\kappa$ alone "
     "gives 0.56079, and the free-plate FEM matches it to $10^{-10}$"),
    ("0.5608", "the closed-form extensional $k^2$ from $e$, $C$, $\\kappa$",
     "hua", "D1: the plane-stress closed form itself, 0.56079, which is the "
     "number this one rounds"),
    ("0.5", "distance between 0.5581 and the closed form 0.5608",
     "hua", "D1: the same two numbers, 0.56079 against 0.55814"),
    ("0.09", "spread of the piezo $k^2$ between 10 and 1 micron",
     "nahi hua", "FEM thickness sweep (T3, T2 for mesh independence); the "
     "spread is small but no closed form predicts it"),
    ("24", "growth of the flexoelectric $k^2$ over the same range, to the two "
     "significant digits the platform supports",
     "nahi hua", "the same FEM sweep (T3); the flexoelectric operator itself "
     "is verified against the uniform-curvature limit (I6, I7), the growth "
     "factor is not"),
    ("15", "lower end of the effect of window anisotropy and orientation on "
     "the coupling",
     "nahi hua", "FEM rotation study (criterion T5 for the mesh/rotation "
     "trend); no independent route"),
    ("19", "upper end of the same range",
     "nahi hua", "the same rotation study (T5); the spread is a property of "
     "the second-moment tensor, which is verified (I8), the spread is not"),
    ("0.450", "$\\zeta$ ratio, memory on $K_{uu}$ over $K_{\\rm eff}$",
     "nahi hua", "a property of the two condensation choices, read off the "
     "FEM matrices (S1b); the pole solver that converts the pole into "
     "$\\zeta$ is itself checked (I4)"),
    ("0.4580", "extensional $k^2$ of the 200x10 strip, plane stress, poling $x$",
     "nahi hua", "the application table (rows[3]); a clamped strip has no closed "
     "form, and the mesh convergence behind the table is the subject of T2"),
    ("0.4024", "the same coupling of the same strip in plane strain",
     "nahi hua", "the application table (rows[2]); the plane-strain and "
     "plane-stress reductions differ by the modelling error of Appendix B"),
    ("0.1", "thickness at which the flexoelectric bending term reaches "
     "$0.1\\,\\%$ of the piezoelectric one",
     "nahi hua", "the design map (F12); the $0.1\\,\\%$ level is a stated "
     "engineering threshold and the thickness is read from the FEM grid"),
    ("0.02", "distance of $\\zeta_{\\rm eff}$ from the classical limit",
     "hua", "I5: at $\\alpha=1$ the pole equation is quadratic and gives "
     "$\\omega\\tau/2=0.15000$ exactly, so the $0.02\\,\\%$ is a comparison "
     "with an exact value"),
]


def abstract_text():
    tex = manuscript_text()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    body = m.group(1) if m else ""
    # superscripts are exponents, not quantities
    body = re.sub(r"\\mathrm\{[^}]*\}", "", body)   # BaTiO_3 is a formula
    body = re.sub(r"\^\{-?\d+\}", "", body)
    body = re.sub(r"\^\d+", "", body)
    return body


def tokens(body):
    seen = []
    for t in re.findall(r"\d+(?:\.\d+)?", body):
        if t not in seen:
            seen.append(t)
    return seen



def manuscript_text():
    """main.tex plus every section file it includes, concatenated."""
    base = os.path.dirname(TEX)
    parts = [open(TEX).read()]
    sec = os.path.join(base, "sec")
    if os.path.isdir(sec):
        for fn in sorted(os.listdir(sec)):
            if fn.endswith(".tex"):
                parts.append(open(os.path.join(sec, fn)).read())
    for fn in sorted(os.listdir(base)):
        if fn.startswith("table_") and fn.endswith(".tex"):
            parts.append(open(os.path.join(base, fn)).read())
    return "\n".join(parts)

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
