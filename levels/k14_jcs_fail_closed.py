from __future__ import annotations
import json, shutil, subprocess, tempfile
from pathlib import Path

def cp_repo(src,dst): shutil.copytree(src,dst,ignore=shutil.ignore_patterns('.levelupdiag','dist','site','__pycache__','.git'))
def runcheck(root):
    return subprocess.run(['node','tools/check_jcs_vectors.mjs'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30).returncode

def run(cfg,report):
    src=Path(cfg['_target_root'])
    report.add('kristal.jcs.baseline','PASS' if runcheck(src)==0 else 'FAIL','jcs','Published JCS vectors pass.' if runcheck(src)==0 else 'Published JCS vectors fail.')
    with tempfile.TemporaryDirectory(prefix='kristal-jcs-') as d:
        r=Path(d)/'r'; cp_repo(src,r)
        p=r/'docs/Technical-Reference/kristal-docs-v5/09-test-vectors/jcs/expected-hashes.txt'; lines=p.read_text().splitlines()
        for i,l in enumerate(lines):
            if l and not l.startswith('#'):
                parts=l.split(); h=parts[-1]; parts[-1]=('0' if h[0]!='0' else '1')+h[1:]; lines[i]=' '.join(parts); break
        p.write_text('\n'.join(lines)+'\n')
        report.add('kristal.jcs.tampered_expected_hash','PASS' if runcheck(r)!=0 else 'FAIL','jcs','JCS checker rejects a tampered expected hash.' if runcheck(r)!=0 else 'JCS checker accepted a tampered expected hash.')
    with tempfile.TemporaryDirectory(prefix='kristal-jcs-') as d:
        r=Path(d)/'r'; cp_repo(src,r)
        p=r/'docs/Technical-Reference/kristal-docs-v5/09-test-vectors/jcs/vectors.json'; x=json.loads(p.read_text());
        if isinstance(x,list): x[0]['input']={'tampered':True}
        elif isinstance(x,dict) and isinstance(x.get('vectors'),list): x['vectors'][0]['input']={'tampered':True}
        p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
        report.add('kristal.jcs.tampered_vector','PASS' if runcheck(r)!=0 else 'FAIL','jcs','JCS checker rejects a semantically tampered vector.' if runcheck(r)!=0 else 'JCS checker accepted a semantically tampered vector.')
