# Adding Kristal-specific levels

A Kristal-specific level belongs here only when it tests an observable contract without reimplementing Kristal semantics.

Good examples:

- compare a declared manifest hash with actual file bytes;
- mutate an isolated copy and ensure a native validator rejects it;
- run the same native builder twice and compare artifact identities;
- invoke a native verifier on corrupted input;
- check the presence/execution of normative fixtures.

Bad examples:

- independently implement the Kristal canonicalization algorithm inside LevelUpDiag and call disagreement a target failure;
- embed a second Exchange compiler in this repository;
- infer truth/authority semantics not stated in Kristal contracts;
- mutate the real target checkout to create a test condition.

## Level contract

Each level module exports:

```python
def run(cfg, report):
    ...
```

Use stable finding IDs under `kristal.*`.

Use verdicts precisely:

- `FAIL`: target violates a contract that could be tested;
- `BLOCKED`: required implementation/evidence does not exist yet;
- `INFRA_ERROR`: local environment cannot execute the intended test;
- `CONFIG_ERROR`: harness/configuration is invalid;
- `WARN`: useful non-blocking concern;
- `PASS`: evidence positively demonstrates the tested condition.

Never turn absence of evidence into PASS.
