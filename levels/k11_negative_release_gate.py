from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ._kristal_helpers import copy_repo, validate_release, write_json, first_recursive_key


def expect_reject(report, src: Path, case_id: str, mutator, description: str):
    with tempfile.TemporaryDirectory(prefix='kristal-neg-') as d:
        root = Path(d) / 'repo'
        copy_repo(src, root)
        mutator(root)
        rc, out = validate_release(root)
        report.add(
            f'kristal.negative.{case_id}', 'PASS' if rc != 0 else 'FAIL', 'negative_gate',
            f'Release gate rejected {description}.' if rc != 0 else f'Release gate ACCEPTED {description}; fail-closed coverage gap.',
            evidence={'exit_code': rc, 'output_tail': out},
        )


def run(cfg, report):
    src = Path(cfg['_target_root'])

    def version(root):
        (root / 'VERSION').write_text('5.0.0-rc.999\n', encoding='utf-8')
    expect_reject(report, src, 'version_mismatch', version, 'a VERSION/release mismatch')

    def exver(root):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/10-examples/structured-epistemic-state.example.json'
        x = json.loads(p.read_text(encoding='utf-8')); x['schema_version'] = '4.0'; write_json(p, x)
    expect_reject(report, src, 'example_schema_version', exver, 'an example downgraded to schema_version 4.0')

    def sid(root):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/02-schemas/assertion-status.schema.json'
        x = json.loads(p.read_text(encoding='utf-8')); x['$id'] = 'https://example.invalid/schema'; write_json(p, x)
    expect_reject(report, src, 'schema_id', sid, 'an invalid schema $id')

    def link(root):
        p = root / 'docs/index.md'; p.write_text(p.read_text(encoding='utf-8') + '\n[broken](definitely-missing-validation-target.md)\n', encoding='utf-8')
    expect_reject(report, src, 'broken_doc_link', link, 'a broken local documentation link')

    def surface(root):
        p = root / 'contract-set.manifest.json'; x = json.loads(p.read_text(encoding='utf-8'))
        x['normative_surfaces'][0]['path'] = 'missing-contract-surface/'; write_json(p, x)
    expect_reject(report, src, 'missing_contract_surface', surface, 'a missing declared contract surface')

    def jcs(root):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/09-test-vectors/jcs/expected-hashes.txt'
        lines = p.read_text(encoding='utf-8').splitlines()
        for i, line in enumerate(lines):
            if line and not line.startswith('#'):
                parts = line.split(); h = parts[-1]; parts[-1] = ('0' if h[0] != '0' else '1') + h[1:]; lines[i] = ' '.join(parts); break
        p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    expect_reject(report, src, 'jcs_hash', jcs, 'a tampered JCS expected hash')

    def canon_version(root):
        p = root / 'kristal-release.json'; x = json.loads(p.read_text(encoding='utf-8')); x['canonicalization_version'] = '999'; write_json(p, x)
    expect_reject(report, src, 'canonicalization_version', canon_version, 'an unsupported canonicalization version')

    def retired_schema_manifest(root):
        (root / 'schema-set.manifest.json').write_text('{"retired":true}\n', encoding='utf-8')
    expect_reject(report, src, 'retired_schema_manifest', retired_schema_manifest, 'the reappearance of schema-set.manifest.json')

    def retired_builder(root):
        p = root / 'tools/build_manifests.py'; p.write_text('print("retired")\n', encoding='utf-8')
    expect_reject(report, src, 'retired_manifest_builder', retired_builder, 'the reappearance of tools/build_manifests.py')
