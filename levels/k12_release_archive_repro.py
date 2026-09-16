from __future__ import annotations

import hashlib
import tempfile
import zipfile
import sys
from pathlib import Path

from ._kristal_helpers import copy_repo, git, init_git_repo, run as run_cmd, combined


def build(root: Path, allow_dirty: bool = False):
    argv = [sys.executable, 'tools/build_release_archive.py']
    if allow_dirty:
        argv.append('--allow-dirty')
    cp = run_cmd(argv, root, 90)
    if cp.returncode:
        return None, combined(cp), None
    zips = sorted((root / 'dist').glob('*.zip'))
    if not zips:
        return None, combined(cp) + '\nno archive found', None
    p = zips[0]
    return hashlib.sha256(p.read_bytes()).hexdigest(), combined(cp), p


def make_repo(src: Path, dst: Path):
    copy_repo(src, dst)
    ok, evidence = init_git_repo(dst)
    return ok, evidence


def run(cfg, report):
    src = Path(cfg['_target_root'])
    with tempfile.TemporaryDirectory(prefix='kristal-archive-') as d:
        d = Path(d)
        a, b = d / 'a', d / 'b'
        oka, ea = make_repo(src, a); okb, eb = make_repo(src, b)
        if not (oka and okb):
            report.add('kristal.archive.git_fixture', 'BLOCKED', 'reproducibility', 'Could not create temporary Git fixtures required by the rc.2 archive builder.', evidence={'a': ea, 'b': eb})
            return

        ha, oa, za = build(a); hb, ob, zb = build(b)
        report.add(
            'kristal.archive.deterministic', 'PASS' if ha and ha == hb else 'FAIL', 'reproducibility',
            'Two independent clean Git release archive builds are byte-identical.' if ha and ha == hb else 'Independent clean Git archive builds did not produce the same bytes.',
            evidence={'sha_a': ha, 'sha_b': hb, 'a_output': oa[-1500:], 'b_output': ob[-1500:]},
        )

        if za:
            with zipfile.ZipFile(za) as z:
                infos = z.infolist(); names = z.namelist()
                bad_ts = [i.filename for i in infos if i.date_time != (1980, 1, 1, 0, 0, 0)]
            report.add('kristal.archive.fixed_timestamps', 'PASS' if not bad_ts else 'FAIL', 'reproducibility', 'Archive entry timestamps are fixed.' if not bad_ts else 'Archive has variable timestamps.', evidence=bad_ts[:20] or None)
            forbidden = [n for n in names if n.startswith('.git/') or n.startswith('dist/') or n.startswith('site/') or '/__pycache__/' in n or n == 'CODE_SNAPSHOT_MANIFEST.md']
            report.add('kristal.archive.forbidden_paths', 'PASS' if not forbidden else 'FAIL', 'release_hygiene', 'Archive excludes VCS/build/snapshot-local artifacts.' if not forbidden else 'Archive contains excluded release artifacts.', evidence=forbidden[:50] or None)

        # Untracked files make the normal release build dirty and therefore must be rejected.
        u = d / 'untracked'; oku, eu = make_repo(src, u)
        if oku:
            (u / '.levelupdiag').mkdir(exist_ok=True); (u / '.levelupdiag/evidence.txt').write_text('diagnostic evidence\n', encoding='utf-8')
            (u / 'random.tmp').write_text('untracked\n', encoding='utf-8')
            normal_sha, normal_out, _ = build(u, allow_dirty=False)
            report.add('kristal.archive.untracked_normal_rejected', 'PASS' if normal_sha is None else 'FAIL', 'release_hygiene', 'Normal release build rejects a dirty worktree containing untracked diagnostics.' if normal_sha is None else 'Normal release build accepted an untracked dirty worktree.', evidence=normal_out[-2500:])
            allow_sha, allow_out, allow_zip = build(u, allow_dirty=True)
            included = []
            if allow_zip:
                with zipfile.ZipFile(allow_zip) as z:
                    included = [n for n in z.namelist() if n.startswith('.levelupdiag/') or n == 'random.tmp']
            report.add('kristal.archive.untracked_allow_dirty_isolated', 'PASS' if allow_sha == ha and not included else 'FAIL', 'release_hygiene', 'Diagnostic --allow-dirty build ignores untracked files and preserves archive identity.' if allow_sha == ha and not included else '--allow-dirty archive was affected by untracked diagnostic files.', evidence={'clean_sha': ha, 'allow_dirty_sha': allow_sha, 'included': included, 'output': allow_out[-2000:]})

        # A modified tracked file must be rejected by the normal release builder.
        t = d / 'tracked-dirty'; okt, et = make_repo(src, t)
        if okt:
            p = t / 'README.md'; p.write_text(p.read_text(encoding='utf-8') + '\nLevelUpDiag tracked mutation.\n', encoding='utf-8')
            dirty_sha, dirty_out, _ = build(t, allow_dirty=False)
            report.add('kristal.archive.tracked_dirty_rejected', 'PASS' if dirty_sha is None else 'FAIL', 'release_hygiene', 'Normal release build rejects modified tracked bytes.' if dirty_sha is None else 'Normal release build accepted modified tracked bytes.', evidence=dirty_out[-2500:])
