"""Offline launcher integration tests; no real provider or credential access."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import openai48_r3 as r


class ReasoningLaunchTests(unittest.TestCase):
    def test_guard_keeps_estimates_reserve_and_unknown_history(self):
        self.assertEqual(str(r.GUARD_CARRY), '0.33970766')
        self.assertEqual(str(Decimal('16') - r.GUARD_CARRY), '15.66029234')

    def test_reserve_new52ids_preserve_all_predecessors(self):
        state = json.loads(r.STATE.read_text()); state.pop('openai48_r3_batches', None); before = copy.deepcopy(state)
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='r3-reserve-test-') as tmp:
            path = Path(tmp) / 'state.json'; path.write_text(json.dumps(state))
            plan = {'proposed_run_start': state['next_pilot_run_start'], 'proposed_config_start': state['next_pilot_config_start'],
                    'slots': [{'slot': f'D48-{i+1:03d}'} for i in range(48)]}
            with patch.object(r, 'STATE', path):
                rows = r.reserve(plan, r.SUITE / 'artifacts/unit-r3-not-launched')
                with self.assertRaises(PermissionError):
                    r.reserve(plan, r.SUITE / 'artifacts/unit-r3-not-launched')
            after = json.loads(path.read_text())
        self.assertEqual(len(rows), 52)
        self.assertEqual([row['retry_of'] for row in rows[:4]], [f'R-{i:04d}' for i in range(274, 278)])
        for key in ('benchmark48_paid_batches', 'openai48_batches', 'openai48_r2_batches'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['next_pilot_run_start'], before['next_pilot_run_start'] + 52)

    def test_disabled_approval_rejected_before_launch(self):
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='r3-approval-test-') as tmp:
            path = Path(tmp) / 'plan.json'; path.write_text('{"unit":true}')
            with patch.object(r, 'make_plan', return_value={'unit': True}), self.assertRaises(PermissionError):
                r.validate(path, {'authorized': False}, r.SUITE / 'artifacts/unit')

    def test_paid_dispatch_preserves_native_context_and_uses_cache_r2(self):
        original = r.r1.context
        def dispatch(*args, **kwargs):
            self.assertIs(r.r1.context, r.reasoning.context)
            with r.r1.context():
                req = r.r1.native.model_smoke.urllib.request.Request(r.r1.BASE + '/responses',
                    data=json.dumps({'model': r.r1.MODEL, 'stream': True,
                        'reasoning': {'effort': 'high', 'context': 'all_turns'}}).encode(),
                    method='POST', headers={r.reasoning.LITE: 'true'})
                self.assertEqual(json.loads(req.data)['reasoning'], {'effort': 'low', 'context': 'all_turns'})
                answer = r.r1.native.model_smoke.estimate({'input_tokens': 3112, 'output_tokens': 32,
                    'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 3109}}, r.r1.pricing())
                self.assertEqual(answer['estimated_cost_usd'], '0.015871')
            return {'runs': []}
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='r3-dispatch-test-') as tmp, \
                patch.object(r.r1, 'dispatch', side_effect=dispatch):
            result = r.dispatch(Path(tmp), [], {}, key='inert-unit-not-real-key')
        self.assertEqual(result['prior_unpriced_requests'], 6)
        self.assertIs(r.r1.context, original)

    def test_reused_main_installs_and_restores_r3_functions_and_carry(self):
        original = r.previous.dispatch
        def main():
            self.assertIs(r.previous.dispatch, r.dispatch)
            self.assertIs(r.previous.make_plan, r.make_plan)
            self.assertIs(r.previous.reserve, r.reserve)
            self.assertEqual(r.previous.GUARD_CARRY, r.GUARD_CARRY)
            self.assertEqual(r.previous.SCOPE, r.SCOPE)
        with patch.object(r.previous, 'main', side_effect=main):
            r.main()
        self.assertIs(r.previous.dispatch, original)


if __name__ == '__main__':
    unittest.main()
