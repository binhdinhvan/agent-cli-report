"""Synthetic HTTP only: no key reads, no real upstream, no polling or retry sleeps."""
import concurrent.futures
import contextlib
import io
import http.client
import json
import pathlib
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from model_smoke import Broker, MODEL, PacingState, handler
from test_model_smoke import TEST_PRICING, UnixHTTP


def response(terminal="response.completed", status=200):
    payload = {"type": terminal, "response": {"model": MODEL,
        "usage": {"input_tokens": 3, "output_tokens": 1, "input_tokens_details": {"cached_tokens": 0}}}}
    stream = io.BytesIO(b'data: ' + json.dumps(payload).encode() + b'\n\n' if terminal else b'')
    stream.code = status
    stream.headers = {"Content-Type": "text/event-stream"}
    return stream


@contextlib.contextmanager
def broker(path, state, ledger, shared, *, entered=None):
    base = handler("inert-key", "inert-token", ledger, threading.Lock(), TEST_PRICING,
        time.monotonic() + 120, serialize_requests=True, min_interval_seconds=30,
        pacing_state=state, budget_ledger=shared, stop_on_provider_failure=True)

    class Tracked(base):
        def do_POST(self):
            if entered:
                entered.set()
            super().do_POST()

    server = Broker(str(path), Tracked)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def call(path):
    conn = UnixHTTP(str(path))
    try:
        conn.request("POST", "/v1/responses", json.dumps({"model": MODEL, "stream": True}),
            {"Authorization": "Bearer inert-token"})
        reply = conn.getresponse()
        reply.read()
        return reply.status
    finally:
        conn.close()


class ProviderStopTests(unittest.TestCase):
    def test_provider_stop_cannot_be_enabled_without_serialization(self):
        with self.assertRaisesRegex(ValueError, "requires serialized"):
            handler("inert-key", "inert-token", [], threading.Lock(), TEST_PRICING,
                time.monotonic() + 120, stop_on_provider_failure=True)

    def test_failed_incomplete_missing_terminal_and_http_errors_latch_batch(self):
        for terminal, status in [("response.failed", 200), ("response.incomplete", 200),
                                 (None, 200), (None, 429), (None, 503)]:
            with self.subTest(terminal=terminal, status=status), tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="provider-stop-") as directory:
                state = PacingState()
                shared, ledgers = [], [[], []]
                first, second = [pathlib.Path(directory) / f'{i}.sock' for i in range(2)]
                with patch("model_smoke.urllib.request.build_opener") as build:
                    build.return_value.open.return_value = response(terminal, status)
                    with broker(first, state, ledgers[0], shared):
                        self.assertEqual(call(first), status)
                        self.assertEqual(call(first), 503)  # Native retry blocked locally.
                    with broker(second, state, ledgers[1], shared):
                        self.assertEqual(call(second), 503)  # New CLI cannot bypass stop.
                    self.assertEqual(build.return_value.open.call_count, 1)
                self.assertEqual(state.stop_reason, "provider_failure")
                self.assertEqual(state.blocked_requests, 2)
                self.assertEqual(len(shared), 1)
                self.assertEqual(ledgers[1], [])

    def test_upstream_exception_latches_batch(self):
        state = PacingState()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="provider-exception-") as directory:
            path = pathlib.Path(directory) / 'broker.sock'
            with broker(path, state, [], []), patch("model_smoke.urllib.request.build_opener") as build:
                build.return_value.open.side_effect = OSError("synthetic error")
                with self.assertRaises(http.client.RemoteDisconnected):
                    call(path)
                self.assertEqual(call(path), 503)
                self.assertEqual(build.return_value.open.call_count, 1)

    def test_two_simultaneous_clients_serialize_across_brokers(self):
        clock = [time.monotonic()]
        waits = []

        def sleep(seconds):
            waits.append(seconds)
            clock[0] += seconds

        state = PacingState(clock=lambda: clock[0], sleep=sleep)
        first_open, release, second_entered = threading.Event(), threading.Event(), threading.Event()
        starts, active = [], [0, 0]
        lock = threading.Lock()

        def open_mock(request, timeout):
            with lock:
                active[0] += 1
                active[1] = max(active)
                index = len(starts)
                starts.append(clock[0])
            try:
                if index == 0:
                    first_open.set()
                    if not release.wait(2):
                        raise RuntimeError("test release timed out")
                return response()
            finally:
                with lock:
                    active[0] -= 1

        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="provider-serial-") as directory:
            first, second = [pathlib.Path(directory) / f'{i}.sock' for i in range(2)]
            shared, ledgers = [], [[], []]
            with broker(first, state, ledgers[0], shared), broker(second, state, ledgers[1], shared, entered=second_entered), patch("model_smoke.urllib.request.build_opener") as build:
                build.return_value.open.side_effect = open_mock
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    one = pool.submit(call, first)
                    try:
                        self.assertTrue(first_open.wait(2))
                        two = pool.submit(call, second)
                        self.assertTrue(second_entered.wait(2))
                        self.assertEqual(len(starts), 1)
                    finally:
                        release.set()
                    self.assertEqual(one.result(timeout=3), 200)
                    self.assertEqual(two.result(timeout=3), 200)
            self.assertEqual(active[1], 1)
            self.assertEqual(waits, [30])
            self.assertEqual(starts[1] - starts[0], 30)
            self.assertEqual(len(shared), 2)
            self.assertIsNone(state.stop_reason)


if __name__ == '__main__':
    unittest.main()
