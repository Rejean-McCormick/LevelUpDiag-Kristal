# Changelog

## 0.5.0 — 2026-09-16

- Promoted RP-2 through RP-5 from WARN-only coverage to executable implementation conformance under `kristal.v5:runtime-pack-portable-conformance@1`.
- Added `verify_runtime_profiles` to the external adapter contract/configurator.
- K15 now requires exact independent reproduction of RP-002, RP-003, RP-004, RP-005, and RP-005-NORUN golden bytes.
- K23 now guards publication of the complete portable Runtime Pack vector set.

## 0.4.0 — 2026-09-16

- execute K15 against a real external implementation adapter instead of readiness-only checks;
- add deterministic Exchange identity/verification and Runtime Pack build/verify adapter execution;
- execute K24 Ed25519/trust negative cases with independent ephemeral fixtures;
- add `CONFIGURE_REFERENCE_ADAPTER.pyw` for the standard sibling layout;
- update the local adapter example for the Node-based `kristal-reference` repository.

## 0.3.0 — 2026-09-16

- Realigned K10/K11/K17 with Kristal rc.2's curated Git-pinned release model.
- Removed the retired `build_manifests.py --check` validator from N05 configuration.
- Rebuilt K12 around committed temporary Git fixtures and clean/dirty archive behavior.
- Added K19 schema-format fail-closed tests.
- Added K20 cross-document contract mutation tests.
- Added K21 Git release identity checks.
- Added K22 TCK/profile consistency checks.
- Added K23 Runtime Pack contract checks.
- Added K24 signature/trust readiness checks.
- Added external implementation-adapter configuration boundary.
- Fixed Deep Split so `latest/summary.json` is the consolidated campaign result rather than the final isolated level.
- Bundled the no-console Windows `.pyw` launcher and taught it to display the summary verdict.

## 0.2.0 — 2026-09-16

- Initial standalone external Kristal validation repository.
- Added K10–K18 deep diagnostics and split-run support.
