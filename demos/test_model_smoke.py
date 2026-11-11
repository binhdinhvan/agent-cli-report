"""Kiểm tra guard/acceptance offline; không đọc credential hoặc gọi Internet."""
import http.client
import http.server
import io
import json
import pathlib
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
from model_smoke import Broker, MARKER, MODEL, ROOT, acceptance, handler
from model_smoke_inside import Bridge
from proxy_headers import REQUEST_HEADERS, protocol_headers
from email.message import Message

# Artificial unit-test rates, never a provider tariff or a benchmark cost measurement.
TEST_PRICING = {"unit_tokens": 1000000, "input_uncached": "1", "input_cache_read": "0.1", "output": "1"}
import socket


class UnixHTTP(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(3)
        self.sock.connect(self.host)


class SmokeTests(unittest.TestCase):
    def test_header_allowlist(self):
        headers = Message()
        for name, value in {"X-OpenAI-Internal-Codex-Responses-Lite": "true", "Authorization": "must-not-forward",
                            "Cookie": "must-not-forward", "Connection": "session-id", "session-id": "hop-by-hop"}.items():
            headers[name] = value
        self.assertEqual(protocol_headers(headers, REQUEST_HEADERS), {"x-openai-internal-codex-responses-lite": "true"})

    def test_headers_through_bridge_and_broker(self):
        pricing = TEST_PRICING
        for status in [200, 404]:
            with self.subTest(status=status), tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="smoke-header-") as directory:
                path = str(pathlib.Path(directory) / "broker.sock")
                ledger = []
                broker = Broker(path, handler("inert-unit-test-key", "unit-test-nonce", ledger, threading.Lock(), pricing, time.monotonic() + 60))
                bridge = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Bridge)
                threads = [threading.Thread(target=s.serve_forever) for s in [broker, bridge]]
                for thread in threads:
                    thread.start()
                try:
                    with patch("model_smoke_inside.UnixHTTP", side_effect=lambda _: UnixHTTP(path)), patch("model_smoke.urllib.request.build_opener") as build:
                        if status == 200:
                            body = b'data: ' + json.dumps({"type": "response.completed", "response": {"model": MODEL}}).encode() + b'\n\n'
                        else:
                            body = b'{"error":{"message":"inert-unit-test-key simulated error"}}'
                        stream = io.BytesIO(body)
                        stream.code = status
                        stream.headers = Message()
                        for name, value in {"Content-Type": "text/event-stream" if status == 200 else "application/json",
                                            "x-codex-turn-state": "inert-sticky-token", "x-request-id": "inert-request-id",
                                            "Set-Cookie": "must-not-forward", "Authorization": "must-not-forward"}.items():
                            stream.headers[name] = value
                        build.return_value.open.return_value = stream
                        connection = http.client.HTTPConnection(*bridge.server_address, timeout=5)
                        connection.request("POST", "/v1/responses", json.dumps({"model": MODEL, "stream": True}),
                            {"Authorization": "Bearer unit-test-nonce", "X-OpenAI-Internal-Codex-Responses-Lite": "true",
                             "x-codex-turn-state": "inert-sticky-token", "session-id": "inert-session", "Cookie": "must-not-forward"})
                        response = connection.getresponse()
                        captured = response.read()
                        self.assertEqual(response.status, status)
                        self.assertEqual(response.getheader("x-codex-turn-state"), "inert-sticky-token")
                        self.assertEqual(response.getheader("x-request-id"), "inert-request-id")
                        self.assertIsNone(response.getheader("Set-Cookie"))
                        self.assertIsNone(response.getheader("Authorization"))
                        self.assertNotIn(b"inert-unit-test-key", captured)
                        connection.close()
                        request = build.return_value.open.call_args.args[0]
                        sent_headers = {k.lower(): v for k, v in request.header_items()}
                        self.assertEqual(sent_headers["x-openai-internal-codex-responses-lite"], "true")
                        self.assertEqual(sent_headers["x-codex-turn-state"], "inert-sticky-token")
                        self.assertEqual(sent_headers["session-id"], "inert-session")
                        self.assertEqual(sent_headers["authorization"], "Bearer inert-unit-test-key")
                        self.assertNotIn("cookie", sent_headers)
                        self.assertEqual(ledger[0]["responses_lite"], "true")
                        if status == 404:
                            self.assertNotIn("inert-unit-test-key", ledger[0]["error_body_excerpt"])
                finally:
                    for server in [bridge, broker]:
                        server.shutdown()
                        server.server_close()
                    for thread in threads:
                        thread.join()

    def test_read_and_final_shapes(self):
        cases = {
            "opencode-v1": [{"type": "tool_use", "part": {"tool": "read", "state": {"status": "completed", "output": MARKER}}}, {"type": "text", "part": {"text": MARKER}}],
            "opencode-v2": [{"type": "tool_use", "part": {"tool": "read", "state": {"status": "completed", "output": MARKER}}}, {"type": "text", "part": {"text": MARKER}}],
            "pi": [{"type": "tool_execution_end", "isError": False, "result": {"content": [{"type": "text", "text": MARKER}]}}, {"type": "message_end", "message": {"role": "assistant", "content": [{"type": "text", "text": MARKER}]}}],
            "codex": [{"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0, "aggregated_output": MARKER}}, {"type": "item.completed", "item": {"type": "agent_message", "text": MARKER}}],
        }
        for tool, events in cases.items():
            checks = acceptance(tool, "\n".join(json.dumps(e) for e in events))
            self.assertTrue(checks["successful_local_read_observed"], tool)
            self.assertTrue(checks["final_exact_marker"], tool)

    def test_final_without_read_fails(self):
        output = json.dumps({"type": "text", "part": {"text": MARKER}})
        checks = acceptance("opencode-v1", output)
        self.assertTrue(checks["final_exact_marker"])
        self.assertFalse(checks["successful_local_read_observed"])

    def test_opencode_progress_and_multiple_final_parts(self):
        for tool in ["opencode-v1", "opencode-v2"]:
            events = [{"type": "text", "part": {"messageID": "progress", "text": "Reading file"}},
                      {"type": "text", "part": {"messageID": "final", "text": MARKER[:10]}},
                      {"type": "text", "part": {"messageID": "final", "text": MARKER[10:]}}]
            self.assertTrue(acceptance(tool, "\n".join(json.dumps(e) for e in events))["final_exact_marker"])
            events.append({"type": "error", "error": {"message": "simulated"}})
            self.assertTrue(acceptance(tool, "\n".join(json.dumps(e) for e in events))["cli_error_event_observed"])

    def test_codex_progress_is_not_final(self):
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": "Reading file now"}},
                  {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0, "aggregated_output": MARKER}},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": MARKER}},
                  {"type": "turn.completed"}]
        checks = acceptance("codex", "\n".join(json.dumps(e) for e in events))
        self.assertTrue(checks["successful_local_read_observed"])
        self.assertTrue(checks["final_exact_marker"])
        events[-2]["item"]["text"] = "incorrect final"
        events[0]["item"]["text"] = MARKER
        self.assertFalse(acceptance("codex", "\n".join(json.dumps(e) for e in events))["final_exact_marker"])

    def test_broker_guards_and_clamp(self):
        ledger = []
        pricing = TEST_PRICING
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="smoke-guard-") as directory:
            path = str(pathlib.Path(directory) / "broker.sock")
            server = Broker(path, handler("inert-unit-test-key", "unit-test-nonce", ledger, threading.Lock(), pricing, time.monotonic() + 60))
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            def call(body, token="unit-test-nonce", endpoint="/v1/responses"):
                connection = UnixHTTP(path)
                connection.request("POST", endpoint, json.dumps(body), {"Authorization": "Bearer " + token})
                response = connection.getresponse()
                result = response.status, response.read()
                connection.close()
                return result
            try:
                with patch("model_smoke.urllib.request.build_opener") as build:
                    payload = {"model": MODEL, "stream": True, "max_output_tokens": 9999}
                    self.assertEqual(call(payload, token="wrong")[0], 403)
                    self.assertEqual(call(payload, endpoint="/v1/chat/completions")[0], 403)
                    self.assertEqual(call({**payload, "model": "wrong"})[0], 400)
                    self.assertEqual(call({**payload, "stream": False})[0], 400)
                    build.assert_not_called()
                    event = {"type": "response.completed", "response": {"model": MODEL, "usage": {"input_tokens": 3, "output_tokens": 1, "input_tokens_details": {"cached_tokens": 0}}}}
                    stream = io.BytesIO(b"data: " + json.dumps(event).encode() + b"\n\n")
                    stream.code = 200
                    stream.headers = {"Content-Type": "text/event-stream"}
                    build.return_value.open.return_value = stream
                    self.assertEqual(call(payload)[0], 200)
                    request = build.return_value.open.call_args.args[0]
                    sent = json.loads(request.data)
                    self.assertEqual(sent["max_output_tokens"], 512)
                    self.assertFalse(sent["store"])
                    self.assertEqual(request.get_header("Authorization"), "Bearer inert-unit-test-key")
                    self.assertEqual(ledger[0]["terminal_type"], "response.completed")
                    ledger.extend([{}, {}, {}])
                    self.assertEqual(call(payload)[0], 400)
                    self.assertEqual(build.return_value.open.call_count, 1)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()
