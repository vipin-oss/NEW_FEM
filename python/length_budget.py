"""Page budget for the manuscript, measured from the sources.

No full TeX Live is installed in this environment; an offline static Tectonic
diagnostic compiles the manuscript separately and reports 35 pages.  The count
below is an area *budget*, not a measurement: every figure's height follows
from its PDF box and its ``width=`` option, every table's height from its row
count, and the prose from its character count.  The one unknown, how much a
page loses to bad breaks, is calibrated on the last revision whose PDF was
counted (34 pages).

    python length_budget.py                  # current tree
    python length_budget.py --calibrate 47a21a3

Writes ``results/length_budget.md``.  The numbers are an estimate with a stated
error of about a page; they are not a measurement and never replace a compile.
"""
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(ROOT, "Paper_12")
RESULTS = os.path.join(ROOT, "results")

TEXTWIDTH = 170.0 * 72.0 / 25.4     # 482.0 pt, from main.tex
TEXTHEIGHT = 252.0 * 72.0 / 25.4    # 714.6 pt
CHARLINE = 100.0                    # characters per line, 10 pt Times, 170 mm
LINESKIP = 12.0                     # pt per line at \linespread 1.0
CAPTION_SKIP = 11.0                 # captions are \small
CAPTION_CHARS = 110.0

FIGS = {}


def mediabox(path):
    """(width, height) in pt of the first page, or None."""
    try:
        data = open(path, "rb").read(4000)
    except OSError:
        return None
    m = re.search(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", data)
    if not m:
        return None
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return x1 - x0, y1 - y0


def read(rel, rev=None):
    if rev:
        r = subprocess.run(["git", "show", "%s:Paper_12/%s" % (rev, rel)],
                           cwd=ROOT, capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else ""
    path = os.path.join(PAPER, rel)
    return open(path).read() if os.path.exists(path) else ""


def expand(rel, rev=None, seen=None):
    """Main source with every \\input resolved, comments dropped."""
    seen = seen or set()
    if rel in seen:
        return ""
    seen.add(rel)
    text = read(rel, rev)
    out = []
    for line in text.split("\n"):
        line = re.sub(r"(?<!\\)%.*$", "", line)
        m = re.match(r"\s*\\input\{([^}]*)\}\s*$", line)
        if m:
            name = m.group(1)
            if not name.endswith(".tex"):
                name += ".tex"
            out.append(expand(name, rev, seen))
        else:
            out.append(line)
    return "\n".join(out)


def caption_lines(block, env):
    m = re.search(r"\\caption(?:\[[^\]]*\])?\{", block)
    if not m:
        return 0.0
    i = m.end()
    depth = 1
    while i < len(block) and depth:
        if block[i] == "{" and block[i - 1] != "\\":
            depth += 1
        elif block[i] == "}" and block[i - 1] != "\\":
            depth -= 1
        i += 1
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", block[m.end():i - 1])
    text = re.sub(r"[{}$\\]", "", text)
    return max(1.0, math.ceil(len(text) / CAPTION_CHARS)) * CAPTION_SKIP


def figure_height(block):
    m = re.search(r"\\includegraphics\[([^\]]*)\]\{([^}]*)\}", block)
    if not m:
        return 0.0
    opts, name = m.group(1), m.group(2)
    w = re.search(r"width\s*=\s*([\d.]*)\s*\\textwidth", opts)
    frac = float(w.group(1)) if (w and w.group(1)) else (1.0 if w else 0.8)
    if name not in FIGS:
        FIGS[name] = mediabox(os.path.join(PAPER, "figures", name))
    box = FIGS[name]
    if not box:
        return 0.5 * TEXTHEIGHT
    return frac * TEXTWIDTH * box[1] / box[0]


def bib_lines(rev=None):
    """Lines the reference list will take: one entry, about 3.4 lines of \\small."""
    if rev:
        r = subprocess.run(["git", "show", "%s:Paper_12/references.bib" % rev],
                           cwd=ROOT, capture_output=True, text=True)
        text = r.stdout
    else:
        text = read("references.bib")
    n = len(re.findall(r"^@", text, re.M))
    return n * 3.4, n


def table_height(block):
    small = bool(re.search(r"\\small|\\footnotesize|\\scriptsize", block))
    skip = 9.5 if small else LINESKIP
    body = block
    rows = body.count("\\\\")
    rules = len(re.findall(r"\\(toprule|midrule|bottomrule|hline)", body))
    nested = sum(1 for _ in re.finditer(r"\\begin\{tabular\}", body))
    return rows * skip + rules * 4.0 + nested * 6.0


def measure(rev=None):
    src = expand("main.tex", rev)
    app = re.search(r"\\appendix", src)
    cut = app.start() if app else len(src)
    floats = {"figure": [], "table": []}
    for env in ("figure", "table"):
        pat = re.compile(r"\\begin\{%s\*?\}.*?\\end\{%s\*?\}" % (env, env), re.S)
        for m in pat.finditer(src):
            floats[env].append((m.start(), m.group(0)))
    start = src.find("\\begin{document}")
    prose = src[max(start, 0):]
    for env in ("figure", "table"):
        pat = re.compile(r"\\begin\{%s\*?\}.*?\\end\{%s\*?\}" % (env, env), re.S)
        prose = pat.sub("\n\nFLOAT\n\n", prose)
    # the appendix marker survives; split there
    i = prose.find("\\appendix")
    bodyprose, appprose = (prose[:i], prose[i:]) if i >= 0 else (prose, "")

    def prose_pt(text):
        displays = len(re.findall(r"\\begin\{(equation|align|eqnarray)\*?\}|\\\[", text))
        chars = len(re.sub(r"\\[a-zA-Z]+\*?", " ", text))
        return (chars / CHARLINE) * LINESKIP + displays * 2.2 * LINESKIP

    def height(env, block):
        if env == "figure":
            return figure_height(block) + caption_lines(block, env) + 16
        return table_height(block) + caption_lines(block, env) + 16

    fb = sum(height("figure", b) for p, b in floats["figure"] if p < cut)
    tb = sum(height("table", b) for p, b in floats["table"] if p < cut)
    fa = sum(height("figure", b) for p, b in floats["figure"] if p >= cut)
    ta = sum(height("table", b) for p, b in floats["table"] if p >= cut)
    details = []
    for env in ("figure", "table"):
        for pos, block in floats[env]:
            lab = re.search(r"\\label\{([^}]*)\}", block)
            details.append((env, lab.group(1) if lab else "?",
                            height(env, block), pos < cut))
    # prose by section
    sections = []
    body_only = bodyprose
    parts = re.split(r"\\section\*?\{", body_only)
    for chunk in parts[1:]:
        name = chunk.split("}")[0]
        name = re.sub(r"\\[a-zA-Z]+", "", name)
        sections.append((name.strip(), prose_pt(chunk),
                         len(re.sub(r"\\[a-zA-Z]+\*?", " ", chunk).split())))
    refl, nrefs = bib_lines(rev)
    return {
        "body_fig": fb, "body_tab": tb, "app_fig": fa, "app_tab": ta,
        "body_txt": prose_pt(bodyprose), "app_txt": prose_pt(appprose),
        "refs": refl * CAPTION_SKIP, "nrefs": nrefs,
        "n_body_fig": sum(1 for p, _ in floats["figure"] if p < cut),
        "n_body_tab": sum(1 for p, _ in floats["table"] if p < cut),
        "n_app_tab": sum(1 for p, _ in floats["table"] if p >= cut),
        "n_app_fig": sum(1 for p, _ in floats["figure"] if p >= cut),
        "body_words": len(re.sub(r"\\[a-zA-Z]+\*?", " ", bodyprose).split()),
        "words": len(re.sub(r"\\[a-zA-Z]+\*?", " ", prose).split()),
        "floats": details,
        "sections": sections,
    }


def total(m):
    return sum(m[k] for k in ("body_fig", "body_tab", "body_txt", "app_fig",
                              "app_tab", "app_txt", "refs"))


def main():
    rev, pages = "47a21a3", 34.0          # last revision whose PDF was counted
    if "--calibrate" in sys.argv:
        i = sys.argv.index("--calibrate")
        rev = sys.argv[i + 1]
        pages = float(sys.argv[i + 2]) if len(sys.argv) > i + 2 else pages
    if "--no-calibration" in sys.argv:
        rev, pages = None, None
    cur = measure()
    old = measure(rev) if rev else None
    tot = total(cur)
    lines = ["# Page budget (estimate, not a measurement)", "",
             "No full TeX Live here; an offline static Tectonic diagnostic compiles "
             "separately. Text width "
             "%.1f pt, text height %.1f pt, %.0f characters per line, %.0f pt per line; "
             "figure heights from each PDF's MediaBox and its `width=` option, table "
             "heights from row counts." % (TEXTWIDTH, TEXTHEIGHT, CHARLINE, LINESKIP), ""]
    rows = [("body figures", cur["body_fig"], "%d" % cur["n_body_fig"]),
            ("body tables", cur["body_tab"], "%d" % cur["n_body_tab"]),
            ("body prose and display maths", cur["body_txt"], "%d words" % cur["body_words"]),
            ("appendix figures", cur["app_fig"], "%d" % cur["n_app_fig"]),
            ("appendix tables", cur["app_tab"], "%d" % cur["n_app_tab"]),
            ("appendix prose", cur["app_txt"], ""),
            ("reference list", cur["refs"], "%d entries" % cur["nrefs"])]
    lines.append("| block | amount | pt | pages |")
    lines.append("|---|---|---|---|")
    for label, pt, amount in rows:
        lines.append("| %s | %s | %.0f | %.2f |" % (label, amount, pt, pt / TEXTHEIGHT))
    lines.append("| **sum** | | **%.0f** | **%.2f** |" % (tot, tot / TEXTHEIGHT))
    lines += ["", "## Where the body stands", "",
              "| | body content | pages of area |", "|---|---|---|"]
    body = cur["body_fig"] + cur["body_tab"] + cur["body_txt"]
    lines.append("| this revision | %.0f pt | %.2f |" % (body, body / TEXTHEIGHT))
    if old:
        ob = old["body_fig"] + old["body_tab"] + old["body_txt"]
        lines.append("| `%s` | %.0f pt | %.2f |" % (rev, ob, ob / TEXTHEIGHT))
        lines.append("| **change** | **%+.0f pt** | **%+.2f** |" % (body - ob, (body - ob) / TEXTHEIGHT))
        lines += ["", "Package content: %.0f -> %.0f pt (%.2f -> %.2f pages)."
                  % (total(old), tot, total(old) / TEXTHEIGHT, tot / TEXTHEIGHT)]
    lines += ["", "## From area to pages", ""]
    if old and pages:
        slack = pages / (total(old) / TEXTHEIGHT)
        est = slack * tot / TEXTHEIGHT
        lines.append("The last counted PDF (`%s`) was %.0f pages for %.2f pages of area, "
                     "so a page of area costs %.2f printed pages -- floats leave gaps that "
                     "cannot be filled." % (rev, pages, total(old) / TEXTHEIGHT, slack))
        lines.append("")
        lines.append("**Estimated PDF now: %.1f pages (target 30, previous %.0f).** "
                     "To reach 30 another %.0f pt = %.1f pages of area has to go."
                     % (est, pages, tot - 30.0 / slack * TEXTHEIGHT,
                        (tot - 30.0 / slack * TEXTHEIGHT) / TEXTHEIGHT))
        lines.append("")
    # biggest floats and sections, both trees are the same in shape
    lines += ["## Biggest items now", "", "| float | pt | pages | in |", "|---|---|---|---|"]
    for env, lab, pt, inbody in sorted(cur["floats"], key=lambda f: -f[2])[:10]:
        lines.append("| `%s` (%s) | %.0f | %.2f | %s |"
                     % (lab, env, pt, pt / TEXTHEIGHT, "body" if inbody else "appendix"))
    lines += ["", "| section | words of source | pages of area |", "|---|---|---|"]
    for name, pt, words in cur["sections"]:
        if pt <= 0:
            continue
        lines.append("| %s | %d | %.2f |" % (name, words, pt / TEXTHEIGHT))
    lines.append("")
    if old and pages:
        need = tot - 30.0 / slack * TEXTHEIGHT
        body_figs = [(lab, pt) for env, lab, pt, inb in cur["floats"]
                     if env == "figure" and inb]
        shrink = sum(pt * 0.15 for _, pt in body_figs)          # widths to 0.85
        verif = [pt for env, lab, pt, _ in cur["floats"] if lab == "tab:verification"]
        small = verif[0] * 0.20 if verif else 0.0               # \footnotesize, tighter rules
        appb = sum(pt for env, lab, pt, inb in cur["floats"]
                   if not inb and env in ("figure", "table") and lab in
                   ("tab:verification", "tab:independent", "tab:sens", "fig:modeshape"))
        lines += ["", "## Levers, measured but **not applied** (round 20 was scope-locked)", "",
                  "To reach %.0f pages, %.0f pt of area (%.1f pages) has to go. "
                  "Ranked by what each is worth:" % (30, need, need / TEXTHEIGHT), "",
                  "| lever | saves | pages | cost to the paper |", "|---|---|---|---|",
                  "| Appendix B to supplementary material (4 floats, %.0f pt) | %.0f pt | %.1f | the verification table is the evidence of Sec. 6.1; a supplementary file is standard practice but changes the submission |"
                  % (appb, appb, appb / TEXTHEIGHT),
                  "| all twelve body figures to 0.85\\textwidth | %.0f pt | %.1f | axes get smaller; none is removed |"
                  % (shrink, shrink / TEXTHEIGHT),
                  "| `tab:verification` at \\footnotesize with tighter rules | %.0f pt | %.1f | 54 rows at 9 pt instead of 12 |"
                  % (small, small / TEXTHEIGHT),
                  "| Sec. 2 and Sec. 5 tightened by a quarter | %.0f pt | %.1f | prose only: the two sections have never been shortened |"
                  % ((cur["sections"][1][1] + cur["sections"][4][1]) * 0.25,
                     (cur["sections"][1][1] + cur["sections"][4][1]) * 0.25 / TEXTHEIGHT),
                  ""]
    lines.append("")
    lines.append("The estimate carries about one page of error and is not a substitute "
                 "for `pdflatex`.")
    out = os.path.join(RESULTS, "length_budget.md")
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
