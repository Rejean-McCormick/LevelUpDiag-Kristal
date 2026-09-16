from __future__ import annotations
import subprocess, sys
from pathlib import Path

def run(cfg,report):
    root=Path(cfg['_target_root'])
    cp=subprocess.run([sys.executable,'-c','import mkdocs; print(mkdocs.__version__)'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if cp.returncode:
        report.add('kristal.docs.mkdocs_environment','INFRA_ERROR','docs','mkdocs is not installed in this validation environment; strict documentation build cannot be executed locally.',evidence=cp.stderr[-2000:],recommendation='Run the committed GitHub conformance workflow or install requirements-dev.txt in a network-enabled isolated environment.')
        return
    b=subprocess.run([sys.executable,'-m','mkdocs','build','--strict','--site-dir',str(Path(cfg.get('_control_root',root/'.levelupdiag'))/'mkdocs-site')],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120)
    report.add('kristal.docs.mkdocs_strict','PASS' if b.returncode==0 else 'FAIL','docs','Strict MkDocs build passes.' if b.returncode==0 else 'Strict MkDocs build fails.',evidence=(b.stdout+b.stderr)[-5000:])
