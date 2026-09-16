# Architecture

## Design goal

`levelupdiag_kristal` is an **external validation harness** for `kristal-framework`. It is intentionally a sibling repository, not vendored into Kristal.

## Recommended topology

```text
C:\\mycode\\Kristal\\
├── kristal-framework\\
└── levelupdiag_kristal\\
```

## Dependency direction

```text
CLI / launchers
      ↓
manifest + config
      ↓
campaign scheduler
      ↓  separate process per level
neutral levels + Kristal-specific levels
      ↓
small shared LevelUpDiag core
      ↓
read-only target observation / explicit native validators / temporary mutation copies
```

The harness must not become a second implementation of Kristal. When a native Kristal validator/builder/verifier exists, the harness invokes it and verifies observable behavior around it.

## Source, target and evidence

```text
levelupdiag_kristal/            committed harness source
levelupdiag_kristal/.levelupdiag/ generated evidence/history
kristal-framework/              external target; treated as read-only
```

Negative levels copy the target into operating-system temporary directories before mutation.

## Process isolation

Each level is launched in a fresh Python process. This isolates imports, failures and transient state from the campaign scheduler.

## Parallel scheduler

The manifest defines `depends_on` and `parallel_safe`. Independent safe levels may run concurrently. Heavy mutation/reproducibility levels run exclusively.

Numeric order is presentation order, not dependency semantics.

## Qualification boundary

The harness distinguishes repository integrity from implementation conformance and production qualification. It must never infer a stronger status from a weaker gate.
