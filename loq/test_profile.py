import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('loq_profile',ROOT/'loq/install-profile.py')
profile=importlib.util.module_from_spec(spec);spec.loader.exec_module(profile)
class ProfileTransactionTests(unittest.TestCase):
    def setup_home(self,path):
        config=path/'.config/ambxst/config';config.mkdir(parents=True)
        (config/'theme.json').write_text('{"keep":"my theme"}')
        hypr=path/'.config/hypr';hypr.mkdir(parents=True)
        (hypr/'hyprland.lua').write_text('-- original desktop\n')
    def test_prepare_failure_restores_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);self.setup_home(home)
            real_copy=profile.atomic_copy;calls=0
            def fail_second(src,dst):
                nonlocal calls
                calls+=1
                if calls==2:raise OSError('simulated write failure')
                return real_copy(src,dst)
            with patch.object(profile,'HOME',home),patch.object(profile,'STATE',home/'.local/state/ambxst-loq'),patch.object(profile.subprocess,'check_output',return_value='balanced\n'),patch.object(profile,'atomic_copy',side_effect=fail_second):
                with self.assertRaisesRegex(OSError,'simulated'):profile.prepare()
            self.assertEqual((home/'.config/ambxst/config/theme.json').read_text(),'{"keep":"my theme"}')
            self.assertEqual((home/'.config/hypr/hyprland.lua').read_text(),'-- original desktop\n')
            self.assertFalse((home/'.local/state/ambxst-loq/active.json').exists())
            self.assertFalse((home/'.local/bin/ambxst-loq').exists())
    def test_symlink_preferences_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);self.setup_home(home)
            target=home/'external-theme';target.write_text('private settings')
            config=home/'.config/ambxst/config/theme.json';config.unlink();config.symlink_to(target)
            with patch.object(profile,'HOME',home),patch.object(profile,'STATE',home/'.local/state/ambxst-loq'):
                with self.assertRaisesRegex(RuntimeError,'Cible spéciale'):profile.prepare()
            self.assertTrue(config.is_symlink());self.assertEqual(target.read_text(),'private settings')
if __name__=='__main__':unittest.main()
