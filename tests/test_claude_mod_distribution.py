"""Keep the Claude enhancement outside other harnesses' discovery roots."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ClaudeModDistributionTest(unittest.TestCase):
    def test_only_claude_registers_the_mod(self):
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(claude.get("hooks"), "./claude-mods/hooks.json")
        for name in (".codex-plugin/plugin.json", ".cursor-plugin/plugin.json",
                     "gemini-extension.json"):
            manifest = json.loads((ROOT / name).read_text())
            self.assertNotIn("claude-mods", json.dumps(manifest))
            self.assertNotIn("ship_gate_mode", json.dumps(manifest))
        self.assertFalse((ROOT / "hooks/hooks.json").exists())

    def test_gate_needs_no_activation_setting(self):
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        config = claude.get("userConfig", {})
        self.assertNotIn("ship_gate_mode", config)
        self.assertEqual(config["ship_gate_checks"]["default"], "[]")

    def test_hook_file_contains_only_one_module(self):
        path = ROOT / "claude-mods/hooks.json"
        self.assertTrue(path.exists())
        hooks = json.loads(path.read_text())
        self.assertEqual(set(hooks), {"description", "modules"})
        self.assertEqual(hooks["modules"], ["./ship-gate.ts"])
        self.assertFalse(list((ROOT / "claude-mods").rglob("plugin.json")))
