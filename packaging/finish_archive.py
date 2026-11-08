"""Finalize ONLY from current successful clean-run evidence; never forge PASS."""
from pathlib import Path
import json,subprocess,shutil,re,platform,sys,hashlib,csv,io,zipfile,collections,email
S=Path(__file__).resolve().parents[1];R=S/'.repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE';W=R/'04_REPRODUCTION/workspace';O=R/'06_VALIDATION/reproduction_test';PY=S/'.repro_work/test-venv/bin/python'
records=json.loads((O/'execution.json').read_text());assert len(records)==5 and all(x['exit_code']==0 for x in records),records
summary=json.loads((W/'results/summary.json').read_text());assert summary['all_pass'] and summary['n_pass']==summary['n_total']==70 and not summary['incremental_regrade']
assert '96/96 claims agree' in (W/'results/paper_number_audit.md').read_text()
subprocess.run([str(PY),'04_REPRODUCTION/compare_outputs.py'],cwd=R,check=True);comparison=json.loads((O/'output_comparison.json').read_text())
for p in (W/'results').rglob('*.json'):
 q=O/'regenerated_results'/p.relative_to(W/'results');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
for p in (W/'results').glob('*.md'):
 q=O/'generated_reports'/p.name;q.parent.mkdir(exist_ok=True);shutil.copy2(p,q)
for f,dst in [('offline-install.log','offline_install.log'),('smoke.log','archive_smoke_tests.log')]:shutil.copy2(S/'.repro_work'/f,O/dst)
import numpy,scipy,matplotlib
(O/'test_environment.json').write_text(json.dumps({'python':platform.python_version(),'implementation':platform.python_implementation(),'numpy':numpy.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'platform':platform.platform(),'machine':platform.machine(),'installation':'fresh venv, --no-index bundled wheelhouse, complete lock','initial_results':'EMPTY, no baseline cache','BLAS_threads':1,'PYTHONHASHSEED':0,'TeX':'NOT AVAILABLE; no compile attempted','MATLAB':'NOT AVAILABLE / NOT EXECUTED','minimum_resources':'NOT DOCUMENTED'},indent=2))
# Library wheel license/source metadata, not guessed identifiers.
wheels=[]
for p in sorted((R/'01_PROGRAM/wheelhouse').glob('*.whl')):
 with zipfile.ZipFile(p) as z:
  name=next(x for x in z.namelist() if x.endswith('.dist-info/METADATA'));m=email.message_from_bytes(z.read(name));wheels.append({'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'name':str(m['Name']),'version':str(m['Version']),'requires_python':str(m['Requires-Python']),'requires_dist':[str(x) for x in m.get_all('Requires-Dist',[])],'license_files':[n for n in z.namelist() if 'license' in n.lower() or 'copying' in n.lower()]})
(R/'09_ARCHIVE_METADATA/wheel_manifest.json').write_text(json.dumps(wheels,indent=2))
pdfs=[]
for p in sorted((R/'02_OVERLEAF/figures').glob('*.pdf')):
 q=W/'Paper_12/figures'/p.name;pdfs.append({'asset':p.name,'baseline_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'regenerated_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'byte_identical':p.read_bytes()==q.read_bytes(),'note':'PDF metadata not a physical tolerance; raster/numerical checks separate'})
(O/'pdf_asset_hash_comparison.json').write_text(json.dumps(pdfs,indent=2))
for f in comparison['figures']:
 if f['status']!='EXACT PIXEL MATCH':
  q=O/'different_figure_previews'/f['figure'];q.parent.mkdir(exist_ok=True);shutil.copy2(W/'Paper_12/figures'/f['figure'],q)
pixels=sum(f['status']=='EXACT PIXEL MATCH' for f in comparison['figures']);status=comparison['program_status'];suite=next(x['elapsed_seconds'] for x in records if x['command'][-1]=='python/run_all.py');runtime=sum(x['elapsed_seconds'] for x in records)
(O/'COMPARISON_INTERPRETATION.md').write_text('''# Comparison interpretation

PASS WITH NUMERICAL DIFFERENCE is not bytewise identity. Every original70 gate
and all96 manuscript claims pass. Numeric differences are listed with exact paths,
values and absolute/relative deltas; no new common tolerance was invented.
verification.runtime_s is timing metadata, not physics. Historical sensitivity
baseline aggregates24 path rows over4 recorded environments; an empty-results
single-stack run emits6 rows. Ordinal list pairings of different environments
are not like-for-like physical-error estimates. Old stacks were retained but
NOT reexecuted. Some optional old plot-display metadata keys may not be emitted;
baseline values remain available and actual plot settings remain in source.
Independent benchmark last-bit frequency differences are graded by unchanged
criteria. All PNG comparisons are explicit; PDF creation-date/font bytes are
not treated as physical errors. No manuscript PDF/TeX compile is represented.
''')
text=f'''# Final package status

**Overall: PARTIAL.** Numerical reproduction completed; manuscript compilation
and a reviewed paper PDF are NOT AVAILABLE. Do not represent static dependency
checks as a successful TeX build or the archive as submission-ready.

| Component | Status | Evidence |
|---|---|---|
| Install/program | {status} | Fresh isolated venv, OFFLINE included wheels + complete lock |
| Numerical workflow | PASS | FULL run_all.py, no --reuse, **70/70 checks pass**, all script exits0 |
| Data | PASS for included numerical data | 33 supplied baseline JSON plus current generated JSON; no experimental raw data |
| Number audit | PASS | **96/96 claims agree**, 0 stale hits of23 |
| Figure regeneration | PASS | 12 PDF/PNG pairs regenerated; **{pixels}/12 exact PNG pixel matches** |
| Manuscript source paths/keys | PASS static only | 12 graphics,61 cited keys,68 bibliography entries, no missing active refs/inputs/cites |
| Manuscript PDF | NOT AVAILABLE | No final paper PDF supplied/generated; page count NOT MEASURED |
| Overleaf/TeX | PARTIAL / NOT COMPILED | Required local class/style supplied, external TeX unavailable; fatal errors cannot be ruled out |
| Regression/smoke tests | PASS | **10/10 unittest tests**; unaltered solver/material/70 gate expressions verified |
| Overall reproduction test | PARTIAL | Numerical {status}; compile component NOT REPRODUCED |

## Actual NEW test, not recovered old evidence

Reconstructed from verified source b1c43a146fb4577f660958e721007a7535c74437.
This is NOT byte-identical recovery of the earlier lost ZIP. Earlier raw logs
are NOT AVAILABLE and are not fabricated. Current execution logs/results are
new, genuinely executed records. Workspace starts EMPTY, demo bootstrap runs
before dependent readers, then full suite and final audits sequentially.
Full suite **{suite:.1f}s**, wrapper total **{runtime:.1f}s**, hardware-dependent.
Exact versions, offline install, script-stage timings, differences and criteria
are retained. Historical alternate stacks/MATLAB were NOT reexecuted.

Portability corrections expose rather than hide cached-history assumptions:
page-budget missing-Git/calibration guard; gradient benchmark reads fresh V2
at original4-decimal precision, not absent prior summary; unused harness-count
summary reads removed from paper audit (same96 active rows/tolerances); report
list shadowing fixed; interpreter docstring example made portable. Exact patch
and preservation audit included. No scientific solver/material/70 gate change.

## Remaining blockers/recommended action

1. Install compatible full TeX Live or use Overleaf, run pdfLaTeX/BibTeX/
   pdfLaTeX/pdfLaTeX, retain logs and manually inspect pages, numbering,
   frontmatter/fonts/boxes. Resolve real errors without changing science.
   Add reviewed manuscript PDF. Static audit cannot certify compile freedom.
2. Supply true author/affiliation/email/journal/CRediT information and confirm
   funding. Existing placeholders/acknowledgements remain unchanged.
3. Verify primary material/benchmark/bibliographic metadata (author notes and
   reference_audit). Original FEM-5 material record/publisher raw data NOT
   AVAILABLE. Density, mu and relaxation remain assumed. No experimental validation.
4. Experimental observations, statistical noise/uncertainty calibration,
   FIM/CRLB/inverse identification and separate full nondimensionalization
   are NOT AVAILABLE / NOT IMPLEMENTED; no substitute data/formula invented.
5. MATLAB/other OS/CPU/Python/older-stack runs are NOT REPRODUCED. Wheels cover
   Linux x86_64 CPython3.11 only. Python/OS/TeX are external prerequisites.
   Project license and earlier pre-import history NOT DOCUMENTED/AVAILABLE;
   clear redistribution/resubmission rights. Third-party notices retained.
6. Existing model limits: linear small strain,2-D plane stress,scalar flexo,
   explicit memory placement and distinct coupling definitions; a/L<=.2 is
   ASSUMED, not validated. Follow KNOWN_LIMITATIONS and comparison interpretation.

Use numerical evidence now, but complete TeX/frontmatter/source/rights review
before claiming submission readiness. All payload SHA-256/ZIP integrity checks
must pass before publication; public asset is the permanent deliverable.
'''
(R/'FINAL_PACKAGE_STATUS.md').write_text(text)
p=R/'09_ARCHIVE_METADATA/run_manifest.json';d=json.loads(p.read_text());d.update(status='Numerical '+status+'; overall PARTIAL (no TeX)',execution=records,full_checks='70/70',paper_claims='96/96',evidence='06_VALIDATION/reproduction_test');p.write_text(json.dumps(d,indent=2))
# Normalize sandbox-only prefixes in historical logs; retain all warnings/errors.
for p in (R/'06_VALIDATION').rglob('*'):
 if p.is_file() and p.suffix in ['.log','.json','.md']:
  t=p.read_text().replace(str(R)+'/','').replace(str(S)+'/','<checkout>/');t=re.sub(r'/tmp/tmp[^/\s\"\']+','<temporary-test-directory>',t);p.write_text(t)
shutil.rmtree(W)
for p in sorted(R.rglob('__pycache__'),key=lambda x:len(x.parts),reverse=True):shutil.rmtree(p)
p=R/'01_PROGRAM/results'
if p.exists() and not list(p.iterdir()):p.rmdir()
subprocess.run([str(PY),'04_REPRODUCTION/audit_archive.py'],cwd=R,check=True)
(R/'09_ARCHIVE_METADATA/final_audit.json').write_text(json.dumps({'overall':'PARTIAL: no manuscript compile/PDF; scientific/rights gaps explicit','numerical':status,'checks':'70/70','number_audit':'96/96;0 stale','regression':'10/10','PNG_exact':pixels,'source_paths_keys':'PASS static','absolute_local_paths':'No detected sandbox-specific absolute file paths','privacy':'No detected private-key/token patterns; not legal/confidentiality certification','single_final':'One canonical02_OVERLEAF tree; baseline and fresh evidence explicitly labeled','excluded':'Old nestedZIP, redundant figure copies, caches/builds/venv/.git/credentials/workspace','important_parameters_results':'33 datasets,1064 field paths,70 criteria,96 expanded claims,12 figures,7 active tables indexed; gaps explicit'},indent=2))
p=R/'09_ARCHIVE_METADATA/package_contents.json';p.write_text('{}');files=[p for p in R.rglob('*') if p.is_file()];counts=collections.Counter(p.relative_to(R).parts[0] for p in files if len(p.relative_to(R).parts)>1);p.write_text(json.dumps({'total_files_including_hash_manifests':len(files)+2,'files_by_folder':dict(sorted(counts.items())),'root_files':['ARCHIVE_README.md','FINAL_PACKAGE_STATUS.md','SHA256SUMS.txt','file_manifest_sha256.csv'],'baseline_JSON':33,'final_figure_PDF':12,'final_figure_PNG':12,'offline_wheels':12},indent=2))
subprocess.run([str(PY),'04_REPRODUCTION/refresh_integrity.py','--zip'],cwd=R,check=True);subprocess.run([str(PY),'04_REPRODUCTION/verify_integrity.py'],cwd=R,check=True)
z=R.parent/(R.name+'.zip')
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None;names=f.namelist();assert len(names)==len(set(names));root=R.name+'/'
 for line in f.read(root+'SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256(f.read(root+n)).hexdigest()==h
 assert not any(any(x in Path(n).parts for x in ['workspace','__pycache__','.git','.venv']) or n.endswith(('.pyc','.aux','.bbl','.blg','.zip')) for n in names)
 print('VERIFIED',z.name,'FILES',len(names),'BYTES',z.stat().st_size,'SHA256',hashlib.sha256(z.read_bytes()).hexdigest())
print((R/'09_ARCHIVE_METADATA/package_contents.json').read_text())
