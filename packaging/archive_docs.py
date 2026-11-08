"""Populate rebuilt archive documentation from inspected source and data."""
from pathlib import Path
import json,ast,csv,io,re,subprocess,hashlib,shutil
S=Path(__file__).resolve().parents[1];R=S/'.repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE'
def w(name,s):
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n')
def dump(name,d):w(name,json.dumps(d,indent=2))
# Actual available source provenance and history; no auth/config copied.
subprocess.run(['git','fetch','origin','arena/adfa7636-new-fem'],cwd=S,check=True,capture_output=True)
tip='b1c43a146fb4577f660958e721007a7535c74437';tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',tip],cwd=S,text=True).splitlines();match=[];diff=[]
for name in tracked:
 p=S/name;b=subprocess.check_output(['git','show',tip+':'+name],cwd=S)
 (match if p.exists() and p.read_bytes()==b else diff).append(name)
assert not diff
w('09_ARCHIVE_METADATA/git_history.tsv',subprocess.check_output(['git','log',tip,'--date=iso-strict','--format=%H%x09%ad%x09%s'],cwd=S,text=True))
w('09_ARCHIVE_METADATA/git_history_changes.txt',subprocess.check_output(['git','log',tip,'--date=iso-strict','--format=%H%nDate: %aI%nSubject: %s','--stat'],cwd=S,text=True))
dump('09_ARCHIVE_METADATA/version_provenance.json',{'source_snapshot_commit':tip,'working_branch':'arena/adfa7636-new-fem','original_files_matched':len(match),'mismatches':diff,'history':'Fetched branch ancestry in git_history.tsv; earlier pre-import scientific history NOT AVAILABLE','packaging_changes':'Five explicitly patched diagnostic/report/docstring files; numerical solver, material source, numerical verification functions and 70 Boolean criteria unchanged','reconstruction':'New archive reconstructed from source; NOT byte-identical recovery of former lost ZIP. Earlier raw package-test logs NOT AVAILABLE; new independent clean-test evidence included.','project_license':'NOT DOCUMENTED'})
# Exact original scientific sources unchanged (except diagnostic/report functions).
checks=[]
for f in ['fem6_core.py','materials.py','run_all.py']:checks.append({'file':f,'byte_identical':(S/'python'/f).read_bytes()==(R/'01_PROGRAM/python'/f).read_bytes()})
a=ast.parse((S/'python/run_verification.py').read_text());b=ast.parse((R/'01_PROGRAM/python/run_verification.py').read_text());A={n.name:ast.dump(n,include_attributes=False) for n in a.body if isinstance(n,ast.FunctionDef)};B={n.name:ast.dump(n,include_attributes=False) for n in b.body if isinstance(n,ast.FunctionDef)}
checks.append({'file':'run_verification.py','changed_functions':[k for k in A if A[k]!=B[k]],'all_numerical_functions_identical':all(A[k]==B[k] for k in A if k!='write_markdown')});assert all(c.get('byte_identical',True) for c in checks) and checks[-1]['all_numerical_functions_identical'];dump('06_VALIDATION/physics_preservation_audit.json',checks)
# Actual source material constants, no invented measurement status.
material={}
for n in ast.walk(ast.parse((R/'01_PROGRAM/python/materials.py').read_text())):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Material' and any(k.arg=='C11' for k in n.keywords):material={k.arg:ast.literal_eval(k.value) for k in n.keywords}
parameters={'material':{'source':'01_PROGRAM/python/materials.py BATIO3','values':material,'units':{'C11':'Pa','C12':'Pa','C13':'Pa','C33':'Pa','C44':'Pa','e31':'C/m^2','e33':'C/m^2','e15':'C/m^2','kappa_r11':'dimensionless','kappa_r33':'dimensionless','rho':'kg/m^3','mu':'C/m'},'EPS0_F_per_m':8.854187817e-12,'provenance':'Supplied source attributes C,e,kappa to Zgonik via unavailable FEM-5 record. Primary source NOT independently verified. rho and scalar mu are assumed.'},'geometry':{'L_m':200e-6,'nominal_h_m':10e-6,'axes':'x length; y thickness; z out of plane','window_a1_m':3e-6,'window_a2_m':1e-6,'theta_rad':0,'operating_range':'a/L<=0.2 ASSUMED, not validated','model':'2-D plane stress (plane strain cross-check); unit out-of-plane measure in area integrals'},'boundary_initial':{'mechanical':'Usually clamped left with higher-order slope; other edges naturally free. Free and clamped-clamped benchmark overrides in sources.','electric':'poling x: left/right electrodes; poling y: bottom/top. Short grounded pair; open one grounded/one floating equipotential with zero charge.','F9_IC':'selected extensional mode normalized to 10 nm tip displacement, zero velocity, zero applied force'},'relaxation':{'law':'Caputo Kelvin-Voigt; separate fractional Zener comparison','F9_tau_s':3e-9,'F9_alphas':[1,.95,.9,.8,.7,.6,.5,.4],'memory_matrix':'K_eff in F9; K_uu compared separately. Do not interchange.'},'numerics':{'mechanical_element':'C1 bicubic BFS, eight mechanical DOFs/node; 32/element','electric_element':'bilinear potential, one DOF/node; 4/element','quadrature':'4x4 Gauss default','mesh':'24x2 F9/orientation; 48x4 production thickness/design; 96x4 and 128x4 witnesses; local overrides in source catalog','F9_modes':8,'F9_steps':4000,'F9_duration':'ten selected-mode periods; dt=10*2*pi/omega/4000','F9_inset_us':[0,.35],'dt_study':'12000/24000/48000 steps over 20 periods, alpha=1, omega*tau=.3','Newmark_beta':.25,'Newmark_gamma':.5,'eigensolver':'diagonally scaled symmetric generalized pencil, dense eigh up to n=2600 else shift-invert eigsh sigma=0 which=LM; mass normalization; some secular calculations use whole spectrum','Newton':'200 iterations, initial omega0*(-.05+1j) or continuation, stop abs(ds)<1e-14*abs(s)','precision':'normally binary64; quoted paper precision is not measured material accuracy','seeds':'No intentional application random draws. Hash seed 0, BLAS threads 1. eigsh v0 not explicitly set; implicit starting-vector behavior not a bitwise seed guarantee'},'sweeps':{'orientation_deg':'0..90 step5, AR=2,3,4,5,7,10; ellipse AR=2 equal M; explicit mirrored solves','design_h_um':[10,7,5,3.5,2.5,1.8,1.3,1],'design_a2_um':[.25,.5,1,2,4,8,16,32],'input_sensitivity':'mu,rho,a2,tau +/-10%; not statistical uncertainty'},'steel_benchmark':{'source':'run_verification.py v2_fem1_benchmark/u_right','L_m':1,'h_m':.2,'E_Pa':2e11,'nu':.3,'rho_kg_m3':7850,'tx_right_Pa':1e6,'left':'clamped','other_edges':'free','domain':'ellipsoid','l_over_L':[.02,.05,.1,.2],'meshes':[[5,1],[10,2],[20,4],[40,8]],'reference_mesh':[60,12]},'absent':{'thermal':'NOT APPLICABLE: no thermal evolution model','nonlinear':'NOT APPLICABLE: linear small strain','pulse':'No paper pulse experiment documented; solver accepts callable loads','FIM_CRLB':'NOT AVAILABLE / NOT IMPLEMENTED; no likelihood/noise model or inverse-identified observations','statistical_uncertainty':'NOT AVAILABLE; perturbation and stack sensitivity are not confidence intervals','full_nondimensionalization':'Separate complete derivation NOT AVAILABLE; existing groups a/L,a2/h,omega*tau,alpha,k²,x retained'},'all_overrides':'source_settings_catalog.json records every assignment/default expression with source line; experiments override defaults','tolerances':'Original 70 expressions in criterion_expressions.json; no new blanket tolerance'}
dump('09_ARCHIVE_METADATA/parameter_manifest.json',parameters)
producer={'verification':'run_verification','flexo_check':'run_flexo_check','material_comparison':'run_material_check','memory_variants':'run_memory_variants','dt_study':'run_dt_study','coupling_check':'run_coupling_check','mode_tracking':'run_mode_tracking','reduction_mac':'run_reduction_mac','application_table':'run_application_table','independent_checks':'run_independent_checks','abstract_audit':'audit_abstract_claims','config_table':'run_config_table','unverified_numbers':'list_unverified','sensitivity':'run_sensitivity','gradient_energy':'check_gradient_energy','coupled_patch':'check_coupled_patch','numerics':'check_numerics','sensitivity_tornado':'sensitivity_tornado','design_map':'run_design_map','k2_closed_form':'derive_k2_closed_form','demo':'run_demos','paper_figures_data':'run_paper_figures','stale_tokens':'check_paper_numbers','coupling_provenance':'coupling_provenance','coupling_provenance_check':'check_coupling_provenance','environment':'run_all','summary':'run_all','run_all_manifest':'run_all','worked_example':'worked_example'}
datasets=[];fields=[]
for p in sorted((R/'03_DATA/results').rglob('*.json')):
 name='run_sensitivity' if p.parent.name=='sensitivity_envs' else producer[p.stem];script=R/'01_PROGRAM/python'/(name+'.py');doc=ast.get_docstring(ast.parse(script.read_text())) or 'NOT DOCUMENTED';schema={}
 def visit(obj,path='$'):
  e=schema.setdefault(path,{'types':set(),'count':0,'min':None,'max':None});e['types'].add(type(obj).__name__);e['count']+=1
  if isinstance(obj,(int,float)) and not isinstance(obj,bool):e['min']=obj if e['min'] is None else min(e['min'],obj);e['max']=obj if e['max'] is None else max(e['max'],obj)
  if isinstance(obj,dict):
   for k,v in obj.items():visit(v,path+'.'+k)
  elif isinstance(obj,list):
   for v in obj:visit(v,path+'[*]')
 visit(json.loads(p.read_text()))
 for key,e in schema.items():
  unit='NOT DOCUMENTED here; consult producer and model SI convention';last=key.split('.')[-1].replace('[*]','')
  for suffix,u in [('_kHz','kHz'),('_um','micrometers'),('_nm','nanometers'),('_deg','degrees'),('_pct','percent'),('_s','seconds')]:
   if last.endswith(suffix):unit=u+' (encoded suffix)'
  if last.startswith('k2') or last in ['alpha','AR','zeta','ratio','delta','a2_over_L']:unit='dimensionless (model definition)'
  fields.append([p.relative_to(R).as_posix(),key,','.join(sorted(e['types'])),e['count'],unit,e['min'],e['max']])
 cmd='python3 python/'+name+'.py'+(' --emit results/sensitivity_envs/'+p.name if p.parent.name=='sensitivity_envs' else '')
 datasets.append({'path':p.relative_to(R).as_posix(),'status':'Supplied generated baseline, NOT experimental raw observations','purpose_from_source':doc[:1200],'producer':script.relative_to(R).as_posix(),'command':cmd,'cwd':'04_REPRODUCTION/workspace','schema_fields':len(schema),'precision':'JSON numbers typically Python/NumPy binary64; manuscript rounds values','historical_stack_status':'NOT REEXECUTED on old environments' if p.parent.name=='sensitivity_envs' else 'New clean-run comparison retained separately','parameters_inputs':'parameter_manifest, source_settings_catalog, producer call expressions and run_manifest order'})
dump('09_ARCHIVE_METADATA/dataset_manifest.json',datasets);buf=io.StringIO();writer=csv.writer(buf);writer.writerow(['dataset','field','types','occurrences','units_or_status','observed_min','observed_max']);writer.writerows(fields);w('03_DATA/data_dictionary_fields.csv',buf.getvalue())
# Actual full run order.
full=[]
for n in ast.parse((R/'01_PROGRAM/python/run_all.py').read_text()).body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FULL_SCRIPTS' for t in n.targets):full=ast.literal_eval(n.value)
extra=['run_demos.py','run_paper_figures.py','make_appendix_tables.py','coupling_provenance.py','make_coupling_table.py','check_coupling_provenance.py','check_final_consistency.py','worked_example.py','check_paper_numbers.py','check_paper_structure.py','check_float_order.py']
dump('09_ARCHIVE_METADATA/run_manifest.json',{'status':'Await current clean-run result; no PASS fabricated','entry':'python3 04_REPRODUCTION/reproduce.py','cwd':'archive root','bootstrap':'run_demos.py generates demo.json before earlier suite readers need it','full_script_order':full+extra,'second_pass':['make_paper_table.py','check_paper_numbers.py','check_float_order.py'],'wrapper_final_audits':['check_paper_numbers.py','check_float_order.py','check_paper_structure.py'],'outputs':'workspace/results and workspace/Paper_12, never silently overwrite baseline','environment':'Python3.11; complete lock; included Linux x86_64 CPython3.11 offline wheels; OMP/BLAS/MKL/NUMEXPR/VECLIB=1, hash=0, Agg','compile_order':['pdflatex main.tex','bibtex main','pdflatex main.tex','pdflatex main.tex'],'compile_cwd':'02_OVERLEAF','TeX':'NOT AVAILABLE / NOT COMPILED','runtime':'Measured in execution.json, original suite approximately14minutes; not a hardware guarantee'})
figs={'F1_geometry':('fig_p1_geometry','schematic; caption geometry'),'F2_convergence':('fig_p11_convergence','on-demand FE mesh convergence'),'F3_fields':('fig_p12_fields','on-demand coupled mode/fields'),'F4_orientation':('fig_orientation','paper_figures_data.json polar/symmetry; polar_sweep'),'F5_design':('fig_p14_design_space','paper_figures_data.json polar'),'F6_damping':('fig_damping','on-demand complex pole/continuation'),'F7_window':('fig_window','on-demand static steel window/size solves'),'F8_thickness':('fig_p7_thickness','demo.json flexo_thickness + coupling_check.json closed_form'),'F9_ringdown':('fig_p6_waterfall','on-demand F9 modal L1 histories; paper_figures_data notes.P6'),'FB1_tracking':('fig_p8_mac','mode_tracking.json'),'FB2_modes':('fig_p4_modeshape','on-demand mode solves'),'F11_designmap':('main/draw','design_map.json; 64 FE combinations')}
fm=[];lines=['# Every manuscript figure — reproducible provenance','','Commands run in prepared workspace AFTER the full workflow. Asset IDs are stable filenames, not compiled figure numbers.','','| Asset (PDF + PNG) | Producer/function | Inputs | Redraw command | Expected/tolerance |','|---|---|---|---|---|']
for p in sorted((R/'02_OVERLEAF/figures').glob('*.pdf')):
 fun,inputs=figs[p.stem];sel=p.stem.split('_')[0];producer_path='01_PROGRAM/python/'+('run_design_map.py' if sel=='F11' else 'run_paper_figures.py');cmd='python3 python/run_design_map.py --replot' if sel=='F11' else 'python3 python/run_paper_figures.py '+sel
 fm.append({'asset':p.relative_to(R).as_posix(),'producer':producer_path,'function':fun,'inputs':inputs,'parameters':'parameter_manifest and source_settings_catalog; exact producer expressions','command':cmd,'cwd':'04_REPRODUCTION/workspace','output':'Paper_12/figures/'+p.name+' and results/figures/paper','expected':'same scientific traces/geometry; original numerical gates; historical pixel tolerance NOT DOCUMENTED, comparison reports exact pixels and differences'})
 lines.append(f'| {p.name} | {producer_path}: {fun} | {inputs} | `{cmd}` | Original 70 gates; no new visual tolerance invented |')
dump('09_ARCHIVE_METADATA/figure_manifest.json',fm);w('07_DOCUMENTATION/FIGURE_PROVENANCE.md','\n'.join(lines))
# Map every major result/gate to actual raw source and acceptance expression.
summary=json.loads((R/'03_DATA/results/summary.json').read_text());expr={x['id']:x for x in json.loads((R/'06_VALIDATION/criterion_expressions.json').read_text())}
groups={'V':('run_verification','verification.json'),'F':('run_flexo_check','flexo_check.json'),'M':('run_material_check','material_comparison.json'),'S':('run_memory_variants','memory_variants.json'),'C':('run_coupling_check','coupling_check.json'),'K':('run_mode_tracking','mode_tracking.json'),'D':('derive_k2_closed_form','k2_closed_form.json'),'I':('run_independent_checks','independent_checks.json'),'G':('run_config_table','config_table.json'),'H':('check_numerics','numerics.json'),'U':('run_sensitivity','sensitivity.json'),'T':('run_demos','demo.json'),'W':('check_gradient_energy','gradient_energy.json')}
special={'V5e':('run_dt_study','dt_study.json'),'P3':('check_coupled_patch','coupled_patch.json'),'Y1':('check_coupled_patch','coupled_patch.json'),'S3':('sensitivity_tornado','sensitivity_tornado.json'),'E1':('run_all','environment.json'),'N3':('check_paper_numbers','stale_tokens.json'),'N4':('check_coupling_provenance','coupling_provenance_check.json'),'N5':('check_final_consistency','final_consistency.md'),'N2':('list_unverified','unverified_numbers.json'),'A1':('run_application_table','application_table.json'),'A2':('audit_abstract_claims','abstract_audit.json'),'P1':('run_paper_figures','figures/paper/*.pdf'),'P2':('run_paper_figures','paper_figures_data.json'),'N1':('check_paper_numbers','paper_number_audit.md')}
results=[];vl=['# Validation criteria — supplied baseline distinguished from new test','','Exact Boolean expressions are preserved in criterion_expressions.json.','','| ID | Quantity | Supplied observation | Existing requirement |','|---|---|---|---|']
for c in summary['checks']:
 a,b=special.get(c['id'],groups.get(c['id'][0],('NOT DOCUMENTED','NOT DOCUMENTED')));results.append({'id':c['id'],'result':c['what'],'producer':'01_PROGRAM/python/'+a+'.py','command':'python3 python/'+a+'.py','cwd':'04_REPRODUCTION/workspace','inputs_parameters':'parameter_manifest/source_settings_catalog; exact call expressions in producer; ordered dependencies in run_manifest','output':'results/'+b,'supplied_observation':c['value'],'criterion':c['criterion'],'Boolean_gate':expr[c['id']]['expression']});vl.append(f"| {c['id']} | {c['what']} | {c['value']} | {c['criterion']} |")
dump('09_ARCHIVE_METADATA/result_provenance.json',results);w('06_VALIDATION/VALIDATION_CRITERIA.md','\n'.join(vl))
claims=[];src=(R/'01_PROGRAM/python/check_paper_numbers.py').read_text()
for n in ast.walk(ast.parse(src)):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='row' and len(n.args)>=5:claims.append({'line':n.lineno,'where':ast.unparse(n.args[0]),'printed':ast.unparse(n.args[1]),'source':ast.unparse(n.args[2]),'expression':ast.get_source_segment(src,n),'note':'94 call expressions expand to 96 runtime rows; same active rows and tolerances'})
dump('09_ARCHIVE_METADATA/paper_claim_manifest.json',claims)
# Read/hashes all entries in excluded old ZIP; never masquerade it as the rebuilt deliverable.
import zipfile
with zipfile.ZipFile(S/'Paper_12.zip') as z:dump('09_ARCHIVE_METADATA/obsolete_zip_inspection.json',[{'entry':n,'bytes':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist() if not n.endswith('/')])
# Required, current human guides. Historical notes remain explicitly historical.
w('ARCHIVE_README.md','''# NEW_FEM complete reproducibility archive

Read FINAL_PACKAGE_STATUS.md FIRST. This is a reconstructed source/data package,
not recovery of the old ZIP bytes and not proof of manuscript compilation.
All available source/data and full provenance are provided; missing information
is explicitly NOT DOCUMENTED / NOT AVAILABLE. No scientific inputs are invented.

01_PROGRAM: Python authority, MATLAB mirror, tests/configuration/offline wheels.
02_OVERLEAF: ONE canonical active manuscript, tables, figures and local class/style.
03_DATA: immutable supplied numerical baseline, auxiliary demo plots, dictionary.
04_REPRODUCTION: workspace preparation, exact workflow, comparison/build/hash tools.
05_DERIVATIONS: existing equations verbatim and historical derivation notes.
06_VALIDATION: supplied evidence separated from current clean isolated test.
07_DOCUMENTATION: current model/numerics/provenance/change/limitations guides;
  history/ contains superseded editorial notes, not competing final papers.
08_FINAL_OUTPUTS: index linking canonical outputs, not duplicate copies.
09_ARCHIVE_METADATA: source/run/parameter/data/result/figure/reference manifests.

Start with 04_REPRODUCTION/REPRODUCE_FROM_SCRATCH.md. The portable prepare tool
reconstructs the original sibling python/, Paper_12/, results/ layout with no
symlinks. Do NOT directly run numerical programs from 01_PROGRAM: they expect
that sibling layout. Empty-results reproduction does not seed baseline data.

Verify before execution: python3 04_REPRODUCTION/verify_integrity.py.
SHA256SUMS hashes all payload including the CSV manifest, except itself.
The CSV omits itself and SHA256SUMS to avoid circular self-hashes.
The old Paper_12.zip and duplicate figures/caches/builds/credentials are omitted.
No project license was supplied; do not infer reuse or resubmission permission.
''')
w('01_PROGRAM/README_PROGRAM.md','''# Program

Authoritative language: Python; tested exact interpreter/versions are recorded
in reproduction_test/test_environment.json. Baseline environment.json is an
older supplied record, not this run. Python3.11, numpy2.4.6, scipy1.17.1 and
matplotlib3.11.2 are pinned; all transitive packages are locked. Offline wheels
cover Linux x86_64 CPython3.11 with compatible manylinux/glibc tags only. Python,
OS and TeX distributions themselves are NOT bundled. Other platforms must
install the lock via network and are NOT TESTED. MATLAB version/toolboxes and
verified execution are NOT DOCUMENTED; the mirror has NOT been executed.

From archive root:
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links 01_PROGRAM/wheelhouse -r 01_PROGRAM/requirements-lock.txt
.venv/bin/python 04_REPRODUCTION/prepare.py
.venv/bin/python 04_REPRODUCTION/reproduce.py
.venv/bin/python 04_REPRODUCTION/compare_outputs.py

The wrapper bootstraps demo.json before run_all.py's early readers, then runs
FULL run_all.py (no --reuse) and final audits sequentially. Exact per-script
order is RUN_ORDER.md/run_manifest.json. Outputs are under workspace/results
and workspace/Paper_12, not silently over the baseline. Runtimes vary; use
actual execution.json and stage timings, not old README estimates.

No new tolerance: all 70 original Boolean expressions are retained. No intended
application RNG draws; hash seed0, BLAS/OMP/MKL/NUMEXPR/VECLIB threads1, Agg.
ARPACK v0 is not explicitly set: no universal bitwise-seed guarantee. Default
binary64, near-canceling coupling can move with stack; quoted digits are not
measured physical precision. K_eff and K_uu memory choices are NOT interchangeable.

Original cached-history/summary assumptions were fixed only in package copies:
length_budget missing calibration/Git guard, fresh V2 instead of stale summary,
dead unused summary reads removed from paper audit, report-list shadowing fixed,
and a nonfunctional absolute interpreter example made portable. Exact patch and
physics-preservation audit included; no solver/material/numerical gate changes.

Git is optional for numerical reproduction; synchronization/reference-network
utilities are optional and were NOT executed. sync_to_overleaf.py can PUSH:
use --dry-run and a remote you control. check_refs.py rewrites its audit.
Never claim older fixed-layout audit assumptions still apply to this manuscript.
''')
w('02_OVERLEAF/README_OVERLEAF.md','''# Independent manuscript project

Upload this directory's CONTENTS to Overleaf; main document main.tex, pdfLaTeX
with BibTeX. Highlights.tex is a submission fragment, not a second main paper.
All active inputs/figures/bibliography are local. elsarticle.cls (3.4c,
2025/01/11) and elsarticle-num.bst are vendored from the pinned real upstream
revision with license/source provenance; their inclusion is NOT a compile test.

Required external TeX environment: compatible full TeX Live with fontenc,
inputenc, graphicx, amsmath, bm, amssymb, amsthm, mathrsfs, mathtools, multirow,
booktabs, siunitx, natbib, float, placeins, hyperref, class dependencies/fonts.
No TeX engine/packages are installed or bundled here. Exact installed TeX
versions are NOT AVAILABLE; cloud Overleaf compilation has NOT been performed.

From this directory:
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex

Status NOT COMPILED. No final manuscript PDF is supplied or generated. Static
paths/labels/citation checks cannot certify fatal-error freedom, frontmatter,
font compatibility, overfull boxes, page count or rendered numbering. Page
count NOT MEASURED; old notes about 31/35 pages are not current evidence.
Author/funding/CRediT placeholders and scientific content were NOT changed to
hide an error. Populate true frontmatter and resolve author-only source risks.
references.bib key existence does not establish DOI accuracy or scientific support.
''')
w('03_DATA/README_DATA.md','''# Data

All supplied JSON are generated numerical/processed baselines, NOT raw laboratory
measurements. No experimental observations, original upstream FEM-5 material
record, publisher raw benchmark data or calibrated noise data were supplied.
33 baseline JSON files include four historical numeric-stack records, which
are retained but NOT reexecuted on those old stacks in this single-stack test.

Dataset status, purpose, producer, command, precision: dataset_manifest.json.
Nested fields/units: DATA_DICTIONARY.md and data_dictionary_fields.csv.
All important interpreted parameters plus exhaustive source defaults/overrides
are in parameter_manifest.json/source_settings_catalog.json. Unknown units
are explicitly NOT DOCUMENTED rather than guessed from magnitudes.

Regenerate from EMPTY results via REPRODUCE_FROM_SCRATCH.md. Fresh outputs are
labeled test evidence; original baselines remain immutable. Complete field/time
arrays are generally not archived because plotting functions held them in
memory; rerun functions (or modify them to export arrays). No missing history
was fabricated. Final figures are ONLY in 02_OVERLEAF/figures. Supplied duplicate
PNGs were identical; some duplicate PDF bytes/metadata differed, and the
manuscript copy is the single canonical asset. Source hashes record exclusions.
''')
w('03_DATA/DATA_DICTIONARY.md',f'''# Data dictionary

Full nested-key dictionary: data_dictionary_fields.csv ({len(fields)} paths,
{len(datasets)} JSON files). $=root, [*]=each list entry. Min/max describe observed
baseline values, NOT admissible input bounds or validated operating limits.
Unknown units are NOT DOCUMENTED; consult source expressions/manuscript.

SI solver conventions: m,s,kg,Pa,C/m²,C/m,F/m; plotting suffixes often encode
µm,nm,kHz,µs. Voigt strain [eps_xx,eps_yy,engineering gamma_xy]. x is length,
y thickness, z out of plane; tensors rotate with poling. Mechanical nodal order
[u,ux,uy,uxy,v,vx,vy,vxy]; electric potential is a separate bilinear nodal field.
Static x/(1+x), modal frequency-ratio coupling and unnormalized x differ.
Read coupling_provenance.json before comparing near-0.56/0.46 quantities.
JSON digits are floating-point storage, NOT experimentally established precision.
No raw experimental, statistical uncertainty, FIM/CRLB or calibrated noise
arrays are available. No missing field/unit was fabricated.
''')
w('04_REPRODUCTION/REPRODUCE_FROM_SCRATCH.md','''# Reproduce from scratch

Extract ZIP retaining its root folder. From that folder, with Python3.11+venv:
python3 04_REPRODUCTION/verify_integrity.py
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links 01_PROGRAM/wheelhouse -r 01_PROGRAM/requirements-lock.txt
.venv/bin/python 04_REPRODUCTION/prepare.py
.venv/bin/python 04_REPRODUCTION/reproduce.py
.venv/bin/python 04_REPRODUCTION/compare_outputs.py

This is the tested offline Linux x86_64 CPython3.11 route. Other platforms need
compatible dependencies/network and are untested. Minimum RAM/disk requirements
were NOT DOCUMENTED; allow working space for a venv, dense matrices and plots.
prepare.py starts with EMPTY results (no supplied cache). --with-baseline is
ONLY for redraw/re-audit, not fresh reproduction. Existing workspace is never
silently deleted: deliberately move/delete it before preparing anew.

Wrapper first computes demo.json because original early suite readers need it,
then runs FULL suite and number/float/structure audits. Stops on nonzero exit.
Original tolerances are not weakened. All logs, exit codes and elapsed times go
to reproduction_test; a new run replaces those evidence files, so copy them if
preservation is needed. Inspect summary.json even if a command returns zero.
Comparison reports all numeric/structural/pixel differences; PDF creation dates
alone are not physics. No common error tolerance was invented.

Compile separately: install full compatible TeX Live or upload 02_OVERLEAF to
Overleaf. Run build_manuscript.sh (or the four documented commands). Do not
compile concurrently with figure generation that writes manuscript assets.
Use canonical 02_OVERLEAF for shipped source or workspace/Paper_12 for fresh
outputs. Inspect every page/log; source checks cannot certify absence of fatal
errors. No TeX compile was performed by this package test.

Modify canonical 01_PROGRAM source/settings, record change in CHANGELOG, prepare
a new workspace and rerun full workflow. Promote ONLY reviewed active tables,
figures and JSON, preserving the old baseline. Do not blindly copy unprinted
legacy tables into the paper. Populate true frontmatter, confirm bibliography,
material/funding/rights, add reviewed manuscript PDF, update status/manifests,
and run refresh_integrity.py. Reproduction is not permission to re-submit.
''')
w('04_REPRODUCTION/RUN_ORDER.md','# Exact execution order\n\nFrom archive root: prepare.py, reproduce.py, compare_outputs.py.\nInside reconstructed workspace, wrapper bootstraps run_demos.py then FULL\nrun_all.py runs these stages:\n\n'+'\n'.join(f'{i+1}. python3 python/{x}' for i,x in enumerate(full+extra))+'''\n
Second pass: make_paper_table.py, check_paper_numbers.py, check_float_order.py.
Wrapper final audits: number audit, float order, structure audit. Then compare.
TeX separately: pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX.
No --reuse in fresh reproduction. Old historical README run times/order do not override this.
''')
w('07_DOCUMENTATION/PROJECT_OVERVIEW.md','''# Project overview

NEW_FEM/FEM-6: fractional-memory piezoelectric–flexoelectric strain-gradient
solids with a rectangular averaging window, C1 Bogner–Fox–Schmit elements.
Python is numerical authority; MATLAB mirror is NOT EXECUTED. Source covers
static/gradient benchmarks, electrical coupling, modes, orientation/window/
thickness sweeps, fractional poles/ringdown and sensitivity. Not an experimentally
identified constitutive record, thermal solver or inverse/FIM pipeline.

All 200 supplied source files were read/inventoried and match fetched snapshot
b1c43a146fb4577f660958e721007a7535c74437. Current local HEAD/index is not used to
invent a scientific source version; exact file hashes and fetched history are
recorded. Earlier pre-import history is NOT AVAILABLE. Historical notes may
conflict with current code; they are not competing final versions.
This ZIP is freshly reconstructed, not the original lost archive bytes. Earlier
raw package-test logs are NOT AVAILABLE. Newly executed evidence is separate.
''')
w('07_DOCUMENTATION/MODEL_DESCRIPTION.md','''# Model description

Authoritative energy/governing/constitutive derivation: sec/02_formulation.tex;
particular/limiting cases: 03_particular_cases and 91_appendixA. Verbatim equations
are indexed in 05_DERIVATIONS. No new scientific equations/parameters are invented.

Small-strain u, potential phi, E=-grad(phi), strain/strain gradient enter elastic,
gradient, piezoelectric, dielectric and scalar flexoelectric enthalpy. Source
factors/signs are authoritative: gradient energy factor1/4 M*C gives stiffness
factor1/2 integral. Cuboid, planar ellipse and 3-D ellipsoid moments differ:
a_i²/3, a_i²/4, a_i²/5. Equal half-width is NOT equal second moment.

BaTiO3 C/e/kappa are attributed to Zgonik through a missing FEM-5 record;
density and mu are assumed. Plane-stress/plane-strain, poling and electrode pair
must be specified together. Mechanical BC include displacement/normal slope or
traction/double traction. Short grounds pair; open grounds one and floats the
other equipotential, zero-net-charge electrode. Condensation gives rank-one
K_oc=K_sc+d*d^T/beta. Modal coupling uses squared-frequency ratios; static
x/(1+x), x=d^T*K_sc^-1*d/beta is a distinct measure. Actual design-map bending
code is modal even where inherited docstring calls both columns mode-free:
this pre-existing wording inconsistency is documented, not silently fixed.

Memory solves M*x''+K*x+tau^alpha*Kd*D_Caputo^alpha*x=f, with Kd explicitly
K_eff or K_uu. They damp differently. F9 is unforced release of selected mode
scaled to10nm tip displacement, zero velocity. For alpha<1 the first-period
decrement conversion is descriptive, not exact exponential damping.
a/L<=0.2 is ASSUMED, not validated. Linear small strain, 2-D plane stress and
scalar flexoelectricity limit applicability. No thermal/nonlinear/FIM/CRLB/
calibrated statistical model is implemented or claimed.
''')
w('07_DOCUMENTATION/NUMERICAL_METHOD.md','''# Numerical method

mesh_rect uses rectangular C1 bicubic BFS displacement with eight mechanical
DOFs/node and bilinear potential with one electric DOF/node: 32+4 per element.
Physical derivative scaling, strain/gradient operators and default4x4 Gauss
quadrature are implemented in fem6_core.assemble/element_matrices. Mechanical
constraints and electric condensation are experiment-specific (see BC source).

modes diagonally scales S=diag(1/sqrt(abs(Kii))), solves generalized symmetric
pencil with dense eigh for n<=2600 else shift-invert eigsh sigma0 whichLM,
then mass-normalizes. Some static free-strip routes use lstsq rcond1e-11;
some coupling secular sums need ALL modes. Precision-sensitive near-canceling
eigenvalue differences must not be replaced by a truncated modal sum.

transient uses mass-normalized modes, projected Kd, full implicit L1 history
b_j=(j+1)^(1-alpha)-j^(1-alpha) with alpha1 special case, Newmark beta1/4,
gamma1/2, fixed step-matrix Cholesky solve. dt/modes depend on experiment;
there is no undocumented universal safe step. Newton pole solve max200,
abs(ds)<1e-14*abs(s), with continuation where required. Polynomial roots for
rational alpha provide an independent algebraic check.

Patch, inertia/symmetry, energy, mesh/time convergence, MAC and modal truncation
remain in original 70 checks. Exact criteria in criterion_expressions.json.
The source catalog records all defaults/overrides as expressions, not invented
runtime values. Existing dimensionless groups a/L,a2/h,omega*tau,alpha,k²,x
are retained; separate full nondimensionalization is NOT AVAILABLE.
''')
w('05_DERIVATIONS/DERIVATION_GUIDE.md','''# Existing derivations and explicit gaps

Governing/constitutive energy and weak statement: 02_formulation, 05_finite_element.
Mechanical/electrode BC: 04_boundary_conditions; IC in figure producers.
Window moments/gradient coefficient and limiting cases: 03_particular_cases,
91_appendixA and source_notes. Worked closed-form/plane-stress/coupling route:
derive_k2_closed_form.py, worked_example.py and their JSON intermediates.
L1/Newmark: fem6_core.py plus manuscript and limiting-case scripts.
Independent beam frequencies, rational-alpha roots and uniform-curvature coupling:
run_independent_checks.py. Exact existing equations are extracted verbatim.

Parameter perturbation: sensitivity_tornado.py +/-10%; numerical-stack
sensitivity: run_sensitivity.py. Neither is statistical uncertainty or FIM.
Full separate nondimensionalization, FIM/CRLB/noise/likelihood/identified
parameters, thermal/nonlinear extensions and original experimental data:
NOT AVAILABLE / NOT IMPLEMENTED. No substitute derivation or result invented.
Historical source notes are preserved but current code/manuscript take precedence.
''')
w('06_VALIDATION/VALIDATION_PROTOCOL.md','''# Validation routes, sources and limits

Exact benchmark quantities/observations/requirements are in VALIDATION_CRITERIA.md
and all70 Boolean expressions in criterion_expressions.json. Actual test results
are regenerated separately; supplied observations are not relabeled new evidence.

FEM-1 static: run_verification.py v2_fem1_benchmark/u_right. Steel rectangle
1x.2m, E2e11Pa, nu.3, rho7850, left clamped, right traction1e6Pa, other edges
free; 20x4, ellipsoid l/L=.2 compared with supplied4.23µm (2% gate). Exact mesh
sweep/refinement in parameter manifest. Supplied bibliography key fem1 DOI
10.1016/j.finel.2026.104681. Metadata/publisher raw data NOT independently
verified/retrieved; original benchmark dataset NOT AVAILABLE.

Euler–Bernnoulli/Timoshenko: independent_checks frequency functions, e=mu=0,
zero gradient, 200x10µm strip, free-edge beam modulus, rho6020, CF betaL1.8751,
CC4.7300, nx48/96/128 ny4. Expected/observed errors in independent_checks.json.
Textbook DOI for these equations NOT DOCUMENTED; do not invent one.
Constitutive coupling: derive_k2_closed_form/run_coupling_check; free/clamped,
2-D stress/strain/3-D reductions distinct. Zgonik attribution via missing FEM-5
record is not primary-source verification. Full C/e/kappa are recorded.

Fractional damping: Newton vs polynomial roots for rational alpha, alpha1 exact
Kelvin–Voigt zeta=omega*tau/2. Uniform-curvature flexoelectric charge/energy:
F3 prescribed quadratic field, x=12mu²/(E_b*h²*kappa33), k²=x/(1+x); exact
independent source derivation and all parameter rows retained. These are
algebraic checks, not experimental BaTiO3 validation.
Patch/gradient/coupled reciprocity/inertia/L1/time/mesh/truncation/MAC checks
retain scripts/data/gates even when no longer printed in Appendix B.

Experimental verification, external original raw datasets, MATLAB execution,
FIM/CRLB/identified noise models and old alternative-stack reruns are
NOT REPRODUCED / NOT AVAILABLE. Numerical-stack sensitivity is not confidence
intervals. See supplied reference_audit and author notes for bibliographic gaps.
''')
w('07_DOCUMENTATION/CHANGELOG.md','''# Changelog

Reconstructed package: inventory/read all200 supplied source files, hash/match
fetched b1c43a1 snapshot, select canonical active manuscript, omit old nested ZIP,
duplicate assets/caches and unprinted generated tables; retain all generators.
Add complete locked/offline dependencies, parameter/data/result/figure manifests,
source/default/equation indices, run order, tests and integrity tools.
Five explicit package-only corrections: missing historical Git/calibration guard;
read fresh verification V2 rather than absent prior summary; remove dead unused
summary reads from paper audit; fix report-list/L1 variable shadowing; replace
nonfunctional absolute interpreter example. Exact patch and original hashes
included. Solver/material/numeric verification functions and70 criteria unchanged.
No scientific source/author placeholders changed to hide TeX errors.

New independent clean-test evidence is recorded; old package/failed-attempt raw
logs are NOT AVAILABLE after the prior lost archive. Earlier conversation reports
are not substituted for raw evidence or claimed bytewise archive recovery.
Available branch history is exported by real Git commands. Earlier pre-import
scientific ancestry is NOT AVAILABLE; historical editorial notes are narratives,
not unverified invented commit ancestry. Current canonical source supersedes them.
''')
w('07_DOCUMENTATION/KNOWN_LIMITATIONS.md','''# Known limitations

No TeX engine/cloud compile or manuscript PDF; source paths cannot certify fatal
error freedom, frontmatter/fonts/overfull boxes/page count. Complete TeX Live is
an external prerequisite. Author/journal/email/CRediT/funding confirmation pending.
Primary-source bibliography/material/benchmark uncertainty retained. rho, mu and
relaxation assumed; FEM-5 original record and publisher raw data NOT AVAILABLE.
a/L<=.2 assumed, not validated; 2-D linear plane stress/scalar flexoelectric law.
Static/modal coupling and K_eff/K_uu memory differ. Design-map inherited wording
calls bending mode-free but actual code is modal; documented inconsistency.
No experimental calibration, statistical uncertainty, FIM/CRLB, thermal/nonlinear
solver or separate complete nondimensionalization. Never fabricated to fill gaps.
Thin-strip differences of eigenvalues are stack-sensitive; quoted digits not
physical measurement accuracy. eigsh has no explicit v0 seed guarantee.
MATLAB and alternative OS/Python/CPU stacks are NOT REPRODUCED; wheels only Linux
x86_64 CPython3.11. No interpreter/OS/TeX bundled. Project license NOT DOCUMENTED.
Full field histories may require rerunning functions; not falsely supplied.
This reconstructed archive is not byte-identical recovery of former ZIP; old
raw test logs unavailable. Current test logs are genuine new executions.
''')
w('07_DOCUMENTATION/RESULT_PROVENANCE.md','''# Result provenance

result_provenance.json maps every70 acceptance criterion: script → source inputs/
parameter/default catalog → exact workspace command → output → supplied expected
observation → unchanged Boolean tolerance. paper_claim_manifest maps each source
claim expression; loops expand to96 active rows. Every figure and active table
has a separate producer/source index. Data dictionary covers every33 baseline JSON.
Current test results/comparison are separate from supplied baselines and from
unavailable raw experimental data. No new uncertainty bound/DOI is invented.
''')
tablemap={'table_application.tex':'make_paper_table.py application_table → application_table.json','table_convergence.tex':'make_appendix_tables.py table_convergence → fresh extensional FE solves at12x2/24x2/36x2/48x4','table_thickness.tex':'make_appendix_tables.py table_thickness → demo.json flexo_thickness','table_params.tex':'hand-curated; materials.py and experiment inputs (assumed vs sourced distinguished)','table_memory.tex':'hand-curated; memory_variants.json, dt_study and paper number audit','table_verification.tex':'hand-curated seven-row selection from verification/closed-form/independent-check JSON','table_worked.tex':'hand-curated worked values; worked_example.py/JSON and paper audit'}
w('07_DOCUMENTATION/TABLE_PROVENANCE.md','# Active table provenance\n\nHand-curated TeX is not falsely called automatically generated. Exact numeric\nsource/precision is validated by the96-claim audit; other legacy table files are\nunprinted and regenerated only as archive outputs.\n\n'+'\n'.join('- '+p.name+': '+tablemap.get(p.name,'NOT DOCUMENTED') for p in sorted((R/'02_OVERLEAF').glob('table_*.tex'))))
w('08_FINAL_OUTPUTS/FINAL_OUTPUT_INDEX.md','''# Single canonical final-output index

Manuscript source, seven active tables and twelve final PDF/PNG figure pairs:
02_OVERLEAF (only one canonical copy). Manuscript PDF NOT AVAILABLE / NOT COMPILED.
Baseline numerical outputs: 03_DATA/results. Supplied validation reports:
06_VALIDATION/supplied_results, explicitly historical. New execution/result/
comparison evidence: 06_VALIDATION/reproduction_test. Source assets and archive
hashes do not substitute for a reviewed compiled paper or scientific clearance.
''')
w('09_ARCHIVE_METADATA/README_METADATA.md','''# Metadata/integrity

Inventory records original hashes/inclusion decisions for every200 source files.
Git exports omit personal author/committer email fields; retain hashes/dates/
subjects/statistics. Version provenance distinguishes remote snapshot/local
index and newly reconstructed package. Exact five-file portability patch and
physics-preservation audit expose changes without altering numeric thresholds.
Source catalog records ALL assignments/defaults as expressions, not invented
runtime values. Parameter/run/dataset/result/claim/figure/reference manifests
are explicit; unknowns remain NOT DOCUMENTED/NOT AVAILABLE.
SHA256SUMS covers all payload plus CSV; cannot self-hash. CSV omits itself and
SHA256SUMS to avoid circular hashes. Third-party notices retained. Project license
NOT DOCUMENTED; hashes are integrity, not permission/scientific correctness.
''')
w('09_ARCHIVE_METADATA/licenses/README_LICENSES.md','''# Rights

Project-specific code/data/manuscript license NOT DOCUMENTED / NOT AVAILABLE.
Public repository/archive access is not itself a license. Confirm rights before
redistribution/adaptation/resubmission. Upstream elsarticle class/style dtx/ins,
README/license and per-file notices preserved with exact commit/blob provenance;
class files identify LPPL. Upstream LICENSE is not a project license grant.
Included wheels carry their own embedded dist-info licenses/notices; unmodified
runtime dependencies for tested platform. No OS/interpreter/TeX is bundled.
''')
w('01_PROGRAM/matlab/README_MATLAB.md','''# MATLAB mirror — NOT EXECUTED

MATLAB release/toolboxes/minimum version and a tested invocation are NOT DOCUMENTED.
MATLAB NOT AVAILABLE. Python is the documented authority. Inspect mirror entry/
self-tests in your licensed environment before claiming equivalence; record
version, toolbox dependencies, result and discrepancies. No MATLAB validation
has been fabricated or relabeled as reproduced.
''')
w('06_VALIDATION/README_VALIDATION.md','''# Evidence hierarchy

supplied_results: source-snapshot reports, may contain superseded counts/layout.
reproduction_test: actual NEW isolated offline test, empty results, no --reuse.
Earlier lost archive raw logs are NOT AVAILABLE and are not reconstructed as
fake execution evidence. Historical failed dependencies are described by exact
portability patch, regression tests and reconstruction note, not forged logs.
criteria/protocol: existing acceptance conditions/source attribution limits.
manuscript_dependency_audit/archive_static_audit: file/syntax/path/key checks,
NOT TeX compilation, primary reference verification or experimental validation.
Full current test status must come from actual exit records/summary, not notes.
''')
w('09_ARCHIVE_METADATA/RECONSTRUCTION_NOTE.md','''# Reconstruction, not bytewise recovery

The previously presented ZIP was not retained in this sandbox and had never
been uploaded to GitHub. This package is reconstructed from the verified source
snapshot. Old 328-file counts, ZIP size/hash and old raw execution logs are NOT
claimed as current artifacts. All new counts/hashes/timings/results come from
this build. Prior known diagnostic bugs are explicitly patched/tested. A fresh
full numerical run and archive audit must finish before release publication.
The user authorized publication to GitHub Release, avoiding another ephemeral link.
''')
# Read bibliography metadata without claiming publisher verification.
s=(R/'02_OVERLEAF/references.bib').read_text();ms=list(re.finditer(r'^@(\w+)\s*\{\s*([^,]+),',s,re.M));refs=[]
for i,m in enumerate(ms):
 block=s[m.start():ms[i+1].start() if i+1<len(ms) else len(s)];doi=re.search(r'\bdoi\s*=\s*\{([^}]+)\}',block,re.I);refs.append({'key':m.group(2),'doi_as_supplied':doi.group(1) if doi else 'NOT DOCUMENTED','status':'Supplied only; primary metadata NOT independently verified; see reference audit/author notes'})
dump('09_ARCHIVE_METADATA/reference_manifest.json',refs)
# Checkout packaging builders remain in repository; archive rebuild uses included refresh_integrity.py.
w('FINAL_PACKAGE_STATUS.md','# Status\n\nPARTIAL; clean test still in progress. Manuscript NOT COMPILED; no paper PDF. Do not infer PASS until final evidence is saved.')
print('Documentation:',len(datasets),'datasets,',len(fields),'dictionary fields,',len(fm),'figures,',len(results),'criteria,',len(refs),'references')
