from __future__ import annotations

import json
from pathlib import Path
from ._kristal_helpers import flatten_keys

RETIRED = ('schema-set.manifest.json', 'tools/build_manifests.py')


def run(cfg, report):
    root = Path(cfg['_target_root'])
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    release = json.loads((root / 'kristal-release.json').read_text(encoding='utf-8'))
    contracts = json.loads((root / 'contract-set.manifest.json').read_text(encoding='utf-8'))

    aligned = release.get('version') == version and contracts.get('release') == version
    report.add(
        'kristal.release_identity.version_alignment',
        'PASS' if aligned else 'FAIL', 'release',
        'VERSION, kristal-release.json and contract-set.manifest.json are aligned.' if aligned
        else 'Release version declarations are not aligned.',
        evidence={
            'VERSION': version,
            'kristal_release_version': release.get('version'),
            'contract_set_release': contracts.get('release'),
        },
    )

    commit_ok = release.get('git', {}).get('commit') is None
    report.add(
        'kristal.release_identity.no_self_embedded_commit',
        'PASS' if commit_ok else 'FAIL', 'release',
        'Release manifest does not self-embed the commit that contains itself.' if commit_ok
        else 'Release manifest self-embeds a Git commit contrary to the rc.2 tag-resolution model.',
        evidence={'git.commit': release.get('git', {}).get('commit')},
    )

    profile_ok = (
        release.get('canonicalization_profile') == 'kristal.v5:jcs-rfc8785'
        and release.get('canonicalization_version') == '1'
    )
    report.add(
        'kristal.release_identity.canonicalization',
        'PASS' if profile_ok else 'FAIL', 'release',
        'Canonicalization profile and version match the v5 release contract.' if profile_ok
        else 'Canonicalization profile/version drifted.',
        evidence={
            'profile': release.get('canonicalization_profile'),
            'version': release.get('canonicalization_version'),
        },
    )

    present = [p for p in RETIRED if (root / p).exists()]
    report.add(
        'kristal.release_model.retired_artifacts_absent',
        'PASS' if not present else 'FAIL', 'release',
        'Retired per-file release manifest machinery is absent.' if not present
        else 'Retired release artifacts reappeared.',
        evidence=present or None,
        recommendation='Remove schema-set.manifest.json and tools/build_manifests.py; rc.2 uses Git-pinned curated surfaces.' if present else None,
    )

    missing = []
    surfaces = []
    for section in ('normative_surfaces', 'profile_surfaces', 'conformance_surfaces', 'informative_surfaces'):
        for entry in contracts.get(section, []):
            path = entry.get('path')
            surfaces.append({'section': section, 'name': entry.get('name'), 'path': path})
            if not path or not (root / path).exists():
                missing.append(path or f'<missing path:{entry.get("name")}>')
    report.add(
        'kristal.contract_surfaces.exist',
        'PASS' if surfaces and not missing else 'FAIL', 'release',
        'All curated contract surfaces exist.' if surfaces and not missing else 'One or more curated contract surfaces are missing.',
        evidence={'surface_count': len(surfaces), 'missing': missing},
    )

    hashish = sorted({k for k in flatten_keys(contracts) if k in {'sha256', 'digest', 'file_hash', 'content_hash'}})
    report.add(
        'kristal.contract_surfaces.curated_not_file_hash_inventory',
        'PASS' if not hashish else 'FAIL', 'release',
        'contract-set.manifest.json remains a curated surface index, not a per-file hash inventory.' if not hashish
        else 'contract-set.manifest.json contains per-file/hash-style keys inconsistent with the curated-surface model.',
        evidence=hashish or None,
    )

    expected_tag = f'v{version}'
    tag_ok = release.get('git', {}).get('tag') == expected_tag
    report.add(
        'kristal.release_identity.tag_name',
        'PASS' if tag_ok else 'FAIL', 'release',
        'Release tag metadata matches VERSION.' if tag_ok else 'Release tag metadata does not match VERSION.',
        evidence={'expected': expected_tag, 'declared': release.get('git', {}).get('tag')},
    )
