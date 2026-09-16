from __future__ import annotations

import json
from pathlib import Path

from ._kristal_helpers import git


def run(cfg, report):
    root = Path(cfg['_target_root'])
    probe = git(root, 'rev-parse', '--is-inside-work-tree')
    if probe.returncode != 0 or probe.stdout.strip() != 'true':
        report.add('kristal.git.repository', 'BLOCKED', 'release_identity', 'Target is not a Git worktree; Git/tag release identity cannot be verified.', evidence=(probe.stdout + probe.stderr)[-2000:])
        return

    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    release = json.loads((root / 'kristal-release.json').read_text(encoding='utf-8'))
    declared_tag = release.get('git', {}).get('tag')
    declared_commit = release.get('git', {}).get('commit')
    expected_tag = f'v{version}'

    head_cp = git(root, 'rev-parse', 'HEAD')
    head = head_cp.stdout.strip() if head_cp.returncode == 0 else None
    status_cp = git(root, 'status', '--porcelain=v1')
    status = status_cp.stdout.strip()
    report.add('kristal.git.worktree_clean', 'PASS' if not status else 'WARN', 'release_identity', 'Git worktree is clean for release qualification.' if not status else 'Git worktree is dirty; framework validation may pass, but official archive/tag qualification should wait for a clean committed state.', evidence=status.splitlines()[:100] or None)

    report.add('kristal.git.declared_tag_matches_version', 'PASS' if declared_tag == expected_tag else 'FAIL', 'release_identity', 'Declared release tag matches VERSION.' if declared_tag == expected_tag else 'Declared release tag does not match VERSION.', evidence={'version': version, 'expected_tag': expected_tag, 'declared_tag': declared_tag})

    # Kristal rc.2 intentionally does not self-embed the commit SHA in the file
    # that is itself part of that commit. Consumers resolve tag -> commit.
    report.add('kristal.git.no_self_embedded_commit', 'PASS' if declared_commit is None else 'FAIL', 'release_identity', 'kristal-release.json leaves git.commit unresolved as required by the tag-resolution model.' if declared_commit is None else 'kristal-release.json self-embeds a commit SHA, contrary to the current release model.', evidence={'declared_commit': declared_commit})

    tag_cp = git(root, 'rev-parse', '-q', '--verify', f'refs/tags/{expected_tag}')
    tag_exists = tag_cp.returncode == 0
    if tag_exists:
        c = git(root, 'rev-list', '-n', '1', expected_tag)
        tag_commit = c.stdout.strip() if c.returncode == 0 else None
        report.add('kristal.git.tag_resolves_immutable_commit', 'PASS' if tag_commit else 'FAIL', 'release_identity', 'Declared release tag resolves to an immutable Git commit.' if tag_commit else 'Declared release tag exists but could not be resolved to a commit.', evidence={'tag': expected_tag, 'tag_commit': tag_commit, 'head': head})
        if tag_commit and head != tag_commit:
            report.add('kristal.git.checkout_at_release_tag', 'WARN', 'release_identity', 'The target checkout is not currently at the declared release tag commit.', evidence={'head': head, 'tag_commit': tag_commit})
        else:
            report.add('kristal.git.checkout_at_release_tag', 'PASS', 'release_identity', 'Target checkout is at the declared release tag commit.', evidence={'head': head, 'tag_commit': tag_commit})
    else:
        candidate = release.get('status') == 'release-candidate'
        report.add('kristal.git.candidate_unpublished_state', 'PASS' if candidate else 'WARN', 'release_identity', 'Release candidate metadata is prepared but the declared tag has not been published yet.' if candidate else 'Declared release tag is absent.', evidence={'tag': expected_tag, 'head': head, 'release_status': release.get('status')})
