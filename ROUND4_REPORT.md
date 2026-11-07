# Round 4 final read-through

Baseline: e00aaba on arena/adfa7636-new-fem. The author's independent baseline
compile reports 31 pages, zero undefined references, two overfull boxes, and
the known frontmatter error. No TeX installation or compile is attempted here.
Final page count and compiler warnings must be checked by the author's compile.

All task gates run sequentially: `python python/run_all.py --reuse`, then
`python python/check_paper_numbers.py`. The existing cache validates against the
unchanged numerical-source digest; all 70 checks are regraded, with the prose,
structure and number checks rerun. This is not seven fresh numerical solves.
Source edits are staged before `git checkout -- .; git clean -fdq`, so cleanup
removes generated drift without erasing edits. Gate logs are outside the repo.

## Task 1 — ordered paragraph read-through

Read Section 3, all seven subsections of Section 7, Appendix A and Appendix C
in the requested order, including captions, displayed equations and table inputs.
- `sec/03_particular_cases.tex`: distinguish turning off gradient stiffness
  from suppressing flexoelectricity; do not call a retained-gradient theory
  classical; distinguish modal mass from the window tensor.
- `sec/07_results.tex`: define AR as the window ratio a1/a2 (confirmed against
  run_demos.py), not the strip ratio; name the plotted quantities explicitly;
  distinguish stiffness used in a coupling measure from memory placement.
- Same file: correct the dimensional pole-ratio notation to -Re(s)/|s|,
  matching the existing plotting implementation; correct the ellipsoid and
  decrement cross-references; identify application-table couplings as modal. The final task-7
  source cross-check distinguishes the modal design-map numerator from its
  mode-free denominator; an interim relabeling in task 1 was reverted.
  No JSON value, numerical claim or constitutive law is changed.
- `sec/91_appendixA.tex`: define window measure and characteristic-length
  notation; call the ellipse integral an axial rather than polar moment.
- `sec/93_appendixC.tex`: explain the two tables and the fractional early-time
  decrement, and remove the inaccurate count of finite-element rows.
- Figures/tables in the reviewed sections are introduced before their source
  environments and discussed; local equations are explained or referenced.
  Physical explanations were retained rather than padded with repeated lead-ins.

Gates: **70/70 PASS; 102/102, zero stale hits** (task1 logs).

## Task 2 — candidate overflow fixes (compile confirmation needed)

- `sec/03_particular_cases.tex`, eq:limitM: split the four-term enthalpy
  across two aligned rows, with the same equation number and all terms intact.
- `sec/91_appendixA.tex`, eq:Mrot: split the three rotated components onto
  three aligned rows, keeping the single equation number.
No font size, figure size or page geometry was reduced. These are source-level
fixes to long displays, not identified compiler-log sites: the two actual
overfull-box locations were not supplied. Their elimination and final page
count cannot be certified until the independent compile. Final source line
ranges are listed in the delivery section.

Gates: **70/70 PASS; 102/102, zero stale hits** (task2 logs).

## Task 3 — figure inspection and presentation

Opened all twelve PNG previews at their native ~220 dpi, including a second
inspection after redrawing. Included PDFs remain vector figures at the paper's
170-mm single-column text width (F5 at 0.86 of that width). F10 is absent from
the supplied set; F1–F9, F11, FB1 and FB2 are the twelve included graphics.

`python/run_paper_figures.py` and both `Paper_12/figures/` and
`results/figures/paper/` copies were updated for:
- F2: fewer labeled logarithmic x ticks, eliminating crowded exponent labels.
- F3: larger scale text and labeled black contours, including signed
  displacement contours so hue is not the only sign/level cue.
- F4: distinct styles/markers, larger legend/contour text, more vertical
  spacing and sufficient polar radius to avoid clipping the AR=10 curve.
- F5: distinct styles/markers and an outside legend; label panel (b) as AR=2,
  the ratio actually used by the existing data producer, not “any aspect ratio.”
- F6: distinct tau styles/markers with a numeric legend, not hue alone;
  larger contour labels. Removed crowded in-panel annotations.
- FB1: keep MAC labels inside the panel; increase manuscript inclusion width
  from 0.72 text width to full width for legibility, without shrinking data.
- FB2: separate the inset and surface axes; replace the erroneous, crowded
  magnification ticks with displacement directly in nm. Same solved field,
  amplitude and potential; the arbitrary 3-D display scaling is not new physics.

`sec/06_validation.tex` and `sec/07_results.tex`: expanded parameter information
in captions; corrected F4's (c,d) panel order and aligned-AR=2 normalization;
corrected F5's anisotropy description. Unchanged images: F1, F7, F8, F9, F11.
Their series use shapes/styles, or quantitative maps use monotone luminance
with numerical colorbars/contours, not a hue-only categorical key. F1 identifies
electrodes/windows with text and geometry. F11 retains its assumed-range label.
No numeric JSON or solver source was changed. The redraw uses existing sweeps
or the existing deterministic field solver; final page fit still needs compile.
Gates: **70/70 PASS; 102/102, zero stale hits** (task3 logs).

## Task 4 — abstract

`Paper_12/main.tex`: retained one narrative paragraph, condensed the opening
model/verification description and retained “The main findings reveal” with
all existing quantitative findings. Replaced the archive-focused ending with
practical uses (electrode selection, window/thickness studies, ring-down
interpretation) and the conditional nature of the predictions. The assumed
operating-range statement was not changed. Physical line count depends on TeX.
`audit_abstract_claims.py` rerun: full numeric-token coverage, no new numeric
token; the existing 3 independently reproduced claims / 11 JSON-traceable
claims / 5 inputs distinction is retained. The audit does not turn the eleven
solver-dependent claims into independent experiments or analytical validations.
Gates: **70/70 PASS; 102/102, zero stale hits** (task4 logs).

## Task 5 — conclusions

`sec/09_conclusions.tex`: added a short model summary; combined window shape
and orientation into one finding to give **six bulleted findings**. Retained
all numerical findings, including the mesh convergence result. Condensed the
closing design/use/limitations discussion, preserving the electrode comparison
and 2.8% kinematic limitation. No change to the assumed operating range.
Gates: **70/70 PASS; 102/102, zero stale hits** (task5 logs).

## Task 6 — citation coverage

Added `Paper_12/check_citation_coverage.py`, a read-only bibliography-key check
against main.tex and recursively reached input files, excluding comments.
Its report is `results/citation_coverage.md`. It detects uncited entries,
undefined citation keys and duplicate bibliography keys; this is not a
publisher-record or claim-support audit. The audit found **68 entries, 61 distinct cited keys, 65 citation commands**,
zero undefined keys and zero duplicates. **Seven uncited entries** are retained
and listed, without inventing citations or changing reference data:
`AltanAifantis1997`, `Jiang2023`, `Love1927`, `PhungVan2024AMM127`,
`PhungVan2024AMM128`, `Schwartz2012EABE36`, `ZhangRen2023EWC39`.
The standalone coverage checker intentionally exits 1 while uncited entries
remain; the requested numerical and structural gates still pass.
`results/reference_audit.md` was neither run nor rewritten.
Gates: **70/70 PASS; 102/102, zero stale hits** (task6 logs).

## Task 7 — numerical and protected-content integrity

Added `Paper_12/check_round4_integrity.py` and `results/round4_integrity.md`.
Against e00aaba it verifies all **33 archived JSON files**, all **13 input
tables**, material/solver/map-producer code, the 102-number audit, bibliography,
reference_audit.md, frontmatter and author declarations/acknowledgement are
byte-identical; all original abstract/conclusion numeric literals and
assumed-range clauses remain. No verified number required a trace-through edit.

The final source-to-producer comparison checks executable expressions rather
than docstrings: `run_design_map.flexo_k2` calls `modal_k2`, while the denominator
uses `static_k2`. Sec. 7.5 now states that distinction explicitly, undoing an
interim task-1 mislabeling. F6's caption names 6.73 MHz as f0, with omega0=2 pi f0,
matching the plotting code's angular-frequency conversion without changing
the physical frequency. Appendix A distinguishes the local one-scale squared
length L from the global strip length. The pole-ratio correction in task 1
matches the unchanged numerical implementation, not a change in physical law.

Gates: **70/70 PASS; 102/102, zero stale hits** (task7 logs).

## Delivery, commits and verification limits

| Task | Commit | Gates |
|---|---|---|
| 1 ordered read-through | `4f2cb1e` | 70/70; 102/102; 0 stale |
| 2 candidate overflow fixes | `adad879` | 70/70; 102/102; 0 stale |
| 3 figures and captions | `d8107bd` | 70/70; 102/102; 0 stale |
| 4 abstract | `e7f84bb` | 70/70; 102/102; 0 stale |
| 5 conclusions | `bb60987` | 70/70; 102/102; 0 stale |
| 6 citation coverage | `c8aef53` | 70/70; 102/102; 0 stale |
| 7 integrity and final report | final delivery HEAD | 70/70; 102/102; 0 stale |

Candidate overflow source ranges: `sec/03_particular_cases.tex:24–32`
(eq:limitM) and `sec/91_appendixA.tex:72–79` (eq:Mrot). These displays were
broken across rows; they are **not confirmed to be the compiler's two reported
sites**, since no log locations were provided. The author must verify the
remaining box count, page count and actual page-level float/heading layout.
Figure and caption changes may affect pagination. Baseline 31 pages is the
author's measured count for e00aaba, not a measurement of this revision.
No TeX installation, compile or placeholder substitution was attempted.

Seven uncited bibliography entries remain as explicitly listed in Task 6 and
citation_coverage.md; no citation was invented to hide them. F10 was not
supplied. The revision does not claim external validation of assumed inputs,
reference metadata, or each constitutive interpretation simply because the
numerical regression gates pass. Final branch: `arena/adfa7636-new-fem` only.
