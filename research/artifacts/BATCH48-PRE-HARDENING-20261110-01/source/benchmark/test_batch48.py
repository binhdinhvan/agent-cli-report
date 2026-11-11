"""Authorization/registry/deadline/classification tests; no credential or provider access."""
import copy
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import batch48 as batch


class Batch48Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(batch.SUITE / "artifacts"), prefix="batch48-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def test_disabled_approval_never_reads_key_or_reserves(self):
        plan = self.root / "plan.json"
        plan.write_text('{}')
        approval = self.root / "approval.json"
        approval.write_text(json.dumps({"launch_authorized": False}))
        with patch.object(batch, "validate_plan"), patch.object(batch, "load_credential") as key, patch.object(batch, "reserve") as reserve:
            argv = ["batch48", "--paid", "--plan", str(plan), "--approval", str(approval), "--artifact-dir", str(self.root / "never")]
            with patch("sys.argv", argv), self.assertRaises(PermissionError):
                batch.main()
            key.assert_not_called()
            reserve.assert_not_called()
        self.assertFalse((self.root / "never").exists())

    def test_plan_hash_budget_and_scope_are_bound(self):
        plan = self.root / "plan.json"
        plan.write_text('{"candidate": true}')
        approval = {"launch_authorized": True, "plan_sha256": batch.digest(plan), "budget_estimate_usd": "16",
            "approved_by": "offline-test-not-real-approval", "approved_at_utc": "2026-11-10T00:00:00Z",
            "scope": "48-first-attempt-slots-no-auto-retry"}
        with patch.object(batch, "validate_plan"):
            self.assertEqual(batch.validate_approval(plan, approval), {"candidate": True})
            for field, value in [("launch_authorized", False), ("plan_sha256", "bad"), ("budget_estimate_usd", "17"), ("scope", "retry")]:
                changed = {**approval, field: value}
                with self.subTest(field=field), self.assertRaises(PermissionError):
                    batch.validate_approval(plan, changed)

    def test_plan_drift_fails_closed(self):
        with patch.object(batch, "make_plan", return_value={"version": 2}):
            with self.assertRaises(ValueError):
                batch.validate_plan({"version": 1})

    def test_reservation_atomic_and_not_reusable_uses_temporary_registry(self):
        registry = self.root / "state.json"
        initial = {"next_pilot_run_start": 70000, "next_pilot_config_start": 71000, "user_owned_field": "keep"}
        registry.write_text(json.dumps(initial))
        plan = {"proposed_run_start": 70000, "proposed_config_start": 71000,
            "slots": [{"slot": f"D48-{i:03d}", "tool": "pi", "task_id": "B-01", "repetition": "1"} for i in range(1, 49)]}
        with patch.object(batch, "STATE", registry):
            rows = batch.reserve(plan, self.root)
            self.assertEqual(len(rows), 48)
            self.assertEqual(rows[0]["run_id"], "R-70000")
            current = json.loads(registry.read_text())
            self.assertEqual(current["user_owned_field"], "keep")
            self.assertEqual(current["next_pilot_run_start"], 70048)
            with self.assertRaises(PermissionError):
                batch.reserve(plan, self.root)

    def test_monotonic_origin_shared_and_timeout(self):
        window = {}
        result = batch.execute(["/usr/bin/python3", "-B", "-c", "print('trusted control')"], self.root, window)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["outer_started_monotonic"], window["origin"])
        self.assertEqual(result["broker_deadline_monotonic"], window["origin"] + 900)
        self.assertEqual(window["deadline"], result["broker_deadline_monotonic"])
        timed = batch.execute(["/usr/bin/python3", "-B", "-c", "while True: pass"], self.root, {}, timeout=0.2)
        self.assertTrue(timed["timed_out"])

    def test_classification_retains_provider_timeout_overlap(self):
        execution = {"timed_out": True, "exit_code": -9, "output_limit_exceeded": False, "stdout": ""}
        good = {"http_status": 200, "terminal_type": "response.completed", "cost": {"estimated_cost_usd": "0.1"}}
        pacing = batch.native.PacingState()
        with patch.object(batch.native, "isolated", return_value=True):
            self.assertEqual(batch.outcome(execution, {"pass": True}, [good], pacing)[:2], ("timeout", "valid"))
            bad = {**good, "terminal_type": "response.failed"}
            self.assertEqual(batch.outcome(execution, {"pass": True}, [bad], pacing)[:2], ("infra_error", "pending_review"))
            pacing.stop_reason = "time_window_exhausted"
            self.assertEqual(batch.outcome(execution, {"pass": True}, [], pacing)[:2], ("timeout", "valid"))

    def test_success_does_not_require_synthetic_marker_but_rejects_error_event(self):
        execution = {"timed_out": False, "exit_code": 0, "output_limit_exceeded": False, "stdout": '{"type":"text"}\n'}
        ledger = [{"http_status": 200, "terminal_type": "response.completed", "cost": {"estimated_cost_usd": "0.1"}}]
        with patch.object(batch.native, "isolated", return_value=True):
            self.assertEqual(batch.outcome(execution, {"pass": True}, ledger, batch.native.PacingState())[:2], ("success", "valid"))
            execution["stdout"] = '{"type":"turn.failed"}\n'
            self.assertEqual(batch.outcome(execution, {"pass": True}, ledger, batch.native.PacingState())[:2], ("failure", "valid"))

    def test_missing_usage_never_zero(self):
        known, unknown = batch.ledger_cost([{"cost": {"estimated_cost_usd": "0.1"}}, {}])
        self.assertEqual(str(known), "0.1")
        self.assertEqual(unknown, 1)

    def test_paid_dispatch_without_key_refused_before_artifact(self):
        with self.assertRaises(PermissionError):
            batch.run_batch(self.root / "never", [], paid=True)
        self.assertFalse((self.root / "never").exists())


if __name__ == "__main__":
    unittest.main()
