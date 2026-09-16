from __future__ import annotations
import subprocess, sys
from pathlib import Path

def run(cfg,report):
    root=Path(cfg['_target_root'])
    cp=subprocess.run([sys.executable,'tools/build_manifests.py','--check'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60)
    release=(root/'RELEASE.md').read_text(encoding='utf-8')
    curated='curated index of public contract surfaces' in release
    if cp.returncode==0:
        verdict='PASS'; msg='Manifest builder agrees with committed manifests.'
    elif curated:
        verdict='FAIL'; msg='build_manifests.py is incompatible with the current curated contract-surface release policy and reports committed manifests out of date.'
    else:
        verdict='FAIL'; msg='Manifest builder reports committed manifests out of date.'
    report.add('kristal.tools.manifest_builder_consistency',verdict,'tooling',msg,evidence=(cp.stdout+cp.stderr)[-5000:],recommendation='Rewrite or retire build_manifests.py; then add its authoritative check to CI.' if cp.returncode else None)
