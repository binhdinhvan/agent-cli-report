"""Offline regression tests; no CLI/provider/key access."""
import copy
import json
import unittest
from freeze_pilot import ROOT, REVIEW, build, cost_summary, reviewed, render


class FreezeTests(unittest.TestCase):
    def test_missing_cost_never_zero(self):
        result = cost_summary([{"cost": {"estimated_cost_usd": "0.2"}}, {}])
        self.assertEqual(result["known_usage_estimated_cost_usd"], "0.2")
        self.assertEqual(result["unpriced_requests"], 1)
        self.assertIsNone(result["estimated_total_usd"])

    def test_review_preserves_raw_and_rejects_mismatch(self):
        review = json.loads((ROOT / REVIEW).read_text())
        run = {"run_id": "R-0009", "status": "failure", "validity": "valid"}
        before = copy.deepcopy(run)
        self.assertEqual(reviewed(run, review), ("infra_error", "pending_review"))
        self.assertEqual(run, before)
        run["status"] = "success"
        with self.assertRaises(ValueError):
            reviewed(run, review)

    def test_full_ledger_and_baseline(self):
        summary, baseline = build()
        self.assertEqual(summary["inference_attempts"], 14)
        self.assertEqual(summary["upstream_requests"], 76)
        self.assertEqual(summary["reviewed_status_counts"], {"success": 8, "infra_error": 3, "timeout": 3})
        self.assertEqual(summary["known_usage_estimated_cost_usd"], "1.10640264")
        self.assertEqual(summary["unpriced_requests"], 6)
        self.assertIsNone(summary["estimated_total_usd"])
        self.assertEqual(summary["p02_cohort_known_estimate_usd"], "0.41671632")
        self.assertEqual(len(summary["launch_errors_without_inference"]), 1)
        self.assertFalse(baseline["paid_runs_authorized"])
        self.assertFalse(baseline["benchmark_protocol_approved"])
        self.assertEqual(len(baseline["pins"]), 4)
        self.assertEqual(baseline["timing_limits"]["wall_seconds"], 900)
        self.assertIn("R-0009", render(summary))
        timeouts = [r for r in summary["runs"] if r["run_id"] in ["R-0030", "R-0034"]]
        self.assertTrue(all(r["reviewed_status"] == "timeout" and r["scope_public_hidden_pass"] for r in timeouts))


if __name__ == "__main__":
    unittest.main()
