"""Tests offline: grading isolated/scope và budget pilot; không provider/credential."""
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
import io
import threading
import time
import tomllib
import argparse
import copy
from decimal import Decimal
from unittest.mock import patch

sys.dont_write_bytecode = True
from pilot import ROOT, grade, pending_cost, known_cost, pilot_config, budget_guard, classify_run, continuation_plan, ORDER, environment_recheck
from verify_pilot_fixtures import INTERVAL_REFERENCE, SCHEDULER_REFERENCE
from model_smoke import Broker, handler, MODEL, pacing_delay
from test_model_smoke import UnixHTTP, TEST_PRICING


class PilotTests(unittest.TestCase):
    def test_environment_recheck_is_explicit_and_separate(self):
        self.assertTrue(environment_recheck("legacy", "search-r2", True, True))
        self.assertFalse(environment_recheck("search-r2", "search-r2", False, True))
        for args in [("legacy", "search-r2", False, True), ("legacy", "search-r2", True, False),
                     ("search-r2", "search-r2", True, True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                environment_recheck(*args)

    def test_cross_environment_history_rejected_before_key_or_artifact(self):
        import pilot
        target = ROOT / "benchmark/artifacts/ENVIRONMENT-GATE-MUST-NOT-EXIST"
        self.assertFalse(target.exists())
        sources = [("--retry-run", ROOT / "benchmark/artifacts/PILOT-SOL-20261106-01/R-0009/result.json"),
                   ("--continue-after", ROOT / "benchmark/artifacts/PILOT-SOL-RETRY-20261106-01/result.json")]
        for flag, source in sources:
            argv = ["pilot", "--artifact-dir", str(target), flag, str(source), "--config-start", "9999", "--environment-profile", "search-r2"]
            with self.subTest(flag=flag), patch.object(sys, "argv", argv), patch.object(sys, "stderr", io.StringIO()), patch.object(pilot, "credential", side_effect=AssertionError("Do not read key")):
                with self.assertRaises(SystemExit) as error:
                    pilot.main()
                self.assertEqual(error.exception.code, 2)
        self.assertFalse(target.exists())

    def test_continuation_skips_successful_slot_and_carries_unknown_cost(self):
        source = ROOT / "benchmark/artifacts/PILOT-SOL-RETRY-20261106-01/result.json"
        batch = json.loads(source.read_text())
        plan, prior, unknown = continuation_plan(batch)
        self.assertEqual(plan, ORDER[1:])
        self.assertEqual(len(plan), 7)
        self.assertNotIn(("P-01", "pi"), plan)
        self.assertEqual(prior, Decimal("0.10501200"))
        self.assertEqual(unknown, 1)
        self.assertEqual(Decimal("3") - prior, Decimal("2.89498800"))

    def test_continuation_rejects_failed_incomplete_or_mismatched_source(self):
        original = json.loads((ROOT / "benchmark/artifacts/PILOT-SOL-RETRY-20261106-01/result.json").read_text())
        for key, value in [("finished_at_utc", None), ("all_planned_runs_completed", False),
                           ("retry_of", None), ("model", "different-model"), ("runs", [])]:
            batch = copy.deepcopy(original)
            batch[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                continuation_plan(batch)
        batch = copy.deepcopy(original)
        batch["runs"][0]["provider_requests"][-1]["terminal_type"] = "response.failed"
        with self.assertRaises(ValueError):
            continuation_plan(batch)

    def test_http_200_is_not_enough_for_task_classification(self):
        execution = {"timed_out": False, "exit_code": 0}
        completed = {"http_status": 200, "terminal_type": "response.completed",
                     "cost": {"estimated_cost_usd": "0.01"}}
        for requests in [[], [{**completed, "terminal_type": "response.failed"}],
                         [{**completed, "terminal_type": "response.incomplete"}],
                         [{**completed, "terminal_type": None}], [{**completed, "cost": {}}],
                         [{**completed, "error_type": "OSError"}], [{**completed, "http_status": 503}]]:
            for passed in [True, False]:
                with self.subTest(requests=requests, grade=passed):
                    self.assertEqual(classify_run(execution, True, {"pass": passed}, requests), "infra_error")
        self.assertEqual(classify_run(execution, True, {"pass": False}, [completed]), "failure")
        self.assertEqual(classify_run(execution, True, {"pass": True}, [completed]), "success")

    def test_saved_sol_failure_is_infra_not_task_failure(self):
        source = ROOT / "benchmark/artifacts/PILOT-SOL-20261106-01/R-0009/result.json"
        run = json.loads(source.read_text())
        self.assertEqual(classify_run(run["execution"], run["isolation_ok"], run["grading"], run["provider_requests"]), "infra_error")

    def test_budget_argument_is_positive_finite(self):
        self.assertEqual(str(budget_guard("3")), "3")
        for value in ["0", "-1", "NaN", "Infinity", "invalid"]:
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                budget_guard(value)

    def test_codex_config_has_one_native_reasoning_setting(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="pilot-config-test-") as directory:
            root = pathlib.Path(directory)
            (root / "codex-home").mkdir()
            pilot_config({"tool": "codex"}, root, "inert-token", "inert prompt")
            cfg = tomllib.loads((root / "codex-home/config.toml").read_text())
            self.assertEqual(cfg["sandbox_mode"], "workspace-write")
            self.assertEqual(cfg["model_reasoning_effort"], "none")
            self.assertEqual(cfg["approval_policy"], "never")

    def test_pacing_delay_and_deadline(self):
        self.assertEqual(pacing_delay(None, 30, 100, 300), 0)
        self.assertEqual(pacing_delay(100, 30, 105, 300), 25)
        self.assertEqual(pacing_delay(100, 30, 140, 300), 0)
        with self.assertRaises(TimeoutError):
            pacing_delay(100, 30, 105, 120)

    def test_pacing_at_actual_broker_boundary(self):
        pricing = TEST_PRICING
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="pilot-pacing-test-") as directory:
            path = str(pathlib.Path(directory) / "broker.sock")
            ledger, finishes, starts = [], [], []
            server = Broker(path, handler("inert-key", "inert-token", ledger, threading.Lock(), pricing, time.monotonic() + 10,
                serialize_requests=True, min_interval_seconds=0.03))
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            class MockOpener:
                def open(self, request, timeout):
                    starts.append(time.monotonic())
                    event = {"type": "response.completed", "response": {"model": MODEL}}
                    response = io.BytesIO(b"data: " + json.dumps(event).encode() + b"\n\n")
                    response.code = 200
                    response.headers = {"Content-Type": "text/event-stream"}
                    return response
            try:
                with patch("model_smoke.urllib.request.build_opener", return_value=MockOpener()):
                    for _ in range(2):
                        connection = UnixHTTP(path)
                        connection.request("POST", "/v1/responses", json.dumps({"model": MODEL, "stream": True}), {"Authorization": "Bearer inert-token"})
                        response = connection.getresponse()
                        self.assertEqual(response.status, 200)
                        response.read()
                        connection.close()
                self.assertGreaterEqual(starts[1] - starts[0], 0.03)
                self.assertEqual(ledger[1]["min_interval_seconds"], 0.03)
                self.assertGreater(ledger[1]["pacing_wait_seconds"], 0)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_broker_global_budget_and_unknown_usage(self):
        pricing = TEST_PRICING
        for unknown in [False, True]:
            with self.subTest(unknown=unknown), tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="pilot-budget-test-") as directory:
                path = str(pathlib.Path(directory) / "broker.sock")
                budget = [{}] if unknown else [{"cost": {"estimated_cost_usd": "0.999"}}]
                ledger = []
                server = Broker(path, handler("inert-key", "inert-token", ledger, threading.Lock(), pricing, time.monotonic() + 30,
                    request_limit=8, output_limit=2048, budget_limit="1", budget_ledger=budget, stop_on_unknown=True, serialize_requests=True))
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                def call():
                    connection = UnixHTTP(path)
                    connection.request("POST", "/v1/responses", json.dumps({"model": MODEL, "stream": True}), {"Authorization": "Bearer inert-token"})
                    response = connection.getresponse()
                    status = response.status
                    response.read()
                    connection.close()
                    return status
                try:
                    with patch("model_smoke.urllib.request.build_opener") as build:
                        event = {"type": "response.completed", "response": {"model": MODEL, "usage": {"input_tokens": 10000, "output_tokens": 0, "input_tokens_details": {"cached_tokens": 0}}}}
                        response = io.BytesIO(b"data: " + json.dumps(event).encode() + b"\n\n")
                        response.code = 200
                        response.headers = {"Content-Type": "text/event-stream"}
                        build.return_value.open.return_value = response
                        if unknown:
                            self.assertEqual(call(), 400)
                            build.assert_not_called()
                        else:
                            self.assertEqual(call(), 200)
                            sent = json.loads(build.return_value.open.call_args.args[0].data)
                            self.assertEqual(sent["max_output_tokens"], 2048)
                            self.assertEqual(len(budget), 2)
                            self.assertEqual(call(), 400)
                            self.assertEqual(build.return_value.open.call_count, 1)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join()

    def test_cost_guard(self):
        self.assertFalse(pending_cost([]))
        self.assertTrue(pending_cost([{"http_status": 429}]))
        values = [{"cost": {"estimated_cost_usd": "0.125"}}, {"cost": {"estimated_cost_usd": "0.875"}}]
        self.assertFalse(pending_cost(values))
        self.assertEqual(str(known_cost(values)), "1.000")

    def test_grading_baseline_reference_scope_and_symlink(self):
        for task_id, module, reference in [("P-01", "intervals.py", INTERVAL_REFERENCE), ("P-02", "scheduler.py", SCHEDULER_REFERENCE)]:
            with self.subTest(task=task_id), tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="pilot-grader-test-") as directory:
                root = pathlib.Path(directory)
                project = root / "project"
                shutil.copytree(ROOT / "benchmark/tasks" / task_id / "fixture", project)
                baseline = grade(project, task_id, root / "baseline")
                self.assertFalse(baseline["pass"])
                self.assertTrue(baseline["scope_ok"])
                (project / module).write_text(reference)
                self.assertTrue(grade(project, task_id, root / "reference")["pass"])
                with (project / "test_public.py").open("a") as handle:
                    handle.write("\n# forbidden edit\n")
                self.assertFalse(grade(project, task_id, root / "tamper")["scope_ok"])
                (project / "unexpected-link").symlink_to(root / "nonexistent-sentinel")
                report = grade(project, task_id, root / "symlink")
                self.assertFalse(report["scope_ok"])
                self.assertIn("unexpected-link", report["invalid_paths"])


if __name__ == "__main__":
    unittest.main()
