import copy
from decimal import Decimal
import json
import unittest
from plan48 import ROOT, SUITE, SUMMARY, build, estimate, make_order, validate_order


class Plan48Tests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((SUITE / "manifest.json").read_text())
        self.summary = json.loads((ROOT / SUMMARY).read_text())

    def test_order_reproducible_balanced_and_complete(self):
        order = make_order(self.manifest)
        self.assertEqual(order, make_order(self.manifest))
        self.assertEqual(len(order), 48)
        self.assertTrue(all(r["status"] == "planned_not_run" for r in order))
        for block in range(1, 13):
            members = [r for r in order if r["block"] == block]
            self.assertEqual(len(members), 4)
            self.assertEqual(len({r["task_id"] for r in members}), 1)
            self.assertEqual(len({r["tool"] for r in members}), 4)

    def test_duplicate_and_measured_status_rejected(self):
        original = make_order(self.manifest)
        for field, value in [("slot", original[1]["slot"]), ("tool", original[1]["tool"]), ("status", "success")]:
            order = copy.deepcopy(original)
            order[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_order(order, self.manifest)

    def test_estimates_are_not_benchmark_or_invoice(self):
        data = estimate(self.summary)
        self.assertEqual(data["scenarios"][0]["estimated_usd"], "5.00059584")
        self.assertEqual(data["scenarios"][2]["estimated_usd"], "15.00178752")
        self.assertEqual(data["proposed_new_estimate_guard_usd"], "16")
        self.assertEqual(Decimal(data["output_only_cost_if_every_request_hits_cap_usd"]), Decimal("14.155776"))
        self.assertEqual(data["historical_pilot_unpriced_requests"], 6)
        self.assertIsNone(data["historical_total_charge_usd"])
        self.assertIsNone(data["measured_benchmark_cost_usd"])
        self.assertIsNone(data["budget_approved_usd"])

    def test_missing_cost_cannot_supply_estimate(self):
        summary = copy.deepcopy(self.summary)
        next(r for r in summary["runs"] if r["run_id"] == "R-0035")["unpriced_requests"] = 1
        with self.assertRaises(ValueError):
            estimate(summary)

    def test_build_explicitly_keeps_gates_closed(self):
        outputs = build()
        planning = json.loads(outputs["planning.json"])
        for field in ["paid_runs_authorized", "fixture_acceptance_ready", "protocol_frozen", "run_ids_reserved"]:
            self.assertFalse(planning[field])
        self.assertEqual(len(planning["input_sha256"]), 12)
        self.assertTrue(all(t["pending"] for t in self.manifest["tasks"]))


if __name__ == "__main__":
    unittest.main()
