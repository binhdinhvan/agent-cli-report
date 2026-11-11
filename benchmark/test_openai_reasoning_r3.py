"""Pure normalization and local Unix broker tests; no real credentials or provider IO."""
import copy
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import openai48_reasoning_r3 as r3
from test_batch48_flow import Local


class ReasoningTests(unittest.TestCase):
    def test_preserves_context_summary_and_other_fields_only_overrides_effort(self):
        payload = {'reasoning': {'effort': 'high', 'context': 'all_turns', 'summary': 'auto', 'extra': {'k': 1}}}
        before = copy.deepcopy(payload)
        result = r3.reasoning_fields(payload, {r3.LITE: 'true'})
        self.assertEqual(result, {**before['reasoning'], 'effort': 'low'})
        self.assertEqual(payload, before)

    def test_absent_null_or_empty_reasoning_without_lite(self):
        for payload in [{}, {'reasoning': None}, {'reasoning': {}}]:
            self.assertEqual(r3.reasoning_fields(payload, {}), {'effort': 'low'})

    def test_invalid_reasoning_types_rejected(self):
        for value in [[], 'low', 1, True]:
            with self.assertRaises(ValueError):
                r3.reasoning_fields({'reasoning': value}, {})

    def test_lite_requires_native_context_no_silent_synthesis(self):
        for context in [None, '', 'last_turn', 'ALL_TURNS']:
            with self.assertRaises(ValueError):
                r3.reasoning_fields({'reasoning': {'context': context}}, {'X-OpenAI-Internal-Codex-Responses-Lite': 'true'})

    def test_replay_native_r277_settings_and_keep_old_raw(self):
        path = r3.ROOT / 'benchmark/suite48/artifacts/OPENAI48-R2-20261110-01/result.json'
        raw = path.read_bytes(); q = json.loads(raw)['native_smoke']['runs'][-1]['requests'][0]
        self.assertEqual(q['http_status'], 400)
        fixed = r3.reasoning_fields(q['native_requested_settings'], {r3.LITE: q['responses_lite']})
        self.assertEqual(fixed['context'], 'all_turns')
        self.assertNotIn('context', q['effective_settings']['reasoning'])
        self.assertEqual(path.read_bytes(), raw)

    def test_outbound_request_preserves_payload_headers_and_restores_globals(self):
        native = r3.r1.native
        original_request = native.model_smoke.urllib.request.Request
        original_handler = native.handler
        payload = {'model': r3.r1.MODEL, 'stream': True, 'reasoning': {'effort': 'high', 'context': 'all_turns', 'summary': 'auto'},
                   'input': [{'role': 'user', 'content': 'test'}], 'max_output_tokens': 2048, 'tools': [],
                   'prompt_cache_options': {'ttl': '30m'}}
        before = copy.deepcopy(payload)
        with r3.context():
            req = native.model_smoke.urllib.request.Request(r3.r1.BASE + '/responses', data=json.dumps(payload).encode(),
                method='POST', headers={r3.LITE: 'true'})
            effective = json.loads(req.data)
            self.assertEqual(effective['reasoning'], {**payload['reasoning'], 'effort': 'low'})
            for k in ('input', 'tools', 'max_output_tokens', 'prompt_cache_options'):
                self.assertEqual(effective[k], payload[k])
            self.assertEqual(effective['service_tier'], 'default'); self.assertFalse(effective['store'])
            self.assertEqual(dict((k.lower(), v) for k, v in req.header_items())[r3.LITE], 'true')
        self.assertEqual(payload, before)
        self.assertIs(native.model_smoke.urllib.request.Request, original_request)
        self.assertIs(native.handler, original_handler)

    def test_wrong_endpoint_still_rejected(self):
        with r3.context(), self.assertRaises(ValueError):
            r3.r1.native.model_smoke.urllib.request.Request('https://wrong.invalid/responses', data=b'{}')

    def test_broker_two_lite_turns_preserve_context_and_cache_cost(self):
        native = r3.r1.native
        ledger = []; virtual = native.VirtualPacing()
        pacing = native.PacingState(clock=virtual.clock, sleep=virtual.sleep)

        class Provider:
            captures = []
            def open(inner, request, timeout):
                payload = json.loads(request.data); inner.captures.append(payload)
                self.assertEqual(payload['reasoning'], {'effort': 'low', 'context': 'all_turns', 'summary': 'auto'})
                self.assertEqual(dict((k.lower(), v) for k, v in request.header_items())[r3.LITE], 'true')
                event = {'type': 'response.completed', 'response': {'model': r3.r1.MODEL, 'status': 'completed',
                    'usage': {'input_tokens': 3112, 'output_tokens': 32,
                              'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 3109}}}}
                return native.Response(b'data: ' + json.dumps(event).encode() + b'\n\n')

        provider = Provider()
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='reasoning-r3-broker-') as tmp, r3.context(), \
                patch.object(native.model_smoke.urllib.request, 'build_opener', return_value=provider), \
                patch.object(socket, 'create_connection', side_effect=AssertionError('Offline test forbids TCP')):
            path = Path(tmp) / 'broker.sock'
            handler = native.handler('inert-unit-key', 'unit-nonce', ledger, threading.Lock(), r3.cache.pricing(),
                time.monotonic() + 900, request_limit=8, output_limit=2048, budget_limit='16', stop_on_unknown=True,
                serialize_requests=True, min_interval_seconds=30, pacing_state=pacing, stop_on_provider_failure=True,
                minimum_request_window_seconds=60)
            server = native.Broker(str(path), handler); thread = threading.Thread(target=server.serve_forever); thread.start()
            try:
                for _ in range(2):
                    client = Local(path)
                    try:
                        client.request('POST', '/v1/responses', json.dumps({'model': r3.r1.MODEL, 'stream': True,
                            'reasoning': {'effort': 'high', 'context': 'all_turns', 'summary': 'auto'}, 'input': []}),
                            {'Authorization': 'Bearer unit-nonce', 'Content-Type': 'application/json', r3.LITE: 'true'})
                        response = client.getresponse(); self.assertEqual(response.status, 200); response.read()
                    finally:
                        client.close()
            finally:
                server.shutdown(); server.server_close(); thread.join()
        self.assertEqual(len(provider.captures), 2)
        for q, payload in zip(ledger, provider.captures):
            self.assertEqual(q['native_requested_settings']['reasoning']['effort'], 'high')
            self.assertEqual(q['effective_settings']['reasoning'], payload['reasoning'])
            self.assertEqual(q['reasoning_normalizer_revision'], 'preserve-native-fields-r3')
            self.assertEqual(q['cost']['estimated_cost_usd'], '0.015871')


if __name__ == '__main__':
    unittest.main()
