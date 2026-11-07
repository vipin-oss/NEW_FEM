# Round 5 author-requested edits

Baseline: 0b527bf on arena/adfa7636-new-fem. The author measured **31 pages**
for that baseline. **The revised page count is not measured here.** No TeX
installation or compilation was attempted; page fit, rendered numbering and
compiler warnings remain for the independent compile.

## Per-edit changes and full validation

Each edit was committed separately, followed by `python python/run_all.py`
(without --reuse) and then `python python/check_paper_numbers.py`, sequentially.
The saved summaries for all seven runs have `incremental_regrade=false` and
all 70 checks passing. No suite ran concurrently with a compile. Intended
edits were committed/staged before `git checkout -- .; git clean -fdq` restored
only generated numerical/build drift. Logs are outside the repository.

| Edit | Commit | Files / change | Full suite; number audit |
|---|---|---|---|
| 1 | 97d2d39 | sec/01_introduction.tex; delete table_comparison.tex, its label/input and table-dependent prose; retain the independent gap/novelty discussion | 70/70; 102/102; 0 stale |
| 2 | fc75b6c | sec/01_introduction.tex, sec/07_results.tex, sec/09_conclusions.tex: plain finding sentences instead of bold lead-ins; remove the procedure's bold label | 70/70; 102/102; 0 stale |
| 3 | 219d673 | python/run_paper_figures.py, F1 assets and sec/02_formulation.tex caption: redraw compact specimens, separate labels from outlines, move footer quantities to caption | 70/70; 102/102; 0 stale |
| 4 | f88c941 | sec/05_finite_element.tex: unboxed ten-step enumerate and “Conditioning and cost”; sec/02_formulation.tex: replace “remarks” with “features” | 70/70; 102/102; 0 stale |
| 5 | cd8c4b9 | python/run_paper_figures.py, F9 assets and sec/07_results.tex caption: inset axes in both panels, first 0.35 microseconds, using the existing histories | 70/70; 102/102; 0 stale |
| 6 | 6d41730 | sec/08_limitations.tex: 1216→415 whitespace-delimited source words (~34%); compact observable routes, retain three identification relations, validity band and modeling limits | 70/70; 102/102; 0 stale |
| 7 | final edit-7 commit in git log | main.tex, sec/06_validation.tex, sec/07_results.tex, sec/92_appendixB.tex, table_verification.tex: benchmark/convergence-only Appendix B, delete sec/93_appendixC.tex and its references; update source audits | 70/70; 96/96; 0 stale |

## Figure details

F1 is regenerated through its existing pipeline function, not retouched as an
image. The 6.8×2.7-inch canvas uses wider specimens and no footer. At the
unchanged 170-mm inclusion width, the PDF-box height decreases from **119.1 mm
to 64.0 mm (53.7% of the baseline height)**. Inspected its ~220-dpi preview:
the cuboid and ellipse labels are clear of outlines/electrodes. Caption keeps
L=200 micrometers, thickness h, a1×a2 and the cuboid/ellipse second moments.

F9 uses matplotlib inset axes inside both panels. Each inset plots the same
(t,u,V) arrays as its parent panel, retaining all eight orders, styles and the
legend, with x-limits 0–0.35 microseconds. Insets and the final preview were
inspected at ~220 dpi; the parent curves and legend remain in place. Insets
add no new response data and do not change the computed decrements.

## Printed-material removal and the number audit

Appendix B now contains seven static/frequency/coupling/convergence benchmark
rows and the convergence table cited in Section 6. Removed patch/constant-strain
and internal kernel, L1 and modal-truncation rows, reduction-MAC diagnostics,
and the pencil/solver-precision discussion from that appendix. Underlying
scripts, JSON and all 70 numerical criteria are retained.

Appendix C and its main.tex input are deleted. No active manuscript input or
reference names app:data, tab:ringdown or tab:closedform. Data availability now
points to the accompanying scripts/JSON and the retained material and benchmark
locations. Generated table_closed_form.tex and table_ringdown.tex remain as
unprinted source-archive outputs of the retained scripts; they are not included
in the PDF or counted as manuscript evidence.

`python/check_paper_numbers.py` now recursively expands only main.tex inputs,
ignoring unprinted archive tables. `check_paper_structure.py` uses the same
expansion; `check_float_order.py` tolerates the deliberately removed appendix.
A probe verified that an unprinted table file cannot satisfy the literal audit.

Exactly six audit rows were removed, reducing **102 to 96**:

| Removed printed claim | Literal | Archived source retained |
|---|---|---|
| closed form, e'C^-1 e | 6.3308e-10 | k2_closed_form.json |
| independent, zeta maximum in alpha | 0.179 | independent_checks.json F2 |
| independent, zeta at alpha=0.3 | 0.108 | independent_checks.json F2 |
| independent, flexo x, uniform curvature (scaled) | 3.570415 | independent_checks.json F3 |
| verification table, MAC of mode 5 across the two reductions | 0.99999 | reduction_mac.json |
| verification table, largest overlap between different modes | 2.8e-6 | reduction_mac.json |

All claims still printed elsewhere remain audited, including the 3-D closed
forms in Section 6, the worked curvature value at its stated precision,
convergence order and clamped-mesh comparison. No value or tolerance was changed
to make a deleted claim pass. The numerical gates for the removed diagnostics
continue to run. Stale-token scanning is retained, with zero hits of 23 tokens.

## Integrity and verification limits

- Core solver, material records, full-suite grading code and numerical-check
  scripts are unchanged. Generated numeric drift is discarded after validation.
- references.bib and results/reference_audit.md are byte-identical to baseline.
  No unpublished reference or new bibliographic data was introduced.
- Author, affiliation, CRediT and acknowledgement placeholders are unchanged;
  the CRediT author labels retain their protected formatting. No bold lead-in
  remains in section running text. No “remark” remains in manuscript headings
  or prose. No deleted-table label or literal “Table 1” reference remains.
- a/L<=0.2 remains an assumed operating range, not a validated threshold.
- Source structural check: balanced environments; zero unresolved references
  or citations; all 12 graphics present. Main-text first-citation order agrees.
- Citation coverage remains 61 cited keys out of 68 bibliography entries; the
  same seven uncited entries from Round 4 remain (see citation_coverage.md).
- Historical Round-4 integrity scripts/reports describe that earlier layout;
  their requirement to retain every table is superseded by these explicit
  author-requested deletions. They are not the Round-5 regression gates.
- Revised page count, known frontmatter error and overfull-box counts are
  **not measured**; the author compiles independently.
