# Configuration reference

Configuration is JSON. `levelupdiag.config.json` is committed. `levelupdiag.config.local.json`, when present, is recursively merged over it and is ignored by Git.

## Core keys

- `target_repo_root`: target Kristal checkout. This repo commits `../kristal-framework`. Relative paths resolve from the harness repository root.
- `control_root`: `"tool"` stores evidence under this harness; `"target"` is supported by the inherited core but is not recommended for this adaptation.
- `control_dir`: generated evidence directory relative to the selected control root.
- `execution.max_parallel`: maximum simultaneous process-isolated levels.
- `execution.default_timeout_seconds`: default external command timeout.
- `execution.fail_fast`: stop scheduling new levels after a hard failure.
- `execution.capture_limit_kb`: bound stdout/stderr stored per command.
- `execution.protect_tracked_files`: compare target tracked Git state before/after a campaign.
- `execution.allow_target_mutation`: allow declared validators marked mutating. Normally false.
- `execution.allow_network`: allow declared validators marked networked. Normally false.
- `scan.*`: bounded scanner limits and exclusions.
- `validators`: explicit native target validators.
- `security.additional_patterns`: optional extra hygiene patterns; never place secrets here.

## Local override example

```json
{
  "target_repo_root": "C:/mycode/Kristal/kristal-framework",
  "execution": {
    "max_parallel": 4
  }
}
```

## Validator object

```json
{
  "id": "stable-id",
  "name": "Human name",
  "command": ["executable", "arg"],
  "cwd": ".",
  "required": true,
  "timeout_seconds": 300,
  "mutates_target": false,
  "network": false,
  "enabled": true
}
```

Commands use argument arrays and execute with `shell=False`. Discovery does not imply execution.

## External implementation adapter

Implementation conformance is intentionally external to the Kristal framework repository. Configure the adapter in `levelupdiag.config.local.json`, not in the committed default config.

```json
{
  "implementation_adapter": {
    "enabled": true,
    "cwd": "../kristal-reference",
    "commands": {
      "exchange_id": ["..."],
      "verify_exchange": ["..."],
      "build_runtime_pack": ["..."],
      "verify_runtime_pack": ["..."],
      "verify_signature": ["..."],
      "verify_trust": ["..."]
    }
  }
}
```

v0.3 uses the first four operation declarations for implementation-readiness evidence. `verify_signature` and `verify_trust` are required before K24 can move beyond `BLOCKED`/`PARTIAL`. Portable signed-fixture I/O semantics are intentionally not invented by the harness.
