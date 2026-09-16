# Operating model

`levelupdiag_kristal` is an **external validation repository**.

## Repository placement

Recommended:

```text
C:\mycode\Kristal\
├── kristal-framework\
└── levelupdiag_kristal\
```

The committed default target is `../kristal-framework`. A machine-local path can be set in `levelupdiag.config.local.json` using `levelupdiag.config.local.example.json` as a template.

## Write boundaries

Normal campaign execution may write only to:

```text
levelupdiag_kristal/.levelupdiag/
```

Kristal itself is treated as read-only.

Levels that need destructive/adversarial behavior copy the target into a temporary directory and mutate only that temporary copy.

## Qualification layers

This harness intentionally separates:

1. **Framework/release integrity** — schemas, examples, release metadata, docs, JCS vectors.
2. **Reference implementation conformance** — executable Exchange/Runtime Pack build/verify semantics.
3. **Ecosystem integration conformance** — Da’at / Interaction Kernel / operational producer-consumer flows.
4. **Production qualification** — operational resilience, security, rollback, load, cross-platform/cross-toolchain evidence.

A PASS at an earlier layer is never promoted to a later layer automatically.

## Evidence lifecycle

Each run gets a unique directory:

```text
.levelupdiag/runs/<run-id>/
```

`latest/` mirrors the newest run summary/results for convenience.

Evidence is not authoritative Kristal data. It is diagnostic evidence owned by this harness repository.

## CI strategy

There are two distinct CI jobs:

- **harness self-test** in this repository: unit tests, manifest/config parse, module importability;
- **Kristal qualification** in an environment where both repositories are available: execute `deep` against the target checkout.

Do not vendor this harness into the Kristal release archive.
