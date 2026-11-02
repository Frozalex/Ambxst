#!/usr/bin/env python3
"""Four HDMI layouts with a confirmation and independent rollback."""
from pathlib import Path
import json
import os
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
os.environ.setdefault("AMBXST_HYPRLAND_LUA", "1")

def menu(options,prompt,timeout=120):
    try:
        p=subprocess.run(['fuzzel','--dmenu','--prompt',prompt,'--background','101010ff','--text-color','eeeeeeff','--selection-color','eeeeeeff','--selection-text-color','101010ff','--border-color','888888ff'],input='\n'.join(options),text=True,capture_output=True,timeout=timeout)
        return p.stdout.strip() if p.returncode==0 else ''
    except subprocess.TimeoutExpired: return ''

def call(*args):
    p=subprocess.run([sys.executable,str(ROOT/'displays.py'),*args],capture_output=True,text=True,timeout=12)
    data=json.loads(p.stdout)
    if p.returncode or data.get('error'): raise RuntimeError(data.get('error') or p.stderr)
    return data

def main():
    outputs=call('list')['monitors']
    external=[m['name'] for m in outputs if not m['name'].startswith(('eDP-','LVDS-','DSI-'))]
    labels={'Étendre à droite':'extend','Dupliquer':'mirror','Externe seul':'external','Portable seul':'internal'}
    choice=menu(list(labels)+['Annuler'],'Écrans : ')
    if choice not in labels: return
    selected=''
    if labels[choice]!='internal':
        if not external: menu(['Aucun écran externe connecté — fermer'],'HDMI : '); return
        selected=external[0] if len(external)==1 else menu(external,'Sortie : ')
        if not selected: return
    data=call('apply','--layout',labels[choice],'--external',selected)
    answer=menu(['Conserver','Revenir'],'Confirmer en moins de 20 s : ',timeout=18)
    call('confirm' if answer=='Conserver' else 'revert','--token',data['token'])

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as error:
        subprocess.run(['notify-send','Écrans HDMI',str(error)],check=False)
        sys.exit(1)
