# Reproduction log (made on this exact archive)

Environment A (pinned, as in `requirements.txt`): Python 3.13, numpy 2.3.5, scipy 1.17.0, matplotlib 3.10.8.
Command: `python3 python/run_all.py` (full run, about 14 minutes).

Result: 68 of 70 checks passed on the first run. The two flagged items were:

| Check | Finding | Resolution |
|---|---|---|
| N2 (list of unverified numbers) | The registry in `python/list_unverified.py` still held two old slope values (-1.52, -0.43). The manuscript quotes -1.53 and -0.44, which match the archived data (finite differences of `demo.json` give -1.5277 and -0.4427). | Fixed: the registry now computes the slopes from `demo.json`. After the fix the script reports 33 entries, 0 stale. |
| N5 (numbers in abstract / captions traced to data) | One untraced literal: "99.98 %" in the Table-5 caption (`sec/07_results.tex`). It is a lower threshold ("exceed 99.98 %"); the underlying minimum is 99.985 % (`results/application_table.json`, `x_displacement_mass_fraction`). | Not a data error; the tracer cannot match a threshold. Left as is. It remains the single FAIL of `run_all.py`. |

Comparison of the fresh results with the archived `results/*.json` (same pinned environment): all
quantities of physical size agree to better than 1e-11 relative (for example k2 = 0.09579543232448805
archived vs 0.09579543232473926 fresh). Differences appear only in round-off-level quantities of size
1e-10 down to 1e-29 (eigenvector overlaps, patch-test residuals, "zero" couplings).

Environment B (newer libraries: numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.2): the same scripts run,
but the noise-floor number `sensitivity.json: spread_h10_pct` changes from 3.4e-6 % (archived and
Environment A) to 5.3e-6 %, which makes check N1 (95/96) report one mismatch against the
manuscript. This is a library-version effect at the 1e-8 relative level. Use the pinned versions to
reproduce the archived numbers.

Missing file: `provenance/FROZEN_LEGACY_K2_SERIES.json` was not in the received archive and was
reconstructed from `legacy_wrong_series` in `results/k2_closed_form.json`.

Not re-run here: the LaTeX build was checked separately (33 pages, 51 references, no undefined
references or citations).
