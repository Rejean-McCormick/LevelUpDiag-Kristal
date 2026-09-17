# Result and campaign model

Generated evidence lives under `levelupdiag_kristal/.levelupdiag/`. Each normal LevelUpDiag run writes:

```text
.levelupdiag/runs/<run-id>/levels/<level-id>/result.json
.levelupdiag/runs/<run-id>/summary.json
.levelupdiag/runs/<run-id>/summary.txt
```

`latest/` contains convenience copies and does not replace history.

## Campaign aggregation

1. diagnostics/config errors cannot become target success;
2. any executed target `FAIL` makes the campaign `FAIL`;
3. required `SKIP`, `BLOCKED`, `PARTIAL`, or `INFRA_ERROR` makes evidence incomplete (`BLOCKED`);
4. equivalent statuses on optional levels degrade to `WARN`;
5. `WARN` remains accepted but visible;
6. missing results are never final evidence.

A level's `required` flag affects completeness, not whether an observed `FAIL` matters. An optional level that actually executes and finds a target failure is still a failure.

## Deep Split aggregation

`RUN_KRISTAL_DEEP_SPLIT` deliberately runs heavy selections separately. In v0.4 it reconstructs the complete `deep` level set from the resulting evidence and writes a master summary:

```text
.levelupdiag/split-runs/<timestamp>/summary.json
.levelupdiag/latest/summary.json
.levelupdiag/latest/split-summary.json
```

The final `latest/summary.json` therefore represents **the complete split campaign**, not the last isolated level executed.

Every consolidated level row records `source_run_id`, because different levels may come from different isolated invocations.
