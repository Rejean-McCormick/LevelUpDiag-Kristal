# 2026-09-16 — LevelUpDiag v0.3 realignment for Kristal rc.2

Kristal rc.2 retired the per-file `schema-set.manifest.json` and `tools/build_manifests.py` model, introduced a curated Git-pinned release identity, strengthened `validate_release.py`, added an executable framework-vector TCK, and changed the release archive builder to require a Git worktree.

LevelUpDiag v0.2 still tested the retired model. This produced stale K10/K11/K17 failures and a broken K12 fixture that removed `.git` before invoking a Git-dependent archive builder. Deep Split also left `latest/summary.json` pointing at the last isolated level instead of the complete split campaign.

v0.3 corrects those diagnostics. K10 and K17 validate the rc.2 release model, K11 drops retired hash-manifest assumptions, K12 creates real temporary Git repos, N05 no longer invokes the retired manifest generator, and Deep Split emits a master campaign summary.

The suite also adds K19–K24 for schema formats, cross-document invariants, Git release identity, TCK/profile consistency, Runtime Pack semantics, and signature/trust readiness.

Expected remaining `BLOCKED` evidence is meaningful: implementation conformance and executable crypto/trust conformance require an external implementation adapter. These are not framework defects.
