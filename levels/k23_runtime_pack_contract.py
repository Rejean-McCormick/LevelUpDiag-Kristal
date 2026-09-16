from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from ._kristal_helpers import copy_repo, validate_conformance, write_json


def run(cfg, report):
    root = Path(cfg['_target_root'])
    base = root / 'docs/Technical-Reference/kristal-docs-v5'
    schema = json.loads((base / '02-schemas/runtime-pack-manifest.schema.json').read_text(encoding='utf-8'))
    vectors = json.loads((base / '09-test-vectors/runtime-pack/vectors.json').read_text(encoding='utf-8'))

    artifact_ok = schema.get('properties', {}).get('artifact_type', {}).get('const') == 'runtime_pack_manifest'
    report.add('kristal.runtime_pack.artifact_type', 'PASS' if artifact_ok else 'FAIL', 'runtime_pack', 'Runtime Pack schema uses artifact_type=runtime_pack_manifest.' if artifact_ok else 'Runtime Pack artifact type discriminator drifted.')

    pattern = schema.get('properties', {}).get('runtime_pack_version', {}).get('pattern', '')
    try:
        rejects_short = re.fullmatch(pattern, '5.0') is None
        accepts_core = re.fullmatch(pattern, '5.0.0') is not None
    except re.error:
        rejects_short = accepts_core = False
    report.add('kristal.runtime_pack.version_shape', 'PASS' if rejects_short and accepts_core else 'FAIL', 'runtime_pack', 'Runtime Pack schema requires semantic x.y.z version shape and accepts 5.0.0.' if rejects_short and accepts_core else 'Runtime Pack version schema no longer enforces the expected x.y.z shape.', evidence={'pattern': pattern})

    versions = sorted({v.get('input', {}).get('runtime_pack_version') for v in vectors.get('vectors', [])})
    report.add('kristal.runtime_pack.tck_core_version', 'PASS' if versions == ['5.0.0'] else 'FAIL', 'runtime_pack', 'Core Runtime Pack TCK vectors use format version 5.0.0 independent of framework rc suffix.' if versions == ['5.0.0'] else 'Runtime Pack vector version drift detected.', evidence=versions)

    rp6 = next((v for v in vectors.get('vectors', []) if v.get('id') == 'RP-006'), None)
    tamper_ok = bool(rp6 and rp6.get('expect_payload_integrity') == 'fail')
    report.add('kristal.runtime_pack.tamper_vector_present', 'PASS' if tamper_ok else 'FAIL', 'runtime_pack', 'RP-006 provides an explicit fail-closed payload-integrity vector.' if tamper_ok else 'RP-006 fail-closed payload vector is missing or weakened.')

    with tempfile.TemporaryDirectory(prefix='kristal-rp-') as d:
        tmp = Path(d) / 'repo'; copy_repo(root, tmp)
        p = tmp / 'docs/Technical-Reference/kristal-docs-v5/09-test-vectors/runtime-pack/vectors.json'
        obj = json.loads(p.read_text(encoding='utf-8'))
        obj['vectors'][0]['input']['runtime_pack_version'] = '5.0'
        write_json(p, obj)
        rc, out = validate_conformance(tmp)
        report.add('kristal.runtime_pack.invalid_version_rejected', 'PASS' if rc != 0 else 'FAIL', 'runtime_pack', 'Native conformance gate rejects a Runtime Pack vector downgraded to runtime_pack_version=5.0.' if rc != 0 else 'Native conformance gate accepted runtime_pack_version=5.0.', evidence={'exit_code': rc, 'output_tail': out})
