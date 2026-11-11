"""Offline scope/allocator/adapter checks for explicit r2 rerun; no real credentials."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import openai48_r2 as r


class OpenAIRerunTests(unittest.TestCase):
    def test_guard_retains_known_unknown_and_conservative_reserve_separately(self):
        self.assertEqual(str(r.GUARD_CARRY), '0.30242716')
        self.assertEqual(str(Decimal('16') - r.GUARD_CARRY), '15.69757284')
        self.assertEqual(r.PRIOR_UNPRICED, 5)

    def test_reserve52fresh_and_preserve_old_with_retry_lineage(self):
        state = json.loads(r.STATE.read_text()); state.pop('openai48_r2_batches', None); before = copy.deepcopy(state)
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='r2-reserve-test-') as tmp:
            path = Path(tmp) / 'state.json'; path.write_text(json.dumps(state))
            plan = {'proposed_run_start': state['next_pilot_run_start'], 'proposed_config_start': state['next_pilot_config_start'],
                    'slots': [{'slot': f'D48-{i+1:03d}'} for i in range(48)]}
            artifact = r.SUITE / 'artifacts/unit-test-not-launched'
            with patch.object(r, 'STATE', path):
                rows = r.reserve(plan, artifact)
                with self.assertRaises(PermissionError):
                    r.reserve(plan, artifact)
            after = json.loads(path.read_text())
        self.assertEqual(len(rows), 52)
        self.assertEqual(rows[0]['retry_of'], 'R-0222')
        self.assertEqual(after['openai48_batches'], before['openai48_batches'])
        self.assertEqual(after['benchmark48_paid_batches'], before['benchmark48_paid_batches'])
        self.assertEqual(after['next_pilot_run_start'], before['next_pilot_run_start'] + 52)

    def test_approval_rejects_before_any_launch(self):
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='r2-approval-test-') as tmp:
            path = Path(tmp) / 'plan.json'; path.write_text('{"unit":true}')
            with patch.object(r, 'make_plan', return_value={'unit': True}):
                with self.assertRaises(PermissionError):
                    r.validate(path, {'authorized': False}, r.SUITE / 'artifacts/unit')

    def test_paid_dispatch_replaces_cache_estimator_and_restores_context(self):
        original = r.r1.context
        fake_result = {'runs': [], 'phase': 'unit'}
        def dispatch(*args, **kwargs):
            self.assertIs(r.r1.context, r.cache.context)
            with r.r1.context(carry=r.GUARD_CARRY):
                rates = r.r1.pricing()
                result = r.r1.native.model_smoke.estimate({'input_tokens': 3112, 'output_tokens': 32,
                    'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 3109}}, rates)
                self.assertEqual(result['estimated_cost_usd'], '0.015871')
            return fake_result.copy()
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='r2-dispatch-test-') as tmp, \
                patch.object(r.r1, 'dispatch', side_effect=dispatch):
            result = r.dispatch(Path(tmp), [], {}, key='inert-test-only')
        self.assertIs(r.r1.context, original)
        self.assertEqual(result['prior_unpriced_requests'], 5)


if __name__ == '__main__':
    unittest.main()
