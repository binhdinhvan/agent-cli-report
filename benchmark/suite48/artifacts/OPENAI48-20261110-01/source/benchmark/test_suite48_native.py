"""Native adapter/production-broker guards against in-memory responses, never the provider."""
import csv
import http.client
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import suite48_native as native


class UnixHTTP(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("local", timeout=10)
        self.path = str(path)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect(self.path)


class Stub:
    def __init__(self, usage=True, terminal="response.completed"):
        self.usage, self.terminal, self.payloads = usage, terminal, []

    def open(self, request, timeout):
        self.payloads.append(json.loads(request.data))
        return native.Response(native.sse([], len(self.payloads), usage=self.usage, terminal=self.terminal))


class NativeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="native48-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def exercise(self, stub, count=2, window=900, budget="16"):
        ledger, all_requests = [], []
        virtual = native.VirtualPacing()
        pacing = native.PacingState(clock=virtual.clock, sleep=virtual.sleep)
        pricing = json.loads((native.ROOT / "research/provider-pricing.json").read_text())
        server = native.Broker(str(self.root / "broker.sock"), native.guarded_handler(
            ledger, all_requests, pacing, virtual.clock() + window, pricing, budget=budget))
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        statuses = []
        try:
            with patch.object(native.model_smoke.urllib.request, "build_opener", return_value=stub), patch.object(
                    socket, "create_connection", side_effect=AssertionError("No external TCP in tests")):
                for _ in range(count):
                    connection = UnixHTTP(self.root / "broker.sock")
                    try:
                        connection.request("POST", "/v1/responses", json.dumps({"model": native.MODEL, "stream": True,
                            "input": [], "max_output_tokens": 9999}), {"Authorization": "Bearer " + native.NONCE, "Content-Type": "application/json"})
                        response = connection.getresponse()
                        statuses.append(response.status)
                        response.read()
                    finally:
                        connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        return ledger, pacing, statuses

    def test_caps_usage_serialization_and_virtual_pacing(self):
        stub = Stub()
        ledger, pacing, statuses = self.exercise(stub, count=9)
        self.assertEqual(len(stub.payloads), 8)
        self.assertEqual(statuses[:8], [200] * 8)
        self.assertEqual(statuses[-1], 400)
        self.assertTrue(all(p["max_output_tokens"] == 2048 and p["store"] is False for p in stub.payloads))
        self.assertTrue(all(q["cost"]["estimated_cost_usd"] == "0.0005688" for q in ledger))
        self.assertTrue(all(q["minimum_request_window_seconds"] == 60 for q in ledger))
        self.assertGreaterEqual(sum(q["pacing_wait_seconds"] for q in ledger), 209.9)

    def test_synthetic_sse_has_complete_usage_for_codex(self):
        events = [json.loads(line[6:]) for line in native.sse([], 1).decode().splitlines() if line.startswith("data: ")]
        completed = events[-1]["response"]
        self.assertEqual(completed["usage"]["total_tokens"], completed["usage"]["input_tokens"] + completed["usage"]["output_tokens"])

    def test_failed_terminal_latches_before_second_upstream(self):
        stub = Stub(terminal="response.failed")
        ledger, pacing, statuses = self.exercise(stub)
        self.assertEqual(statuses, [200, 503])
        self.assertEqual(len(ledger), 1)
        self.assertEqual(pacing.stop_reason, "provider_failure")
        self.assertEqual(pacing.blocked_requests, 1)

    def test_missing_usage_is_unknown_and_blocks_next(self):
        ledger, pacing, statuses = self.exercise(Stub(usage=False))
        self.assertEqual(statuses, [200, 400])
        self.assertEqual(len(ledger), 1)
        self.assertIsNone(ledger[0]["cost"]["estimated_cost_usd"])

    def test_reserve_blocks_without_upstream(self):
        stub = Stub()
        ledger, pacing, statuses = self.exercise(stub, window=50)
        self.assertEqual(statuses, [408, 408])
        self.assertEqual(ledger, [])
        self.assertEqual(stub.payloads, [])
        self.assertEqual(pacing.stop_reason, "time_window_exhausted")

    def test_estimate_guard_blocks_next_not_invoice_cap(self):
        ledger, pacing, statuses = self.exercise(Stub(), budget="0.0001")
        self.assertEqual(statuses, [200, 400])
        self.assertEqual(len(ledger), 1)
        self.assertGreater(float(ledger[0]["cost"]["estimated_cost_usd"]), 0.0001)

    def test_slot_mapping_does_not_allocate_paid_ids(self):
        with native.ORDER.open() as stream:
            rows = native.slot_mapping(csv.DictReader(stream))
        self.assertEqual(len(rows), 48)
        self.assertEqual(len([row for row in rows if row["repetition"] == "1"]), 16)
        self.assertTrue(all("run_id" not in row and "config_id" not in row for row in rows))
        with self.assertRaises(ValueError):
            native.slot_mapping([rows[0], rows[0]])
        with self.assertRaises(ValueError):
            native.prepare({}, "C-0140", "B-01")

    def test_cli_refuses_paid_and_requires_explicit_offline(self):
        command = [sys.executable, "-B", str(native.ROOT / "benchmark/suite48_native.py"), "--artifact-dir", str(self.root / "never-created")]
        outcome = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertEqual(outcome.returncode, 2)
        self.assertIn("Only offline", outcome.stderr)
        self.assertFalse((self.root / "never-created").exists())

    def test_bounded_executor_and_duration_fields(self):
        execution = native.execute(["/usr/bin/python3", "-B", "-c", "print('trusted control')"], self.root)
        self.assertEqual(execution["exit_code"], 0)
        self.assertGreaterEqual(execution["outer_finished_monotonic"], execution["outer_started_monotonic"])
        self.assertIsNone(execution["native_clock"])
        execution = native.execute(["/usr/bin/python3", "-B", "-c", "while True: pass"], self.root, timeout=0.2)
        self.assertTrue(execution["timed_out"])
        self.assertFalse(pathlib.Path("/proc", str(execution["supervisor_host_pid"])).exists())


if __name__ == "__main__":
    unittest.main()
