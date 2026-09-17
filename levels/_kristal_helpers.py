from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

IGNORE_NAMES = {
    '.git', '.levelupdiag', 'dist', 'site', '__pycache__', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', '.tox', 'node_modules',
}


def copy_repo(src: Path, dst: Path) -> None:
    """Copy current working bytes without VCS/runtime evidence."""
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(*sorted(IGNORE_NAMES)),
    )


def run(argv: list[str], cwd: Path, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout,
        check=False,
    )


def combined(cp: subprocess.CompletedProcess[str], limit: int = 8000) -> str:
    return ((cp.stdout or '') + (cp.stderr or ''))[-limit:]


def validate_release(root: Path, timeout: int = 90) -> tuple[int, str]:
    cp = run([sys.executable, 'tools/validate_release.py'], root, timeout)
    return cp.returncode, combined(cp)


def validate_conformance(root: Path, timeout: int = 90) -> tuple[int, str]:
    cp = run([sys.executable, 'tools/validate_conformance.py'], root, timeout)
    return cp.returncode, combined(cp)


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def init_git_repo(root: Path) -> tuple[bool, str]:
    """Initialize and commit a deterministic-enough temporary Git repo."""
    env = os.environ.copy()
    env.update({
        'GIT_AUTHOR_NAME': 'LevelUpDiag',
        'GIT_AUTHOR_EMAIL': 'levelupdiag@example.invalid',
        'GIT_COMMITTER_NAME': 'LevelUpDiag',
        'GIT_COMMITTER_EMAIL': 'levelupdiag@example.invalid',
        'GIT_AUTHOR_DATE': '2000-01-01T00:00:00+00:00',
        'GIT_COMMITTER_DATE': '2000-01-01T00:00:00+00:00',
    })
    commands = [
        ['git', 'init', '-q'],
        ['git', 'config', 'user.name', 'LevelUpDiag'],
        ['git', 'config', 'user.email', 'levelupdiag@example.invalid'],
        ['git', 'add', '-A'],
        ['git', 'commit', '-q', '-m', 'LevelUpDiag fixture'],
    ]
    out = []
    for argv in commands:
        try:
            cp = subprocess.run(
                argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace', timeout=60,
                check=False,
            )
        except FileNotFoundError:
            return False, 'git executable not found'
        out.append(f"$ {' '.join(argv)}\n{combined(cp, 2000)}")
        if cp.returncode:
            return False, '\n'.join(out)
    return True, '\n'.join(out)


def git(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return run(['git', *args], root, timeout)


def first_recursive_key(obj, key: str):
    """Return (mapping, key) for first recursive key occurrence, else (None, None)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj, key
        for value in obj.values():
            found, k = first_recursive_key(value, key)
            if found is not None:
                return found, k
    elif isinstance(obj, list):
        for value in obj:
            found, k = first_recursive_key(value, key)
            if found is not None:
                return found, k
    return None, None


def flatten_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from flatten_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from flatten_keys(value)


def adapter_settings(cfg):
    adapter = cfg.get('implementation_adapter') or {}
    cwd = Path(adapter.get('cwd', '.'))
    if not cwd.is_absolute():
        cwd = (Path(cfg['_tool_root']) / cwd).resolve(strict=False)
    return adapter, cwd, adapter.get('commands') or {}


def render_adapter_command(template, **values):
    if not isinstance(template, list) or not template:
        raise ValueError('adapter command must be a non-empty argv list')
    rendered = []
    for item in template:
        text = str(item)
        for key, value in values.items():
            text = text.replace('{' + key + '}', str(value))
        rendered.append(text)
    return rendered


def run_adapter(cfg, operation: str, *, timeout: int = 90, **values):
    adapter, cwd, commands = adapter_settings(cfg)
    if not adapter.get('enabled'):
        raise RuntimeError('implementation adapter is disabled')
    if operation not in commands:
        raise RuntimeError(f'implementation adapter operation is not configured: {operation}')
    argv = render_adapter_command(commands[operation], **values)
    cp = run(argv, cwd, timeout)
    return cp, cwd, argv
