import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import json
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"loq"))
spec=importlib.util.spec_from_file_location('displays',ROOT/'loq/displays.py')
d=importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
def monitor(name, disabled=False, mirror='none'):
    return dict(name=name,width=1920,height=1080,refreshRate=60.0,x=0,y=0,scale=1.25,transform=0,disabled=disabled,mirrorOf=mirror)
class DisplayTests(unittest.TestCase):
    def setUp(self): self.items=[monitor('eDP-1'),monitor('HDMI-A-1')]
    def test_extend(self):
        rules=d.plan(self.items,'extend','HDMI-A-1')
        self.assertIn('auto-right',rules[1]); self.assertNotIn('disable',' '.join(rules))
    def test_mirror(self): self.assertIn('mirror,eDP-1',d.plan(self.items,'mirror','HDMI-A-1')[1])
    def test_internal_only(self): self.assertEqual(d.plan(self.items,'internal','')[-1],'HDMI-A-1,disable')
    def test_external_only(self): self.assertEqual(d.plan(self.items,'external','HDMI-A-1')[-1],'eDP-1,disable')
    def test_disconnected_and_bad_names_rejected(self):
        for value in ['DP-999','HDMI-A-1; reboot','eDP-1']:
            with self.assertRaises(ValueError): d.plan(self.items,'mirror',value)
    def test_no_internal_rejected(self):
        with self.assertRaises(ValueError): d.plan([monitor('DP-1')],'external','DP-1')
    def test_snapshot_keeps_scale_and_disabled(self):
        rules=d.snapshot([monitor('eDP-1'),monitor('HDMI-A-1',True)])
        self.assertIn('1.25',rules[0][1]); self.assertEqual(rules[1][1],'HDMI-A-1,disable')
    def test_snapshot_source_before_mirror(self):
        rules=d.snapshot([monitor('HDMI-A-1',mirror='eDP-1'),monitor('eDP-1')])
        self.assertEqual(rules[0][0],'eDP-1'); self.assertIn('mirror,eDP-1',rules[1][1])
    def test_watchdog_started_before_changes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d,'monitors',return_value=self.items), patch.object(d.subprocess,'Popen') as popen, patch.object(d,'keyword') as keyword:
            path=Path(tmp)/'pending.json'
            def check(_): self.assertTrue(popen.called); self.assertTrue(path.exists())
            keyword.side_effect=check
            result=d.apply(path,'mirror','HDMI-A-1')
            self.assertTrue(result['pending']); self.assertEqual(result['timeout'],20)
            self.assertTrue(popen.call_args.kwargs['start_new_session'])
    def test_apply_failure_restores(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d,'monitors',return_value=self.items), patch.object(d.subprocess,'Popen'), patch.object(d,'keyword',side_effect=[None,RuntimeError('mode refused'),None,None]) as keyword:
            path=Path(tmp)/'pending.json'
            with self.assertRaisesRegex(RuntimeError,'mode refused'): d.apply(path,'mirror','HDMI-A-1')
            self.assertFalse(path.exists()); self.assertEqual(keyword.call_count,4)
    def test_stale_token_does_not_revert_new_layout(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d,'keyword') as keyword:
            path=Path(tmp)/'pending.json';path.write_text(json.dumps(dict(token='new',rules=[])))
            d.restore_pending(path,'old');self.assertTrue(path.exists());keyword.assert_not_called()
    def test_restore_skips_unplugged_output(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d,'monitors',return_value=[monitor('eDP-1')]),patch.object(d,'keyword') as keyword:
            path=Path(tmp)/'pending.json';path.write_text(json.dumps(dict(token='t',rules=d.snapshot(self.items))))
            d.restore_pending(path,'t'); self.assertEqual(keyword.call_count,1); self.assertFalse(path.exists())
    def test_hyprctl_zero_exit_with_error_is_failure(self):
        with patch.object(d,'run',return_value='Invalid monitor rule'):
            with self.assertRaises(RuntimeError): d.keyword('HDMI-A-1,disable')
if __name__=='__main__': unittest.main()

class MultiOutputTests(unittest.TestCase):
    def test_external_only_disables_other_outputs(self):
        rules=d.plan([monitor('eDP-1'),monitor('HDMI-A-1'),monitor('DP-2')],'external','HDMI-A-1')
        self.assertIn('eDP-1,disable',rules)
        self.assertIn('DP-2,disable',rules)
        self.assertFalse(any(rule=='HDMI-A-1,disable' for rule in rules))

class WatchdogProcessTests(unittest.TestCase):
    def test_independent_worker_restores_after_parent_exits(self):
        import os
        import sys
        import time
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'bin';binary.mkdir()
            helper=binary/'hyprctl'
            helper.write_text('#!/usr/bin/env python3\nimport sys,json,os\nfrom pathlib import Path\nif sys.argv[1]=="-j": print(json.dumps('+repr([monitor('eDP-1'),monitor('HDMI-A-1')])+'))\nelse:\n with Path(os.environ["FAKE_LOG"]).open("a") as f: f.write(sys.argv[-1]+"\\n")\n print("ok")\n')
            helper.chmod(0o755)
            import shutil
            shutil.copy2(ROOT/'loq/hyprbridge.py',root/'hyprbridge.py')
            script=root/'displays.py'
            script.write_text((ROOT/'loq/displays.py').read_text().replace('TIMEOUT = 20','TIMEOUT = 0.4'))
            env=dict(os.environ,PATH=str(binary)+os.pathsep+os.environ['PATH'],XDG_STATE_HOME=str(root/'state'),FAKE_LOG=str(root/'calls'),AMBXST_PREVIEW='0')
            parent=subprocess.run([sys.executable,str(script),'apply','--layout','mirror','--external','HDMI-A-1'],env=env,capture_output=True,text=True,timeout=5)
            self.assertEqual(parent.returncode,0,parent.stdout+parent.stderr)
            self.assertTrue(json.loads(parent.stdout)['pending'])
            pending=root/'state/ambxst-loq/displays/pending.json'
            deadline=time.monotonic()+4
            while pending.exists() and time.monotonic()<deadline: time.sleep(.05)
            self.assertFalse(pending.exists(),'Watchdog failed to remove restored transaction')
            self.assertEqual(len((root/'calls').read_text().splitlines()),4)
