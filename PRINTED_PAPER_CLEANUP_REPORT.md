# Printed-paper cleanup report

## Checkout and scope

The supplied checkout was the initial commit `4d2be09`, containing only README.md,
not the stated `c352653` paper. Restored the files of
`c352653f8005abd70274b0e691d826f9e0a76a85` onto the fixed session branch
`arena/adfa7636-new-fem`; no branch was switched. Thus the session diff includes
the imported project. Editorial changes should be reviewed relative to c352653.
The fixes are committed and pushed to the fixed session branch
`origin/arena/adfa7636-new-fem`, not `origin/arena/7f5acba6-new-fem`.
The latter branch cannot be pushed from this Arena session.

## Defect 1: printed verification flags

Removed all fifteen bibliography note fields beginning UNVERIFIED, without
changing their remaining metadata. Removed the bibliography-status sentences
from the introduction, Data availability, and section/appendix opening blocks.
Moved the author actions into AUTHOR_TODO.md. Removing a flag does not verify
a reference. The publisher records were not independently checked.

## Defect 2: repeated opening blocks and inputs

Removed ten Notation and provenance blocks, plus repetitive provenance prose
in Sections 1, 3 and 7. Retained local symbol definitions and added short
running-text definitions where needed for window coordinates, length, time-step
index, density, modal frequencies, nodal loads and mass/acceleration.
Section 2 remains the central statement of assumed density, flexoelectric
coefficient, window operating range, fractional order and relaxation time;
Section 6 refers back rather than repeating the assumption statement. Physical
scaling explanations and operating-range limitations were retained.
All equation-environment counts, labels, and figure inclusion commands match
the requested source commit. No verified physics number was intentionally changed.

**Final compiled page count: awaiting the author’s independent compilation.
The <=31-page target is not certified here.**
No layout compression or removal of equations or figures was used to force it.

## Defect 3: American spelling

No `modelling` occurs in current manuscript TeX. The existing occurrence in a
published bibliography title was deliberately retained unchanged.

## Validation (sequential)

- First run_all: 69/70, solely because expanding all old prose-token checks to
  bibliography titles wrongly flagged seven legitimate occurrences of `plate`.
  Fixed by scanning bibliography files for only the three new editorial tokens;
  no published title was changed.
- Final `python python/run_all.py`: **70/70 PASS**.
- Subsequent `python python/check_paper_numbers.py`: **102/102**, **0 stale hits**
  across 23 forbidden tokens, including UNVERIFIED, Notation and provenance,
  and fields from memory. These three also scan references.bib.
- Source structural audit: balanced braces/math/environments, zero unresolved
  labels/citations, all 12 included graphics and input files present.
- Source checks: zero doubled Appendix reference constructions; zero
  period-terminated paragraph titles; zero forbidden editorial tokens in TeX/BibTeX.
- Compile attempted only after the suite finished: exit 127, `pdflatex` missing.
  `bibtex` and `tectonic` are also absent; no offline Tectonic bundle was supplied.
  Downloading Tectonic failed at the release-asset host because of network access
  restrictions. No diagnostic PDF could be built. Therefore zero undefined
  references, no doubled Appendix, and no double-period headings are confirmed
  at source level only, **not in a compiled PDF**. No page estimate is reported
  as a measured count. Author/frontmatter placeholders were left unchanged.
- Updated source-audit/page-budget messaging to avoid claiming a successful
  current Tectonic compile based on a historical hardcoded statement.

Generated numeric/figure drift was restored after runs; only final validation
summaries were retained. `results/reference_audit.md` is byte-identical to
c352653. No blanket checkout/clean was used: it would erase the requested patch
and, initially, the imported source. No build leftovers remain in Paper_12.
Author/affiliation/CRediT/acknowledgement placeholders were not altered.

## Author-only reference status (still UNVERIFIED)

| Entry key | What the author should check |
|---|---|
| `Gupta2026Rayleigh` | Resolve retained 2024 versus Crossref published-print 2026; confirm final volume/pages. |
| `Mindlin1968` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `Kogan1964` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `YudinTagantsev2013` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `Zubko2013` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `Cross2006` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `Caputo1967` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `BagleyTorvik1983` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `Koeller1984` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `ColeCole1941` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `HavriliakNegami1967` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `EnelundLesieutre1999` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `Roundy2003` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `ErturkInman2011` | Check authors, title, year, journal/book, volume, pages and DOI against publisher record; fields recalled from memory. |
| `fem1` | Check all fields against the publisher record; transcribed from published FEM-1. |

## Final requested delivery

At the author’s request, no additional TeX installation or compilation was
attempted. The author independently compiles with full TeX Live and will
verify the rendered flags, page count, references and heading punctuation.
Immediately before commit/push, the gates were rerun sequentially:
`python python/run_all.py` passed 70/70, followed by
`python python/check_paper_numbers.py` passing 102/102 with zero stale hits.
Generated numerical and figure drift was discarded, retaining the final
validation summaries. The original published bibliography title containing
“modelling” remains unchanged, as required by the original instructions.
