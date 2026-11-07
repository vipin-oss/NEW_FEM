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
  decrement cross-references; identify application-table couplings as modal,
  and design-map couplings as mode-free, matching their producer scripts.
  No JSON value, numerical claim or constitutive law is changed.
- `sec/91_appendixA.tex`: define window measure and characteristic-length
  notation; call the ellipse integral an axial rather than polar moment.
- `sec/93_appendixC.tex`: explain the two tables and the fractional early-time
  decrement, and remove the inaccurate count of finite-element rows.
- Figures/tables in the reviewed sections are introduced before their source
  environments and discussed; local equations are explained or referenced.
  Physical explanations were retained rather than padded with repeated lead-ins.

Gates: **70/70 PASS; 102/102, zero stale hits** (task1 logs).
