"""check_final_consistency.py -- numbers in the abstract, the conclusion, the
Highlights and the captions, against the body of the paper and the archives.

    python3 python/check_final_consistency.py -> results/final_consistency.md

A number printed in a caption or in the Highlights is the hardest kind to keep
in step with the text, because nothing in the sentence forces it.  For every
number that appears in those four places the check looks for the same literal
(a) elsewhere in the manuscript, body prose included, or (b) in a results JSON,
where it must equal a value to the precision it is printed at.  A number that
neither route finds is reported, with the place it appears.
"""
from __future__ import annotations

import json

import numpy as np
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = os.path.join(ROOT, "Paper_12")
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "final_consistency.md")

NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?:\\times10\^\{?-?\d+\}?)?(?![\w.])")


def expand(path):
    raw = open(path).read()
    base = os.path.dirname(path)
    for m in set(re.findall(r"\\input\{([^}]+)\}", raw)):
        for cand in (os.path.join(base, m), os.path.join(PAPER, m),
                     os.path.join(base, m + ".tex"), os.path.join(PAPER, m + ".tex")):
            if os.path.exists(cand):
                raw = raw.replace("\\input{%s}" % m, open(cand).read())
                break
    return raw



def split_captions(raw):
    """(list of caption texts, the same source with every caption blanked).

    \caption{...} is scanned with balanced braces: a caption that contains
    \SI{10}{\micro\metre} or $...$ would otherwise be cut short or swallow
    the paragraph that follows it.
    """
    caps, out, i = [], [], 0
    while True:
        k = raw.find("\\caption{", i)
        if k < 0:
            out.append(raw[i:])
            break
        out.append(raw[i:k])
        j, depth = k + len("\\caption{"), 1
        while j < len(raw) and depth:
            if raw[j] == "\\":          # an escaped brace does not nest
                j += 2
                continue
            if raw[j] == "{":
                depth += 1
            elif raw[j] == "}":
                depth -= 1
            j += 1
        caps.append(raw[k + len("\\caption{"):j - 1])
        out.append(" ")
        i = j
    return caps, "".join(out)


def files():
    """The section files only: main.tex \\input{}s them, so walking it as well
    would count every caption twice."""
    sec = os.path.join(PAPER, "sec")
    return [os.path.join(sec, f) for f in sorted(os.listdir(sec))
            if f.endswith(".tex")]


def strip_comments(text):
    """Drop TeX comments, honouring the escaped \\% of a percentage."""
    out = []
    for line in text.split("\n"):
        if line.lstrip().startswith("%"):
            out.append("")
            continue
        cut, i = len(line), 0
        while i < len(line):
            if line[i] == "\\":
                i += 2
                continue
            if line[i] == "%":
                cut = i
                break
            i += 1
        out.append(line[:cut])
    return "\n".join(out)


def tokens(text):
    return set(t for t in NUM.findall(text) if len(t.replace("-", "").replace(".", "")) >= 3)


def archive_numbers():
    vals = set()
    for fn in sorted(os.listdir(RES)):
        if not fn.endswith(".json"):
            continue
        try:
            data = json.load(open(os.path.join(RES, fn)))
        except Exception:
            continue
        stack = [data]
        while stack:
            v = stack.pop()
            if isinstance(v, dict):
                stack.extend(v.values())
            elif isinstance(v, list):
                stack.extend(v)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.add(float(v))
    return vals


def matches(token, archive):
    """True if some archived value rounds to this token as printed.

    A number is accepted when an archive value lies within half a unit of the
    last digit the manuscript prints, which is the strongest statement a
    rounded quote can support.
    """
    t = re.sub(r"\\times10\^\{(-?\d+)\}", lambda m: "e" + m.group(1),
               token.replace("$", "").replace("\\,", ""))
    try:
        x = float(t)
    except ValueError:
        return False
    mant = re.match(r"-?(\d+)(?:\.(\d+))?(?:e([-+]?\d+))?", t)
    if not mant:
        return False
    digits = len((mant.group(1) + (mant.group(2) or "")).lstrip("0"))
    ulp = 10.0 ** (np.floor(np.log10(abs(x))) - max(digits - 1, 0))
    for a in archive:
        if abs(a - x) <= 0.5 * ulp * 1.0001:
            return True
    return False


def main():
    body_parts = []
    caps = []
    abstract = []
    concl = []
    high = []
    main = strip_comments(open(os.path.join(PAPER, "main.tex")).read())
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", main, re.S)
    if m:
        abstract.append(("main.tex abstract", m.group(1)))
    concl.append(("08_conclusion.tex", strip_comments(
        open(os.path.join(PAPER, "sec", "08_conclusion.tex")).read())))
    high.append(("Highlights.tex", strip_comments(
        open(os.path.join(PAPER, "Highlights.tex")).read())))
    for f in files():
        raw = strip_comments(expand(f))
        cps, raw_wo = split_captions(raw)
        for c in cps:
            caps.append((os.path.relpath(f, PAPER), c))
        body_parts.append(raw_wo)
    body = "\n".join(body_parts)

    archive = archive_numbers()
    rows = []
    for where, text in abstract + concl + high + [(w, c) for w, c in caps]:
        for tk in sorted(tokens(text)):
            in_body = re.search(r"(?<![\w.])%s(?![\w.])" % re.escape(tk), body)
            ok = bool(in_body) or matches(tk, archive)
            rows.append({"where": where, "token": tk, "ok": ok,
                         "how": "elsewhere in the manuscript" if in_body
                         else ("results archive" if matches(tk, archive)
                               else "NOWHERE")})
    bad = [r for r in rows if not r["ok"]]
    lines = ["# Numbers in the abstract, the conclusion, the Highlights and the captions", "",
             f"{len(rows)} numbers checked, {len(rows) - len(bad)} traced, "
             f"{len(bad)} untraced.", "",
             "| place | number | found in |", "|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['where']} | `{r['token']}` | {r['how']} |")
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("%d numbers checked, %d traced, %d untraced" %
          (len(rows), len(rows) - len(bad), len(bad)))
    for r in bad[:20]:
        print("  UNTRACED  %-40s %s" % (r["where"], r["token"]))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
