# levelupdiag_kristal

External deep-validation, release-integrity and adversarial test harness for **Kristal Framework**.

This repository is intentionally separate from `kristal-framework`.

Recommended Windows layout:

```text
C:\mycode\Kristal\
├── kristal-framework\
└── levelupdiag_kristal\
```

The committed default target is `..\kristal-framework`. All LevelUpDiag source, configuration and generated evidence stay in this repository. The Kristal target is treated as read-only except inside temporary copies created by adversarial tests.

## Quick start

GUI, no console flash:

```text
LEVELUPDIAG_KRISTAL_LAUNCHER.pyw
```

PowerShell:

```powershell
cd C:\mycode\Kristal\levelupdiag_kristal
python -m pip install -r requirements-dev.txt
.\RUN_KRISTAL_DEEP_SPLIT.ps1
```

Direct:

```bash
python scripts/run_deep_split.py --target ../kristal-framework
```

## Validation levels

| Level | Purpose |
|---|---|
| N00 | harness integrity |
| N01 | target/VCS/runtime context |
| N02 | bounded repository inventory |
| N03 | repository hygiene |
| N04 | tooling discovery |
| N05 | native Kristal validators declared in config |
| N06 | bounded security/secret hygiene |
| K10 | rc.2 curated release-model integrity |
| K11 | adversarial native release-gate mutations |
| K12 | deterministic Git release archive + dirty/untracked behavior |
| K13 | negative JSON Schema mutation campaign |
| K14 | JCS fail-closed/tamper campaign |
| K15 | framework TCK coverage vs external implementation adapter |
| K16 | strict MkDocs build |
| K17 | retired release-model guard |
| K18 | v5 normative/version hygiene |
| K19 | JSON Schema `date-time` / URI fail-closed validation |
| K20 | cross-document normative invariant mutations |
| K21 | Git VERSION/tag/commit release identity |
| K22 | TCK identity-profile consistency |
| K23 | Runtime Pack type/version/profile/tamper contract |
| K24 | signature/trust contract + executable verifier readiness |

## Kristal rc.2 model

v0.4 follows the current Kristal release model:

```text
Git tag + immutable commit
        ↓
curated contract-set.manifest.json
        ↓
framework/release validation
        ↓
framework-vector TCK
```

The following are intentionally retired and their reappearance is a failure:

```text
schema-set.manifest.json
tools/build_manifests.py
```

`contract-set.manifest.json` is not an exhaustive per-file hash inventory.

## Deep Split

`Deep Split` is the recommended maximum campaign on Windows. Heavy levels run as isolated LevelUpDiag invocations, and v0.4 consolidates them afterward into one authoritative summary:

```text
.levelupdiag/latest/summary.json
.levelupdiag/latest/summary.txt
.levelupdiag/latest/split-summary.json
.levelupdiag/split-runs/<timestamp>/
```

The final summary represents the **whole deep campaign**. It no longer reports PASS merely because the last isolated level passed.

Run it with:

```powershell
.\RUN_KRISTAL_DEEP_SPLIT.ps1
```

or:

```bash
python scripts/run_deep_split.py --target ../kristal-framework
```

## Verdict semantics

```text
PASS
WARN
FAIL
SKIP
BLOCKED
PARTIAL
ERROR
INFRA_ERROR
CONFIG_ERROR
```

A required `BLOCKED`, `PARTIAL`, missing result or infrastructure failure is never promoted to PASS.

For Kristal, these claims stay distinct:

```text
framework/release integrity PASS
!=
implementation conformance PASS
!=
production qualification PASS
```

With `kristal-reference` configured, K15 executes the official Exchange/Runtime Pack core vectors against the external implementation and K24 executes independent Ed25519/trust fixtures. RP-2..RP-5 remain a later byte-format qualification surface until the framework publishes sufficiently pinned fixtures/profiles.

## External implementation adapter

Do not place a reference implementation inside `kristal-framework` only to satisfy the harness. Keep it external and configure it locally:

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
      "verify_runtime_profiles": ["..."],
      "verify_signature": ["..."],
      "verify_trust": ["..."]
    }
  }
}
```

Use `levelupdiag.config.local.json`; it is machine-local and Git-ignored. The repository also includes `CONFIGURE_REFERENCE_ADAPTER.pyw`, which safely creates/updates this local adapter block for the standard sibling layout.

## Evidence boundary

Generated evidence belongs here:

```text
levelupdiag_kristal/.levelupdiag/
```

Normal diagnostics do not write `.levelupdiag` into Kristal.

Adversarial levels create temporary copies. K12 additionally initializes temporary Git repositories because the Kristal rc.2 release archive builder correctly requires Git metadata.

## Requirements

For the full campaign:

- Python 3.10+
- Git
- Node.js (`node`)
- packages in `requirements-dev.txt`
- MkDocs for K16 / native full validation
- sibling `kristal-framework`, or explicit `--target`

Recommended setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Other campaigns

Read-oriented baseline:

```bash
python levelupdiag.py run baseline
```

Baseline + declared native validators:

```bash
python levelupdiag.py run standard
```

Single-process full campaign:

```bash
python levelupdiag.py run deep
```

Individual levels:

```bash
python levelupdiag.py run K12
python levelupdiag.py run K21
python levelupdiag.py run K24
```

## Harness self-test

```bash
python -m unittest discover -s tests -v
python levelupdiag.py list
```

On Windows:

```powershell
.\VALIDATE_HARNESS.ps1
```

## Ownership boundary

This repository owns validation orchestration, adversarial test definitions, qualification evidence and adapter boundaries.

It does **not** own Kristal schemas, Exchange/Runtime Pack semantics, Da’at implementation, Interaction Kernel contracts, or Orgo/Konnaxion operational state.

### Runtime Pack portable profile (v0.5)

When `kristal-reference >= 0.2.0` is connected, K15 executes RP-2 through RP-5 against `kristal.v5:runtime-pack-portable-conformance@1` and requires exact golden bytes. Rerun `CONFIGURE_REFERENCE_ADAPTER.pyw` after applying the v0.5 overlay so the local adapter config receives the `verify_runtime_profiles` operation.
