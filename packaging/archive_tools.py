from pathlib import Path
R=Path(__file__).resolve().parents[1]/'.repro_work/NEW_FEM_COMPLETE_REPRODUCIBILITY_ARCHIVE'
def w(name,s):
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n')
w('04_REPRODUCTION/audit_archive.py',r'''
"""Static dependency checks do NOT compile or validate physics/DOI metadata."""
from pathlib import Path
import json,re,ast,shutil
R=Path(__file__).resolve().parents[1];P=R/'02_OVERLEAF';seen=set();inputs=[];issues=[]
def expand(p):
 if p in seen:return ''
 seen.add(p);s=re.sub(r'(?<!\\)%[^\n]*','',p.read_text())
 def inc(m):
  q=P/m.group(1)
  if not q.suffix:q=q.with_suffix('.tex')
  inputs.append({'source':p.relative_to(R).as_posix(),'target':q.relative_to(R).as_posix(),'exists':q.exists()})
  if not q.exists():issues.append('Missing input '+q.relative_to(R).as_posix());return ''
  return expand(q)
 return re.sub(r'\\(?:input|include)\{([^}]+)\}',inc,s)
body=expand(P/'main.tex');labels=re.findall(r'\\label\{([^}]+)\}',body);refs=set(re.findall(r'\\(?:ref|eqref|pageref|autoref)\{([^}]+)\}',body));cites=set()
for s in re.findall(r'\\cite\w*\*?(?:\[[^]]*\])*\{([^}]+)\}',body):cites.update(x.strip() for x in s.split(','))
keys=set(re.findall(r'^@\w+\s*\{\s*([^,]+),',(P/'references.bib').read_text(),re.M))
missing_refs=sorted(refs-set(labels));missing_cites=sorted(cites-keys);duplicates=[x for x in set(labels) if labels.count(x)>1];issues+=missing_refs+missing_cites+duplicates
graphics=[]
for name in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',body):
 choices=[P/name,P/'figures'/name]
 if not Path(name).suffix:choices += [p.with_suffix(s) for p in list(choices) for s in ['.pdf','.png','.jpg']]
 q=next((p for p in choices if p.is_file()),None);graphics.append({'requested':name,'resolved':q.relative_to(R).as_posix() if q else None})
 if not q:issues.append('Missing graphic '+name)
for kind,ext in [('documentclass','.cls'),('bibliographystyle','.bst')]:
 for name in re.findall(r'\\'+kind+r'(?:\[[^]]*\])?\{([^}]+)\}',body):
  if not (P/(name+ext)).exists():issues.append('Missing '+name+ext)
syntax=[];absolute=[];secrets=[]
for p in R.rglob('*'):
 if not p.is_file() or any(x in p.relative_to(R).parts for x in ['workspace','__pycache__','.venv']):continue
 if p.suffix in ['.py','.md','.json','.txt','.csv','.log','.tex','.bib','.sh']:
  s=p.read_text(errors='replace')
  if re.search(r'/(?:home|tmp)/[^\s\"\']+',s):absolute.append(p.relative_to(R).as_posix())
  if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}',s):secrets.append(p.relative_to(R).as_posix())
  if p.suffix=='.py':
   try:ast.parse(s);syntax.append(p.relative_to(R).as_posix())
   except SyntaxError:issues.append('Python syntax '+p.relative_to(R).as_posix())
report={'status':'PASS' if not issues else 'FAIL','scope':'Static source/path/key audit, NOT compile/DOI/physical validation','inputs':inputs,'graphics':graphics,'cited_keys':len(cites),'bib_keys':len(keys),'missing_refs':missing_refs,'missing_cites':missing_cites,'duplicate_labels':duplicates,'uncited_keys':sorted(keys-cites),'issues':issues,'tex_tools':{x:bool(shutil.which(x)) for x in ['pdflatex','bibtex','latexmk','tectonic']}}
(R/'06_VALIDATION/manuscript_dependency_audit.json').write_text(json.dumps(report,indent=2))
static={'status':'PASS' if not issues and not absolute and not secrets else 'FAIL','Python_sources_parsed':syntax,'absolute_local_path_files':absolute,'private_key_token_pattern_files':secrets,'issues':issues,'privacy_limit':'Pattern scan is not legal/confidentiality certification. No Git config, venv/cache/builds shipped. Binary embedded paths not assessed.'}
(R/'06_VALIDATION/archive_static_audit.json').write_text(json.dumps(static,indent=2));print('Static manuscript',report['status'],'graphics',len(graphics),'cites',len(cites),'/',len(keys));print('Archive',static['status'],'absolute paths',absolute)
raise SystemExit(static['status']!='PASS')
''')
w('04_REPRODUCTION/compare_outputs.py',r'''
from pathlib import Path
import json
from PIL import Image,ImageChops,ImageStat
R=Path(__file__).resolve().parents[1];W=R/'04_REPRODUCTION/workspace';O=R/'06_VALIDATION/reproduction_test';changes=[];datasets=[]
skip={'summary','environment','run_all_manifest','abstract_audit','stale_tokens','unverified_numbers','coupling_provenance_check'}
for p in sorted((R/'03_DATA/results').glob('*.json')):
 if p.stem in skip:continue
 q=W/'results'/p.name
 if not q.exists():datasets.append({'dataset':p.name,'status':'MISSING'});continue
 differences=[];structure=[];counts=[0]
 def compare(a,b,path='$'):
  if isinstance(a,bool) or isinstance(b,bool):
   if a!=b:structure.append({'path':path,'baseline':a,'current':b})
  elif isinstance(a,(float,int)) and isinstance(b,(float,int)):
   counts[0]+=1
   if a!=b:d=abs(b-a);differences.append({'path':path,'baseline':a,'current':b,'absolute':d,'relative':d/abs(a) if a else None})
  elif isinstance(a,dict) and isinstance(b,dict):
   for k in sorted(a.keys()|b.keys()):
    if k not in a or k not in b:structure.append({'path':path+'.'+k,'status':'key missing on one side'})
    else:compare(a[k],b[k],path+'.'+k)
  elif isinstance(a,list) and isinstance(b,list):
   if len(a)!=len(b):structure.append({'path':path,'baseline_length':len(a),'current_length':len(b)})
   for i,(x,y) in enumerate(zip(a,b)):compare(x,y,f'{path}[{i}]')
 compare(json.loads(p.read_text()),json.loads(q.read_text()));datasets.append({'dataset':p.name,'status':'EXACT NUMERIC MATCH' if not differences and not structure else 'DIFFERENCES RECORDED','numeric_values':counts[0],'numeric_differences':len(differences),'max_absolute':max((x['absolute'] for x in differences),default=0),'max_relative':max((x['relative'] for x in differences if x['relative'] is not None),default=0),'structural_differences':structure});changes += [{'dataset':p.name,**x} for x in differences]
figures=[]
for p in sorted((R/'02_OVERLEAF/figures').glob('*.png')):
 q=W/'Paper_12/figures'/p.name
 if not q.exists():figures.append({'figure':p.name,'status':'MISSING'});continue
 a=Image.open(p).convert('RGB');b=Image.open(q).convert('RGB')
 if a.size!=b.size:figures.append({'figure':p.name,'status':'SIZE DIFFERENCE'});continue
 d=ImageChops.difference(a,b);figures.append({'figure':p.name,'status':'EXACT PIXEL MATCH' if d.getbbox() is None else 'PIXEL DIFFERENCE','size':a.size,'rms_RGB':ImageStat.Stat(d).rms})
s=json.loads((W/'results/summary.json').read_text());ok=s['all_pass'] and s['n_pass']==s['n_total']==70;missing=any(x['status']=='MISSING' for x in datasets+figures);status='FAIL' if not ok or missing else ('PASS WITH NUMERICAL DIFFERENCE' if changes or any(x.get('structural_differences') for x in datasets) else 'PASS')
out={'program_status':status,'overall':'PARTIAL: manuscript NOT COMPILED','acceptance':'Original70 Boolean criteria, no new global tolerance. Differences diagnostic; historical sensitivity arrays may pair differing stacks by index, not like-for-like physics. Runtime differences are metadata. PDF bytes not physically graded.','datasets':datasets,'figures':figures,'n_pass':s['n_pass'],'n_total':s['n_total']};(O/'output_comparison.json').write_text(json.dumps(out,indent=2));(O/'numeric_differences.json').write_text(json.dumps(changes,indent=2));print(status,'70-gate result',s['n_pass'],'PNG exact',sum(x['status']=='EXACT PIXEL MATCH' for x in figures),'/12','numeric differences',len(changes));raise SystemExit(not ok or missing)
''')
w('04_REPRODUCTION/verify_integrity.py',r'''
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parents[1];bad=[];count=0
for line in (R/'SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1);p=R/n
 if p.resolve().is_relative_to(R) and p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h:count+=1
 else:bad.append(n)
print('Verified',count,'files;',len(bad),'mismatches');print('\n'.join(bad));sys.exit(bool(bad))
''')
w('04_REPRODUCTION/refresh_integrity.py',r'''
from pathlib import Path
import csv,io,hashlib,zipfile,sys
R=Path(__file__).resolve().parents[1]
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name not in ['SHA256SUMS.txt','file_manifest_sha256.csv'] and not any(x in p.relative_to(R).parts for x in ['workspace','__pycache__','.venv','.git']))
b=io.StringIO();c=csv.writer(b);c.writerow(['relative_path','bytes','sha256'])
for p in files:c.writerow([p.relative_to(R).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
f=R/'file_manifest_sha256.csv';f.write_text(b.getvalue());files.append(f);s=R/'SHA256SUMS.txt';s.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(R).as_posix()+'\n' for p in sorted(files)));files.append(s)
if '--zip' in sys.argv:
 z=R.parent/(R.name+'.zip')
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
  for p in sorted(files):archive.write(p,R.name+'/'+p.relative_to(R).as_posix())
 print('Built',z.name,len(files),'files',z.stat().st_size,'bytes')
''')
w('01_PROGRAM/tests/test_archive.py',r'''
from pathlib import Path
import unittest,json,ast,subprocess,sys,tempfile,contextlib,io,importlib.util,shutil
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'01_PROGRAM/python'))
def load(n):
 s=importlib.util.spec_from_file_location('test_'+n,R/'01_PROGRAM/python'/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class ArchiveTests(unittest.TestCase):
 def test_dependencies(self):
  p=subprocess.run([sys.executable,str(R/'04_REPRODUCTION/audit_archive.py')],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
 def test_material(self):self.assertEqual(json.loads((R/'09_ARCHIVE_METADATA/parameter_manifest.json').read_text())['material']['values']['rho'],6020)
 def test_all_figures_mapped(self):
  f=json.loads((R/'09_ARCHIVE_METADATA/figure_manifest.json').read_text());a=json.loads((R/'06_VALIDATION/manuscript_dependency_audit.json').read_text());self.assertEqual({x['asset'] for x in f},{x['resolved'] for x in a['graphics']})
 def test_criteria(self):self.assertEqual(len(json.loads((R/'06_VALIDATION/criterion_expressions.json').read_text())),70)
 def test_python_syntax(self):
  for p in (R/'01_PROGRAM/python').glob('*.py'):ast.parse(p.read_text())
 def test_data_paths(self):
  d=json.loads((R/'09_ARCHIVE_METADATA/dataset_manifest.json').read_text());self.assertEqual(len(d),33)
  for x in d:self.assertTrue((R/x['path']).is_file());self.assertTrue((R/x['producer']).is_file())
 def test_no_git(self):
  m=load('length_budget')
  with patch.object(m.subprocess,'run',side_effect=FileNotFoundError):self.assertEqual(m.read('main.tex',rev='NOT_AVAILABLE'),'')
 def test_gradient_without_summary(self):
  m=load('check_gradient_energy')
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'verification.json').write_bytes((R/'03_DATA/results/verification.json').read_bytes());m.RES=tmp
   with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(m.main(),0)
   self.assertFalse((p/'summary.json').exists());expected=next(x['value'] for x in json.loads((R/'03_DATA/results/summary.json').read_text())['checks'] if x['id']=='V2');self.assertEqual(json.loads((p/'gradient_energy.json').read_text())['fem1_benchmark_uR_um'],float(expected.split()[0]))
 def test_report_list(self):
  m=load('run_verification')
  with tempfile.TemporaryDirectory() as tmp:
   m.OUT=tmp;m.write_markdown(json.loads((R/'03_DATA/results/verification.json').read_text()));self.assertIn('## V7',(Path(tmp)/'verification.md').read_text())
 def test_number_audit_without_summary(self):
  m=load('check_paper_numbers')
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)
   for q in (R/'03_DATA/results').glob('*.json'):
    if q.name!='summary.json':shutil.copy2(q,p/q.name)
   m.RES=tmp;m.TEX=str(R/'02_OVERLEAF/main.tex')
   with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(m.main(),0)
   self.assertIn('96/96 claims agree',(p/'paper_number_audit.md').read_text());self.assertFalse((p/'summary.json').exists())
if __name__=='__main__':unittest.main()
''')
print('Tools/tests added')
