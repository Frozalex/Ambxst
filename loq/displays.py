#!/usr/bin/env python3
"""Transient Hyprland display layouts with an independent rollback watchdog."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from hyprbridge import monitor_command

TIMEOUT = 20

def run(args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=8)
    if p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip() or "Hyprland indisponible")
    return p.stdout.strip()

def monitors():
    result = json.loads(run(["hyprctl", "-j", "monitors", "all"]))
    if not isinstance(result, list): raise RuntimeError("Réponse Hyprland invalide")
    return result

def name(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value): raise ValueError("Nom de connecteur invalide")
    return value

def keyword(rule):
    response = run(monitor_command(rule))
    if response != "ok": raise RuntimeError(response or "Règle écran refusée")

def snapshot(items):
    rules=[]
    # Restore source monitors before mirrored outputs.
    for m in sorted(items, key=lambda m: m.get("mirrorOf", "none") not in ("none", "", None)):
        connector=name(m["name"])
        if m.get("disabled"):
            rules.append((connector, connector + ",disable")); continue
        rule=f'{connector},{m["width"]}x{m["height"]}@{m["refreshRate"]:.3f},{m["x"]}x{m["y"]},{m["scale"]},transform,{m.get("transform",0)}'
        mirror=m.get("mirrorOf")
        if mirror and mirror != "none": rule += ",mirror," + name(mirror)
        rules.append((connector,rule))
    return rules

def plan(items, layout, external):
    connected={m["name"]: m for m in items}
    internal=next((m["name"] for m in items if m["name"].startswith(("eDP-", "LVDS-", "DSI-"))),None)
    if not internal: raise ValueError("Écran interne non identifié ; aucun changement appliqué")
    if layout == "internal":
        return [f"{name(internal)},preferred,0x0,1"] + [f"{name(n)},disable" for n in connected if n != internal]
    external=name(external)
    if external not in connected or external == internal: raise ValueError("Sélectionner un écran externe connecté")
    if layout == "extend": return [f"{internal},preferred,0x0,1", f"{external},preferred,auto-right,1"]
    if layout == "mirror": return [f"{internal},preferred,0x0,1", f"{external},preferred,auto,1,mirror,{internal}"]
    if layout == "external": return [f"{external},preferred,0x0,1"] + [f"{name(n)},disable" for n in connected if n != external]
    raise ValueError("Disposition inconnue")

def state_dir():
    base=Path(os.environ.get("XDG_STATE_HOME",Path.home()/".local/state"))/"ambxst-loq/displays"
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return base

def restore_pending(path, token=None):
    if not path.exists(): return
    data=json.loads(path.read_text())
    if token and data["token"] != token: return
    connected={m["name"] for m in monitors()}
    errors=[]
    for connector, rule in data["rules"]:
        if connector not in connected: continue
        try: keyword(rule)
        except RuntimeError as e: errors.append(str(e))
    if errors: raise RuntimeError("Retour incomplet : " + "; ".join(errors))
    path.unlink()

def apply(path, layout, external):
    if path.exists(): raise RuntimeError("Valider ou annuler le changement précédent")
    items=monitors()
    rules=plan(items,layout,external)
    token=uuid.uuid4().hex
    path.write_text(json.dumps({"token":token,"rules":snapshot(items)}))
    try:
        # Start watchdog BEFORE changing a monitor. It survives shell exit/crash.
        subprocess.Popen([sys.executable,str(Path(__file__).resolve()),"watchdog","--token",token], stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
        for rule in rules: keyword(rule)
    except BaseException:
        restore_pending(path,token)
        raise
    return {"pending":True,"token":token,"timeout":TIMEOUT,"message":"Conserver cette disposition ? Retour automatique dans 20 secondes."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["list","apply","confirm","revert","watchdog"])
    p.add_argument("--layout",choices=["extend","mirror","external","internal"])
    p.add_argument("--external",default="")
    p.add_argument("--token")
    args=p.parse_args()
    if args.command=="list": print(json.dumps({"monitors":monitors()})); return
    if os.environ.get("AMBXST_PREVIEW")=="1": raise RuntimeError("Les changements d’écran sont désactivés en aperçu")
    if args.command=="watchdog": time.sleep(TIMEOUT)
    base=state_dir(); path=base/"pending.json"
    with (base/"lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if args.command=="apply": result=apply(path,args.layout,args.external)
        elif args.command=="confirm":
            if not path.exists(): raise RuntimeError("Le délai a expiré ; sélectionner de nouveau la disposition")
            data=json.loads(path.read_text())
            if not args.token or args.token != data["token"]: raise RuntimeError("Validation périmée")
            path.unlink(); result={"pending":False,"message":"Disposition conservée pour cette session"}
        else:
            restore_pending(path,args.token)
            result={"pending":False,"message":"Disposition précédente restaurée"}
    print(json.dumps(result))

if __name__=="__main__":
    try: main()
    except (OSError,ValueError,KeyError,RuntimeError,subprocess.TimeoutExpired) as e:
        print(json.dumps({"error":str(e)})); sys.exit(1)
