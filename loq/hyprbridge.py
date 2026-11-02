"""Small bridge between Hyprland legacy keywords and current Lua IPC."""
import json
import os
import re
import subprocess

def lua(value):
    if isinstance(value, bool): return 'true' if value else 'false'
    if isinstance(value, (int,float)): return str(value)
    if isinstance(value, str): return json.dumps(value,ensure_ascii=False)
    if isinstance(value, dict):
        return '{'+','.join('['+lua(k)+']='+lua(v) for k,v in value.items())+'}'
    raise TypeError('Unsupported Lua value')

def lua_mode():
    forced=os.environ.get('AMBXST_HYPRLAND_LUA', '1')
    if forced in ('0','1'): return forced=='1'
    try:
        result=subprocess.run(['hyprctl','-j','version'],capture_output=True,text=True,timeout=3)
        data=json.loads(result.stdout)
        if not isinstance(data,dict): return False
        match=re.search(r'(\d+)\.(\d+)',data.get('version',''))
        return bool(match and tuple(map(int,match.groups())) >= (0,57))
    except (OSError,ValueError,subprocess.TimeoutExpired): return False

def monitor_table(rule):
    parts=rule.split(',')
    result={'output':parts[0]}
    if parts[1]=='disable': return dict(result,disabled=True)
    result.update(mode=parts[1],position=parts[2],scale=parts[3],disabled=False,mirror='',transform=0)
    for i in range(4,len(parts),2):
        key,value=parts[i:i+2]
        if key not in ('transform','mirror'): raise ValueError('Unsupported monitor field')
        result[key]=int(value) if key=='transform' else value
    return result

def monitor_command(rule):
    if lua_mode(): return ['hyprctl','eval','hl.monitor('+lua(monitor_table(rule))+')']
    return ['hyprctl','keyword','monitor',rule]

def effects_command(effects):
    if lua_mode():
        config={}
        for path,value in effects.items():
            node=config
            keys=path.split(':')
            for key in keys[:-1]: node=node.setdefault(key,{})
            node[keys[-1]]=value=='true'
        return ['hyprctl','eval','hl.config('+lua(config)+')']
    return ['hyprctl','--batch','; '.join(f'keyword {key} {value}' for key,value in effects.items())]

def dpms_command(state):
    if state not in ('on','off'): raise ValueError('Invalid DPMS state')
    if lua_mode(): return ['hyprctl','dispatch','hl.dsp.dpms('+lua({'action':state})+')']
    return ['hyprctl','dispatch','dpms',state]
