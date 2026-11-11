"""Explicit mixed schedule/approval/reservation tests; never provider/credential."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import retry_continue48 as retry


class RetryContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(retry.SUITE / "artifacts"), prefix="retry45-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def test_exact_retry_then_unrun_suffix_and_prior_cost(self):
        rows, known, missing = retry.predecessors()
        self.assertEqual(len(rows), 45)
        self.assertEqual(rows[0]["retry_of"], "R-0089")
        self.assertEqual(rows[0]["tool"], "opencode-v2")
        self.assertEqual(rows[0]["continuation_of"]["config_id"], "C-0190")
        self.assertEqual([r["slot"] for r in rows], [f"D48-{n:03d}" for n in range(4, 49)])
        self.assertTrue(all("retry_of" not in row for row in rows[1:]))
        self.assertEqual(rows[1]["continuation_of"]["run_id"], "R-0090")
        self.assertEqual((known, missing), ("0.21341376", 2))

    def approval(self, path):
        return {"launch_authorized": True, "plan_sha256": retry.cont.batch.digest(path), "scope": retry.SCOPE,
                "budget_estimate_usd": "16", "prior_unpriced_acknowledged": True, "retry_of": "R-0089",
                "rubric_revision": "b01-evidence-r2", "approved_by": "offline-test-not-real-approval", "approved_at_utc": "test"}

    def test_approval_binds_retry_budget_scope_unknown(self):
        path = self.root / "plan.json"
        plan = {"version": "test"}
        retry.cont.batch.native.write(path, plan)
        good = self.approval(path)
        with patch.object(retry, "make_plan", return_value=plan):
            self.assertEqual(retry.validate(path, good), plan)
            for key, value in [("launch_authorized", False), ("retry_of", "R-0088"), ("scope", "retry-all"),
                               ("budget_estimate_usd", "17"), ("prior_unpriced_acknowledged", False),
                               ("rubric_revision", "r3"), ("plan_sha256", "bad")]:
                with self.subTest(key=key), self.assertRaises(PermissionError):
                    retry.validate(path, {**good, key: value})

    def test_disabled_approval_before_key_or_reserve(self):
        plan_path, approval_path = self.root / "plan.json", self.root / "approval.json"
        retry.cont.batch.native.write(plan_path, {})
        retry.cont.batch.native.write(approval_path, {"launch_authorized": False})
        argv = ["retry45", "--paid", "--plan", str(plan_path), "--approval", str(approval_path),
                "--artifact-dir", str(self.root / "never")]
        with patch("sys.argv", argv), patch.object(retry, "make_plan", return_value={}), \
                patch.object(retry.cont.batch, "load_credential") as key, patch.object(retry, "reserve") as reserve:
            with self.assertRaises(PermissionError):
                retry.main()
            key.assert_not_called()
            reserve.assert_not_called()
        self.assertFalse((self.root / "never").exists())

    def test_fresh_atomic_reservation_preserves_predecessors_and_blocks_repeat(self):
        registry = self.root / "state.json"
        previous = [{"reserved": [{"run_id": "R-0039", "config_id": "C-0140"}]},
                    {"reserved": [{"run_id": "R-0089", "config_id": "C-0190"}]}]
        retry.cont.batch.native.write(registry, {"next_pilot_run_start": 134, "next_pilot_config_start": 235,
            "benchmark48_paid_batches": previous, "user_work": "keep"})
        rows, known, missing = retry.predecessors()
        plan = {"slots": rows, "proposed_run_start": 134, "proposed_config_start": 235,
                "prior_known_usd": known, "prior_unpriced_requests": missing}
        with patch.object(retry, "STATE", registry):
            reserved = retry.reserve(plan, self.root)
            self.assertEqual((reserved[0]["run_id"], reserved[-1]["run_id"]), ("R-0134", "R-0178"))
            current = json.loads(registry.read_text())
            self.assertEqual(current["benchmark48_paid_batches"][:2], previous)
            self.assertEqual(current["user_work"], "keep")
            self.assertEqual((current["next_pilot_run_start"], current["next_pilot_config_start"]), (179, 280))
            with self.assertRaises(PermissionError):
                retry.reserve(plan, self.root)

    def test_plan_refuses_third_predecessor(self):
        registry = self.root / "state.json"
        retry.cont.batch.native.write(registry, {"benchmark48_paid_batches": [{}, {}, {}]})
        with patch.object(retry, "STATE", registry), self.assertRaises(PermissionError):
            retry.make_plan()


if __name__ == "__main__":
    unittest.main()
