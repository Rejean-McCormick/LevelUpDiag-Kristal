from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ._kristal_helpers import copy_repo, validate_release, write_json


def expect_reject(report, src: Path, case_id: str, mutate, description: str):
    with tempfile.TemporaryDirectory(prefix='kristal-crossdoc-') as d:
        root = Path(d) / 'repo'
        copy_repo(src, root)
        mutate(root)
        rc, out = validate_release(root)
        report.add(
            f'kristal.cross_document.{case_id}', 'PASS' if rc != 0 else 'FAIL', 'contract_invariant',
            f'Cross-document gate rejected {description}.' if rc != 0 else f'Cross-document gate ACCEPTED {description}.',
            evidence={'exit_code': rc, 'output_tail': out},
        )


def run(cfg, report):
    src = Path(cfg['_target_root'])

    def stale_runtime_version(root: Path):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/03-reproducibility/allowed-runtime-pack-policies.md'
        text = p.read_text(encoding='utf-8')
        old = 'runtime_pack_version = 5.0.0'
        if old not in text:
            raise RuntimeError('expected runtime_pack_version marker not found')
        p.write_text(text.replace(old, 'runtime_pack_version = 5.0', 1), encoding='utf-8')
    expect_reject(report, src, 'runtime_pack_version_drift', stale_runtime_version, 'runtime_pack_version drift back to 5.0')

    def wrong_distribution_type(root: Path):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/06-integration/konnaxion-distribution-contract.md'
        text = p.read_text(encoding='utf-8')
        old = 'artifact_type = "runtime_pack_manifest"'
        if old not in text:
            raise RuntimeError('expected runtime_pack_manifest marker not found')
        p.write_text(text.replace(old, 'artifact_type = "runtime_pack"', 1), encoding='utf-8')
    expect_reject(report, src, 'runtime_pack_artifact_type_drift', wrong_distribution_type, 'Konnaxion distribution artifact_type drift')

    def weaken_reference_exchange(root: Path):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/02-schemas/exchange-manifest.schema.json'
        obj = json.loads(p.read_text(encoding='utf-8'))
        rule = obj['allOf'][0]['then']
        rule['required'] = []
        rule['properties']['authority_recognition_refs'].pop('minItems', None)
        write_json(p, obj)
    expect_reject(report, src, 'reference_exchange_authority_rule', weaken_reference_exchange, 'a reference_exchange rule without mandatory authority recognition')
