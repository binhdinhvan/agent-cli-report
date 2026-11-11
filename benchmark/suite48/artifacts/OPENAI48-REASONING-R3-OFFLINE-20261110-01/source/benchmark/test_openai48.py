"""Offline tests only; no real credentials or provider calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import openai48 as o


class OpenAI48Tests(unittest.TestCase):
    def test_budget_does_not_reset_old_known_or_unknown(self):
        self.assertEqual(str(o.CARRY), '0.28498016')
        self.assertEqual(str(o.REMAINING), '15.71501984')

    def test_cost_openai_not_shop_rates(self):
        usage = {'input_tokens': 16, 'output_tokens': 9, 'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}}
        self.assertEqual(o.estimate(usage, o.pricing())['estimated_cost_usd'], '0.000122')

    def test_unknown_cachewrite_and_long_context_not_zero(self):
        for usage in [None, {}, {'input_tokens': 10, 'output_tokens': 1},
                      {'input_tokens': 10, 'output_tokens': 1, 'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 1}},
                      {'input_tokens': 272001, 'output_tokens': 1, 'input_tokens_details': {'cached_tokens': 0}}]:
            with self.subTest(usage=usage):
                self.assertIsNone(o.estimate(usage, o.pricing())['estimated_cost_usd'])

    def test_all_native_configs_low_and_local_no_real_key(self):
        for tool in ['opencode-v1', 'opencode-v2', 'pi', 'codex']:
            with self.subTest(tool=tool), tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='openai-config-test-') as tmp:
                root = Path(tmp)
                for name in ['xdg-config/opencode', 'agent', 'codex-home']:
                    (root / name).mkdir(parents=True)
                args = o.config({'tool': tool}, root, 'inert-local-test-token', 'test prompt')
                all_text = '\n'.join(p.read_text() for p in root.rglob('*') if p.is_file())
                self.assertIn('low', all_text + json.dumps(args))
                self.assertNotIn('shopaikey', all_text)
                self.assertNotIn('api.openai.com', all_text)
                self.assertNotIn('none', all_text)
                if tool == 'pi':
                    self.assertEqual(args[args.index('--thinking') + 1], 'low')

    def test_context_restores_frozen_globals_and_enforces_payload(self):
        old_base = o.native.model_smoke.BASE_URL
        old_budget = o.batch.BUDGET
        with o.context():
            request = o.native.model_smoke.urllib.request.Request(o.BASE + '/responses',
                data=json.dumps({'model': o.MODEL, 'reasoning': {'effort': 'none'}, 'stream': True}).encode(), method='POST')
            payload = json.loads(request.data)
            self.assertEqual(payload['reasoning'], {'effort': 'low'})
            self.assertEqual(payload['service_tier'], 'default')
            self.assertFalse(payload['store'])
            with self.assertRaises(ValueError):
                o.native.model_smoke.urllib.request.Request('https://api.shopaikey.com/v1/responses', data=b'{}')
        self.assertEqual(o.native.model_smoke.BASE_URL, old_base)
        self.assertEqual(o.batch.BUDGET, old_budget)

    def test_approval_rejected_before_preflight_key_or_network(self):
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='openai-approval-test-') as tmp:
            path = Path(tmp) / 'plan.json'
            path.write_text('{"unit":"plan"}')
            with patch.object(o, 'make_plan', return_value={'unit': 'plan'}):
                with self.assertRaises(PermissionError):
                    o.validate(path, {'authorized': False})

    def test_smoke_does_not_give_reference_solution(self):
        self.assertIn('Do not edit any file', o.SMOKE_PROMPT)
        self.assertNotIn('pagination', o.SMOKE_PROMPT)


if __name__ == '__main__':
    unittest.main()
