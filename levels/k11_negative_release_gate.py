from __future__ import annotations
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

def cp_repo(src:Path,dst:Path):
    shutil.copytree(src,dst,ignore=shutil.ignore_patterns('.levelupdiag','dist','site','__pycache__','.git'))

def validate(root:Path):
    cp=subprocess.run([sys.executable,'tools/validate_release.py'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',timeout=60)
    return cp.returncode, (cp.stdout+cp.stderr)[-5000:]

def expect_reject(report, src, case_id, mutator, description):
    with tempfile.TemporaryDirectory(prefix='kristal-neg-') as d:
        root=Path(d)/'repo'; cp_repo(src,root); mutator(root); rc,out=validate(root)
        report.add(f'kristal.negative.{case_id}','PASS' if rc!=0 else 'FAIL','negative_gate',
                   f'Release gate rejected {description}.' if rc!=0 else f'Release gate ACCEPTED {description}; fail-closed coverage gap.',
                   evidence={'exit_code':rc,'output_tail':out})

def run(cfg, report):
    src=Path(cfg['_target_root'])
    def version(root): (root/'VERSION').write_text('5.0.0-rc.999\n',encoding='utf-8')
    expect_reject(report,src,'version_mismatch',version,'a VERSION/release mismatch')
    def exver(root):
        p=root/'docs/Technical-Reference/kristal-docs-v5/10-examples/structured-epistemic-state.example.json'; x=json.loads(p.read_text()); x['schema_version']='4.0'; p.write_text(json.dumps(x,indent=2)+'\n')
    expect_reject(report,src,'example_schema_version',exver,'an example downgraded to schema_version 4.0')
    def sid(root):
        p=root/'docs/Technical-Reference/kristal-docs-v5/02-schemas/assertion-status.schema.json'; x=json.loads(p.read_text()); x['$id']='https://example.invalid/schema'; p.write_text(json.dumps(x,indent=2)+'\n')
    expect_reject(report,src,'schema_id',sid,'an invalid schema $id')
    def link(root):
        p=root/'docs/index.md'; p.write_text(p.read_text()+"\n[broken](definitely-missing-validation-target.md)\n",encoding='utf-8')
    expect_reject(report,src,'broken_doc_link',link,'a broken local documentation link')
    def surface(root):
        p=root/'contract-set.manifest.json'; x=json.loads(p.read_text()); x['normative_surfaces'][0]['path']='missing-contract-surface/'; p.write_text(json.dumps(x,indent=2)+'\n')
    expect_reject(report,src,'missing_contract_surface',surface,'a missing declared contract surface')
    def jcs(root):
        p=root/'docs/Technical-Reference/kristal-docs-v5/09-test-vectors/jcs/expected-hashes.txt'; lines=p.read_text().splitlines();
        for i,l in enumerate(lines):
            if l and not l.startswith('#'):
                parts=l.split(); h=parts[-1]; parts[-1]=('0' if h[0]!='0' else '1')+h[1:]; lines[i]=' '.join(parts); break
        p.write_text('\n'.join(lines)+'\n')
    expect_reject(report,src,'jcs_hash',jcs,'a tampered JCS expected hash')
    def schema_content(root):
        p=root/'docs/Technical-Reference/kristal-docs-v5/02-schemas/assertion-status.schema.json'; x=json.loads(p.read_text()); x['description']=str(x.get('description',''))+' tamper-without-manifest-update'; p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
    expect_reject(report,src,'schema_hash_drift',schema_content,'a normative schema content change without schema-set manifest update')
    def smhash(root):
        p=root/'schema-set.manifest.json'; x=json.loads(p.read_text()); x['entries'][0]['sha256']='0'*64; p.write_text(json.dumps(x,indent=2)+'\n')
    expect_reject(report,src,'schema_manifest_hash_tamper',smhash,'a tampered schema-set manifest entry hash')
