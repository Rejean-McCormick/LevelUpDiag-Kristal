# Adaptation guide

This repository is already an adaptation of the neutral LevelUpDiag frame for Kristal.

## Principles

1. Prefer public/native Kristal validators before recreating their logic.
2. Add a Kristal level only for an observable contract, adversarial condition, independent cross-check or qualification boundary.
3. Keep destructive mutations in temporary target copies.
4. Keep committed config machine-independent; use `levelupdiag.config.local.json` for local paths.
5. Do not add Da’at/IK/Orgo semantics here unless the test calls their real contracts/implementations.
6. Missing implementation evidence is `BLOCKED`, not PASS.
7. Environment/tool absence is `INFRA_ERROR`, not target FAIL.

See `ADDING_KRISTAL_LEVELS.md` for the level contract used by this adaptation.
