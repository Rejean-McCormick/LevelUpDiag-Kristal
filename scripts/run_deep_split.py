from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.config import load_config
from levelupdiag_core.manifest import load_manifest, resolve_selection
from levelupdiag_core.verdicts import campaign_verdict, exit_code


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def run_campaign_selection(target: str, selection: str, out_dir: Path):
    cmd = [sys.executable, str(ROOT / 'levelupdiag.py'), '--target', target, 'run', selection]
    cp = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    (out_dir / f'{selection}.log').write_text(cp.stdout, encoding='utf-8')
    latest_summary = ROOT / '.levelupdiag' / 'latest' / 'summary.json'
    summary = read_json(latest_summary) if latest_summary.exists() else None
    if summary:
        write_json(out_dir / f'{selection}.summary.json', summary)
    return cp.returncode, summary


def run_isolated_level(target: str, meta: dict, out_dir: Path, stamp: str):
    lid = meta['id']
    run_id = f'deep-split-{stamp}-{lid}'
    result_path = out_dir / 'results' / f'{lid}.result.json'
    result_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(ROOT / 'levelupdiag.py'), '_worker',
        '--level', lid,
        '--run-id', run_id,
        '--output', str(result_path),
        '--target', target,
    ]
    timeout = int(meta.get('timeout_seconds') or 300)
    try:
        cp = subprocess.run(
            cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout, check=False,
        )
        output = cp.stdout or ''
        code = cp.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or '') if isinstance(exc.stdout, str) else ''
        code = 30
        now = utc_now()
        write_json(result_path, {
            'schema': 'levelupdiag.report.v2',
            'standard': 'LevelUpDiag',
            'standard_version': '1.0.0',
            'run_id': run_id,
            'level_id': lid,
            'level_name': meta['name'],
            'purpose': meta.get('purpose', ''),
            'target_repo_root': target,
            'started_at': now,
            'ended_at': now,
            'verdict': 'INFRA_ERROR',
            'findings': [{
                'id': 'diagnostics.worker.timeout',
                'verdict': 'INFRA_ERROR',
                'category': 'diagnostics',
                'message': f'Isolated split worker exceeded its {timeout}s timeout.',
            }],
            'artifacts': [],
            'metrics': {},
        })
    (out_dir / f'{lid}.log').write_text(output, encoding='utf-8')
    if not result_path.exists():
        now = utc_now()
        write_json(result_path, {
            'schema': 'levelupdiag.report.v2', 'standard': 'LevelUpDiag', 'standard_version': '1.0.0',
            'run_id': run_id, 'level_id': lid, 'level_name': meta['name'], 'purpose': meta.get('purpose', ''),
            'target_repo_root': target, 'started_at': now, 'ended_at': now, 'verdict': 'ERROR',
            'findings': [{'id': 'diagnostics.worker.missing_result', 'verdict': 'ERROR', 'category': 'diagnostics', 'message': 'Isolated split worker did not produce a result file.', 'evidence': {'exit_code': code, 'output_tail': output[-4000:]}}],
            'artifacts': [], 'metrics': {},
        })
    data = read_json(result_path)
    latest_result = ROOT / '.levelupdiag' / 'latest' / lid / 'result.json'
    latest_result.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(result_path, latest_result)
    return code, data


def main() -> int:
    ap = argparse.ArgumentParser(description='Run Kristal deep diagnostics in isolated selections and consolidate the result.')
    ap.add_argument('--target', help='Kristal repository path; default comes from levelupdiag.config.json')
    ap.add_argument('--only', help='Diagnostic subset of Kristal levels, comma-separated (for harness testing). Default runs all K levels.')
    args = ap.parse_args()

    cfg = load_config(ROOT, args.target)
    target = cfg['_target_root']
    manifest = load_manifest(ROOT)
    deep_meta = resolve_selection(manifest, 'deep')
    deep_levels = [x['id'] for x in deep_meta]
    level_meta = {x['id']: x for x in manifest['levels']}
    kristal_meta = [x for x in deep_meta if x['id'].startswith('K')]
    partial = False
    if args.only:
        requested = {x.strip().upper() for x in args.only.split(',') if x.strip()}
        known_k = {x['id'] for x in kristal_meta}
        unknown = sorted(requested - known_k)
        if unknown:
            ap.error('unknown --only level(s): ' + ', '.join(unknown))
        kristal_meta = [x for x in kristal_meta if x['id'] in requested]
        deep_levels = [x['id'] for x in deep_meta if not x['id'].startswith('K')] + [x['id'] for x in kristal_meta]
        partial = True

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    control = ROOT / '.levelupdiag'
    out_dir = control / 'split-runs' / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    invocations = []

    # Run shared prerequisite campaigns once.
    for selection in ('baseline', 'N05'):
        code, summary = run_campaign_selection(target, selection, out_dir)
        selected_verdict = None
        run_id = None
        if summary:
            run_id = summary.get('run_id')
            if selection == 'baseline':
                selected_verdict = summary.get('verdict')
            else:
                row = next((r for r in summary.get('levels', []) if r.get('id') == 'N05'), None)
                selected_verdict = (row or {}).get('verdict') or summary.get('verdict')
        invocations.append({'selection': selection, 'exit_code': code, 'verdict': selected_verdict, 'run_id': run_id, 'log': f'{selection}.log'})
        print(f"{selection:>8}: verdict={selected_verdict or 'UNKNOWN':<12} exit={code}")

    # Run each Kristal-specific level once, directly and in process isolation.
    for meta in kristal_meta:
        code, data = run_isolated_level(target, meta, out_dir, stamp)
        verdict = data.get('verdict', 'ERROR')
        invocations.append({'selection': meta['id'], 'exit_code': code, 'verdict': verdict, 'run_id': data.get('run_id'), 'log': f"{meta['id']}.log"})
        print(f"{meta['id']:>8}: verdict={verdict:<12} exit={code}")

    consolidated = []
    missing = []
    for lid in deep_levels:
        rp = control / 'latest' / lid / 'result.json'
        if not rp.exists():
            missing.append(lid)
            consolidated.append({'id': lid, 'name': level_meta[lid]['name'], 'verdict': 'ERROR', 'source_run_id': None})
            continue
        data = read_json(rp)
        consolidated.append({'id': lid, 'name': data.get('level_name', level_meta[lid]['name']), 'verdict': data.get('verdict', 'ERROR'), 'source_run_id': data.get('run_id')})

    required_map = {lid: bool(level_meta[lid].get('required', False)) for lid in deep_levels}
    campaign_rows = [{'level_id': r['id'], 'verdict': r['verdict']} for r in consolidated]
    verdict = campaign_verdict(campaign_rows, required_map)
    counts = {}
    for row in consolidated:
        counts[row['verdict']] = counts.get(row['verdict'], 0) + 1

    summary = {
        'schema': 'levelupdiag.campaign-summary.v2',
        'standard': 'LevelUpDiag',
        'standard_version': manifest.get('standard_version', '1.0.0'),
        'run_id': f'deep-split-{stamp}',
        'selection': 'deep-split-partial' if partial else 'deep-split',
        'target_repo_root': target,
        'started_at': started_at,
        'ended_at': utc_now(),
        'verdict': verdict,
        'counts': counts,
        'expected_levels': deep_levels,
        'required_levels': [lid for lid in deep_levels if required_map[lid]],
        'levels': consolidated,
        'split_invocations': invocations,
        'missing_level_results': missing,
        'split_evidence_dir': str(out_dir),
    }
    write_json(out_dir / 'summary.json', summary)
    (out_dir / 'summary.txt').write_text(
        '\n'.join([
            f'LevelUpDiag deep-split - {verdict}',
            f'Target: {target}', '',
            *[f"{r['id']:>3}  {r['verdict']:<12} {r['name']}" for r in consolidated],
            '', f'Evidence: {out_dir}',
        ]) + '\n', encoding='utf-8',
    )

    latest = control / 'latest'
    latest.mkdir(parents=True, exist_ok=True)
    write_json(latest / 'summary.json', summary)
    shutil.copy2(out_dir / 'summary.txt', latest / 'summary.txt')
    write_json(latest / 'split-summary.json', summary)

    print('')
    print(f'DEEP SPLIT OVERALL: {verdict}')
    for row in consolidated:
        print(f"  {row['id']:>3}  {row['verdict']:<12} {row['name']}")
    print(f'Split evidence: {out_dir}')
    return exit_code(verdict)


if __name__ == '__main__':
    raise SystemExit(main())
