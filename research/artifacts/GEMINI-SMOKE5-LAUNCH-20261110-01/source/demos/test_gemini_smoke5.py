"""Offline tests of scoped5-request exception; never real provider or credential."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import gemini_smoke5 as smoke


def frames(marker=smoke.MARKER, usage=True, kind="response.completed"):
    response = {"status": "completed" if kind == "response.completed" else "failed", "model": smoke.MODEL}
    if usage:
        response["usage"] = {"input_tokens": 10, "output_tokens": 8}
    return [json.dumps({"type": "response.output_text.delta", "delta": marker}),
            json.dumps({"type": kind, "response": response})]


class Response(io.BytesIO):
    code = 200
    headers = {"content-type": "text/event-stream"}

    def __init__(self, events=None):
        super().__init__(b"".join(("data: " + s + "\n\n").encode() for s in (events or frames())))


class Clock:
    value = 0.0

    def clock(self):
        return self.value

    def sleep(self, duration):
        self.value += duration


class GeminiSmokeTests(unittest.TestCase):
    def test_minimal_model_payload_and_cap(self):
        p = smoke.payload()
        self.assertEqual(p["model"], "gemini-3.8-flash")
        self.assertEqual(p["max_output_tokens"], 256)
        self.assertTrue(p["stream"])
        self.assertNotIn("reasoning", p)
        self.assertNotIn("tools", p)

    def test_success_retains_usage_not_sol_costs(self):
        parsed = smoke.parse(Response())
        self.assertTrue(parsed["pass"])
        self.assertEqual(parsed["usage"], {"input_tokens": 10, "output_tokens": 8})
        self.assertNotIn("estimated_cost_usd", parsed)

    def test_usage_missing_not_zero_or_pass(self):
        parsed = smoke.parse(Response(frames(usage=False)))
        self.assertFalse(parsed["pass"])
        self.assertIsNone(parsed["usage"])

    def test_failed_terminal_cannot_pass(self):
        self.assertFalse(smoke.parse(Response(frames(kind="response.failed")))["pass"])

    def test_wrong_marker_cannot_pass(self):
        self.assertFalse(smoke.parse(Response(frames(marker="wrong")))["pass"])

    def test_partial_events_retained_after_stream_exception(self):
        def broken():
            yield b'data: {"type":"response.created"}\n'
            yield b'\n'
            raise TimeoutError("unit stream timeout")
        captured = {}
        with self.assertRaises(TimeoutError):
            smoke.parse(broken(), captured)
        self.assertEqual(captured["events"][0]["event"]["type"], "response.created")

    def test_approval_binds_model_request_cap_and_unpriced_scope(self):
        approval = {"authorized": True, "scope": smoke.SCOPE, "model": smoke.MODEL, "provider": smoke.BASE,
                    "max_requests": 5, "allow_unpriced_for_this_smoke_only": True,
                    "approved_by": "unit-test-not-real", "approved_at_utc": "test", "input_sha256": {"test": "hash"}}
        with patch.object(smoke, "inputs", return_value={"test": "hash"}):
            smoke.validate(approval)
            for field, value in [("authorized", False), ("max_requests", 6), ("model", "gpt-6.1-sol"),
                                 ("allow_unpriced_for_this_smoke_only", False), ("scope", "benchmark48")]:
                with self.subTest(field=field), self.assertRaises(PermissionError):
                    smoke.validate({**approval, field: value})
            with self.assertRaises(ValueError):
                smoke.validate({**approval, "input_sha256": {}})

    def test_disabled_approval_blocks_before_key_or_artifact(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="gemini-test-") as temporary:
            root = Path(temporary)
            (root / "approval.json").write_text('{"authorized":false}')
            argv = ["gemini_smoke5", "--approval", str(root / "approval.json"), "--artifact-dir", str(root / "never")]
            with patch("sys.argv", argv), patch.object(smoke, "credential") as key, self.assertRaises(PermissionError):
                smoke.main()
            key.assert_not_called()
            self.assertFalse((root / "never").exists())

    def test_exact_five_calls_virtual_pacing_cost_null(self):
        class Opener:
            calls = 0
            def open(self, request, timeout):
                self.calls += 1
                return Response()
        opener, virtual = Opener(), Clock()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="gemini-test-") as temporary:
            result = smoke.run(Path(temporary), "unit-inert-key", opener, clock=virtual.clock, sleep=virtual.sleep)
        self.assertEqual((opener.calls, result["passes"], result["not_run"]), (5, 5, 0))
        self.assertEqual([r["started_monotonic"] for r in result["requests"]], [0, 30, 60, 90, 120])
        self.assertIsNone(result["estimated_cost_usd"])

    def test_first_timeout_stops_without_retry(self):
        class Broken:
            calls = 0
            def open(self, request, timeout):
                self.calls += 1
                raise TimeoutError("unit timeout")
        opener, virtual = Broken(), Clock()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="gemini-test-") as temporary:
            result = smoke.run(Path(temporary), "unit-inert-key", opener, clock=virtual.clock, sleep=virtual.sleep)
        self.assertEqual((opener.calls, result["passes"], result["not_run"]), (1, 0, 4))
        self.assertEqual(result["requests"][0]["error_type"], "TimeoutError")


if __name__ == "__main__":
    unittest.main()
