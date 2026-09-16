from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ._kristal_helpers import copy_repo, first_recursive_key, validate_release, write_json


def expect_reject(report, src: Path, case_id: str, mutate, description: str):
    with tempfile.TemporaryDirectory(prefix='kristal-format-') as d:
        root = Path(d) / 'repo'
        copy_repo(src, root)
        mutate(root)
        rc, out = validate_release(root)
        report.add(
            f'kristal.schema_format.{case_id}', 'PASS' if rc != 0 else 'FAIL', 'schema_format',
            f'Format-aware validation rejected {description}.' if rc != 0 else f'Format-aware validation ACCEPTED {description}.',
            evidence={'exit_code': rc, 'output_tail': out},
        )


def run(cfg, report):
    src = Path(cfg['_target_root'])

    def bad_datetime(root: Path):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/10-examples/reader-policy-validated-only.example.json'
        obj = json.loads(p.read_text(encoding='utf-8'))
        obj['created_at'] = 'not-a-date-time'
        write_json(p, obj)
    expect_reject(report, src, 'invalid_date_time', bad_datetime, 'an invalid RFC 3339 date-time')

    def bad_uri(root: Path):
        p = root / 'docs/Technical-Reference/kristal-docs-v5/10-examples/claim-ir.example.json'
        obj = json.loads(p.read_text(encoding='utf-8'))
        container, key = first_recursive_key(obj, 'source_url')
        if container is None:
            raise RuntimeError('claim-ir example no longer contains source_url')
        container[key] = 'not a uri'
        write_json(p, obj)
    expect_reject(report, src, 'invalid_uri', bad_uri, 'an invalid URI in a schema-formatted field')
