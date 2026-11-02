#!/usr/bin/env python3
"""Opt-in Hyprland shortcuts, stored in Ambxst's own editable preferences."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile

AZERTY_ROW = ["ampersand", "eacute", "quotedbl", "apostrophe", "parenleft", "minus", "egrave", "underscore", "ccedilla", "agrave"]


def shortcut(key, *modifiers):
    return {"key": key, "modifiers": list(modifiers)}


def validate(data):
    seen = set()

    def register(binding):
        if not binding.get("key"):
            return
        signature = (tuple(sorted(binding.get("modifiers", []))), binding["key"].lower())
        if signature in seen:
            raise ValueError("Raccourci en double : " + "+".join((*signature[0], signature[1])))
        seen.add(signature)

    def core(node):
        if "key" in node:
            register(node)
        else:
            for value in node.values():
                if isinstance(value, dict):
                    core(value)

    core(data["ambxst"])
    for binding in data["custom"]:
        if binding.get("enabled", True):
            for key in binding["keys"]:
                register(key)


def transform(source):
    data = copy.deepcopy(source)
    core = data["ambxst"]
    core["launcher"].update(shortcut("R", "SUPER"))
    core["clipboard"].update(shortcut("V", "SUPER", "CTRL"))
    core["system"]["tools"].update(shortcut("S", "SUPER", "CTRL"))
    core["system"]["screenshot"].update(shortcut("Print"))
    replacements = {
        "window.toggle-float": shortcut("V", "SUPER"),
        "workspace.toggle-special": shortcut("S", "SUPER"),
        "workspace.move-window-special": shortcut("S", "SUPER", "SHIFT"),
    }
    for binding in data["custom"]:
        actions = binding.get("actions", [])
        if len(actions) == 1 and actions[0]["id"] in replacements:
            binding["keys"] = [copy.deepcopy(replacements[actions[0]["id"]])]
        for key in binding["keys"]:
            # French unshifted symbols keep workspace selection independent of Shift.
            workspace_action = any(a["id"].startswith("workspace.") or a["id"] == "scrolling.move-column-workspace" for a in actions)
            if workspace_action and "SUPER" in key["modifiers"]:
                if key["key"] in list("1234567890"):
                    key["key"] = AZERTY_ROW["1234567890".index(key["key"])]
                elif key["key"] in ["code:" + str(n) for n in range(10, 20)]:
                    key["key"] = AZERTY_ROW[int(key["key"].split(":")[1]) - 10]
            if key["key"] in ("mouse_down", "mouse_up") and key["modifiers"] == ["SUPER"]:
                if len(actions) == 1 and actions[0]["id"] == "workspace.switch-occupied":
                    offset = "+1" if key["key"] == "mouse_down" else "-1"
                    actions[0]["args"]["offset"] = offset
                    binding["name"] = "Switch Occupied Workspace " + offset

    # These commands are executed only when their shortcut is pressed.
    commands = [
        ("Terminal", "Q", "kitty"),
        ("Files", "E", "dolphin"),
        ("Exit Session", "M", "hyprshutdown"),
        ("Pseudo Tiling", "P", "hyprctl dispatch 'hl.dsp.window.pseudo()'"),
        ("Toggle Split", "J", "hyprctl dispatch 'hl.dsp.layout(\"togglesplit\")'"),
    ]
    for label, key, command in commands:
        name = "LOQ Hyprland: " + label
        data["custom"] = [b for b in data["custom"] if b["name"] != name]
        data["custom"].append({
            "name": name, "enabled": True, "keys": [shortcut(key, "SUPER")],
            "actions": [{"id": "command.run", "args": {"command": command}, "layouts": []}],
        })
    validate(data)
    return data


def atomic_write(path, payload):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".loq-binds-", delete=False) as stream:
        stage = Path(stream.name)
        stream.write(payload)
    try:
        shutil.copymode(path, stage)
        stage.replace(path)
    finally:
        stage.unlink(missing_ok=True)


def update(home, restore=None):
    path = home / ".config/ambxst/binds.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError("Un fichier binds.json ordinaire est requis.")
    original = path.read_bytes()
    if restore:
        payload = restore.read_bytes()
        validate(json.loads(payload))
    else:
        updated = transform(json.loads(original))
        if updated == json.loads(original):
            print("Raccourcis Hyprland déjà appliqués.")
            return
        payload = (json.dumps(updated, ensure_ascii=False, indent=4) + "\n").encode()
    backup_dir = home / ".local/state/ambxst-loq/keybindings"
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = backup_dir / (stamp + ".json")
    with backup.open("xb") as stream:
        stream.write(original)
    backup.chmod(0o600)
    atomic_write(path, payload)
    print("Raccourcis restaurés." if restore else "Raccourcis Hyprland appliqués.")
    print("Sauvegarde :", backup)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", type=Path, help="restaurer un fichier de sauvegarde")
    args = parser.parse_args()
    update(Path.home(), args.restore)
