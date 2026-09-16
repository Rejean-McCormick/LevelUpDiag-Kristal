from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator
MAP={
'authority-registry.example.json':'authority-registry.schema.json','claim-ir.example.json':'claim-ir.schema.json','exchange-federation-manifest.example.json':'exchange-federation-manifest.schema.json','exchange-shard-manifest.example.json':'exchange-shard-manifest.schema.json','exchange.example.json':'exchange-manifest.schema.json','medical-authority-recognition.example.json':'authority-recognition.schema.json','plural-authority-federation.example.json':'exchange-federation-manifest.schema.json','reader-policy-validated-only.example.json':'reader-policy.schema.json','resolved-claim-ir.example.json':'resolved-claim-ir.schema.json','revocations.example.json':'revocations.schema.json','runtime-pack-manifest.example.json':'runtime-pack-manifest.schema.json','structured-epistemic-state.example.json':'structured-epistemic-state.schema.json','validation-report.example.json':'validation-report.schema.json','divergent-fork.example.json':'structured-epistemic-state.schema.json','independent-research-evidence-bundle.example.json':'structured-epistemic-state.schema.json','mythology-corpus-kristal.example.json':'structured-epistemic-state.schema.json','publisher-declared-system-kristal.example.json':'structured-epistemic-state.schema.json','wikidata-seed-kristal.example.json':'structured-epistemic-state.schema.json'}
def invalid(v,d): return bool(list(v.iter_errors(d)))
def run(cfg,report):
    root=Path(cfg['_target_root']); base=root/'docs/Technical-Reference/kristal-docs-v5'; fails=[]; total=0; removals=0
    for exn,sn in MAP.items():
        data=json.loads((base/'10-examples'/exn).read_text()); schema=json.loads((base/'02-schemas'/sn).read_text()); v=Draft202012Validator(schema)
        mut=dict(data); mut['schema_version']='4.0'; total+=1
        if not invalid(v,mut): fails.append(f'{exn}: schema_version 4.0 accepted')
        for key in schema.get('required',[]):
            if key in data:
                m=dict(data); m.pop(key); total+=1; removals+=1
                if not invalid(v,m): fails.append(f'{exn}: removing required {key} accepted')
    report.add('kristal.schemas.negative_top_level','PASS' if not fails else 'FAIL','schema_conformance',
               f'All {total} negative schema mutations were rejected.' if not fails else f'{len(fails)} negative schema mutations were accepted.',evidence=fails[:100] or {'cases':total,'required_field_removals':removals})
    report.metrics.update({'negative_cases':total,'failures':len(fails)})
