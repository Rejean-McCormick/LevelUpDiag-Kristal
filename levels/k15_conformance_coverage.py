from __future__ import annotations
import re
from pathlib import Path

def run(cfg,report):
    root=Path(cfg['_target_root'])
    doc=root/'docs/Technical-Reference/kristal-docs-v5/03-reproducibility/reproducibility-acceptance-tests.md'
    text=doc.read_text(encoding='utf-8')
    ids=sorted(set(re.findall(r'\b(?:EX|RP)-\d+\b',text)))
    exec_files=[]
    for p in root.rglob('*'):
        if p.is_file() and p.suffix in {'.py','.js','.mjs','.ts'}:
            low=p.name.lower()
            if any(k in low for k in ('exchange','runtime_pack','runtime-pack','reproduc','conformance')) and 'tools/check_jcs' not in p.as_posix(): exec_files.append(p.relative_to(root).as_posix())
    report.add('kristal.acceptance.normative_cases_present','PASS' if ids else 'FAIL','coverage','Normative EX/RP acceptance cases are documented.' if ids else 'No EX/RP acceptance cases found.',evidence=ids)
    report.add('kristal.acceptance.executable_suite','BLOCKED' if not exec_files else 'PASS','coverage','No executable Exchange/Runtime Pack conformance suite is present for the documented EX/RP cases.' if not exec_files else 'Executable conformance surfaces were found.',evidence=exec_files or None,recommendation='Implement the documented EX/RP fixtures as executable tests before claiming reference implementation conformance.' if not exec_files else None)
    toolnames=[p.name for p in (root/'tools').glob('*') if p.is_file()]
    impl=any(any(k in n.lower() for k in ('exchange','runtime','pack','compiler','verify')) for n in toolnames)
    report.add('kristal.reference_implementation.present','BLOCKED' if not impl else 'PASS','coverage','No reference Exchange/Runtime Pack builder-verifier executable is present in tools/.' if not impl else 'Reference build/verify tooling appears present.',evidence=toolnames,recommendation='Add a reference builder/verifier or point this campaign at the implementation repository.' if not impl else None)
