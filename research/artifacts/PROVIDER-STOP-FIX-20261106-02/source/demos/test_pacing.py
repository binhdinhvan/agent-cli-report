"""Offline cross-broker regression: fake monotonic time, inert HTTP responses, no key/API."""
import io
import json
import pathlib
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from model_smoke import Broker, MODEL, PacingState, handler, pacing_delay
from test_model_smoke import TEST_PRICING, UnixHTTP


class PacingTests(unittest.TestCase):
    def exercise(self, first_status=200, *, expired=False, failure=False):
        clock = [time.monotonic()]
        sleeps = []

        def sleep(seconds):
            sleeps.append(seconds)
            clock[0] += seconds

        state = PacingState(clock=lambda: clock[0], sleep=sleep)
        ledgers = [[], []]
        shared_budget = []

        def response(status):
            payload = {"type": "response.completed", "response": {"model": MODEL,
                "usage": {"input_tokens": 3, "output_tokens": 1, "input_tokens_details": {"cached_tokens": 0}}}}
            stream = io.BytesIO(b'data: ' + json.dumps(payload).encode() + b'\n\n' if status == 200 else b'{"error":"synthetic"}')
            stream.code = status
            stream.headers = {"Content-Type": "text/event-stream"}
            return stream

        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="cross-pacing-") as directory:
            for index in range(2):
                path = str(pathlib.Path(directory) / f'{index}.sock')
                deadline = clock[0] + (10 if expired and index else 120)
                server = Broker(path, handler("inert-key", "inert-token", ledgers[index], threading.Lock(),
                    TEST_PRICING, deadline, serialize_requests=True, min_interval_seconds=30,
                    budget_ledger=shared_budget, pacing_state=state))
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                try:
                    with patch("model_smoke.urllib.request.build_opener") as build:
                        if failure and index == 0:
                            build.return_value.open.side_effect = OSError("synthetic upstream failure")
                        else:
                            build.return_value.open.return_value = response(first_status if index == 0 else 200)
                        conn = UnixHTTP(path)
                        conn.request("POST", "/v1/responses", json.dumps({"model": MODEL, "stream": True}),
                            {"Authorization": "Bearer inert-token"})
                        try:
                            reply = conn.getresponse()
                            reply.read()
                            self.assertEqual(reply.status, 408 if expired and index else first_status if index == 0 else 200)
                        except Exception:
                            if not (failure and index == 0):
                                raise
                        finally:
                            conn.close()
                        if expired and index:
                            build.assert_not_called()
                        else:
                            self.assertEqual(build.return_value.open.call_count, 1)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join()
                self.assertEqual(state.last_finished, clock[0])
                clock[0] += 2  # CLI startup/teardown does not reset pacing.
        if expired:
            self.assertEqual(sleeps, [])
            self.assertEqual(len(shared_budget), 1)
        else:
            self.assertEqual(sleeps, [28])
            self.assertEqual(ledgers[1][0]['pacing_wait_seconds'], 28)
            self.assertEqual(len(shared_budget), 2)

    def test_completed_response_across_brokers(self):
        self.exercise()

    def test_http_error_across_brokers(self):
        self.exercise(503)

    def test_exception_across_brokers(self):
        self.exercise(failure=True)

    def test_deadline_blocks_next_broker_without_upstream(self):
        self.exercise(expired=True)

    def test_delay_boundaries(self):
        self.assertEqual(pacing_delay(None, 30, 100, 200), 0)
        self.assertEqual(pacing_delay(60, 30, 100, 200), 0)
        with self.assertRaises(TimeoutError):
            pacing_delay(100, 30, 110, 130)


if __name__ == '__main__':
    unittest.main()
