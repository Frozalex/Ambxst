#!/usr/bin/env python3
"""Atomically apply Ambxst-only files; roll back every intermediate write on failure."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import json
import os
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home()
STATE=HOME/'.local/state/ambxst-loq'

def atomic_copy(src,dst):
    stage=dst.with_name(dst.name+'.loq-stage')
    if stage.exists() or stage.is_symlink():raise RuntimeError('Fichier temporaire déjà présent : '+str(stage))
    try:
        if src.is_symlink():stage.symlink_to(os.readlink(src))
        else:shutil.copy2(src,stage)
        stage.replace(dst)
    finally:
        if stage.exists() or stage.is_symlink():stage.unlink()

def undo(records):
    for record in reversed(records):
        path=Path(record['path'])
        if record['existed']:atomic_copy(Path(record['backup']),path)
        elif path.is_file() or path.is_symlink():path.unlink()

def prepare():
    if (STATE/'active.json').exists():raise RuntimeError('Une préparation existe déjà.')
    launcher=HOME/'.local/bin/ambxst-loq'
    if launcher.exists() or launcher.is_symlink():raise RuntimeError('Ne pas remplacer un lanceur déjà présent.')
    changes={}
    for src in (ROOT/'assets/presets/Lenovo LOQ').glob('*.json'):
        if src.name!='info.json':changes[HOME/'.config/ambxst/config'/src.name]=src.read_bytes()
    desktop='[Desktop Entry]\nType=Application\nName=Écrans HDMI — LOQ\nComment=Étendre, dupliquer ou choisir l’écran actif\nExec=python3 '+json.dumps(str(ROOT/'loq/display-menu.py'),ensure_ascii=False)+'\nIcon=video-display\nCategories=Settings;HardwareSettings;\nTerminal=false\n'
    changes[HOME/'.local/share/applications/ambxst-loq-displays.desktop']=desktop.encode()
    changes[HOME/'.config/ambxst/active_preset']=b'Lenovo LOQ\n'
    changes[HOME/'.cache/ambxst/colors.json']=(ROOT/'assets/colors/LOQ Monochrome/dark.json').read_bytes()
    wall=HOME/'.cache/ambxst/wallpapers.json'
    data=json.loads(wall.read_text()) if wall.exists() else {}
    data.update(activeColorPreset='LOQ Monochrome',currentWall=str(ROOT/'assets/wallpapers_example/ambxst-01.png'),perScreenWallpapers={},tintEnabled=True,wallPath=str(ROOT/'assets/wallpapers_example'))
    changes[wall]=(json.dumps(data,indent=4)+'\n').encode()
    # Validate all targets before writing: only regular Ambxst preference files.
    for path in changes:
        if path.is_symlink() or (path.exists() and not path.is_file()):raise RuntimeError('Cible spéciale préservée : '+str(path))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=STATE/stamp;backup.mkdir(parents=True,mode=0o700)
    records=[]
    main=HOME/'.config/hypr/hyprland.lua'
    if main.is_symlink():(backup/'previous-main').symlink_to(os.readlink(main))
    else:shutil.copy2(main,backup/'previous-main')
    for i,path in enumerate(changes):
        old=backup/str(i);existed=path.exists()
        if existed:shutil.copy2(path,old)
        records.append({'path':str(path),'backup':str(old),'existed':existed})
    manifest={'backup':str(backup),'records':records,'main':str(main),'source':str(ROOT),'profile':subprocess.check_output(['powerprofilesctl','get'],text=True).strip()}
    try:
        for path,payload in changes.items():
            path.parent.mkdir(parents=True,exist_ok=True)
            stage=backup/'payload';stage.write_bytes(payload);atomic_copy(stage,path)
        launcher.parent.mkdir(parents=True,exist_ok=True);launcher.symlink_to(ROOT/'loq/launch')
        (STATE/'active.json').write_text(json.dumps(manifest,indent=2))
    except BaseException:
        undo(records)
        if launcher.is_symlink() and launcher.resolve()==ROOT/'loq/launch':launcher.unlink()
        raise
    print('Préférences Ambxst préparées. Sauvegarde :',backup)

def restore():
    manifest=json.loads((STATE/'active.json').read_text());backup=Path(manifest['backup'])
    subprocess.run([str(ROOT/'loq/launch'),'quit'],check=False)
    preserved=STATE/('settings-after-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));preserved.mkdir(mode=0o700)
    for i,record in enumerate(manifest['records']):
        path=Path(record['path'])
        if path.is_file() and not path.is_symlink():shutil.copy2(path,preserved/str(i))
    main=Path(manifest['main'])
    if not main.is_symlink() and main.exists() and '-- AMBXST LOQ SESSION' in main.read_text():
        atomic_copy(backup/'previous-main',main)
    undo(manifest['records'])
    launcher=HOME/'.local/bin/ambxst-loq'
    if launcher.is_symlink() and launcher.resolve()==ROOT/'loq/launch':launcher.unlink()
    subprocess.run(['hyprctl','reload'],check=True)
    subprocess.run(['powerprofilesctl','set',manifest['profile']],check=False)
    for command in [['qs','-c','rice','-n','-d'],['waybar'],['hypridle']]:
        if command[0]!='qs' and subprocess.run(['pgrep','-x',command[0]],capture_output=True).returncode==0:continue
        subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    (STATE/'active.json').rename(STATE/'restored.json')
    print('Ancien bureau restauré. Les préférences Ambxst récentes sont conservées dans',preserved)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','restore']);args=parser.parse_args()
    if args.command=='prepare':prepare()
    else:restore()
