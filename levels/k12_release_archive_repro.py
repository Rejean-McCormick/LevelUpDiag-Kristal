from __future__ import annotations
import hashlib, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

def cp_repo(src,dst): shutil.copytree(src,dst,ignore=shutil.ignore_patterns('.levelupdiag','dist','site','__pycache__','.git'))
def build(root):
    cp=subprocess.run([sys.executable,'tools/build_release_archive.py'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60)
    if cp.returncode: return None,cp.stdout+cp.stderr,None
    zips=list((root/'dist').glob('*.zip')); p=zips[0]
    return hashlib.sha256(p.read_bytes()).hexdigest(),cp.stdout,p

def run(cfg,report):
    src=Path(cfg['_target_root'])
    with tempfile.TemporaryDirectory(prefix='kristal-archive-') as d:
        a=Path(d)/'a'; b=Path(d)/'b'; cp_repo(src,a); cp_repo(src,b)
        ha,oa,za=build(a); hb,ob,zb=build(b)
        report.add('kristal.archive.deterministic','PASS' if ha and ha==hb else 'FAIL','reproducibility',
                   'Two clean release archive builds are byte-identical.' if ha and ha==hb else 'Release archive builds are not byte-identical.',evidence={'sha_a':ha,'sha_b':hb})
        if za:
            with zipfile.ZipFile(za) as z:
                infos=z.infolist(); bad_ts=[i.filename for i in infos if i.date_time!=(1980,1,1,0,0,0)]
                names=[i.filename for i in infos]
            report.add('kristal.archive.fixed_timestamps','PASS' if not bad_ts else 'FAIL','reproducibility','Archive entry timestamps are fixed.' if not bad_ts else 'Archive has variable timestamps.',evidence=bad_ts[:20] or None)
            forbidden=[n for n in names if n.startswith('.git/') or n.startswith('dist/') or '/__pycache__/' in n or n.startswith('site/')]
            report.add('kristal.archive.forbidden_paths','PASS' if not forbidden else 'FAIL','reproducibility','Archive excludes standard build/VCS artifacts.' if not forbidden else 'Archive includes forbidden build/VCS artifacts.',evidence=forbidden[:50] or None)
        clean=Path(d)/'clean'; dirty=Path(d)/'diag'; cp_repo(src,clean); cp_repo(src,dirty); (dirty/'.levelupdiag').mkdir(); (dirty/'.levelupdiag/evidence.txt').write_text('diagnostic evidence\n')
        hc,_,_=build(clean); hd,_,zd=build(dirty)
        included=False
        if zd:
            with zipfile.ZipFile(zd) as z: included=any(n.startswith('.levelupdiag/') for n in z.namelist())
        report.add('kristal.archive.diagnostic_evidence_excluded','FAIL' if included or hc!=hd else 'PASS','release_hygiene',
                   'Release archive ignores diagnostic runtime evidence.' if not included and hc==hd else 'Release archive is affected by .levelupdiag runtime evidence.',
                   evidence={'clean_sha':hc,'with_evidence_sha':hd,'evidence_in_archive':included},recommendation='Exclude .levelupdiag from build_release_archive.py before using LevelUpDiag in release workflows.' if included or hc!=hd else None)
