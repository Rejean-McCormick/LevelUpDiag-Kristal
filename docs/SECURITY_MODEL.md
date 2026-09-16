# Security and non-mutation model

LevelUpDiag is diagnostic tooling, not an OS sandbox.

This Kristal adaptation reduces risk by:

- living outside the target repository;
- storing generated evidence under the harness repo;
- not auto-executing discovered project commands;
- using `shell=False`;
- bounding commands with timeouts;
- blocking validators declared mutating/networked unless explicitly enabled;
- copying Kristal to a temporary directory before adversarial mutation;
- redacting common credential assignments from command output;
- bounding source/security scans;
- sampling target tracked Git state before and after campaigns.

The generic security level is a **hygiene heuristic**, not a security audit.

## Trust assumptions

A declared native validator executes with the user's OS permissions. A malicious target repository could therefore execute malicious code if a validator imports/runs target code. Run qualification campaigns in a disposable CI worker or constrained development environment when the target is not trusted.

## Network

Network use is disabled by default. The current deep suite is designed to run locally except for dependency installation done outside the campaign.

## Secrets

Do not commit credentials to this repository or `levelupdiag.config.local.json`. Evidence should be reviewed before external publication even though output redaction is enabled.
