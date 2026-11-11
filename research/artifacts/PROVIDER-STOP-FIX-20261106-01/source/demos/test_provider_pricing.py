"""Offline pricing gates; synthetic rates only, no provider requests or key reads."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
from estimate_provider_cost import estimate, pricing_ready, require_pricing
import provider_probe
import provider_stream_probe
from preflight import ensure_fresh_id
import model_smoke
sys.path.insert(0, str(provider_probe.ROOT / "benchmark"))
import pilot


class PricingTests(unittest.TestCase):
    def test_missing_rates_are_not_zero(self):
        usage = {"input_tokens": 10, "output_tokens": 2, "input_tokens_details": {"cached_tokens": 4}}
        self.assertIsNone(estimate(usage, {"unit_tokens": 1000, "input_uncached": None})["estimated_cost_usd"])
        self.assertFalse(pricing_ready({"unit_tokens": 0, "input_uncached": "1", "input_cache_read": "1", "output": "1"}))
        rates = {"unit_tokens": 1000, "input_uncached": "1", "input_cache_read": "0.1", "output": "2"}
        self.assertEqual(estimate(usage, rates)["estimated_cost_usd"], "0.0104")

    def test_model_and_missing_price_gate(self):
        self.assertEqual(provider_probe.MODEL, "gpt-6.1-sol")
        with patch("estimate_provider_cost.pricing_ready", return_value=False), self.assertRaisesRegex(ValueError, "Pricing pending"):
            require_pricing(provider_probe.MODEL, provider_probe.BASE_URL)
        with self.assertRaisesRegex(ValueError, "Pricing pending"):
            require_pricing("different-model", provider_probe.BASE_URL)

    def test_paid_probes_block_before_credential_or_artifact(self):
        target = provider_probe.ROOT / "demos/artifacts/PRICE-GATE-MUST-NOT-BE-CREATED"
        self.assertFalse(target.exists())
        with patch("estimate_provider_cost.pricing_ready", return_value=False), patch.object(sys, "argv", ["probe", "--stage", "responses", "--artifact-dir", str(target)]), patch.object(provider_probe, "credential", side_effect=AssertionError("Credential must not be read")):
            with self.assertRaisesRegex(ValueError, "Pricing pending"):
                provider_probe.main()
        with patch("estimate_provider_cost.pricing_ready", return_value=False), patch.object(sys, "argv", ["stream", "--artifact-dir", str(target)]), patch.object(provider_stream_probe, "credential", side_effect=AssertionError("Credential must not be read")):
            with self.assertRaisesRegex(ValueError, "Pricing pending"):
                provider_stream_probe.main()
        self.assertFalse(target.exists())

    def test_retired_ids_cannot_be_reused(self):
        with self.assertRaisesRegex(ValueError, "retired"):
            ensure_fresh_id("C-0040")
        ensure_fresh_id("C-0041")

    def test_agent_runners_block_before_credentials(self):
        smoke_target = provider_probe.ROOT / "demos/artifacts/PRICE-GATE-SMOKE-MUST-NOT-EXIST"
        pilot_target = provider_probe.ROOT / "benchmark/artifacts/PRICE-GATE-PILOT-MUST-NOT-EXIST"
        self.assertFalse(smoke_target.exists())
        self.assertFalse(pilot_target.exists())
        with patch("estimate_provider_cost.pricing_ready", return_value=False), patch.object(sys, "argv", ["smoke", "--artifact-dir", str(smoke_target), "--config-start", "45"]), patch.object(model_smoke, "credential", side_effect=AssertionError("Credential must not be read")):
            with self.assertRaisesRegex(ValueError, "Pricing pending"):
                model_smoke.main()
        with patch("estimate_provider_cost.pricing_ready", return_value=False), patch.object(pilot.csv, "DictReader", return_value=[]), patch.object(sys, "argv", ["pilot", "--artifact-dir", str(pilot_target), "--run-start", "9", "--config-start", "49"]), patch.object(pilot, "credential", side_effect=AssertionError("Credential must not be read")):
            with self.assertRaisesRegex(ValueError, "Pricing pending"):
                pilot.main()
        self.assertFalse(smoke_target.exists())
        self.assertFalse(pilot_target.exists())


if __name__ == "__main__":
    unittest.main()
