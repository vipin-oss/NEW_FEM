# Rebuild the published reproducibility package

Scientific input snapshot: `b1c43a146fb4577f660958e721007a7535c74437`.
This is a reconstructed archive, not a claim to recover the previous lost ZIP's
bytes or unavailable raw logs. The new full numerical test and hashes are real.
Original scientific working files are not edited by these builders; five
explicit package-only diagnostic/report fixes are recorded in the ZIP.

Use a fresh `.repro_work` output directory (move any previous one deliberately).
From this repository root, on the tested Linux x86_64 CPython 3.11 platform:

```sh
printf '\n.repro_work/\n' >> .git/info/exclude
python3 -m venv .repro_work/venv
.repro_work/venv/bin/pip install numpy==2.4.6 scipy==1.17.1 matplotlib==3.11.2
.repro_work/venv/bin/pip freeze > .repro_work/requirements-lock.txt
.repro_work/venv/bin/pip download -r .repro_work/requirements-lock.txt -d .repro_work/wheelhouse
python3 packaging/build_archive.py
python3 packaging/archive_docs.py
python3 packaging/archive_tools.py
python3 -m venv .repro_work/test-venv
.repro_work/test-venv/bin/pip install --no-index --find-links .repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE/01_PROGRAM/wheelhouse -r .repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE/01_PROGRAM/requirements-lock.txt > .repro_work/offline-install.log 2>&1
.repro_work/test-venv/bin/python -m unittest discover -s .repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE/01_PROGRAM/tests -v > .repro_work/smoke.log 2>&1
.repro_work/test-venv/bin/python .repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE/04_REPRODUCTION/prepare.py
.repro_work/test-venv/bin/python .repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE/04_REPRODUCTION/reproduce.py
.repro_work/test-venv/bin/python packaging/finish_archive.py
```

Do not run two numerical workflows or compile concurrently. The finalizer
refuses to claim PASS unless the current full run exits zero with all 70 gates
and 96 printed-number claims passing. It preserves the actual fresh results,
compares outputs, checks all hashes, excludes caches/build/workspace, then creates
one ZIP. No TeX is installed or compiled; package status remains PARTIAL.

`archive_docs.py` retrieves/verifies the source commit and upstream class/style
using GitHub. Initial dependency download needs PyPI. The FINISHED ZIP includes
runtime wheels for the tested platform and its numerical reproduction is offline.
The ZIP contains separate portable `04_REPRODUCTION` tools; these checkout-only
packaging builders are not its numerical entry point.

Publication: GitHub binary-asset upload endpoint was unavailable in this sandbox.
The requested ZIP is therefore explicitly stored on the session branch under
`reproducibility/` (below GitHub's 100 MiB per-file hard limit), with SHA-256 and a
permanent tagged raw download link. The release notes link to that same file.
No virtual environment, cached work tree, or old nested ZIP is newly committed.
