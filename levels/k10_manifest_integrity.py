from __future__ import annotations
import hashlib, json
from pathlib import Path

def digest_entries(entries):
    payload=''.join(f"{e['path']}\0{e['sha256']}\n" for e in sorted(entries,key=lambda x:x['path']))
    return hashlib.sha256(payload.encode()).hexdigest()

def run(cfg, report):
    root=Path(cfg['_target_root'])
    version=(root/'VERSION').read_text(encoding='utf-8').strip()
    sm=json.loads((root/'schema-set.manifest.json').read_text(encoding='utf-8'))
    schema_dir=root/'docs/Technical-Reference/kristal-docs-v5/02-schemas'
    actual=sorted(p.relative_to(root).as_posix() for p in schema_dir.glob('*.json'))
    entries=sm.get('entries',[])
    listed=sorted(e.get('path') for e in entries if isinstance(e,dict))
    report.add('kristal.schema_manifest.coverage', 'PASS' if listed==actual else 'FAIL','manifest',
               'Schema manifest covers exactly the normative schema files.' if listed==actual else 'Schema manifest file set differs from normative schema directory.',
               evidence={'listed':len(listed),'actual':len(actual),'missing':sorted(set(actual)-set(listed)),'extra':sorted(set(listed)-set(actual))})
    bad=[]
    for e in entries:
        p=root/e['path']
        if not p.is_file(): bad.append({'path':e['path'],'reason':'missing'}); continue
        got=hashlib.sha256(p.read_bytes()).hexdigest()
        if got!=e.get('sha256'): bad.append({'path':e['path'],'expected':e.get('sha256'),'actual':got})
    report.add('kristal.schema_manifest.file_hashes','FAIL' if bad else 'PASS','manifest',
               'All schema manifest file hashes match.' if not bad else 'Schema manifest contains stale or invalid file hashes.', evidence=bad or None)
    computed='sha256:'+digest_entries(entries)
    report.add('kristal.schema_manifest.set_digest','PASS' if computed==sm.get('schema_set_digest') else 'FAIL','manifest',
               'Schema-set digest matches the entry set.' if computed==sm.get('schema_set_digest') else 'Schema-set digest does not match the manifest entries.',
               evidence={'declared':sm.get('schema_set_digest'),'computed':computed})
    report.add('kristal.schema_manifest.release','PASS' if sm.get('release')==version else 'FAIL','manifest',
               'Schema manifest release matches VERSION.' if sm.get('release')==version else 'Schema manifest release does not match VERSION.')
    kr=json.loads((root/'kristal-release.json').read_text(encoding='utf-8'))
    ok=(kr.get('version')==version and kr.get('canonicalization_profile')=='kristal.v5:jcs-rfc8785')
    report.add('kristal.release_identity.basic','PASS' if ok else 'FAIL','release',
               'Release identity and canonicalization profile are aligned.' if ok else 'Release identity/canonicalization mismatch.', evidence={'version':version,'release':kr})
