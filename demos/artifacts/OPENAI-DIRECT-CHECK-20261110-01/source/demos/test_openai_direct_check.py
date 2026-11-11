"""Offline scope/redaction/parser tests; dummy keys only, never user's key/network."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import openai_direct_check as check


class Response(io.BytesIO):
    code = 200
    def __init__(self, body, content_type="application/json"):
        super().__init__(body)
        self.headers = {"content-type": content_type, "x-request-id": "unit-request-id"}


def stream():
    events = [{"type": "response.output_text.delta", "delta": check.MARKER},
        {"type": "response.completed", "response": {"status": "completed", "model": check.MODEL,
         "usage": {"input_tokens": 20, "output_tokens": 30, "input_tokens_details": {"cached_tokens": 0},
                   "output_tokens_details": {"reasoning_tokens": 10}}}}]
    return b"".join(("data: " + json.dumps(e) + "\n\n").encode() for e in events)


class Clock:
    value = 0.0
    def clock(self):
        return self.value
    def sleep(self, delay):
        self.value += delay


class OpenAICheckTests(unittest.TestCase):
    def test_fixed_payload_uses_documented_low_and_cap(self):
        self.assertEqual(check.BASE, "https://api.openai.com/v1")
        p = check.payload()
        self.assertEqual((p["model"], p["max_output_tokens"]), ("gpt-6.1-sol", 1024))
        self.assertEqual(p["reasoning"], {"effort": "low"})
        self.assertEqual(p["service_tier"], "default")
        self.assertNotIn("tools", p)

    def test_redaction_masks_full_and_partial_error_key(self):
        text = check.redact({"error": "Incorrect key: sk-proj-unit****suffix", "other": "unit-full-secret"}, "unit-full-secret")
        self.assertNotIn("unit-full-secret", text)
        self.assertNotIn("sk-proj-unit", text)
        self.assertNotIn("suffix", text)

    def test_private_dummy_credential_and_bad_permissions(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="openai-key-unit-") as temporary:
            key = Path(temporary) / "dummy.key"
            key.write_text("unit-only-inert-key\n")
            key.chmod(0o600)
            self.assertEqual(check.credential(key), "unit-only-inert-key")
            key.chmod(0o664)
            with self.assertRaises(PermissionError):
                check.credential(key)

    def test_dummy_symlink_rejected(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="openai-key-unit-") as temporary:
            key, link = Path(temporary) / "dummy.key", Path(temporary) / "link.key"
            key.write_text("unit-only-inert-key")
            key.chmod(0o600)
            link.symlink_to(key)
            with self.assertRaises(OSError):
                check.credential(link)

    def test_scoped_approval_no_provider_or_request_escalation(self):
        good = {"authorized": True, "scope": check.SCOPE, "provider": check.BASE, "model": check.MODEL,
                "max_generation_requests": 1, "max_catalog_requests": 1, "retries_authorized": False,
                "approved_by": "unit-test-not-real", "approved_at_utc": "test", "input_sha256": {"test": "hash"}}
        with patch.object(check, "inputs", return_value={"test": "hash"}):
            check.validate(good)
            for name, value in [("authorized", False), ("provider", "https://api.shopaikey.com/v1"),
                                ("max_generation_requests", 2), ("max_catalog_requests", 2), ("retries_authorized", True)]:
                with self.subTest(name=name), self.assertRaises(PermissionError):
                    check.validate({**good, name: value})
            with self.assertRaises(ValueError):
                check.validate({**good, "input_sha256": {}})

    def test_disabled_approval_precedes_key_and_artifact(self):
        with tempfile.TemporaryDirectory(dir=str(check.ROOT / "demos/artifacts"), prefix="openai-gate-unit-") as temporary:
            root = Path(temporary)
            (root / "approval.json").write_text('{"authorized":false}')
            argv = ["openai", "--approval", str(root / "approval.json"), "--artifact-dir", str(root / "never")]
            with patch("sys.argv", argv), patch.object(check, "credential") as key, self.assertRaises(PermissionError):
                check.main()
            key.assert_not_called()
            self.assertFalse((root / "never").exists())

    def test_catalog_then_single_generation_no_catalog_private_data(self):
        class Opener:
            urls = []
            def open(inner, request, timeout):
                inner.urls.append(request.full_url)
                if request.full_url.endswith("/models"):
                    return Response(json.dumps({"data": [{"id": check.MODEL}, {"id": "ft:private-model"}]}).encode())
                return Response(stream(), "text/event-stream")
        opener, clock = Opener(), Clock()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="openai-flow-unit-") as temporary:
            result = check.run(Path(temporary), "unit-only-inert-key", opener, clock=clock.clock, sleep=clock.sleep)
            saved = (Path(temporary) / "result.json").read_text()
        self.assertEqual(opener.urls, [check.BASE + "/models", check.BASE + "/responses"])
        self.assertEqual((result["provider_http_requests"], result["generation_requests"], result["status"]), (2, 1, "pass"))
        self.assertNotIn("ft:private-model", saved)
        self.assertEqual(result["requests"][1]["started_monotonic"], 30)
        self.assertEqual(result["requests"][1]["usage"]["output_tokens_details"]["reasoning_tokens"], 10)
        self.assertIsNone(result["estimated_cost_usd"])

    def test_missing_model_stops_without_generation_or_fallback(self):
        class Opener:
            calls = 0
            def open(inner, request, timeout):
                inner.calls += 1
                return Response(b'{"data":[{"id":"other-model"}]}')
        opener = Opener()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="openai-flow-unit-") as temporary:
            result = check.run(Path(temporary), "unit-only-inert-key", opener)
        self.assertEqual((opener.calls, result["generation_requests"], result["status"]), (1, 0, "stopped"))

    def test_timeout_stops_without_retry(self):
        class Opener:
            calls = 0
            def open(inner, request, timeout):
                inner.calls += 1
                raise TimeoutError("unit timeout")
        opener = Opener()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="openai-flow-unit-") as temporary:
            result = check.run(Path(temporary), "unit-only-inert-key", opener)
        self.assertEqual((opener.calls, result["generation_requests"]), (1, 0))
        self.assertEqual(result["requests"][0]["error_type"], "TimeoutError")


if __name__ == "__main__":
    unittest.main()
