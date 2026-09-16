from __future__ import annotations

import json
from pathlib import Path


def run(cfg, report):
    root = Path(cfg['_target_root'])
    retired = [p for p in ('schema-set.manifest.json', 'tools/build_manifests.py') if (root / p).exists()]
    report.add('kristal.tools.retired_release_model_absent', 'PASS' if not retired else 'FAIL', 'tooling', 'Retired per-file manifest tooling is absent.' if not retired else 'Retired manifest tooling reappeared.', evidence=retired or None)

    release_text = (root / 'RELEASE.md').read_text(encoding='utf-8').lower()
    curated = 'curated' in release_text and 'contract' in release_text and 'git' in release_text
    report.add('kristal.tools.release_policy_curated_git_pinned', 'PASS' if curated else 'FAIL', 'tooling', 'RELEASE.md describes the curated, Git-pinned contract-surface model.' if curated else 'RELEASE.md no longer clearly describes the curated Git-pinned release model.')

    contracts = json.loads((root / 'contract-set.manifest.json').read_text(encoding='utf-8'))
    has_legacy_entries = 'entries' in contracts or 'schema_set_digest' in contracts or 'contract_set_digest' in contracts
    report.add('kristal.tools.contract_set_not_legacy_inventory', 'PASS' if not has_legacy_entries else 'FAIL', 'tooling', 'contract-set.manifest.json is not the retired exhaustive hash inventory.' if not has_legacy_entries else 'contract-set.manifest.json contains legacy inventory/digest fields.')

    archive = root / 'tools/build_release_archive.py'
    text = archive.read_text(encoding='utf-8') if archive.exists() else ''
    git_based = 'ls-files' in text and 'working tree is not clean' in text
    report.add('kristal.tools.archive_git_tracked_model', 'PASS' if git_based else 'FAIL', 'tooling', 'Release archive tooling is Git-tracked-file based and enforces a clean worktree by default.' if git_based else 'Release archive tooling does not expose the expected Git-tracked clean-worktree model.')

    spec = root / 'docs/Technical-Reference/kristal-docs-v5/00-overview/specification-status.md'
    spec_text = spec.read_text(encoding='utf-8').lower() if spec.exists() else ''
    retirement_declared = (
        'schema-set.manifest.json' in release_text
        and 'build_manifests.py' in release_text
        and 'retired' in release_text
        and 'schema-set.manifest.json' in spec_text
        and 'build_manifests.py' in spec_text
        and 'retired' in spec_text
    )
    report.add('kristal.tools.retired_model_documented_as_retired', 'PASS' if retirement_declared else 'FAIL', 'tooling', 'Release/specification docs explicitly describe the old schema-set/build_manifests machinery as retired.' if retirement_declared else 'Retired release machinery is not clearly documented as retired.')
