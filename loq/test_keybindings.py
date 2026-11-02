import json
from pathlib import Path
import tempfile
import unittest

from keybindings import transform, update


def source():
    def core(key):
        return {"key": key, "modifiers": ["SUPER"], "action": {"id": "ambxst.launcher", "args": {}}}
    return {
        "ambxst": {"launcher": core("Super_L"), "clipboard": core("V"),
                   "system": {"tools": core("S"), "screenshot": core("Print")}},
        "custom": [{"name": "Personal", "enabled": True,
                    "keys": [{"key": "9", "modifiers": ["ALT"]}],
                    "actions": [{"id": "command.run", "args": {"command": "personal-app"}}]}],
        "defaultAmbxstBinds": {"must": "remain unchanged"},
    }


class KeybindingTests(unittest.TestCase):
    def test_azerty_workspace_selection_does_not_require_shift(self):
        before = source()
        for modifiers, action in [(["SUPER"], "workspace.switch"), (["SUPER", "SHIFT"], "workspace.move-window")]:
            before["custom"].append({"name": action, "enabled": True,
                                    "keys": [{"key": "1", "modifiers": modifiers}],
                                    "actions": [{"id": action, "args": {"index": "1"}}]})
        after = transform(before)
        workspaces = [b for b in after["custom"] if b["name"].startswith("workspace.")]
        self.assertEqual([b["keys"][0]["key"] for b in workspaces], ["ampersand", "ampersand"])
        self.assertEqual([b["keys"][0]["modifiers"] for b in workspaces], [["SUPER"], ["SUPER", "SHIFT"]])
        self.assertEqual(after, transform(after))

    def test_repeat_preserves_personal_shortcuts_and_native_defaults(self):
        before = source()
        after = transform(before)
        self.assertEqual(before["custom"][0], after["custom"][0])
        self.assertEqual(before["defaultAmbxstBinds"], after["defaultAmbxstBinds"])
        self.assertEqual(after, transform(after))
        self.assertEqual(before, source())

    def test_conflict_leaves_original_file_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / ".config/ambxst/binds.json"
            path.parent.mkdir(parents=True)
            data = source()
            data["custom"][0]["keys"] = [{"key": "Q", "modifiers": ["SUPER"]}]
            path.write_text(json.dumps(data))
            original = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "double"):
                update(home)
            self.assertEqual(path.read_bytes(), original)

    def test_backup_and_restore_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / ".config/ambxst/binds.json"
            path.parent.mkdir(parents=True)
            original = json.dumps(source(), separators=(",", ":")).encode()
            path.write_bytes(original)
            update(home)
            backup = next((home / ".local/state/ambxst-loq/keybindings").glob("*.json"))
            self.assertEqual(backup.read_bytes(), original)
            update(home, backup)
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
