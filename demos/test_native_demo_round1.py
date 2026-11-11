"""Offline unit checks for deterministic demo transport/configuration, no service/API/key."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import native_demo_round1 as demo


class NativeDemoTests(unittest.TestCase):
    def test_case_names_unique_and_cover_both_cli_permissions(self):
        cases=demo.cases()
        self.assertEqual(len(cases),13)
        self.assertEqual(len({c['id'] for c in cases}),13)
        self.assertEqual(sum('permission' in c for c in cases),10)

    def test_plugin_transport_calls_only_fixed_empty_args_tool(self):
        provider=demo.Provider({'tool':'opencode-v1','plugin':'v1'})
        request=SimpleNamespace(data=json.dumps({'tools':[{'name':'report_marker'}]}).encode())
        text=provider.open(request,45).read().decode()
        self.assertIn('report_marker',text)
        self.assertTrue(provider.injected)
        self.assertNotIn('python3',text)
        final=provider.open(request,45).read().decode()
        self.assertIn(demo.MARKER,final)

    def test_shell_fixture_writes_only_named_local_witness(self):
        provider=demo.Provider({'tool':'opencode-v2','permission':'allow'})
        text=provider.open(SimpleNamespace(data=b'{"tools":[{"name":"shell"}]}'),45).read().decode()
        self.assertIn(demo.WITNESS,text)
        self.assertNotIn('.local/credentials',text)
        self.assertNotIn('api.openai.com',text)

    def test_title_bootstrap_does_not_inject_tool(self):
        provider=demo.Provider({'tool':'opencode-v1','permission':'allow'})
        provider.open(SimpleNamespace(data=b'{"tools":[]}'),45)
        self.assertFalse(provider.injected)

    def test_permission_configuration_v1_overlap_order(self):
        with tempfile.TemporaryDirectory(dir='/tmp/opencode',prefix='demo-config-unit-') as tmp:
            root=Path(tmp);p=root/'xdg-config/opencode/opencode.json';p.parent.mkdir(parents=True)
            p.write_text('{"permission":{"*":"deny"}}')
            cfg=demo.configure(root,{'tool':'opencode-v1','permission':'overlap-deny'})
            self.assertEqual(cfg['permission']['bash'],{'*':'allow','python3 *':'deny'})

    def test_permission_configuration_v2_last_match_order(self):
        with tempfile.TemporaryDirectory(dir='/tmp/opencode',prefix='demo-config-unit-') as tmp:
            root=Path(tmp);p=root/'xdg-config/opencode/opencode.json';p.parent.mkdir(parents=True)
            p.write_text('{"permissions":[]}')
            cfg=demo.configure(root,{'tool':'opencode-v2','permission':'overlap-allow'})
            self.assertEqual(cfg['permissions'][-1],{'action':'shell','resource':'python3 *','effect':'allow'})


if __name__=='__main__':unittest.main()
