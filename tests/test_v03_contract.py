from __future__ import annotations

import json
import unittest
from pathlib import Path

from levelupdiag_core.manifest import load_manifest, resolve_selection


class V03ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]

    def test_version_is_030(self):
        self.assertEqual((self.root / 'VERSION').read_text(encoding='utf-8').strip(), '0.3.0')

    def test_retired_manifest_generator_not_declared(self):
        cfg = json.loads((self.root / 'levelupdiag.config.json').read_text(encoding='utf-8'))
        ids = {v.get('id') for v in cfg.get('validators', [])}
        self.assertNotIn('manifest-generator', ids)
        self.assertIn('framework-conformance', ids)

    def test_deep_contains_new_levels(self):
        m = load_manifest(self.root)
        ids = [x['id'] for x in resolve_selection(m, 'deep')]
        for lid in ('K19','K20','K21','K22','K23','K24'):
            self.assertIn(lid, ids)

    def test_split_runner_targets_deep_manifest(self):
        text = (self.root / 'scripts/run_deep_split.py').read_text(encoding='utf-8')
        self.assertIn("resolve_selection(manifest, 'deep')", text)
        self.assertIn("write_json(latest / 'summary.json', summary)", text)

    def test_external_adapter_disabled_by_default(self):
        cfg = json.loads((self.root / 'levelupdiag.config.json').read_text(encoding='utf-8'))
        self.assertFalse(cfg['implementation_adapter']['enabled'])


if __name__ == '__main__':
    unittest.main()
