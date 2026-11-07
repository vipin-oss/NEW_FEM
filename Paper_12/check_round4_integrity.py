"""Check Round 4's immutable numerical and author-owned content against e00aaba.

Run from any directory: python Paper_12/check_round4_integrity.py
Requires the local baseline Git object; never writes reference_audit.md.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
BASE = "e00aaba"


def old(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def same(path):
    return (ROOT / path).read_bytes() == old(path)


def block(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def main():
    files = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True
    ).splitlines()
    data = [p for p in files if p.startswith("results/") and p.endswith(".json")]
    tables = [p for p in files if p.startswith("Paper_12/table_") and p.endswith(".tex")]
    solvers = ["python/" + p for p in
               ("fem6_core.py", "materials.py", "run_design_map.py", "deterministic.py",
                "check_paper_numbers.py", "audit_abstract_claims.py")]
    before = old("Paper_12/main.tex").decode()
    after = (ROOT / "Paper_12/main.tex").read_text()
    checks = {
        f"all {len(data)} archived JSON files unchanged": all(map(same, data)),
        f"all {len(tables)} input tables unchanged": all(map(same, tables)),
        "solver, material, map producer and number-audit sources unchanged": all(map(same, solvers)),
        "bibliography metadata unchanged": same("Paper_12/references.bib"),
        "reference_audit.md unchanged": same("results/reference_audit.md"),
        "frontmatter before abstract unchanged":
            before.split(r"\begin{abstract}")[0] == after.split(r"\begin{abstract}")[0],
        "author declarations and acknowledgement unchanged":
            block(before, r"\section*{", r"\appendix") ==
            block(after, r"\section*{", r"\appendix"),
    }
    # Reorganization may repeat a symbol index; preserve every existing abstract
    # and conclusion numeral (including reported exponents) instead of counting
    # duplicate appearances of the same number.
    for label, a, b in (
            ("abstract", block(before, r"\begin{abstract}", r"\end{abstract}"),
             block(after, r"\begin{abstract}", r"\end{abstract}")),
            ("conclusion", old("Paper_12/sec/09_conclusions.tex").decode(),
             (ROOT / "Paper_12/sec/09_conclusions.tex").read_text())):
        tokens = lambda text: set(re.findall(r"\d+(?:\.\d+)?", text))
        checks[f"all baseline {label} numeric literals retained"] = tokens(a) <= tokens(b)
    # Check the assumed-range mathematical clauses across the manuscript.
    before_ranges, after_ranges = [], []
    for path in files:
        if path.startswith("Paper_12/") and path.endswith(".tex"):
            pattern = r"\$a(?:_2)?/L\\le0\.2\$"
            before_ranges += re.findall(pattern, old(path).decode())
            after_ranges += re.findall(pattern, (ROOT / path).read_text())
    checks["assumed operating-range clauses retained"] = sorted(before_ranges) == sorted(after_ranges)
    lines = ["# Round 4 numerical/content integrity", "", f"Baseline: `{BASE}`.", ""]
    for label, ok in checks.items():
        lines.append(f"- {'PASS' if ok else 'FAIL'}: {label}")
    lines += ["", "This complements, not replaces, the 102-claim JSON audit.",
              "Figure axis formatting/units and explanatory text may change; numerical",
              "archives, input tables and protected author content must not.", ""]
    (ROOT / "results" / "round4_integrity.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
