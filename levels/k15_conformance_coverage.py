from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path

from ._kristal_helpers import adapter_settings, combined, read_json, run_adapter, write_json


def _safe_json(stdout: str):
    try:
        return json.loads(stdout)
    except Exception:
        return None


def _write_payloads(payloads: dict, root: Path) -> None:
    for rel, encoded in payloads.items():
        path = root.joinpath(*rel.split('/'))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(encoded))


def run(cfg, report):
    root = Path(cfg['_target_root'])
    base = root / 'docs/Technical-Reference/kristal-docs-v5'
    acceptance = base / '03-reproducibility/reproducibility-acceptance-tests.md'
    text = acceptance.read_text(encoding='utf-8')
    required = {'EX-1','EX-2','EX-3','EX-4','RP-1','RP-2','RP-3','RP-4','RP-5','RP-6'}
    import re
    found = set(re.findall(r'\b(?:EX|RP)-\d+\b', text))
    missing = sorted(required - found)
    report.add('kristal.acceptance.normative_cases_present', 'PASS' if not missing else 'FAIL', 'coverage',
               'All core EX/RP acceptance cases are documented.' if not missing else 'Normative acceptance cases are missing.',
               evidence={'found': sorted(found), 'missing': missing})

    framework_surfaces = [
        root / 'tools/validate_conformance.py',
        root / 'tools/kristal_tck.mjs',
        base / '09-test-vectors/TCK.md',
        base / '09-test-vectors/exchange/vectors.json',
        base / '09-test-vectors/runtime-pack/vectors.json',
    ]
    missing_surfaces = [p.relative_to(root).as_posix() for p in framework_surfaces if not p.exists()]
    report.add('kristal.acceptance.framework_tck_present', 'PASS' if not missing_surfaces else 'FAIL', 'coverage',
               'Framework-vector TCK surfaces are present.' if not missing_surfaces else 'Framework-vector TCK surfaces are incomplete.',
               evidence=missing_surfaces or [p.relative_to(root).as_posix() for p in framework_surfaces])
    if missing_surfaces:
        return

    adapter, cwd, commands = adapter_settings(cfg)
    required_ops = {'exchange_id', 'verify_exchange', 'build_runtime_pack', 'verify_runtime_pack', 'verify_runtime_profiles'}
    missing_ops = sorted(required_ops - set(commands))
    if not adapter.get('enabled'):
        report.add('kristal.implementation_adapter.connected', 'BLOCKED', 'coverage',
                   'No external Kristal compiler/verifier adapter is connected; implementation conformance remains NOT TESTED.',
                   recommendation='Configure implementation_adapter in levelupdiag.config.local.json when a concrete implementation is available.')
        return
    if missing_ops or not cwd.exists():
        report.add('kristal.implementation_adapter.connected', 'BLOCKED', 'coverage',
                   'Implementation adapter is incomplete or its cwd does not exist.',
                   evidence={'cwd': str(cwd), 'missing_operations': missing_ops},
                   recommendation='Declare exchange_id, verify_exchange, build_runtime_pack, verify_runtime_pack, and verify_runtime_profiles commands and fix adapter cwd.')
        return

    report.add('kristal.implementation_adapter.connected', 'PASS', 'coverage',
               'External implementation adapter is connected.', evidence={'cwd': str(cwd), 'operations': sorted(commands)})

    exchange_doc = read_json(base / '09-test-vectors/exchange/vectors.json')
    rp_doc = read_json(base / '09-test-vectors/runtime-pack/vectors.json')
    ex_evidence = []
    rp_evidence = []
    failures = []

    with tempfile.TemporaryDirectory(prefix='levelupdiag-k15-') as td:
        temp = Path(td)
        computed_ids = {}
        for vector in exchange_doc.get('vectors', []):
            vf = temp / f"{vector['id']}.json"
            write_json(vf, vector)
            cp_id, _, argv_id = run_adapter(cfg, 'exchange_id', input=vf, timeout=90)
            parsed = _safe_json(cp_id.stdout or '')
            actual_id = parsed.get('kristal_id') if isinstance(parsed, dict) else None
            expected_id = vector.get('expected_kristal_id')
            id_ok = cp_id.returncode == 0 and actual_id == expected_id
            computed_ids[vector['id']] = actual_id

            cp_verify, _, argv_verify = run_adapter(cfg, 'verify_exchange', input=vf, timeout=90)
            expected_verify = 0 if vector.get('expect_declared_hash_integrity', 'pass') == 'pass' else 1
            verify_ok = cp_verify.returncode == expected_verify
            ex_evidence.append({
                'vector': vector['id'], 'id_ok': id_ok, 'verify_ok': verify_ok,
                'expected_verify_rc': expected_verify, 'actual_verify_rc': cp_verify.returncode,
                'actual_id': actual_id, 'expected_id': expected_id,
                'exchange_id_command': argv_id, 'verify_command': argv_verify,
            })
            if not id_ok or not verify_ok:
                failures.append(f"Exchange {vector['id']}")

        for rel in exchange_doc.get('relations', []):
            left, right = computed_ids.get(rel['left']), computed_ids.get(rel['right'])
            ok = (left == right) if rel.get('expect') == 'same_id' else (left != right)
            ex_evidence.append({'relation': rel['id'], 'ok': ok, 'left': left, 'right': right, 'expect': rel.get('expect')})
            if not ok:
                failures.append(f"Exchange relation {rel['id']}")

        rp001 = next((v for v in rp_doc.get('vectors', []) if v.get('id') == 'RP-001'), None)
        rp006 = next((v for v in rp_doc.get('vectors', []) if v.get('id') == 'RP-006'), None)
        if not rp001 or not rp006:
            failures.append('Runtime Pack RP-001/RP-006 fixture missing')
        else:
            request = temp / 'RP-001.json'
            write_json(request, rp001)
            out1, out2 = temp / 'rp-build-1', temp / 'rp-build-2'
            cp_b1, _, argv_b1 = run_adapter(cfg, 'build_runtime_pack', input=request, output_dir=out1, timeout=90)
            cp_b2, _, argv_b2 = run_adapter(cfg, 'build_runtime_pack', input=request, output_dir=out2, timeout=90)
            m1, m2 = out1 / 'runtime-pack.manifest.json', out2 / 'runtime-pack.manifest.json'
            deterministic = cp_b1.returncode == 0 and cp_b2.returncode == 0 and m1.exists() and m2.exists() and m1.read_bytes() == m2.read_bytes()
            expected_id = rp001.get('expected_runtime_pack_id')
            actual_id = read_json(m1).get('runtime_pack_id') if m1.exists() else None
            id_ok = actual_id == expected_id
            cp_v, _, argv_v = run_adapter(cfg, 'verify_runtime_pack', manifest=m1, payload_dir=out1, timeout=90) if m1.exists() else (None, None, [])
            verify_ok = bool(cp_v and cp_v.returncode == 0)
            rp_evidence.append({'vector': 'RP-001', 'build_rcs': [cp_b1.returncode, cp_b2.returncode], 'deterministic_manifest': deterministic,
                                'id_ok': id_ok, 'verify_ok': verify_ok, 'actual_id': actual_id, 'expected_id': expected_id,
                                'build_command': argv_b1, 'verify_command': argv_v})
            if not (deterministic and id_ok and verify_ok):
                failures.append('Runtime Pack RP-001')

            tamper_dir = temp / 'rp006'
            tamper_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = tamper_dir / 'runtime-pack.manifest.json'
            write_json(manifest_path, rp006['input'])
            _write_payloads(rp006.get('payloads', {}), tamper_dir)
            cp_bad, _, argv_bad = run_adapter(cfg, 'verify_runtime_pack', manifest=manifest_path, payload_dir=tamper_dir, timeout=90)
            reject_ok = cp_bad.returncode == 1
            rp_evidence.append({'vector': 'RP-006', 'tamper_rejected': reject_ok, 'actual_rc': cp_bad.returncode, 'verify_command': argv_bad})
            if not reject_ok:
                failures.append('Runtime Pack RP-006')

    report.add('kristal.implementation.exchange_core_vectors', 'FAIL' if any(x.startswith('Exchange') for x in failures) else 'PASS', 'implementation_conformance',
               'External implementation passes the executable Exchange core vectors and identity relations.' if not any(x.startswith('Exchange') for x in failures) else 'External implementation failed one or more executable Exchange vectors.',
               evidence=ex_evidence)
    report.add('kristal.implementation.runtime_pack_core_vectors', 'FAIL' if any(x.startswith('Runtime Pack') for x in failures) else 'PASS', 'implementation_conformance',
               'External implementation passes deterministic RP-001 build/verify and rejects RP-006 tampering.' if not any(x.startswith('Runtime Pack') for x in failures) else 'External implementation failed one or more Runtime Pack core-vector checks.',
               evidence=rp_evidence)

    portable = base / '09-test-vectors/runtime-pack/portable-vectors.json'
    if not portable.exists():
        report.add('kristal.implementation.extended_runtime_pack_profiles', 'FAIL', 'implementation_conformance',
                   'Portable RP-2..RP-5 vector file is missing.')
        return
    cp_portable, _, argv_portable = run_adapter(cfg, 'verify_runtime_profiles', vectors=portable, timeout=120)
    parsed_portable = _safe_json(cp_portable.stdout or '')
    results = parsed_portable.get('results', []) if isinstance(parsed_portable, dict) else []
    expected = {'RP-002','RP-003','RP-004','RP-005','RP-005-NORUN'}
    passed = {r.get('id') for r in results if isinstance(r, dict) and r.get('ok') is True}
    portable_ok = (
        cp_portable.returncode == 0
        and isinstance(parsed_portable, dict)
        and parsed_portable.get('ok') is True
        and parsed_portable.get('profile') == 'kristal.v5:runtime-pack-portable-conformance@1'
        and passed == expected
    )
    report.add('kristal.implementation.extended_runtime_pack_profiles', 'PASS' if portable_ok else 'FAIL', 'implementation_conformance',
               'External implementation independently reproduces RP-2..RP-5 portable golden bytes.' if portable_ok else 'External implementation failed one or more RP-2..RP-5 portable materialization vectors.',
               evidence={'command': argv_portable, 'exit_code': cp_portable.returncode, 'passed': sorted(x for x in passed if x), 'expected': sorted(expected), 'output': parsed_portable or combined(cp_portable)},
               recommendation=None if portable_ok else 'Update the implementation to conform to kristal.v5:runtime-pack-portable-conformance@1.')
