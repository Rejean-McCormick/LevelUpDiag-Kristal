# CI integration

## Harness repository CI

The included `.github/workflows/self-test.yml` validates this repository independently of Kristal.

## Joint Kristal qualification CI

A joint CI job should check out both repositories as siblings:

```text
workspace/
├── kristal-framework/
└── levelupdiag_kristal/
```

Then install harness/runtime dependencies and run:

```bash
cd levelupdiag_kristal
python -m pip install -r requirements-dev.txt
python levelupdiag.py --target ../kristal-framework run deep
```

Archive as CI artifacts:

```text
levelupdiag_kristal/.levelupdiag/runs/**
```

Do not copy `.levelupdiag/` into `kristal-framework`.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | accepted (`PASS` or `WARN`) |
| 10 | target validation failure |
| 20 | required evidence incomplete/blocked |
| 30 | harness/config/infrastructure error |
| 64 | CLI usage error |

For a production qualification branch, treat 10, 20 and 30 as non-promotable outcomes.
