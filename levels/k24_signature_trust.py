from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ._kristal_helpers import adapter_settings, combined, run as run_process, run_adapter


def run_level_crypto(cfg, temp: Path):
    tool_root = Path(cfg['_tool_root'])
    generator = tool_root / 'scripts/generate_crypto_fixtures.mjs'
    cp = run_process(['node', str(generator), str(temp)], tool_root, 60)
    return cp


def run(cfg, report):
    root = Path(cfg['_target_root'])
    base = root / 'docs/Technical-Reference/kristal-docs-v5'
    security = base / '07-security/downgrade-rollback-policy.md'
    text = security.read_text(encoding='utf-8')

    import re
    ed_ok = bool(re.search(r'\bed25519\b', text, flags=re.I)) and 'mandatory-to-implement' in text
    report.add('kristal.security.ed25519_baseline_declared', 'PASS' if ed_ok else 'FAIL', 'signature_trust',
               'Security contract declares Ed25519 as the mandatory-to-implement signature baseline.' if ed_ok else 'Mandatory signature algorithm baseline is missing or ambiguous.')

    required_terms = ['trust root', 'revoked', 'signature_invalid', 'missing_signature']
    missing = [term for term in required_terms if term.lower() not in text.lower()]
    report.add('kristal.security.trust_revocation_contract_present', 'PASS' if not missing else 'FAIL', 'signature_trust',
               'Security policy declares trust-root, revocation and signature-failure semantics.' if not missing else 'Security policy is missing expected trust/revocation semantics.', evidence=missing or None)

    schemas = [
        base / '02-schemas/exchange-manifest.schema.json',
        base / '02-schemas/runtime-pack-manifest.schema.json',
        base / '02-schemas/revocations.schema.json',
    ]
    signature_shapes = {}
    for p in schemas:
        obj = json.loads(p.read_text(encoding='utf-8'))
        signature_shapes[p.name] = bool(obj.get('$defs', {}).get('signature'))
    report.add('kristal.security.signature_schema_surfaces', 'PASS' if all(signature_shapes.values()) else 'FAIL', 'signature_trust',
               'Core Exchange, Runtime Pack and revocation schemas expose signature structures.' if all(signature_shapes.values()) else 'One or more core security schemas lack a signature structure.', evidence=signature_shapes)

    adapter, cwd, commands = adapter_settings(cfg)
    crypto_ops = {'verify_signature', 'verify_trust'}
    if not adapter.get('enabled') or not crypto_ops.issubset(commands) or not cwd.exists():
        report.add('kristal.security.executable_crypto_vectors', 'BLOCKED', 'signature_trust',
                   'No complete external signature/trust verifier adapter is connected.',
                   evidence={'required_adapter_operations': sorted(crypto_ops), 'cwd': str(cwd)},
                   recommendation='Connect an implementation adapter exposing verify_signature and verify_trust.')
        return

    cases = []
    failures = []
    with tempfile.TemporaryDirectory(prefix='levelupdiag-k24-') as td:
        temp = Path(td)
        gen = run_level_crypto(cfg, temp)
        if gen.returncode != 0:
            report.add('kristal.security.fixture_generation', 'INFRA_ERROR', 'signature_trust',
                       'Could not generate independent Ed25519/trust fixtures.', evidence=combined(gen))
            return
        report.add('kristal.security.fixture_generation', 'PASS', 'signature_trust',
                   'Independent ephemeral Ed25519/trust fixtures generated without persisting private keys.')

        matrix = [
            ('verify_signature', 'signature-valid.json', 0),
            ('verify_signature', 'signature-wrong-key.json', 1),
            ('verify_signature', 'signature-tampered-message.json', 1),
            ('verify_trust', 'trust-valid.json', 0),
            ('verify_trust', 'trust-revoked.json', 1),
            ('verify_trust', 'trust-future-revocation.json', 0),
            ('verify_trust', 'trust-expired.json', 1),
        ]
        for op, name, expected in matrix:
            fixture = temp / name
            cp, _, argv = run_adapter(cfg, op, fixture=fixture, timeout=60)
            ok = cp.returncode == expected
            cases.append({'operation': op, 'fixture': name, 'expected_rc': expected, 'actual_rc': cp.returncode, 'ok': ok, 'command': argv,
                          'output': combined(cp, 2000)})
            if not ok:
                failures.append(name)

    report.add('kristal.security.executable_crypto_vectors', 'PASS' if not failures else 'FAIL', 'signature_trust',
               'External verifier passes valid signature/trust cases and fails closed for wrong-key, tamper, revocation and expiry.' if not failures else 'External crypto/trust verifier failed one or more executable security cases.',
               evidence=cases, recommendation=None if not failures else 'Inspect adapter verifier behavior and security fixture handling.')
