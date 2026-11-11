"""Cache billing and local Unix broker regressions; dummy keys, no TCP/provider calls."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import openai48_cache_r2 as r2
from test_batch48_flow import Local


def usage():
    return {'input_tokens': 3112, 'output_tokens': 32, 'total_tokens': 3144,
            'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 3109},
            'output_tokens_details': {'reasoning_tokens': 0}}


class CacheCostTests(unittest.TestCase):
    def test_real_failure_replay_gets_conservative_guard_not_null(self):
        raw = r2.ROOT / 'benchmark/suite48/artifacts/OPENAI48-20261110-01/result.json'
        before = raw.read_bytes()
        q = json.loads(before)['native_smoke']['runs'][0]['requests'][1]
        answer = r2.estimate(q['cost']['usage'], r2.pricing())
        self.assertEqual(answer['estimated_cost_usd'], '0.015871')
        self.assertEqual(answer['published_tariff_lower_usd'], '0.0080985')
        self.assertTrue(answer['conservative_upper_bound'])
        self.assertIsNone(answer['billed_12h_write_tokens'])
        self.assertIsNone(q['cost']['estimated_cost_usd'])
        self.assertEqual(raw.read_bytes(), before)

    def test_reported_30m_exact_no_double_count(self):
        u = usage()
        u['input_tokens_details']['cache_write_tokens_details'] = {'ttl_30m_tokens': 3109, 'ttl_12h_tokens': 0}
        answer = r2.estimate(u, r2.pricing())
        self.assertEqual(answer['ordinary_input_tokens'], 3)
        self.assertEqual(answer['estimated_cost_usd'], '0.0080985')
        self.assertFalse(answer['conservative_upper_bound'])

    def test_reported_12h(self):
        u = usage()
        u['input_tokens_details']['cache_write_tokens_details'] = {'ttl_30m_tokens': 0, 'ttl_12h_tokens': 3109}
        answer = r2.estimate(u, r2.pricing())
        self.assertEqual(answer['estimated_cost_usd'], '0.015871')
        self.assertFalse(answer['conservative_upper_bound'])

    def test_mixed_lifetimes_and_cached_reads(self):
        u = {'input_tokens': 12000, 'output_tokens': 100, 'input_tokens_details': {
            'cached_tokens': 4000, 'cache_write_tokens': 7000,
            'cache_write_tokens_details': {'ttl_30m_tokens': 3000, 'ttl_12h_tokens': 4000}}}
        answer = r2.estimate(u, r2.pricing())
        self.assertEqual(answer['ordinary_input_tokens'], 1000)
        self.assertEqual(Decimal(answer['estimated_cost_usd']), Decimal('0.0309'))

    def test_zero_writes_prior_minimal_check_cost_preserved(self):
        u = {'input_tokens': 16, 'output_tokens': 9, 'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}}
        self.assertEqual(r2.estimate(u, r2.pricing())['estimated_cost_usd'], '0.000122')

    def test_reasoning_is_already_part_of_output(self):
        u = usage(); u['output_tokens_details']['reasoning_tokens'] = 32
        self.assertEqual(r2.estimate(u, r2.pricing())['estimated_cost_usd'], '0.015871')

    def test_estimator_does_not_mutate_inputs(self):
        u, rates = usage(), r2.pricing()
        before = copy.deepcopy((u, rates))
        r2.estimate(u, rates)
        self.assertEqual((u, rates), before)

    def test_missing_usage_or_counts_is_not_zero(self):
        cases = [None, [], {}, {'input_tokens_details': []}]
        for container, key in [(None, 'input_tokens'), (None, 'output_tokens'), ('input_tokens_details', 'cached_tokens'),
                               ('input_tokens_details', 'cache_write_tokens')]:
            u = usage(); del (u if container is None else u[container])[key]; cases.append(u)
        for u in cases:
            with self.subTest(u=u):
                self.assertIsNone(r2.estimate(u, r2.pricing())['estimated_cost_usd'])

    def test_invalid_token_types_negative_boolean(self):
        for container, key in [(None, 'input_tokens'), (None, 'output_tokens'), ('input_tokens_details', 'cached_tokens'),
                               ('input_tokens_details', 'cache_write_tokens')]:
            for value in [-1, True, 2.5, '32', None]:
                u = usage(); (u if container is None else u[container])[key] = value
                with self.subTest(key=key, value=value):
                    self.assertIsNone(r2.estimate(u, r2.pricing())['estimated_cost_usd'])

    def test_invalid_write_breakdowns_not_silently_bounded(self):
        for breakdown in [None, [], {}, {'ttl_30m_tokens': 1},
                           {'ttl_30m_tokens': 3108, 'ttl_12h_tokens': 0},
                           {'ttl_30m_tokens': -1, 'ttl_12h_tokens': 3110},
                           {'ttl_30m_tokens': True, 'ttl_12h_tokens': 3108}]:
            u = usage(); u['input_tokens_details']['cache_write_tokens_details'] = breakdown
            with self.subTest(breakdown=breakdown):
                self.assertIsNone(r2.estimate(u, r2.pricing())['estimated_cost_usd'])

    def test_overlapping_input_counts_rejected(self):
        u = usage(); u['input_tokens_details']['cached_tokens'] = 4
        self.assertIsNone(r2.estimate(u, r2.pricing())['estimated_cost_usd'])

    def test_long_context_and_invalid_totals_rejected(self):
        for key, value in [('input_tokens', 272001), ('total_tokens', 0), ('total_tokens', True)]:
            u = usage(); u[key] = value
            self.assertIsNone(r2.estimate(u, r2.pricing())['estimated_cost_usd'])

    def test_invalid_reasoning_details_rejected(self):
        for value in [-1, 33, True, '0']:
            u = usage(); u['output_tokens_details']['reasoning_tokens'] = value
            self.assertIsNone(r2.estimate(u, r2.pricing())['estimated_cost_usd'])

    def test_invalid_rates_rejected(self):
        for key in ('unit_tokens', 'input_uncached', 'input_cache_read', 'cache_write_30m', 'cache_write_12h', 'output'):
            for value in ['NaN', 'Infinity', '-1', None]:
                rates = r2.pricing(); rates[key] = value
                self.assertIsNone(r2.estimate(usage(), rates)['estimated_cost_usd'])
        rates = r2.pricing(); rates['cache_write_12h'] = '1'
        self.assertIsNone(r2.estimate(usage(), rates)['estimated_cost_usd'])

    def test_budget_and_unknown_old_costs_retained(self):
        self.assertEqual(str(r2.CARRY), '0.28655616')
        self.assertEqual(r2.UNPRICED_CARRY, 5)
        self.assertEqual(str(Decimal('16') - r2.CARRY), '15.71344384')

    def test_context_uses_revision2_and_restores_revision1(self):
        old_estimate, old_pricing = r2.r1.estimate, r2.r1.pricing
        with r2.context():
            self.assertEqual(r2.r1.native.model_smoke.estimate(usage(), r2.pricing())['estimated_cost_usd'], '0.015871')
        self.assertIs(r2.r1.estimate, old_estimate)
        self.assertIs(r2.r1.pricing, old_pricing)


class BrokerCacheRegressionTests(unittest.TestCase):
    def run_broker(self, *, missing=False, budget=False):
        native = r2.r1.native
        ledger, all_requests = [], []
        if budget:
            # A tiny remaining guard exercises the next-request budget stop.
            carry = Decimal('15.999999')
        else:
            carry = r2.CARRY
        virtual = native.VirtualPacing()
        pacing = native.PacingState(clock=virtual.clock, sleep=virtual.sleep)

        class Provider:
            captures = []
            def open(inner, request, timeout):
                inner.captures.append(json.loads(request.data))
                event = {'type': 'response.completed', 'response': {'model': r2.r1.MODEL, 'status': 'completed', 'usage': usage()}}
                if missing:
                    del event['response']['usage']['input_tokens_details']['cache_write_tokens']
                return native.Response(b'data: ' + json.dumps(event).encode() + b'\n\n')

        provider = Provider()
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='cache-r2-broker-') as tmp, \
                r2.context(carry=carry), patch.object(native.model_smoke.urllib.request, 'build_opener', return_value=provider), \
                patch.object(socket, 'create_connection', side_effect=AssertionError('No TCP egress in offline test')):
            path = Path(tmp) / 'broker.sock'
            handler = native.handler('unit-inert-not-real-key', 'unit-nonce', ledger, threading.Lock(), r2.pricing(),
                time.monotonic() + 900, request_limit=8, output_limit=2048, budget_limit='16',
                budget_ledger=all_requests, stop_on_unknown=True, serialize_requests=True, min_interval_seconds=30,
                pacing_state=pacing, stop_on_provider_failure=True, minimum_request_window_seconds=60)
            server = native.Broker(str(path), handler)
            thread = threading.Thread(target=server.serve_forever); thread.start()
            statuses = []
            try:
                for _ in range(3):
                    client = Local(path)
                    try:
                        client.request('POST', '/v1/responses', json.dumps({'model': r2.r1.MODEL, 'stream': True, 'input': []}),
                            {'Authorization': 'Bearer unit-nonce', 'Content-Type': 'application/json'})
                        response = client.getresponse(); statuses.append(response.status); response.read()
                    finally:
                        client.close()
            finally:
                server.shutdown(); server.server_close(); thread.join()
        return statuses, ledger, provider.captures

    def test_three_positive_cachewrite_requests_not_blocked(self):
        statuses, ledger, captures = self.run_broker()
        self.assertEqual(statuses, [200, 200, 200])
        self.assertEqual(len(captures), 3)
        self.assertTrue(all(q['cost']['estimated_cost_usd'] == '0.015871' for q in ledger))
        self.assertTrue(all(q['effective_settings']['reasoning'] == {'effort': 'low'} for q in ledger))

    def test_missing_counts_still_block_followup_without_upstream_retry(self):
        statuses, ledger, captures = self.run_broker(missing=True)
        self.assertEqual(statuses, [200, 400, 400])
        self.assertEqual(len(captures), 1)
        self.assertIsNone(ledger[0]['cost']['estimated_cost_usd'])

    def test_soft_budget_still_blocks_next_request(self):
        statuses, ledger, captures = self.run_broker(budget=True)
        self.assertEqual(statuses, [200, 400, 400])
        self.assertEqual(len(captures), 1)


if __name__ == '__main__':
    unittest.main()
