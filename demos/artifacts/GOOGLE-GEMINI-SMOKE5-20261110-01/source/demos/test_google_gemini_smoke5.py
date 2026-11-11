"""Offline Google adapter tests; dummy keys only, no provider or user-key reads."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import google_gemini_smoke5 as google


def stream(marker=google.MARKER, usage=True, finish="stop", done=True):
    events = [{"model": google.MODEL, "choices": [{"index": 0, "delta": {"content": marker}, "finish_reason": None}]},
              {"model": google.MODEL, "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]}]
    if usage:
        events.append({"choices": [], "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20,
                                                "completion_tokens_details": {"reasoning_tokens": 3}}})
    raw = b"".join(("data: " + json.dumps(e) + "\n\n").encode() for e in events)
    return raw + (b"data: [DONE]\n\n" if done else b"")


class Response(io.BytesIO):
    code = 200
    headers = {"content-type": "text/event-stream"}

    def __init__(self):
        super().__init__(stream())


class GoogleSmokeTests(unittest.TestCase):
    def test_direct_google_endpoint_and_payload_not_responses(self):
        self.assertEqual(google.URL, "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
        self.assertNotIn("shopaikey", google.BASE)
        p = google.payload()
        self.assertEqual((p["model"], p["max_tokens"]), ("gemini-3.8-flash", 256))
        self.assertTrue(p["stream_options"]["include_usage"])
        self.assertIn("messages", p)
        self.assertNotIn("input", p)
        self.assertNotIn("reasoning_effort", p)

    def test_chat_sse_and_original_usage_retained(self):
        parsed = google.parse(Response())
        self.assertTrue(parsed["pass"] and parsed["done_received"])
        self.assertEqual(parsed["usage"]["completion_tokens_details"]["reasoning_tokens"], 3)
        self.assertEqual(parsed["usage"]["completion_tokens"], 8)
        self.assertNotIn("prompt_tokens_details", parsed["usage"])

    def test_missing_usage_or_length_or_wrong_marker_fail(self):
        for kwargs in ({"usage": False}, {"finish": "length"}, {"marker": "wrong"}):
            with self.subTest(kwargs=kwargs):
                self.assertFalse(google.parse(io.BytesIO(stream(**kwargs)))["pass"])

    def test_partial_stream_retained_on_error(self):
        def broken():
            yield b'data: {"choices":[{"index":0,"delta":{"content":"partial"}}]}\n'
            yield b'\n'
            raise TimeoutError("unit timeout")
        captured = {}
        with self.assertRaises(TimeoutError):
            google.parse(broken(), captured)
        self.assertEqual(len(captured["events"]), 1)

    def test_dummy_credential_permissions_only_not_user_file(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="google-key-policy-test-") as temporary:
            key = Path(temporary) / "dummy.key"
            key.write_text("unit-only-inert-key\n")
            key.chmod(0o600)
            self.assertEqual(google.credential(key), "unit-only-inert-key")
            key.chmod(0o664)
            with self.assertRaises(PermissionError):
                google.credential(key)

    def test_dummy_credential_symlink_rejected(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="google-key-policy-test-") as temporary:
            key, link = Path(temporary) / "dummy.key", Path(temporary) / "link.key"
            key.write_text("unit-only-inert-key")
            key.chmod(0o600)
            link.symlink_to(key)
            with self.assertRaises(OSError):
                google.credential(link)

    def test_google_approval_cannot_reuse_shopaikey_or_allow_six(self):
        good = {"authorized": True, "scope": google.SCOPE, "model": google.MODEL, "provider": google.BASE,
                "max_requests": 5, "allow_unpriced_for_this_smoke_only": True, "retries_authorized": False,
                "approved_by": "unit-test-not-real", "approved_at_utc": "test", "input_sha256": {"test": "hash"}}
        with patch.object(google, "inputs", return_value={"test": "hash"}):
            google.validate(good)
            for name, value in [("authorized", False), ("provider", "https://api.shopaikey.com/v1"),
                                ("max_requests", 6), ("retries_authorized", True), ("scope", "benchmark48"),
                                ("allow_unpriced_for_this_smoke_only", False)]:
                with self.subTest(name=name), self.assertRaises(PermissionError):
                    google.validate({**good, name: value})
            with self.assertRaises(ValueError):
                google.validate({**good, "input_sha256": {}})

    def test_prepare_plan_never_reads_key_or_creates_opener(self):
        with tempfile.TemporaryDirectory(dir=str(google.ROOT / "demos/artifacts"), prefix="google-prep-test-") as temporary:
            target = Path(temporary) / "fresh"
            with patch("sys.argv", ["google", "--prepare-plan", "--artifact-dir", str(target)]), \
                    patch.object(google, "credential") as key, patch.object(google.urllib.request, "build_opener") as network:
                google.main()
            key.assert_not_called()
            network.assert_not_called()
            self.assertFalse(json.loads((target / "approval-template.json").read_text())["authorized"])

    def test_disabled_run_never_reads_key_or_calls_network(self):
        with tempfile.TemporaryDirectory(dir=str(google.ROOT / "demos/artifacts"), prefix="google-gate-test-") as temporary:
            root = Path(temporary)
            approval = root / "approval.json"
            approval.write_text('{"authorized":false}')
            with patch("sys.argv", ["google", "--run", "--approval", str(approval), "--artifact-dir", str(root / "never")]), \
                    patch.object(google, "credential") as key, patch.object(google.urllib.request, "build_opener") as network:
                with self.assertRaises(PermissionError):
                    google.main()
            key.assert_not_called()
            network.assert_not_called()
            self.assertFalse((root / "never").exists())

    def test_five_calls_virtual_pacing_and_usage_totals(self):
        class Clock:
            value = 0.0
            def clock(self):
                return self.value
            def sleep(self, delay):
                self.value += delay
        class Opener:
            calls = 0
            def open(inner, request, timeout):
                self.assertEqual(request.full_url, google.URL)
                inner.calls += 1
                return Response()
        clock, opener = Clock(), Opener()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="google-flow-test-") as temporary:
            result = google.run(Path(temporary), "unit-only-inert-key", opener, clock=clock.clock, sleep=clock.sleep)
        self.assertEqual((opener.calls, result["passes"], result["not_run"]), (5, 5, 0))
        self.assertEqual([r["started_monotonic"] for r in result["requests"]], [0, 30, 60, 90, 120])
        self.assertEqual(result["token_totals"], {"prompt_tokens": 60, "completion_tokens": 40})
        self.assertIsNone(result["estimated_cost_usd"])

    def test_timeout_stops_and_never_falls_back(self):
        class Opener:
            calls = 0
            def open(inner, request, timeout):
                self.assertEqual(request.full_url, google.URL)
                inner.calls += 1
                raise TimeoutError("unit only")
        opener = Opener()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="google-flow-test-") as temporary:
            result = google.run(Path(temporary), "unit-only-inert-key", opener)
        self.assertEqual((opener.calls, result["passes"], result["not_run"]), (1, 0, 4))
        self.assertEqual(result["token_totals"], {"prompt_tokens": None, "completion_tokens": None})


if __name__ == "__main__":
    unittest.main()
