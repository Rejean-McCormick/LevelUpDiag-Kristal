from __future__ import annotations

import copy
from pathlib import Path
from .util import read_json


class ConfigError(RuntimeError):
    pass


def _merge(base, overlay):
    out = copy.deepcopy(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(tool_root: Path, target_override=None):
    base_path = tool_root / "levelupdiag.config.json"
    if not base_path.exists():
        raise ConfigError(f"Missing configuration: {base_path}")
    cfg = read_json(base_path)
    local = tool_root / "levelupdiag.config.local.json"
    if local.exists():
        cfg = _merge(cfg, read_json(local))
    if cfg.get("schema") != "levelupdiag.config.v2":
        raise ConfigError("Unsupported config schema")

    target_value = target_override or cfg.get("target_repo_root", "auto")
    if str(target_value).lower() == "auto":
        target = tool_root.parent
    else:
        p = Path(target_value).expanduser()
        target = p if p.is_absolute() else (tool_root / p)
    target = target.resolve(strict=False)
    if not target.exists() or not target.is_dir():
        raise ConfigError(f"Target repository root is not a directory: {target}")

    cfg["_tool_root"] = str(tool_root.resolve())
    cfg["_target_root"] = str(target)

    control = Path(cfg.get("control_dir", ".levelupdiag"))
    if control.is_absolute():
        raise ConfigError("control_dir must be relative")

    control_owner = str(cfg.get("control_root", "target")).lower()
    if control_owner == "tool":
        base = tool_root.resolve()
    elif control_owner == "target":
        base = target
    else:
        raise ConfigError("control_root must be 'tool' or 'target'")

    control_root = (base / control).resolve(strict=False)
    if not control_root.is_relative_to(base):
        raise ConfigError("control_dir escapes configured control_root")

    cfg["_control_owner"] = control_owner
    cfg["_control_root"] = str(control_root)
    return cfg
