"""Continuation/rubric tests offline only; no credential/provider; temp registry."""
import copy
from decimal import Decimal
import json
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

import continue48 as cont
from suite48_solutions import answer


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(cont.SUITE / "artifacts"), prefix="continue48-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def test_suffix_only_no_original_ids_reused(self):
        rows, known, unknown = cont.prior_state()
        self.assertEqual(len(rows), 47)
        self.assertEqual(rows[0]["slot"], "D48-002")
        self.assertEqual(rows[-1]["slot"], "D48-048")
        self.assertTrue(all("run_id" not in row and "config_id" not in row for row in rows))
        self.assertEqual(rows[0]["continuation_of"]["run_id"], "R-0040")
        self.assertEqual(known, "0.06853344")
        self.assertEqual(unknown, 1)

    def test_budget_injected_into_slot_and_broker_and_restored(self):
        previous = cont.batch.BUDGET
        with patch.object(cont.batch.native, "handler", return_value="sentinel") as handler:
            with cont.context({"remaining_known_guard_usd": "15.93146656"}):
                self.assertEqual(cont.batch.BUDGET, Decimal("15.93146656"))
                self.assertEqual(cont.runtime.SUITE, cont.REV)
                self.assertEqual(cont.batch.native.handler(budget_limit="16"), "sentinel")
                self.assertEqual(handler.call_args.kwargs["budget_limit"], "15.93146656")
                with self.assertRaises(ValueError):
                    cont.batch.native.handler(budget_limit="17")
        self.assertEqual(cont.batch.BUDGET, previous)
        self.assertEqual(cont.runtime.SUITE, cont.SUITE)

    def test_approval_binds_unknown_rubric_and_no_retry_scope(self):
        path = self.root / "plan.json"
        plan = {"scope": cont.SCOPE}
        cont.batch.native.write(path, plan)
        approval = {"launch_authorized": True, "plan_sha256": cont.batch.digest(path),
            "scope": cont.SCOPE, "budget_estimate_usd": "16", "prior_unpriced_acknowledged": True,
            "rubric_revision": "b01-evidence-r2", "approved_by": "offline-test-not-real-approval",
            "approved_at_utc": "2026-11-10T00:00:00Z"}
        with patch.object(cont, "make_plan", return_value=plan):
            self.assertEqual(cont.validate(path, approval), plan)
            for field, bad in [("launch_authorized", False), ("plan_sha256", "bad"),
                               ("prior_unpriced_acknowledged", False), ("rubric_revision", "r1"),
                               ("scope", "retry"), ("budget_estimate_usd", "17")]:
                with self.subTest(field=field), self.assertRaises(PermissionError):
                    cont.validate(path, {**approval, field: bad})

    def test_disabled_launch_before_key_reserve_or_artifact(self):
        plan_path, approval_path = self.root / "plan.json", self.root / "approval.json"
        plan = {"scope": cont.SCOPE}
        cont.batch.native.write(plan_path, plan)
        cont.batch.native.write(approval_path, {"launch_authorized": False})
        argv = ["continue48", "--paid", "--plan", str(plan_path), "--approval", str(approval_path),
                "--artifact-dir", str(self.root / "must-not-exist")]
        with patch("sys.argv", argv), patch.object(cont, "make_plan", return_value=plan), \
                patch.object(cont.batch, "load_credential") as key, patch.object(cont, "reserve") as reserve:
            with self.assertRaises(PermissionError):
                cont.main()
            key.assert_not_called()
            reserve.assert_not_called()
        self.assertFalse((self.root / "must-not-exist").exists())

    def test_atomic_suffix_reservation_preserves_predecessor_and_refuses_second(self):
        state_path = self.root / "state.json"
        predecessor = {"artifact": "old-kept", "reserved": [{"run_id": "R-0039", "config_id": "C-0140"}]}
        cont.batch.native.write(state_path, {"next_pilot_run_start": 87, "next_pilot_config_start": 188,
            "benchmark48_paid_batches": [predecessor], "user_owned": "keep"})
        rows, known, unknown = cont.prior_state()
        plan = {"slots": rows, "proposed_run_start": 87, "proposed_config_start": 188,
                "prior_known_usd": known, "prior_unpriced_requests": unknown}
        with patch.object(cont, "STATE", state_path):
            reserved = cont.reserve(plan, self.root)
            self.assertEqual((reserved[0]["run_id"], reserved[-1]["run_id"]), ("R-0087", "R-0133"))
            saved = json.loads(state_path.read_text())
            self.assertEqual(saved["benchmark48_paid_batches"][0], predecessor)
            self.assertEqual(saved["user_owned"], "keep")
            self.assertEqual((saved["next_pilot_run_start"], saved["next_pilot_config_start"]), (134, 235))
            with self.assertRaises(PermissionError):
                cont.reserve(plan, self.root)

    def test_dispatch_keeps_cumulative_unknown_and_does_not_charge_synthetic(self):
        plan = {"remaining_known_guard_usd": "15.93146656", "prior_known_usd": "0.06853344",
            "prior_unpriced_requests": 1, "protocol": "r2", "rubric_revision": "b01-evidence-r2",
            "input_sha256": {}, "resource_identity": {}}
        base = {"known_usage_estimate_usd": "0.1"}
        with patch.object(cont.batch, "run_batch", return_value=base.copy()):
            result = cont.dispatch(self.root, [], plan, paid=True, key="offline-inert-not-real")
            self.assertEqual(result["benchmark_known_cumulative_usd"], "0.16853344")
            self.assertIsNone(result["benchmark_estimated_total_usd"])
            self.assertEqual(result["prior_unpriced_requests"], 1)
        with patch.object(cont.batch, "run_batch", return_value=base.copy()):
            self.assertIsNone(cont.dispatch(self.root, [], plan)["benchmark_known_cumulative_usd"])

    def test_rubric_revision_regressions_in_grader_sandbox(self):
        observed = json.loads((cont.PRIOR / "D48-001/grader/snapshot/answer.json").read_text())
        base = answer()
        graph_added = copy.deepcopy(base)
        graph_added["cycle_error"]["evidence"].append("aliases.py:ALIASES")
        graph_only = copy.deepcopy(base)
        graph_only["cycle_error"]["evidence"] = ["aliases.py:ALIASES"]
        unrelated = copy.deepcopy(graph_added)
        unrelated["cycle_error"]["evidence"].append("defaults.py:DEFAULTS")
        fake = copy.deepcopy(base)
        fake["cycle_error"]["evidence"] = ["aliases.py:not_real"]
        empty = copy.deepcopy(base)
        empty["cycle_error"]["evidence"] = []
        wrong = copy.deepcopy(graph_added)
        wrong["cycle_error"]["message"] = "incorrect"
        for i, (value, expected) in enumerate([(base, True), (graph_added, True), (observed, True),
                                             (graph_only, False), (unrelated, False), (fake, False),
                                             (empty, False), (wrong, False)]):
            with self.subTest(case=i):
                project = self.root / f"project-{i}"
                shutil.copytree(cont.REV / "B-01/fixture", project)
                (project / "answer.json").write_text(json.dumps(value))
                with patch.object(cont.runtime, "SUITE", cont.REV):
                    result = cont.runtime.grade(project, "B-01", self.root / f"grade-{i}")
                self.assertEqual(result["pass"], expected)
        # Counterfactual only: original record and raw rubric are untouched.
        self.assertEqual(json.loads((cont.PRIOR / "result.json").read_text())["runs"][0]["status"], "infra_error")


if __name__ == "__main__":
    unittest.main()
