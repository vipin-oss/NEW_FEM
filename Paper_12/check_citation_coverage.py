"""Check citation-key coverage without resolving or changing reference metadata.

Run: python Paper_12/check_citation_coverage.py
Only files reached by main.tex inputs are scanned; comments are ignored.
This does not check whether a cited source supports a scientific claim.
"""
from pathlib import Path
import re

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent


def uncomment(text):
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def expand(path, stack=()):
    path = path.resolve()
    if path in stack:
        raise ValueError(f"Cyclic input: {path}")
    text = uncomment(path.read_text())

    def include(match):
        child = PAPER / match.group(1)
        if not child.suffix:
            child = child.with_suffix(".tex")
        return expand(child, (*stack, path))

    return re.sub(r"\\(?:input|include)\{([^}]+)\}", include, text)


def main():
    text = expand(PAPER / "main.tex")
    keys = re.findall(r"^\s*@\w+\s*\{\s*([^,\s]+)\s*,",
                      (PAPER / "references.bib").read_text(), re.M)
    entries = set(keys)
    citations = set()
    occurrences = 0
    pattern = r"\\cite(?:p|t|alp|alt|author|year|yearpar)?\*?(?:\s*\[[^\]]*\]){0,2}\s*\{([^}]+)\}"
    for match in re.finditer(pattern, text):
        occurrences += 1
        citations.update(k.strip() for k in match.group(1).split(","))
    missing = sorted(citations - entries)
    uncited = sorted(entries - citations)
    duplicates = sorted(k for k in entries if keys.count(k) > 1)
    lines = ["# Citation-key coverage", "",
             "Source-only audit of main.tex and its recursively expanded inputs;",
             "comments ignored. Does not verify reference metadata or scientific support.",
             "No reference-audit file or bibliography field is modified.", "",
             f"- Bibliography entries: {len(keys)}",
             f"- Distinct keys cited in text: {len(citations)}",
             f"- Citation commands: {occurrences}"]
    for label, values in (("Undefined citation keys", missing),
                          ("Uncited bibliography entries", uncited),
                          ("Duplicate entry keys", duplicates)):
        lines.append(f"- {label}: {', '.join(values) if values else 'none'}")
    lines += ["", "Reproduce with `python Paper_12/check_citation_coverage.py`.", ""]
    (ROOT / "results" / "citation_coverage.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return int(bool(missing or uncited or duplicates))


if __name__ == "__main__":
    raise SystemExit(main())
