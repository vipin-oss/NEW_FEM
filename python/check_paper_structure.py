"""
check_paper_structure.py -- what can be checked about the manuscript without a
TeX installation.

There is no pdflatex, latexmk, xelatex or tectonic in this environment and
`pip install tectonic` finds no distribution, so the paper is *not compiled*
here.  What can be checked is everything a compiler would report as an error
before it reaches the typesetter:

  * balanced braces, and no stray $ or unmatched begin/end,
  * every environment closed, in the right order,
  * every \\ref/\\eqref/\\cite having a \\label/\\bibitem,
  * every \\includegraphics file present (following \\graphicspath),
  * every \\input file present,
  * the numbers audit (python/check_paper_numbers.py) agreeing.

Run: python3 python/check_paper_structure.py
     -> results/paper_structure.md, exit status 0 if all clean.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
PAPER = os.path.join(ROOT, "Paper_12")


def strip_comments(s):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", ln) for ln in s.splitlines())


def main():
    src = open(os.path.join(PAPER, "main.tex")).read()
    body = strip_comments(src)
    problems = []

    # braces
    depth = 0
    for i, ch in enumerate(body):
        depth += (ch == "{") - (ch == "}")
        if depth < 0:
            problems.append(f"unbalanced brace near char {i}")
            depth = 0
    if depth:
        problems.append(f"{depth} unclosed brace(s)")
    if body.count("$") % 2:
        problems.append("odd number of $ (display math unbalanced)")

    # environments
    stack = []
    for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", body):
        kind, name = m.group(1), m.group(2)
        if kind == "begin":
            stack.append(name)
        else:
            if not stack or stack[-1] != name:
                problems.append(f"mismatched \\end{{{name}}}")
            else:
                stack.pop()
    if stack:
        problems.append(f"unclosed environments: {stack}")

    # references
    labels = set(re.findall(r"\\label\{([^}]+)\}", body))
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", body))
    cites = set()
    for m in re.finditer(r"\\cite\{([^}]+)\}", body):
        cites |= {c.strip() for c in m.group(1).split(",")}
    bibs = set(re.findall(r"\\bibitem\{([^}]+)\}", body))
    missing_ref = sorted(refs - labels)
    missing_cite = sorted(cites - bibs)
    unused_bib = sorted(bibs - cites)

    # graphics
    gp = re.search(r"\\graphicspath\{((?:\{[^}]*\})+)\}", body)
    roots = re.findall(r"\{([^}]*)\}", gp.group(1)) if gp else [""]
    gfx = re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", body)
    missing_gfx = [f for f in gfx
                   if not any(os.path.exists(os.path.join(PAPER, r, f))
                              for r in roots)]
    inputs = re.findall(r"\\input\{([^}]+)\}", body)
    def have(f):
        return (os.path.exists(os.path.join(PAPER, f))
                or os.path.exists(os.path.join(PAPER, f + ".tex")))

    missing_in = [f for f in inputs if not have(f)]

    # numbers audit
    p = subprocess.run([sys.executable, os.path.join(HERE,
                                                     "check_paper_numbers.py")],
                       capture_output=True, text=True)
    audit = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "?"

    ok = not (problems or missing_ref or missing_cite or missing_gfx
              or missing_in) and p.returncode == 0
    lines = ["# Structural check of Paper_12/main.tex", "",
             "**No TeX distribution is available in this environment** "
             "(pdflatex, latexmk, xelatex and tectonic are all absent, and "
             "`pip install tectonic` finds no distribution), so the "
             "manuscript is NOT COMPILED here.  This file lists what a "
             "compiler would have flagged before typesetting.", "",
             f"- braces and math: {'ok' if not problems else 'PROBLEM'}",
             f"- environments: {'ok' if not problems else 'PROBLEM'}",
             f"- unresolved \\\\ref: {missing_ref if missing_ref else 'none'}",
             f"- undefined \\\\cite: {missing_cite if missing_cite else 'none'}",
             f"- missing graphics: {missing_gfx if missing_gfx else 'none'}"
             f" ({len(gfx)} included)",
             f"- missing \\\\input: {missing_in if missing_in else 'none'}",
             f"- numbers audit: {audit}",
             "", "## Detail"]
    lines += [f"- {x}" for x in problems] or ["- nothing to report"]
    with open(os.path.join(RES, "paper_structure.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    for ln in lines[2:]:
        print("  " + ln)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
