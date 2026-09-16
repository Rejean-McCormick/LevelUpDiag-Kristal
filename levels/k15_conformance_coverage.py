from __future__ import annotations

import json
import re
from pathlib import Path


def run(cfg, report):
    root = Path(cfg['_target_root'])
    base = root / 'docs/Technical-Reference/kristal-docs-v5'
    acceptance = base / '03-reproducibility/reproducibility-acceptance-tests.md'
    text = acceptance.read_text(encoding='utf-8')
    required = {'EX-1','EX-2','EX-3','EX-4','RP-1','RP-2','RP-3','RP-4','RP-5','RP-6'}
    found = set(re.findall(r'\b(?:EX|RP)-\d+\b', text))
    missing = sorted(required - found)
    report.add('kristal.acceptance.normative_cases_present', 'PASS' if not missing else 'FAIL', 'coverage', 'All core EX/RP acceptance cases are documented.' if not missing else 'Normative acceptance cases are missing.', evidence={'found': sorted(found), 'missing': missing})

    framework_surfaces = [
        root / 'tools/validate_conformance.py',
        root / 'tools/kristal_tck.mjs',
        base / '09-test-vectors/TCK.md',
        base / '09-test-vectors/exchange/vectors.json',
        base / '09-test-vectors/runtime-pack/vectors.json',
    ]
    missing_surfaces = [p.relative_to(root).as_posix() for p in framework_surfaces if not p.exists()]
    report.add('kristal.acceptance.framework_tck_present', 'PASS' if not missing_surfaces else 'FAIL', 'coverage', 'Framework-vector TCK surfaces are present.' if not missing_surfaces else 'Framework-vector TCK surfaces are incomplete.', evidence=missing_surfaces or [p.relative_to(root).as_posix() for p in framework_surfaces])

    adapter = cfg.get('implementation_adapter') or {}
    enabled = bool(adapter.get('enabled'))
    commands = adapter.get('commands') or {}
    required_ops = {'exchange_id', 'verify_exchange', 'build_runtime_pack', 'verify_runtime_pack'}
    missing_ops = sorted(required_ops - set(commands)) if enabled else sorted(required_ops)
    if not enabled:
        report.add('kristal.implementation_adapter.connected', 'BLOCKED', 'coverage', 'No external Kristal compiler/verifier adapter is connected; implementation conformance remains NOT TESTED.', recommendation='Configure implementation_adapter in levelupdiag.config.local.json when a concrete implementation is available.')
    elif missing_ops:
        report.add('kristal.implementation_adapter.connected', 'BLOCKED', 'coverage', 'Implementation adapter is enabled but does not declare all required logical operations.', evidence={'missing_operations': missing_ops}, recommendation='Declare exchange_id, verify_exchange, build_runtime_pack and verify_runtime_pack commands.')
    else:
        cwd = Path(adapter.get('cwd', '.'))
        if not cwd.is_absolute():
            cwd = (Path(cfg['_tool_root']) / cwd).resolve(strict=False)
        report.add('kristal.implementation_adapter.connected', 'PASS' if cwd.exists() else 'BLOCKED', 'coverage', 'External implementation adapter is declared.' if cwd.exists() else 'Implementation adapter cwd does not exist.', evidence={'cwd': str(cwd), 'operations': sorted(commands)}, recommendation=None if cwd.exists() else 'Fix implementation_adapter.cwd.')
