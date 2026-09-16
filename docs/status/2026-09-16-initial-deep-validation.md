> **Historical v0.2 evidence — superseded by Kristal rc.2 and LevelUpDiag v0.3.**
> The findings below describe the pre-rc.2 release model that motivated the correction. Do not follow the old recommendation to regenerate `schema-set.manifest.json`; rc.2 intentionally retired that file and `tools/build_manifests.py` in favor of the curated Git-pinned release model.

# Kristal Deep Validation Report — 2026-09-16

## Verdict

**Not production-qualified yet.**

The framework/release integrity gate is healthy in several important areas, but the deeper campaign found release-integrity gaps and missing executable implementation-conformance coverage.

## Strong passes

- Native `python tools/validate_release.py`: PASS.
- Version alignment: PASS.
- Documentation local links/navigation: PASS.
- Published JCS vectors: PASS.
- JCS fail-closed mutation tests: PASS for tampered expected hash and tampered input vector.
- Schema negative campaign: **210/210 invalid mutations rejected**, including 192 required-field removals.
- Security hygiene bounded scan: PASS; 98 files scanned, no configured secret-pattern matches or high-risk filenames.
- Release archive reproducibility on two clean copies: PASS; byte-identical SHA-256.
- Release archive timestamps are fixed and common VCS/build outputs are excluded.

## Confirmed failures / blockers

### 1. `schema-set.manifest.json` is stale

All **13/13** schema file hashes recorded in `schema-set.manifest.json` differ from the actual schema bytes in the uploaded source snapshot. This condition existed in the source snapshot before the validation-status documentation changes.

The manifest's aggregate digest is internally consistent with its own stale entries, but those entries no longer describe the current schema files.

### 2. `validate_release.py` does not fail closed on schema-manifest drift

Mutation tests proved that the current release gate accepts:

- a normative schema content modification without updating `schema-set.manifest.json`;
- a deliberately falsified schema entry hash inside `schema-set.manifest.json`.

Both mutated repositories still returned `Kristal framework/release integrity validation: PASS`.

This is a release-integrity gap and should be fixed before stable production qualification.

### 3. `build_manifests.py` is inconsistent with current release policy

`RELEASE.md` says `contract-set.manifest.json` is a curated index of public contract surfaces and is not a per-file inventory. The existing `build_manifests.py` still tries to generate a hashed file inventory and therefore reports all three generated files as out of date:

- `contract-set.manifest.json`
- `schema-set.manifest.json`
- `kristal-release.json`

The tool should be rewritten or retired. It must not be used blindly to regenerate current release metadata.

### 4. Release ZIP includes LevelUpDiag runtime evidence

`build_release_archive.py` is deterministic on clean inputs, but it does not exclude `.levelupdiag/`. Adding only `.levelupdiag/evidence.txt` changes the archive hash and the evidence file is included in the release ZIP.

If LevelUpDiag is used, run it externally or update the archive exclusion list before integrating it into the repository/CI workspace.

### 5. EX/RP implementation conformance is documented but not executable

The normative reproducibility document defines:

- EX-1, EX-2, EX-3, EX-4
- RP-1, RP-2, RP-3, RP-4, RP-5, RP-6

No executable Exchange/Runtime Pack conformance suite or reference Exchange/Runtime Pack builder-verifier was found in this Kristal framework repository.

Therefore reference implementation conformance cannot yet be demonstrated from this repository alone.

## Environment-blocked evidence

- `mkdocs build --strict` could not be executed locally because `mkdocs` is not installed and this sandbox has no package-network access. The committed CI workflow declares the strict MkDocs build, so this should be verified by the actual GitHub Actions run.
- Git tag/commit/clean-tree release identity cannot be verified from the extracted snapshot because `.git` metadata is not present.
- A second independent RFC 8785 implementation could not be installed because the environment has no package-network access. The bundled Node JCS vectors and mutation tests do pass.

## Production qualification gates recommended

Before promoting from RC to stable production-qualified status:

1. Fix and verify `schema-set.manifest.json` against actual schema bytes.
2. Make `validate_release.py` recompute and verify every schema manifest hash and the aggregate schema-set digest.
3. Rewrite/retire `build_manifests.py` so one manifest model is authoritative.
4. Exclude `.levelupdiag/` from release archives, or keep LevelUpDiag external.
5. Turn EX-1..EX-4 and RP-1..RP-6 into executable fixtures.
6. Add a reference Exchange build/verify implementation and Runtime Pack build/verify implementation, or run the TCK against the implementation repository that owns those functions.
7. Run `mkdocs build --strict` in CI and retain its evidence.
8. Run the same conformance fixtures on at least Windows and Linux.
9. Add a second independent RFC 8785 implementation to the cross-toolchain campaign.
10. Run Da’at + Interaction Kernel end-to-end build/revision/artifact-ready tests with retry, duplication, corruption and crash recovery.

## LevelUpDiag assessment

Use LevelUpDiag as the **test campaign orchestrator and evidence model**. Do not reimplement Kristal logic in LevelUpDiag.

Recommended split:

```text
Kristal native tools/tests
    validate_release.py
    schema/JCS/TCK tests
    Exchange/Runtime Pack builder/verifier tests
    Da’at/IK E2E tests
           |
           v
LevelUpDiag
    scheduling
    timeout/isolation
    PASS/WARN/FAIL/BLOCKED semantics
    security/repository baseline
    evidence capture/history
           |
           v
CI release qualification
```

This is not overkill for Kristal because determinism, content identity and fail-closed behavior are core product requirements rather than optional QA concerns.
