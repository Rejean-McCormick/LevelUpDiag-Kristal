# Kristal validation matrix

## Native/release surfaces

| Area | Evidence | Harness level |
|---|---|---|
| required release files | `tools/validate_release.py` | N05 |
| JSON parse / Draft 2020-12 schemas | native validator | N05 |
| schema IDs | native validator | N05 |
| examples against schemas | native validator | N05 |
| version alignment | `tools/check_version_alignment.py` | N05 |
| docs links/navigation | `tools/check_docs.py` | N05 |
| JCS vectors | `tools/check_jcs_vectors.mjs` | N05 / K14 |
| schema-set coverage/hash/digest | independent cross-check | K10 |
| release metadata/canonicalization identity | independent cross-check | K10 |
| manifest tooling vs release policy | independent cross-check | K17 |
| v5 acceptance-document hygiene | independent cross-check | K18 |

## Adversarial/fail-closed surfaces

K11 creates isolated target copies and verifies that the native release gate rejects critical mutations:

- version/release mismatch;
- downgraded example schema version;
- invalid schema `$id`;
- broken local documentation link;
- missing declared contract surface;
- tampered JCS expected hash;
- normative schema content drift without manifest update;
- tampered schema-manifest hash.

A mutation that is accepted by the native release validator is a **FAIL** even if the baseline release gate is green.

## Reproducibility surfaces

K12 verifies:

- two independent clean release archive builds are byte-identical;
- fixed ZIP timestamps;
- standard VCS/build paths are excluded;
- diagnostic evidence does not contaminate the release artifact.

K13 performs generated negative schema tests by changing `schema_version` and removing top-level required fields from published examples.

K14 verifies JCS fail-closed behavior by tampering expected hashes and vector inputs.

## Implementation-conformance surfaces

K15 inspects whether the documented Exchange and Runtime Pack acceptance cases have executable coverage.

Expected normative case set:

```text
EX-1 EX-2 EX-3 EX-4
RP-1 RP-2 RP-3 RP-4 RP-5 RP-6
```

Until Kristal exposes a reference Exchange/Runtime Pack builder/verifier and executable fixtures, this layer should remain `BLOCKED`, not PASS.

## Future levels

When implementation tooling exists, extend the suite with native Kristal tests rather than duplicating implementation semantics here:

- canonical Exchange byte equality;
- `kristal_id` equality across repeated/cross-toolchain builds;
- signature-envelope invariance;
- fail-closed Exchange verification;
- Runtime Pack `pack_id` equality;
- payload/row-group/index determinism;
- Runtime Pack delete/rebuild identity;
- query-result equivalence;
- revocation/authority/Reader Policy behavior;
- Windows/Linux cross-platform determinism;
- Da’at `build.request -> artifact.ready` E2E;
- retry/idempotency/crash-recovery scenarios through Interaction Kernel.
