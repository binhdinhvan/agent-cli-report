"""Offline scope/approval/atomic reservation checks for continuation43."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import continue43 as current


class Continue43Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(current.SUITE / "artifacts"), prefix="continue43-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def test_only43_unattempted_slots_no_retry(self):
        rows, known, missing = current.predecessors()
        self.assertEqual([r["slot"] for r in rows], [f"D48-{n:03d}" for n in range(6, 49)])
        self.assertEqual(rows[0]["tool"], "pi")
        self.assertEqual(rows[0]["continuation_of"]["run_id"], "R-0136")
        self.assertTrue(all("retry_of" not in row and "run_id" not in row for row in rows))
        self.assertEqual((known, missing), ("0.25185936", 3))

    def test_approval_cannot_authorize_retry_or_extra_budget(self):
        path = self.root / "plan.json"
        current.cont.batch.native.write(path, {})
        approval = {"launch_authorized": True, "plan_sha256": current.cont.batch.digest(path), "scope": current.SCOPE,
            "budget_estimate_usd": "16", "prior_unpriced_acknowledged": True, "retries_authorized": False,
            "rubric_revision": "b01-evidence-r2", "approved_by": "offline-test-not-real", "approved_at_utc": "test"}
        with patch.object(current, "make_plan", return_value={}):
            self.assertEqual(current.validate(path, approval), {})
            for name, value in [("launch_authorized", False), ("retries_authorized", True), ("budget_estimate_usd", "17"),
                                ("scope", "retryR135"), ("prior_unpriced_acknowledged", False), ("plan_sha256", "bad")]:
                with self.subTest(name=name), self.assertRaises(PermissionError):
                    current.validate(path, {**approval, name: value})

    def test_disabled_launch_never_reads_key_or_reserves(self):
        plan_path, approval_path = self.root / "plan.json", self.root / "approval.json"
        current.cont.batch.native.write(plan_path, {})
        current.cont.batch.native.write(approval_path, {"launch_authorized": False})
        argv = ["continue43", "--paid", "--plan", str(plan_path), "--approval", str(approval_path),
                "--artifact-dir", str(self.root / "never")]
        with patch("sys.argv", argv), patch.object(current, "make_plan", return_value={}), \
                patch.object(current.cont.batch, "load_credential") as key, patch.object(current, "reserve") as reserve:
            with self.assertRaises(PermissionError):
                current.main()
            key.assert_not_called()
            reserve.assert_not_called()
        self.assertFalse((self.root / "never").exists())

    def test_atomic_ids_use_test_namespace_and_block_second_reservation(self):
        registry = self.root / "state.json"
        previous = [{"reserved": [{"run_id": "R-0039", "config_id": "C-0140"}]}, {"reserved": []}, {"reserved": []}]
        current.cont.batch.native.write(registry, {"next_pilot_run_start": 500000, "next_pilot_config_start": 510000,
            "benchmark48_paid_batches": previous, "user_work": "keep"})
        rows, known, missing = current.predecessors()
        plan = {"slots": rows, "proposed_run_start": 500000, "proposed_config_start": 510000,
                "prior_known_usd": known, "prior_unpriced_requests": missing}
        with patch.object(current, "STATE", registry):
            reserved = current.reserve(plan, self.root)
            self.assertEqual((reserved[0]["run_id"], reserved[-1]["run_id"]), ("R-500000", "R-500042"))
            saved = json.loads(registry.read_text())
            self.assertEqual(saved["benchmark48_paid_batches"][:3], previous)
            self.assertEqual(saved["user_work"], "keep")
            self.assertEqual((saved["next_pilot_run_start"], saved["next_pilot_config_start"]), (500043, 510043))
            with self.assertRaises(PermissionError):
                current.reserve(plan, self.root)

    def test_reserve_rejects_retry_row(self):
        registry = self.root / "state.json"
        current.cont.batch.native.write(registry, {"benchmark48_paid_batches": [{}, {}, {}]})
        rows = [{"retry_of": "R-0135"}] * 43
        with patch.object(current, "STATE", registry), self.assertRaises(ValueError):
            current.reserve({"slots": rows}, self.root)

    def test_plan_rejects_fourth_predecessor(self):
        registry = self.root / "state.json"
        current.cont.batch.native.write(registry, {"benchmark48_paid_batches": [{}, {}, {}, {}]})
        with patch.object(current, "STATE", registry), self.assertRaises(PermissionError):
            current.make_plan()


if __name__ == "__main__":
    unittest.main()
