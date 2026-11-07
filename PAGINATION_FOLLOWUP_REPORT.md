# Round 4 pagination follow-up

Baseline: 195e228 on arena/adfa7636-new-fem. The independent baseline compile
reported 33 pages, zero undefined references and two overfull boxes (one in
Acknowledgements, one 1.9-pt output box). No TeX installation/compile attempted.

## Abstract

`Paper_12/main.tex`: explicitly say “reducing the thickness of a 200-micrometer-long
strip from 10 micrometers to 1 micrometer.” Make the assumed-range statement
and the assumed-input statement separate sentences. Every original numeric
literal in the abstract is retained; the assumption itself is unchanged.

## Compact figures, without removing verified content

`python/run_paper_figures.py`: canvas heights changed F4 6.1→5.2 inches,
F5 3.3→2.85 inches, F6 3.3→2.9 inches and FB2 3.6→2.9 inches. Canvas widths
and font sizes are unchanged. FB2's axes/inset were repositioned to use the
shorter canvas. Existing categorical markers, line styles, labeled contours
and all data remain. Reopened all four changed PNGs at ~220 dpi and checked
labels, legends and separation. No graph panel or equation was deleted.

`sec/07_results.tex`: FB1 inclusion width changed from 1.00 to 0.90 text width
(170→153 mm), still wider than its pre-Round-4 0.72 width; fonts scale with
this inclusion, with the plotted 8.5-point annotations about 8.5 points at
153 mm (using the tight-cropped PDF width). Other inclusion widths remain unchanged. The FB1 asset was not redrawn.

Actual PDF bounding boxes and the resulting inclusion dimensions are below.
Saved crop boxes differ from nominal Matplotlib canvas sizes because of tight
bounding-box export. Manuscript dimensions are geometric measurements, not a
measurement of page count or float placement.

| Figure | Previous PDF box (in) | New PDF box (in) | Previous inclusion W × H (mm) | New inclusion W × H (mm) |
|---|---|---|---|---|
| F4_orientation | 7.06 × 6.25 | 7.04 × 5.48 | 170.0 × 150.5 | 170.0 × 132.1 |
| F5_design | 6.40 × 3.16 | 6.40 × 2.82 | 146.2 × 72.3 | 146.2 × 64.4 |
| F6_damping | 7.09 × 3.16 | 7.08 × 2.80 | 170.0 × 75.7 | 170.0 × 67.2 |
| FB1_tracking | 6.01 × 2.82 | 6.01 × 2.82 | 170.0 × 79.8 | 153.0 × 71.9 |
| FB2_modes | 6.37 × 3.40 | 6.37 × 2.92 | 170.0 × 90.6 | 170.0 × 77.9 |

Total reduction in these included figure heights: **55.5 mm**, before
caption/float effects. No page geometry, body font or line spacing was changed.
The **<=32-page target remains to be confirmed by the author's compile**;
33 pages describes the supplied baseline, not this revision.

Only redundant Round-4 prose was trimmed: the extra archive-focused abstract
ending, caption descriptions duplicated by the legend or immediately preceding
text (F3/F4/F8/FB1), and repeated Appendix-C table explanations. Necessary
parameter information remains in the text and referenced input table.

## Validation, run sequentially

1. `python python/run_all.py` — **FULL run**, no `--reuse`: **70/70 PASS**.
   Full suite plus subsequent audit took approximately 13 minutes. The saved
   summary has `incremental_regrade=false` and the numerical producer scripts
   were executed, not simply regraded from cache.
2. `python python/check_paper_numbers.py` — **102/102 agree**, **zero stale hits**
   across 23 forbidden tokens.

After validation, restored generated JSON/figure drift while retaining staged
source changes and intended redraws. Numeric archives, verified input tables,
reference metadata, protected author content and reference_audit.md remain
unchanged. Full-run logs are outside the repository; this report records their
results. No changes were made to the protected Acknowledgements to address its
overfull box. The output-box warning may improve with shorter figures, but
neither warning's elimination is certified without the independent compile.
