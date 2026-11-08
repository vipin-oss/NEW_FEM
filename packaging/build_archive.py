"""Build a portable scientific archive from the original NEW_FEM checkout.
Run with Python >=3.11; scientific reproduction is separate and must complete
before finish_archive.py publishes any PASS claims. No TeX installation.
"""
from pathlib import Path
import json,re,shutil,hashlib,ast,subprocess,sys,urllib.request,base64,difflib,csv,io
SOURCE=Path(__file__).resolve().parents[1]
WORK=SOURCE/'.repro_work'; R=WORK/'NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE'
D=['01_PROGRAM','02_OVERLEAF','03_DATA','04_REPRODUCTION','05_DERIVATIONS','06_VALIDATION','07_DOCUMENTATION','08_FINAL_OUTPUTS','09_ARCHIVE_METADATA']
for d in D:(R/d).mkdir(parents=True,exist_ok=True)
def write(name,s):
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n')
def dump(name,o):write(name,json.dumps(o,indent=2))
def copy(p,name):
 q=R/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
active=set()
def expand(name):
 active.add(name);text=re.sub(r'(?<!\\)%[^\n]*','',(SOURCE/'Paper_12'/name).read_text())
 for n in re.findall(r'\\(?:input|include)\{([^}]+)\}',text):
  n=n if Path(n).suffix else n+'.tex'
  if n not in active:expand(n)
expand('main.tex');active.update(['references.bib','Highlights.tex'])
selection=[]
for p in sorted(SOURCE.rglob('*')):
 rel=p.relative_to(SOURCE)
 if not p.is_file() or any(x in rel.parts for x in ['.git','.repro_work','__pycache__','packaging','reproducibility']):continue
 s=rel.as_posix();b=p.read_bytes();target=None;reason=''
 if s.startswith(('python/','matlab/')):target='01_PROGRAM/'+s;reason='Scientific programs, all utilities, or unexecuted MATLAB mirror'
 elif s.startswith('docs/'):target='05_DERIVATIONS/source_notes/'+p.name;reason='Supplied historical derivation/audit notes; current manuscript/code take precedence'
 elif s.startswith('Paper_12/figures/'):target='02_OVERLEAF/'+s[len('Paper_12/'):];reason='Canonical manuscript figure'
 elif s.startswith('Paper_12/'):
  local=s[len('Paper_12/'):]
  if local in active:target='02_OVERLEAF/'+local;reason='Active manuscript dependency or highlights'
  elif p.suffix=='.py':target='01_PROGRAM/manuscript_tools/'+p.name;reason='Manuscript auditing utility'
  elif p.suffix=='.md':target='07_DOCUMENTATION/history/'+s;reason='Supplied historical editorial notes, NOT current build instructions'
  else:reason='Inactive generated table; generator and numeric inputs retained'
 elif s.startswith('results/figures/paper/'):
  canonical=SOURCE/'Paper_12/figures'/p.name
  assert canonical.exists()
  if p.suffix=='.png':assert b==canonical.read_bytes()
  reason='Duplicate figure role; canonical manuscript copy selected. Some PDF metadata bytes differ; PNGs identical.'
 elif s.startswith('results/'):
  if p.suffix=='.json' or '/figures/' in s:target='03_DATA/'+s;reason='Supplied numerical baseline/stack records or auxiliary demo preview'
  elif p.suffix=='.md':target='06_VALIDATION/supplied_results/'+p.name;reason='Supplied audit evidence, not a newly executed test'
  else:reason='Superseded unprinted generated TeX output'
 elif p.suffix=='.md':target='07_DOCUMENTATION/history/'+s;reason='Historical supplied project narrative'
 elif s=='.gitignore':target='01_PROGRAM/source.gitignore';reason='Original configuration'
 elif s=='Paper_12.zip':reason='Obsolete nested deliverable; excluded to avoid competing final manuscript'
 else:reason='Not relevant to scientific reproduction'
 if target:copy(p,target)
 # Reading every byte is part of the inventory; AST parse source/config text.
 kind='binary'
 try:
  text=b.decode();kind='text'
  if p.suffix=='.py':ast.parse(text)
 except UnicodeDecodeError:pass
 selection.append({'path':s,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'kind':kind,'decision':'INCLUDE' if target else 'EXCLUDE','target':target,'reason':reason})
dump('09_ARCHIVE_METADATA/source_inventory_and_selection.json',selection)
# Only these diagnostic/report/docstring corrections; never modify physics/gates.
p=R/'01_PROGRAM/python/run_sensitivity.py';p.write_text(p.read_text().replace('/tmp/vA/bin/python python/run_sensitivity.py --emit results/sensitivity_envs/a.json','python3 python/run_sensitivity.py --emit results/sensitivity_envs/a.json'))
p=R/'01_PROGRAM/python/length_budget.py';s=p.read_text();old='''        r = subprocess.run(["git", "show", "%s:Paper_12/%s" % (rev, rel)],
                           cwd=ROOT, capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else ""''';new='''        try:
            r = subprocess.run(["git", "show", "%s:Paper_12/%s" % (rev, rel)],
                               cwd=ROOT, capture_output=True, text=True)
        except FileNotFoundError:
            return ""
        return r.stdout if r.returncode == 0 else ""''';assert old in s;s=s.replace(old,new).replace('    old = measure(rev) if rev else None\n','''    old = measure(rev) if rev else None
    calibration_missing = old is not None and total(old) <= 0
    if calibration_missing:
        old = None
''').replace('    rows = [("body figures",','''    if calibration_missing:
        lines += ["Historical calibration NOT AVAILABLE; compiled pages NOT MEASURED.", ""]
    rows = [("body figures",''');p.write_text(s)
p=R/'01_PROGRAM/python/check_gradient_energy.py';s=p.read_text();a=s.index('    with open(os.path.join(RES, "summary.json"))');b=s.index('    out = {',a);s=s[:a]+'''    # Read fresh V2, not a summary generated later by run_all.
    l020 = next(row for row in V["fem1"]["length"]
                if abs(row["l_over_L"] - 0.20) < 1e-9)
    u_bench_um = float(f"{l020['u'] * 1e6:.4f}")
'''+s[b:];p.write_text(s)
p=R/'01_PROGRAM/python/check_paper_numbers.py';s=p.read_text();a=s.index('    # the count is checked in words');b=s.index('    # ---- the independent routes',a);s=s[:a]+'''    # Harness count is not printed; no previous summary is needed.

'''+s[b:];p.write_text(s)
p=R/'01_PROGRAM/python/run_verification.py';s=p.read_text();a=s.index('    L = R["l1_scheme"]',s.index('def write_markdown'));b=s.index('    A("\\n## V6',a);s=s[:a]+s[a:b].replace('    L = R["l1_scheme"]','    l1 = R["l1_scheme"]').replace('L[','l1[')+s[b:];p.write_text(s)
patch=[];changes=[]
for name in ['run_sensitivity.py','length_budget.py','check_gradient_energy.py','check_paper_numbers.py','run_verification.py']:
 a=(SOURCE/'python'/name).read_text();b=(R/'01_PROGRAM/python'/name).read_text();patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='original/python/'+name,tofile='packaged/01_PROGRAM/python/'+name));changes.append({'file':name,'original_sha256':hashlib.sha256(a.encode()).hexdigest(),'packaged_sha256':hashlib.sha256(b.encode()).hexdigest()})
write('09_ARCHIVE_METADATA/packaging_portability.patch',''.join(patch));dump('09_ARCHIVE_METADATA/source_modifications.json',changes)
# Actual public upstream files, pinned by commit, with license/source.
revision='04aee43a9049051128c5d58b617dcd05e34df8b4';vendors=[]
for f in ['elsarticle.cls','elsarticle-num.bst','LICENSE','README.md','elsarticle.dtx','elsarticle.ins']:
 u=f'https://api.github.com/repos/STM-Document-Engineering/elsarticle/contents/{f}?ref={revision}'
 data=json.load(urllib.request.urlopen(u));b=base64.b64decode(data['content']);name='02_OVERLEAF/'+f if f.endswith(('.cls','.bst')) else '09_ARCHIVE_METADATA/licenses/elsarticle_'+f
 q=R/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);vendors.append({'path':name,'source_api':u,'commit':revision,'blob_sha':data['sha'],'sha256':hashlib.sha256(b).hexdigest()})
dump('09_ARCHIVE_METADATA/third_party_sources.json',vendors)
copy(WORK/'requirements-lock.txt','01_PROGRAM/requirements-lock.txt');write('01_PROGRAM/requirements.txt','numpy==2.4.6\nscipy==1.17.1\nmatplotlib==3.11.2')
shutil.copytree(WORK/'wheelhouse',R/'01_PROGRAM/wheelhouse',dirs_exist_ok=True)
write('04_REPRODUCTION/prepare.py','''from pathlib import Path
import argparse,shutil
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--with-baseline',action='store_true');a=p.parse_args()
w=R/'04_REPRODUCTION/workspace'
if w.exists():raise SystemExit('Existing workspace: move/remove deliberately before preparing again')
w.mkdir()
for s,d in [('01_PROGRAM/python','python'),('01_PROGRAM/matlab','matlab'),('02_OVERLEAF','Paper_12'),('05_DERIVATIONS/source_notes','docs')]:shutil.copytree(R/s,w/d)
shutil.copytree(R/'01_PROGRAM/manuscript_tools',w/'Paper_12',dirs_exist_ok=True)
(w/'results').mkdir()
if a.with_baseline:
 shutil.copytree(R/'03_DATA/results',w/'results',dirs_exist_ok=True)
 shutil.copytree(R/'02_OVERLEAF/figures',w/'results/figures/paper',dirs_exist_ok=True)
print('Prepared',w.relative_to(R),'baseline' if a.with_baseline else 'EMPTY results')
''')
write('04_REPRODUCTION/reproduce.py','''from pathlib import Path
import os,sys,subprocess,json,time
R=Path(__file__).resolve().parents[1];w=R/'04_REPRODUCTION/workspace';o=R/'06_VALIDATION/reproduction_test';o.mkdir(exist_ok=True)
if not w.exists():raise SystemExit('Run prepare.py first')
e=dict(os.environ)
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:e[k]='1'
e.update(PYTHONHASHSEED='0',MPLBACKEND='Agg',PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1')
records=[]
for s in ['run_demos.py','run_all.py','check_paper_numbers.py','check_float_order.py','check_paper_structure.py']:
 print('RUN',s,flush=True);t=time.monotonic()
 with (o/(s+'.log')).open('w') as log:p=subprocess.run([sys.executable,'python/'+s],cwd=w,env=e,stdout=log,stderr=subprocess.STDOUT)
 records.append({'command':['python3','python/'+s],'cwd':'04_REPRODUCTION/workspace','exit_code':p.returncode,'elapsed_seconds':time.monotonic()-t});(o/'execution.json').write_text(json.dumps(records,indent=2));print('EXIT',s,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
''')
write('04_REPRODUCTION/build_manuscript.sh','''#!/bin/sh
set -eu
cd "$(dirname "$0")/../02_OVERLEAF"
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
''')
# Source-level comprehensive catalog and unmodified Boolean criteria.
settings=[];criteria=[]
for p in sorted((R/'01_PROGRAM/python').glob('*.py')):
 s=p.read_text()
 for n in ast.walk(ast.parse(s)):
  if isinstance(n,(ast.Assign,ast.AnnAssign)) and n.value is not None:
   for target in n.targets if isinstance(n,ast.Assign) else [n.target]:settings.append({'source':p.relative_to(R).as_posix(),'line':n.lineno,'target':ast.unparse(target),'expression':ast.get_source_segment(s,n.value),'interpretation':'Source expression, not necessarily an input or runtime value; units in producer/manuscript, otherwise NOT DOCUMENTED'})
  if isinstance(n,ast.FunctionDef):
   args=n.args.posonlyargs+n.args.args
   defaults=list(zip(args[-len(n.args.defaults):] if n.args.defaults else [],n.args.defaults))+[(a,d) for a,d in zip(n.args.kwonlyargs,n.args.kw_defaults) if d is not None]
   for a,d in defaults:settings.append({'source':p.relative_to(R).as_posix(),'line':n.lineno,'target':n.name+'.'+a.arg,'expression':ast.unparse(d),'interpretation':'Default; actual call sites may override'})
  if p.name=='run_all.py' and isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='chk' and n.args and isinstance(n.args[0],ast.Constant):criteria.append({'id':n.args[0].value,'source':p.relative_to(R).as_posix(),'line':n.lineno,'expression':ast.get_source_segment(s,n)})
dump('09_ARCHIVE_METADATA/source_settings_catalog.json',settings);dump('06_VALIDATION/criterion_expressions.json',criteria);assert len(criteria)==70
# Full manuscript equations verbatim: no novel derivation.
equations=['# Existing governing equations — verbatim source extracts\n\nContext and assumptions remain in the authoritative section files. No new equations invented.\n']
for p in sorted((R/'02_OVERLEAF/sec').glob('*.tex')):
 s=p.read_text()
 for m in re.finditer(r'\\begin\{(equation\*?|align\*?|multline\*?|gather\*?)\}.*?\\end\{\1\}',s,re.S):equations.extend(['\n## '+p.relative_to(R).as_posix()+':'+str(s[:m.start()].count('\n')+1),'```latex',m.group(0),'```'])
write('05_DERIVATIONS/GOVERNING_EQUATIONS.md','\n'.join(equations))
print('Built skeleton:',R,'source files inspected',len(selection),'criteria',len(criteria))
