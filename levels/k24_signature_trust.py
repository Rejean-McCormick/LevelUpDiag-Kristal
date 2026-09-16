from __future__ import annotations

import json
import re
from pathlib import Path


def run(cfg, report):
    root = Path(cfg['_target_root'])
    base = root / 'docs/Technical-Reference/kristal-docs-v5'
    security = base / '07-security/downgrade-rollback-policy.md'
    text = security.read_text(encoding='utf-8')

    ed_ok = bool(re.search(r'\bed25519\b', text, flags=re.I)) and 'mandatory-to-implement' in text
    report.add('kristal.security.ed25519_baseline_declared', 'PASS' if ed_ok else 'FAIL', 'signature_trust', 'Security contract declares Ed25519 as the mandatory-to-implement signature baseline.' if ed_ok else 'Mandatory signature algorithm baseline is missing or ambiguous.')

    required_terms = ['trust root', 'revoked', 'signature_invalid', 'missing_signature']
    missing = [term for term in required_terms if term.lower() not in text.lower()]
    report.add('kristal.security.trust_revocation_contract_present', 'PASS' if not missing else 'FAIL', 'signature_trust', 'Security policy declares trust-root, revocation and signature-failure semantics.' if not missing else 'Security policy is missing expected trust/revocation semantics.', evidence=missing or None)

    schemas = [
        base / '02-schemas/exchange-manifest.schema.json',
        base / '02-schemas/runtime-pack-manifest.schema.json',
        base / '02-schemas/revocations.schema.json',
    ]
    signature_shapes = {}
    for p in schemas:
        obj = json.loads(p.read_text(encoding='utf-8'))
        defs = obj.get('$defs', {})
        sig = defs.get('signature')
        signature_shapes[p.name] = bool(sig)
    report.add('kristal.security.signature_schema_surfaces', 'PASS' if all(signature_shapes.values()) else 'FAIL', 'signature_trust', 'Core Exchange, Runtime Pack and revocation schemas expose signature structures.' if all(signature_shapes.values()) else 'One or more core security schemas lack a signature structure.', evidence=signature_shapes)

    adapter = cfg.get('implementation_adapter') or {}
    commands = adapter.get('commands') or {}
    crypto_ops = {'verify_signature', 'verify_trust'}
    if not adapter.get('enabled') or not crypto_ops.issubset(commands):
        report.add('kristal.security.executable_crypto_vectors', 'BLOCKED', 'signature_trust', 'No external signature/trust verifier adapter is connected, so valid/bad signature, wrong-key, revoked-key and trust-root fail-closed cases are NOT TESTED.', evidence={'required_adapter_operations': sorted(crypto_ops)}, recommendation='Connect an implementation adapter exposing verify_signature and verify_trust before claiming production security conformance.')
    else:
        report.add('kristal.security.executable_crypto_vectors', 'PARTIAL', 'signature_trust', 'Crypto adapter operations are declared, but v0.3 does not yet define portable signed-fixture I/O semantics.', evidence={'configured_operations': sorted(commands)}, recommendation='Add signed fixture corpus + adapter I/O contract before promoting this level to PASS.')
