"""Fake-clock HTTP regression for timing revisions; no provider/key/real retry sleeps."""
import io
import json
import pathlib
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from timing_policy import timing_policy, validate_history_timing
from model_smoke import Broker, MODEL, PacingState, handler
from test_model_smoke import UnixHTTP, TEST_PRICING


class TimingPolicyTests(unittest.TestCase):
    def request(self, elapsed, *, policy="paced-900", previous_elapsed=None):
        limits = timing_policy(policy)
        start = time.monotonic()
        clock = [start + elapsed]
        waits = []

        def sleep(seconds):
            waits.append(seconds)
            clock[0] += seconds

        state = PacingState(clock=lambda: clock[0], sleep=sleep)
        state.last_finished = None if previous_elapsed is None else start + previous_elapsed
        ledger = []
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="timing-guard-") as directory:
            path = str(pathlib.Path(directory) / "broker.sock")
            server = Broker(path, handler("inert-key", "inert-token", ledger, threading.Lock(), TEST_PRICING,
                start + limits["wall_seconds"], serialize_requests=True, min_interval_seconds=30, pacing_state=state,
                stop_on_provider_failure=True, minimum_request_window_seconds=limits["minimum_request_window_seconds"]))
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            statuses = []
            try:
                with patch("model_smoke.urllib.request.build_opener") as build:
                    event = {"type": "response.completed", "response": {"model": MODEL,
                        "usage": {"input_tokens": 3, "output_tokens": 1, "input_tokens_details": {"cached_tokens": 0}}}}
                    stream = io.BytesIO(b"data: " + json.dumps(event).encode() + b"\n\n")
                    stream.code = 200
                    stream.headers = {"Content-Type": "text/event-stream"}
                    build.return_value.open.return_value = stream
                    # A rejected timing request must latch locally, including a native retry.
                    attempts = 2 if elapsed >= 841 or previous_elapsed == 820 else 1
                    for _ in range(attempts):
                        connection = UnixHTTP(path)
                        try:
                            connection.request("POST", "/v1/responses", json.dumps({"model": MODEL, "stream": True}),
                                {"Authorization": "Bearer inert-token"})
                            reply = connection.getresponse()
                            reply.read()
                            statuses.append(reply.status)
                        finally:
                            connection.close()
                    count = build.return_value.open.call_count
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
        return statuses, count, state, ledger, waits

    def test_guard_blocks_last_seconds_and_does_not_open_upstream(self):
        statuses, count, state, ledger, waits = self.request(899)
        self.assertEqual(statuses, [408, 408])
        self.assertEqual(count, 0)
        self.assertEqual(ledger, [])
        self.assertEqual(waits, [])
        self.assertEqual(state.stop_reason, "time_window_exhausted")
        self.assertEqual(state.blocked_requests, 0)  # Not a provider failure.
        self.assertEqual(state.timing_blocked_requests, 2)

    def test_pacing_must_leave_request_reserve_before_any_sleep(self):
        statuses, count, state, ledger, waits = self.request(830, previous_elapsed=820)
        self.assertEqual(statuses, [408, 408])  # 20s pacing would leave only50s.
        self.assertEqual(count, 0)
        self.assertEqual(waits, [])
        self.assertEqual(state.stop_reason, "time_window_exhausted")

    def test_sufficient_pacing_and_reserve_dispatches_once(self):
        statuses, count, state, ledger, waits = self.request(790, previous_elapsed=780)
        self.assertEqual(statuses, [200])
        self.assertEqual(count, 1)
        self.assertEqual(waits, [20])
        self.assertEqual(ledger[0]["deadline_remaining_seconds_at_dispatch"], 90)
        self.assertIsNone(state.stop_reason)

    def test_work_after_300_seconds_not_cut_off_by_new_policy(self):
        self.assertEqual(self.request(310, policy="legacy-300")[0], [408])
        self.assertEqual(self.request(310, policy="paced-900")[0], [200])

    def test_policy_limits_preserve_request_and_output_caps(self):
        new, old = timing_policy("paced-900"), timing_policy("legacy-300")
        self.assertEqual((new["wall_seconds"], new["minimum_request_window_seconds"]), (900, 60))
        self.assertEqual((new["request_limit"], new["output_limit"]), (8, 2048))
        self.assertEqual((old["wall_seconds"], old["minimum_request_window_seconds"]), (300, 0))
        with self.assertRaises(ValueError):
            timing_policy("unreviewed")

    def test_changed_timing_cannot_silently_reuse_history(self):
        validate_history_timing("legacy-300", "paced-900", True, True)
        validate_history_timing("paced-900", "paced-900", False, False)
        for args in [("legacy-300", "paced-900", False, True), ("legacy-300", "paced-900", True, False),
                     ("paced-900", "paced-900", True, True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                validate_history_timing(*args)


if __name__ == "__main__":
    unittest.main()
