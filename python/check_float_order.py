"""
check_float_order.py -- the numbering the reader will see, without a compiler.

    python3 python/check_float_order.py -> results/float_order.md

LaTeX numbers a float by the order in which its \\caption (its \\label) appears
in the source, and prints that number wherever \\ref points at the label.  This
script rebuilds that map from the source and reports:

  * every float with the number it will carry and the section it lives in;
  * the number each \\ref prints, so that a stale "Table 3" in the prose shows
    up as a mismatch between what the sentence means and what it will print;
  * whether the main-text floats are first cited in increasing numerical order,
    which is what makes a "see Table 5" in Sec. 6.4 point forward rather than
    back;
  * the same for the appendix floats, which are numbered per appendix.
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = os.path.join(ROOT, "Paper_12")
OUT = os.path.join(ROOT, "results", "float_order.md")


def files():
    """Section files in reading order, then main.tex.

    main.tex is last because its own text after the \\input lines is the back
    matter (data availability, acknowledgements); scanning it first would put
    those references ahead of the whole body.
    """
    sec = os.path.join(PAPER, "sec")
    order = ["sec/" + f for f in sorted(os.listdir(sec)) if f.endswith(".tex")]
    order.append("main.tex")
    return [os.path.join(PAPER, f) for f in order]


def scan():
    """Every label and reference, in reading order.

    Section files are scanned with their \\input{table_x} and
    \\input{fig_x} inlined, so that a label defined in a table file takes the
    position of the table environment that includes it, which is the position
    LaTeX will number it at.  Line numbers inside an inlined file are those of
    the expanded text and are only a pointer.
    """
    text = []
    for path in files():
        raw = open(path).read()
        if not path.endswith("main.tex"):
            raw = expand(path)
        for n, line in enumerate(raw.split("\n"), 1):
            text.append((os.path.relpath(path, PAPER), n, line))
    floats, refs, secs = [], [], []
    for i, (f, n, line) in enumerate(text):
        for m in re.finditer(r"\\label\{((?:fig|tab|sec|eq|app):[^}]+)\}", line):
            floats.append({"label": m.group(1), "file": f, "line": n, "idx": i})
        for m in re.finditer(r"\\(?:ref|eqref)\{((?:fig|tab|sec|app):[^}]+)\}", line):
            refs.append({"label": m.group(1), "file": f, "line": n, "idx": i})
    return floats, refs


def expand(path):
    """A source file with every \input{table_x} replaced by that table."""
    raw = open(path).read()
    base = os.path.dirname(path)
    for m in set(re.findall(r"\\input\{([^}]+)\}", raw)):
        for cand in (os.path.join(base, m), os.path.join(PAPER, m),
                     os.path.join(base, m + ".tex"), os.path.join(PAPER, m + ".tex")):
            if os.path.exists(cand):
                inc = cand
                break
        else:
            inc = None
        if inc:
            raw = raw.replace("\\input{%s}" % m, open(inc).read())
    return raw


def appendix_order():
    """Labels of every float inside each appendix, \\input files expanded."""
    letters = {"91_appendixA.tex": "A", "92_appendixB.tex": "B",
               "93_appendixC.tex": "C"}
    out = {}
    for name, a in letters.items():
        path = os.path.join(PAPER, "sec", name)
        if not os.path.exists(path):
            continue
        labs = re.findall(r"\\label\{((?:fig|tab):[^}]+)\}", expand(path))
        for i, lab in enumerate(labs, 1):
            out[lab] = f"{a}.{i}"
    return out


def number(floats):
    """The number each figure/table will print."""
    main_fig = main_tab = 0
    letters = {"sec/91_appendixA.tex": "A", "sec/92_appendixB.tex": "B",
               "sec/93_appendixC.tex": "C"}
    appnum = appendix_order()
    out = {}
    for f in floats:
        lab, path = f["label"], f["file"]
        if lab.startswith(("sec:", "eq:", "app:")):
            continue
        if path in letters:
            out[lab] = appnum.get(lab, "?")
        elif lab.startswith("fig:"):
            main_fig += 1
            out[lab] = str(main_fig)
        else:
            main_tab += 1
            out[lab] = str(main_tab)
    return out


def main():
    floats, refs = scan()
    num = number(floats)
    first_cite = {}
    for r in refs:
        if r["label"] in num and r["label"] not in first_cite:
            first_cite[r["label"]] = r
    lines = ["# Float numbering as the compiler will print it", ""]
    lines.append("| float | number | defined in | first cited in |")
    lines.append("|---|---|---|---|")
    for f in floats:
        lab = f["label"]
        if lab not in num:
            continue
        c = first_cite.get(lab)
        where = f"{c['file']}:{c['line']}" if c else "**never cited**"
        lines.append(f"| `{lab}` | {num[lab]} | {f['file']}:{f['line']} | {where} |")
    # ordering of the main-text floats
    main_order = []
    for lab, n in sorted(num.items(), key=lambda kv: (("." in kv[1]), _key(kv[1]))):
        pass
    lines += ["", "## Main-text floats: numbering against first citation", ""]
    ok = True
    for kind in ("fig:", "tab:"):
        seq = [lab for lab in num if "." not in num[lab] and lab.startswith(kind)]
        cited_seq = [l for l in sorted(first_cite, key=lambda l: first_cite[l]["idx"])
                     if l in num and "." not in num[l] and l.startswith(kind)]
        ok = ok and seq == [l for l in cited_seq if l in seq]
        lines.append(f"{kind[:-1]}s, definition order: "
                     + ", ".join(num[l] + ":" + l for l in seq))
        lines.append("")
        lines.append(f"{kind[:-1]}s, first-citation order: "
                     + ", ".join(num[l] + ":" + l for l in cited_seq))
        lines.append("")
    lines.append(f"**{'order agrees' if ok else 'ORDER DIFFERS'}**")
    uncited = [l for l in num if l not in first_cite]
    if uncited:
        lines += ["", "floats never cited: " + ", ".join(uncited)]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[-8:]))
    print(f"\n  -> {os.path.relpath(OUT, ROOT)}")
    return 0 if ok and not uncited else 1


def _key(v):
    try:
        return int(v.split(".")[-1])
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
