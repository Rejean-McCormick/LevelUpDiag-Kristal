# Kristal validation matrix

## Native framework and release surfaces

| Area | Evidence | Harness level |
|---|---|---|
| complete native framework gate | `tools/validate_release.py` / `tools/validate_conformance.py` | N05 |
| version/canonicalization/release metadata | independent cross-check | K10 |
| curated contract surfaces + retired model absence | independent cross-check | K10 / K17 |
| adversarial release-gate mutations | isolated temporary copies | K11 |
| Git-only deterministic release ZIP | temporary committed Git fixtures | K12 |
| generated negative JSON Schema cases | schema/example mutation campaign | K13 |
| JCS tamper/fail-closed | vector mutation campaign | K14 |
| framework TCK vs implementation coverage | EX/RP inventory + adapter readiness | K15 |
| strict documentation build | `mkdocs build --strict` | K16 |
| retired manifest model guard | docs/tool/archive policy cross-check | K17 |
| v5 normative hygiene | documentation/version scan | K18 |
| JSON Schema format enforcement | invalid date-time + URI mutations | K19 |
| cross-document semantic invariants | runtime pack/reference-exchange mutations | K20 |
| Git tag/commit/version identity | actual target Git metadata | K21 |
| TCK/profile consistency | vectors + docs + native conformance gate | K22 |
| Runtime Pack contract | type/version/profile/tamper semantics | K23 |
| signatures/trust | contract checks + external crypto adapter requirement | K24 |

## rc.2 release model

LevelUpDiag v0.4 follows the Kristal rc.2 release model:

- Git tag + immutable commit identify published repository bytes;
- `contract-set.manifest.json` is a curated contract-surface index, not a per-file hash inventory;
- `schema-set.manifest.json` is retired;
- `tools/build_manifests.py` is retired;
- the release archive is built from Git-tracked files;
- normal release archive builds require a clean worktree;
- `--allow-dirty` is diagnostic-only and must not admit untracked files into the archive.

## K11 — global fail-closed gate

K11 verifies that `tools/validate_release.py` rejects:

- `VERSION` / release mismatch;
- an example downgraded to schema version 4.0;
- an invalid schema `$id`;
- a broken local documentation link;
- a missing curated contract surface;
- a tampered JCS expected hash;
- an unsupported canonicalization version;
- reappearance of `schema-set.manifest.json`;
- reappearance of `tools/build_manifests.py`.

Format-specific and cross-document semantic mutations live in K19 and K20 rather than being duplicated here.

## K12 — Git release archive

K12 creates fresh temporary Git repositories from the current target bytes, commits them, then verifies:

- two independent clean builds are byte-identical;
- ZIP timestamps are fixed;
- `.git`, `dist`, `site`, Python caches and `CODE_SNAPSHOT_MANIFEST.md` are excluded;
- the normal builder rejects untracked/dirty worktrees;
- diagnostic `--allow-dirty` builds ignore untracked `.levelupdiag` and arbitrary temporary files;
- modified tracked bytes are rejected by the normal builder.

The test no longer strips `.git` and then asks a Git-dependent builder to run.

## K15 — implementation conformance boundary

Framework-vector conformance and implementation conformance remain distinct.

Required normative acceptance cases:

```text
EX-1 EX-2 EX-3 EX-4
RP-1 RP-2 RP-3 RP-4 RP-5 RP-6
```

K15 expects the framework TCK and vectors to exist. Full implementation conformance remains `BLOCKED` until an external implementation adapter is configured with at least:

```text
exchange_id
verify_exchange
build_runtime_pack
verify_runtime_pack
verify_runtime_profiles
```

The implementation does not need to live in `kristal-framework`.

## K19–K24

K19 verifies `FormatChecker`-style enforcement using invalid date-time and URI mutations.

K20 breaks cross-document invariants, including Runtime Pack version/type conventions and mandatory authority recognition for Reference Exchange.

K21 distinguishes an unpublished release-candidate worktree from a published tag. A dirty worktree is visible as `WARN`; a published tag with a missing/mismatched immutable commit pin is a `FAIL`.

K22 verifies that Exchange and Runtime Pack vector profiles agree with the TCK documentation and native conformance gate.

K23 verifies Runtime Pack artifact type, version shape, core `5.0.0` vectors and explicit tamper rejection.

K24 validates the published security contract but remains `BLOCKED` for executable cryptographic conformance until an external verifier exposes signature/trust operations. A contract-only PASS is not promoted to production-security PASS.


## Portable Runtime Pack implementation gate

K15 uses `verify_runtime_profiles` to execute RP-002, RP-003, RP-004, RP-005, and RP-005-NORUN under `kristal.v5:runtime-pack-portable-conformance@1`. Exact bytes are required.
