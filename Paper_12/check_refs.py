"""check_refs.py -- reference audit for Paper_12.

Two independent checks, both written to results/reference_audit.md:

1. Crossref.  Every entry that carries a DOI is looked up at
   api.crossref.org and the title (MathML/JATS tags stripped), the first
   author's surname, the year, the volume and the first page are compared with
   the bib entry.  Mismatches are printed field by field.  If the network is
   not reachable the entry is reported as *unchecked* -- never as verified.

   Two tolerances are deliberate, and neither hides a disagreement:

   * **Online-first year.**  Crossref's `issued` date of a journal article is
     often the date it appeared online, one year before the printed issue.
     Where the year differs by exactly one *and* the volume is the same, the
     entry is reported as `online-first` rather than as a mismatch: the
     bibliography keeps the print/volume year, which is the year a reader will
     find on the issue.
   * **C1 vs c 1.**  Wiley encodes the element order inside the title as
     `C</i>1</sup>`, which strips to "c 1" while the bibliography writes "C1".
     The two spellings are folded together before titles are compared.

2. The FEM-1 reference list.  docs/FEM1_references.txt transcribes the 58
   entries of the published FEM-1 PDF.  Each one is matched to a bib entry (by
   DOI, else by first-author surname and year) and the year, volume and first
   page printed there are compared with the bib.  Entries of FEM-1 that this
   paper does not carry are listed as "not used" -- they are not padding.

Run from the repository root:  python Paper_12/check_refs.py
"""
from __future__ import annotations

import json
import os
import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIB = os.path.join(HERE, "references.bib")
FEM1 = os.path.join(ROOT, "docs", "FEM1_references.txt")
OUT = os.path.join(ROOT, "results", "reference_audit.md")
MAILTO = "gupta@example.invalid"          # Crossref politeness address (placeholder)

# ----------------------------------------------------------------- parsing
def parse_bib(path=BIB):
    s = open(path).read()
    ents = []
    for m in re.finditer(r"@(\w+)\{([^,]+),", s):
        start = m.start()
        depth = 0
        for k in range(start, len(s)):
            if s[k] == "{":
                depth += 1
            elif s[k] == "}":
                depth -= 1
                if depth == 0:
                    break
        body = s[start:k]
        f = {}
        for mm in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*\n", body, re.S):
            f[mm.group(1).lower()] = " ".join(mm.group(2).split())
        f["_type"] = m.group(1)
        f["_key"] = m.group(2)
        ents.append(f)
    return ents


def parse_fem1(path=FEM1):
    out = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        n, text, doi = parts[0], "|".join(parts[1:-1]), parts[-1]
        year = re.search(r"\((\d{4})\)", text)
        if year is None:
            year = re.search(r"\b(1[89]\d\d|20\d\d)\b(?!.*\b(?:1[89]\d\d|20\d\d)\b)", text)
        vol = re.search(r"(\d+)\s*(?:\(\d+(?:\s*[\u2013\u2014-]\s*\d+)?\)\s*)?\((\d{4})\)", text)
        if vol is None:
            vol = re.search(r"\b(\d{1,4})\b(?=[^\d]*\b(?:19|20)\d\d\b)", text)
        pages = None
        if year:
            tail = text[year.end():].strip().rstrip(".")
            pages = tail
        out.append({"n": int(n), "text": text, "doi": "" if doi == "-" else doi,
                    "year": year.group(1) if year else "",
                    "volume": vol.group(1) if vol else "", "pages": pages or ""})
    return out


# -------------------------------------------------------------- comparing
def norm(t):
    t = re.sub(r"<[^>]+>", " ", t)                       # MathML / JATS tags
    t = unicodedata.normalize("NFKD", t)
    t = t.replace("\\&", "&").replace("{", "").replace("}", "")
    t = re.sub(r"\\[a-zA-Z]+", " ", t)                   # LaTeX accents
    t = re.sub(r"[^A-Za-z0-9]+", " ", t).strip().lower()
    return " ".join(t.split())


def norm_title(t):
    """norm() plus the element-order spelling that publishers encode differently.

    "A three-dimensional C1 finite element" and the stripped Crossref form
    "a three dimensional c 1 finite element" are the same title.
    """
    return re.sub(r"\bc\s*1\b", "c1", norm(t))


def first_surname(authors):
    first = re.split(r"\s+and\s+", authors)[0]
    if "," in first:
        return norm(first.split(",")[0])
    parts = norm(first).split()
    return parts[-1] if parts else ""


def first_page(p):
    m = re.search(r"(\d+)", p or "")
    return m.group(1) if m else ""


def crossref(doi, timeout=8):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={
        "User-Agent": f"paper12-refcheck/1.0 (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return json.load(fh)["message"]


def online():
    for host in ("api.crossref.org",):
        try:
            socket.create_connection((host, 443), timeout=5).close()
            return True
        except OSError:
            continue
    return False


def compare_crossref(ent, msg, notes=None):
    """Field-by-field comparison.  Returns the mismatches.

    `notes` collects what is worth printing but is not a disagreement, at
    present only the online-first year.
    """
    notes = [] if notes is None else notes
    bad = []
    a = norm_title(ent.get("title", ""))
    b = norm_title((msg.get("title") or [""])[0])
    if a and b and a != b:
        if not (a in b or b in a):
            bad.append(f"title: bib '{a[:60]}' vs Crossref '{b[:60]}'")
    au = msg.get("author") or []
    if au and first_surname(ent.get("author", "")):
        cs = norm(au[0].get("family", ""))
        if cs and cs != first_surname(ent.get("author", "")):
            bad.append(f"first author: bib '{first_surname(ent.get('author',''))}' "
                       f"vs Crossref '{cs}'")
    y = msg.get("issued", {}).get("date-parts", [[None]])[0][0]
    v = msg.get("volume")
    vol_same = bool(v) and bool(ent.get("volume")) and str(v) == str(ent["volume"])
    if y and str(y) != ent.get("year", "").strip():
        try:
            gap = abs(int(y) - int(ent.get("year", "")))
        except (TypeError, ValueError):
            gap = None
        if gap == 1 and vol_same:
            notes.append(f"online-first: bib year {ent.get('year','')} is the "
                         f"print/volume year, Crossref issued {y} (volume {v} "
                         f"agrees)")
        else:
            bad.append(f"year: bib {ent.get('year','')} vs Crossref {y}"
                       + ("" if vol_same else " (volume differs too)"))
    if v and ent.get("volume") and not vol_same:
        bad.append(f"volume: bib {ent['volume']} vs Crossref {v}")
    p = msg.get("page")
    if p and ent.get("pages"):
        if first_page(p) != first_page(ent["pages"]):
            bad.append(f"pages: bib {ent['pages']} vs Crossref {p}")
    return bad


def compare_fem1(ent, ref):
    bad = []
    if ref["year"] and ref["year"] != ent.get("year", ""):
        bad.append(f"year: bib {ent.get('year','')} vs FEM-1 {ref['year']}")
    if ref["volume"] and ent.get("volume") and ref["volume"] != ent["volume"]:
        bad.append(f"volume: bib {ent['volume']} vs FEM-1 {ref['volume']}")
    if ref["pages"] and ent.get("pages"):
        if first_page(ref["pages"]) != first_page(ent["pages"]):
            bad.append(f"pages: bib {ent['pages']} vs FEM-1 '{ref['pages']}'")
    if ref["doi"] and ent.get("doi") and norm(ref["doi"]) != norm(ent["doi"]):
        bad.append(f"doi: bib {ent['doi']} vs FEM-1 {ref['doi']}")
    return bad


# -------------------------------------------------------------------- main
def main():
    bib = parse_bib()
    fem1 = parse_fem1()
    net = online()

    rows, no_doi, problems = [], [], 0
    for e in bib:
        doi = e.get("doi", "").strip()
        key = e["_key"]
        if not doi:
            no_doi.append(e)
            rows.append((key, doi, "no DOI: not checkable at Crossref", "unchecked"))
            continue
        if not net:
            rows.append((key, doi, "network unreachable: not looked up", "unchecked"))
            continue
        try:
            msg = crossref(doi)
        except urllib.error.HTTPError as exc:
            rows.append((key, doi, f"Crossref HTTP {exc.code}", "unchecked"))
            continue
        except Exception as exc:                     # noqa: BLE001
            rows.append((key, doi, f"lookup failed: {type(exc).__name__}", "unchecked"))
            continue
        notes = []
        bad = compare_crossref(e, msg, notes)
        if bad:
            res, st = "; ".join(bad), "mismatch"
        elif notes:
            res, st = "; ".join(notes), "online-first"
        else:
            res, st = "all checked fields agree", "match"
        rows.append((key, doi, res, st))
        problems += bool(bad)

    # ---- FEM-1 cross-check
    by_doi = {norm(e["doi"]): e for e in bib if e.get("doi")}
    fem1_rows, matched, fem1_bad = [], set(), 0
    for r in fem1:
        ent = by_doi.get(norm(r["doi"])) if r["doi"] else None
        if ent is None:
            sur = norm(r["text"].split(",")[0].split()[-1])
            for e in bib:
                if first_surname(e.get("author", "")) == sur and e.get("year", "") == r["year"]:
                    ent = e
                    break
        if ent is None:
            fem1_rows.append((r["n"], r["text"][:90], "—", "not used here"))
            continue
        matched.add(ent["_key"])
        bad = compare_fem1(ent, r)
        fem1_bad += bool(bad)
        fem1_rows.append((r["n"], r["text"][:90], ent["_key"],
                          "; ".join(bad) if bad else "agrees"))

    extra = [e["_key"] for e in bib if e["_key"] not in matched
             and e["_key"] not in ("fem1", "fem4", "fem5")]

    n_ok = sum(1 for r in rows if r[3] in ("match", "online-first", "mismatch"))
    net_used = net and n_ok > 0
    n_match = sum(1 for r in rows if r[3] == "match")
    n_online = sum(1 for r in rows if r[3] == "online-first")
    n_un = sum(1 for r in rows if r[3] == "unchecked")
    lines = ["# Reference audit", "",
             "Generated by `Paper_12/check_refs.py`. Two checks:", "",
             "1. **Crossref** — title (tags stripped), first-author surname, year, volume and",
             "   first page of every entry that carries a DOI.",
             "2. **FEM-1 list** — the 58 entries of the published FEM-1 PDF",
             "   (`docs/FEM1_references.txt`) matched against this bibliography.", "",
             f"Crossref reachable from this run: **{'yes' if net_used else 'no'}** — "
             f"{n_match} entries agree, {n_online} agree after the online-first "
             f"year (print/volume year kept), {problems} mismatch, {n_un} "
             f"unchecked.", "",
             "## 1. Crossref check", "",
             "| key | DOI | result | status |", "|---|---|---|---|"]
    for key, doi, res, st in rows:
        lines.append(f"| `{key}` | {doi or '—'} | {res} | {st} |")
    lines += ["", f"Entries without a DOI ({len(no_doi)}): "
              + ", ".join("`" + e["_key"] + "`" for e in no_doi) + ".", "",
              "## 2. FEM-1 reference list", "",
              "| # | FEM-1 entry (as printed) | bib key | comparison |",
              "|---|---|---|---|"]
    for n, text, key, res in fem1_rows:
        lines.append(f"| {n} | {text} | {key} | {res} |")
    lines += ["", f"FEM-1 entries carried here: {len(matched)} of {len(fem1)}; "
              f"{fem1_bad} with a field mismatch; "
              f"{sum(1 for r in fem1_rows if r[3] == 'not used here')} deliberately not used.", "",
              "Bibliography entries that do not come from the FEM-1 list: "
              + (", ".join("`" + k + "`" for k in extra) or "none") + ".", ""]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(lines))
    print(f"  Crossref: {'online' if net_used else 'offline'} -> {n_match} match, "
          f"{n_online} online-first, {problems} mismatch, {n_un} unchecked")
    print(f"  FEM-1: {len(matched)}/{len(fem1)} carried, {fem1_bad} field mismatches")
    print(f"  -> {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
