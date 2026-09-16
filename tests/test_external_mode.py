from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from levelupdiag_core.config import load_config


class ExternalModeTests(unittest.TestCase):
    def test_tool_owned_control_directory(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            tool = base / "levelupdiag_kristal"
            target = base / "kristal-framework"
            tool.mkdir()
            target.mkdir()
            (tool / "levelupdiag.config.json").write_text(
                json.dumps({
                    "schema": "levelupdiag.config.v2",
                    "target_repo_root": "../kristal-framework",
                    "control_root": "tool",
                    "control_dir": ".levelupdiag",
                }),
                encoding="utf-8",
            )
            cfg = load_config(tool)
            self.assertEqual(Path(cfg["_target_root"]), target.resolve())
            self.assertEqual(Path(cfg["_control_root"]), (tool / ".levelupdiag").resolve())
            self.assertFalse(Path(cfg["_control_root"]).is_relative_to(target.resolve()))

    def test_invalid_control_owner_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            tool = base / "tool"
            target = base / "target"
            tool.mkdir(); target.mkdir()
            (tool / "levelupdiag.config.json").write_text(
                json.dumps({
                    "schema": "levelupdiag.config.v2",
                    "target_repo_root": "../target",
                    "control_root": "somewhere-else",
                }),
                encoding="utf-8",
            )
            with self.assertRaises(Exception):
                load_config(tool)


if __name__ == "__main__":
    unittest.main()
