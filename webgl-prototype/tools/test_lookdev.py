"""不啟動伺服器、不寫入擷取目錄的契約檢查。"""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
TOOLS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('capture_server', TOOLS / 'scene_capture_server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class LookdevContract(unittest.TestCase):
    def test_default_and_injection_order(self):
        source = 'function animate(now){requestAnimationFrame(animate);}'
        hook = (TOOLS / 'scene_capture_hook.js').read_text()
        expected = source.replace('function animate(now){', 'function animate(now){if(window.__captureFreeze)return;') + '\n' + hook
        self.assertEqual(server.injected_source(source), expected)
        preview = server.injected_source(source, True)
        self.assertLess(preview.index('const LOOKDEV_PARAMS'), preview.index('const captureButton'))
        self.assertIn('window.__captureLookdev = true', preview)

    def test_output_isolation(self):
        self.assertEqual(len(server.LOOKDEV_ALLOWED), 4)
        self.assertFalse(server.BASE_ALLOWED & server.LOOKDEV_ALLOWED)
        self.assertTrue(all(p.startswith('captures/web-lookdev/') and p.endswith('.png') for p in server.LOOKDEV_ALLOWED))

    def test_props_contract(self):
        source = (server.ROOT / 'webgl-prototype/taiwan-study.js').read_text()
        combined = server.injected_source(source, True, True)
        self.assertLess(combined.index('const LOOKDEV_PARAMS'), combined.index('const PROPS_SCATTER_PARAMS'))
        self.assertLess(combined.index('const PROPS_SCATTER_PARAMS'), combined.index('const captureButton'))
        self.assertNotIn('const PROPS_SCATTER_PARAMS', server.injected_source(source, True))
        self.assertLess(combined.index('window.__propsObstacles=[]'), combined.index('const batches=new Map()'))
        self.assertNotIn('props.reduce(', combined)
        self.assertIn('props.assertBudget()', combined)
        self.assertEqual(server.PROPS_ALLOWED, {f'captures/web-props/{s}.png' for s in server.SHOT_IDS} | {'captures/web-props/stats.json'})
        self.assertFalse(server.PROPS_ALLOWED & (server.BASE_ALLOWED | server.LOOKDEV_ALLOWED))
        with self.assertRaises(ValueError):
            server.injected_source(source, False, True)
        subprocess.run(['node', '--input-type=module', '--check'], input=combined, text=True, check=True)
        invalid = subprocess.run([sys.executable, '-B', str(TOOLS / 'scene_capture_server.py'), '--props'], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn('--props requires --lookdev', invalid.stderr)

    def test_params_match(self):
        hook = (TOOLS / 'lookdev_hook.js').read_text()
        inline = json.loads(hook.split('const LOOKDEV_PARAMS = ', 1)[1].split(';', 1)[0])
        snapshot = json.loads((server.ART / 'lookdev/lookdev-params-v01.json').read_text())
        self.assertEqual(inline, snapshot)
        self.assertFalse(inline['qualityPresets']['medium']['dof'])
        self.assertEqual(inline['qualityPresets']['medium']['aoResolutionScale'], .5)

    def test_python_and_combined_module_syntax(self):
        ast.parse((TOOLS / 'scene_capture_server.py').read_text())
        source = (server.ROOT / 'webgl-prototype/taiwan-study.js').read_text()
        self.assertEqual(source.count('function animate(now){'), 1, '原模組動畫簽章已改，需更新注入點')
        for mode in (False, True):
            subprocess.run(['node', '--input-type=module', '--check'], input=server.injected_source(source, mode), text=True, check=True)


if __name__ == '__main__':
    unittest.main()
