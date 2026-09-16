from __future__ import annotations

import json
from pathlib import Path

from ._kristal_helpers import validate_conformance

EX_PROFILE = 'kristal.v5:exchange-id-core@1'
RP_PROFILE = 'kristal.v5:runtime-pack-id-core@1'


def run(cfg, report):
    root = Path(cfg['_target_root'])
    base = root / 'docs/Technical-Reference/kristal-docs-v5'
    ex = json.loads((base / '09-test-vectors/exchange/vectors.json').read_text(encoding='utf-8'))
    rp = json.loads((base / '09-test-vectors/runtime-pack/vectors.json').read_text(encoding='utf-8'))
    tck = (base / '09-test-vectors/TCK.md').read_text(encoding='utf-8')
    ex_readme = (base / '09-test-vectors/exchange/README.md').read_text(encoding='utf-8')
    rp_readme = (base / '09-test-vectors/runtime-pack/README.md').read_text(encoding='utf-8')
    acceptance = (base / '03-reproducibility/reproducibility-acceptance-tests.md').read_text(encoding='utf-8')

    ex_ok = ex.get('id_profile') == EX_PROFILE and EX_PROFILE in (tck + ex_readme) and EX_PROFILE in acceptance
    report.add('kristal.tck.exchange_profile_lock', 'PASS' if ex_ok else 'FAIL', 'tck_profile', 'Exchange TCK, TCK documentation and acceptance tests agree on the identity profile.' if ex_ok else 'Exchange identity profile drift exists across TCK surfaces.', evidence={'vector_profile': ex.get('id_profile'), 'expected': EX_PROFILE})

    rp_id = (rp.get('id_profile') or {}).get('id')
    rp_ok = rp_id == RP_PROFILE and RP_PROFILE in (tck + rp_readme)
    report.add('kristal.tck.runtime_pack_profile_lock', 'PASS' if rp_ok else 'FAIL', 'tck_profile', 'Runtime Pack vectors and published TCK vector documentation agree on the identity profile.' if rp_ok else 'Runtime Pack identity profile drift exists.', evidence={'vector_profile': rp_id, 'expected': RP_PROFILE})

    payload_boundary = 'payload/hash-target fixtures rather than complete Exchange Manifest instances' in tck
    report.add('kristal.tck.exchange_fixture_boundary', 'PASS' if payload_boundary else 'FAIL', 'tck_profile', 'TCK explicitly distinguishes Exchange hash-target fixtures from full Exchange Manifest instances.' if payload_boundary else 'TCK no longer clearly distinguishes payload/hash-target fixtures from complete manifests.')

    rc, out = validate_conformance(root)
    report.add('kristal.tck.native_conformance_gate', 'PASS' if rc == 0 else 'FAIL', 'tck_profile', 'Native framework-vector conformance gate passes.' if rc == 0 else 'Native framework-vector conformance gate failed.', evidence={'exit_code': rc, 'output_tail': out})
