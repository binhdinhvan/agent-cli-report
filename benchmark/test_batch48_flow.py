"""Exercise batch stop/continue decisions using only a local Unix broker and mocked workers."""
import http.client
import json
import pathlib
import socket
import tempfile
import time
import unittest
from decimal import Decimal
from unittest.mock import patch

import batch48 as batch


class Local(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("local", timeout=5)
        self.path = str(path)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect(self.path)


class Fake:
    def __init__(self, usage=True, terminal="response.completed"):
        self.usage, self.terminal, self.captures = usage, terminal, []

    def open(self, request, timeout):
        self.captures.append(json.loads(request.data))
        return batch.native.Response(batch.native.sse([], len(self.captures), usage=self.usage, terminal=self.terminal))


class BatchFlowTests(unittest.TestCase):
    def run_case(self, *, usage=True, terminal="response.completed", grading=True, budget=Decimal("16")):
        with tempfile.TemporaryDirectory(dir=str(batch.SUITE / "artifacts"), prefix="batchflow-") as temporary:
            base = pathlib.Path(temporary)
            artifact = base / "outputs"
            artifact.mkdir()
            rows = [{"slot": f"D48-{n:03d}", "task_id": "B-02", "tool": "pi", "repetition": "1"} for n in (1, 2)]
            counter = []

            def prepare(spec, config_id, task_id, paid=False):
                root = base / ("runtime" + str(len(counter)))
                counter.append(root)
                (root / "project").mkdir(parents=True)
                return {**spec, "binary": __file__, "binary_sha256": batch.digest(pathlib.Path(__file__))}, root, "unit-local-nonce", ["never-executed"], ["never-executed"]

            def execute(command, root, window, timeout):
                start = time.monotonic()
                window.update(origin=start, deadline=start + timeout, broker_deadline=start + 900)
                client = Local(root / "broker.sock")
                try:
                    client.request("POST", "/v1/responses", json.dumps({"model": batch.native.MODEL, "stream": True, "input": []}),
                        {"Authorization": "Bearer unit-local-nonce", "Content-Type": "application/json"})
                    response = client.getresponse()
                    self.assertEqual(response.status, 200)
                    response.read()
                finally:
                    client.close()
                return {"exit_code": 0, "timed_out": False, "output_limit_exceeded": False, "stdout": "", "stderr": "",
                    "duration_ms": 1, "supervisor_host_pid": 999999999, "witness": {}}

            with patch.object(batch, "prepare", side_effect=prepare), patch.object(batch, "execute", side_effect=execute), patch.object(
                    batch, "grade", return_value={"pass": grading}), patch.object(batch.native, "isolated", return_value=True), patch.object(
                    batch.native, "event_acceptance", return_value={"tool": True, "final": True}), patch.object(
                    batch.native, "SyntheticProvider", side_effect=lambda *args: Fake(usage, terminal)), patch.object(batch, "BUDGET", budget):
                result = batch.run_batch(artifact, rows)
            return result

    def test_unknown_usage_stops_suffix(self):
        result = self.run_case(usage=False)
        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(result["runs"][0]["status"], "infra_error")
        self.assertEqual(result["plan"][1]["status"], "not_run")
        self.assertIsNone(result["estimated_total_usd"])

    def test_failed_terminal_stops_suffix(self):
        result = self.run_case(terminal="response.failed")
        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(result["plan"][1]["status"], "not_run")

    def test_task_failure_does_not_selectively_stop_batch(self):
        result = self.run_case(grading=False)
        self.assertEqual([r["status"] for r in result["runs"]], ["failure", "failure"])
        self.assertTrue(result["all_slots_executed"])

    def test_estimate_guard_stops_next_slot(self):
        result = self.run_case(budget=Decimal("0.0001"))
        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(result["stop_reason"], "estimate_guard")
        self.assertEqual(result["plan"][1]["status"], "not_run")


if __name__ == "__main__":
    unittest.main()
