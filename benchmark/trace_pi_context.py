"""Replay offline Pi qua broker thật/mock upstream; chỉ hash opaque context của pilot nhân tạo."""
import hashlib
import io
import json
import pathlib
import threading
import time
from unittest.mock import patch

from pilot import ROOT, RUNTIME, prepare, execute, Broker, handler, write, now, sha256


def hashed(value):
    return hashlib.sha256(value.encode()).hexdigest()


def item_summary(item):
    blob = item.get("encrypted_content")
    return {"id": item.get("id"), "keys": sorted(item), "encrypted_length": len(blob) if blob else 0,
            "encrypted_sha256": hashed(blob) if blob else None}


def main():
    raise SystemExit("Trace dataset was withdrawn at the user's request; no trace/provider execution. Prepare a new sol dataset before using this historical helper.")
    source = ROOT / "benchmark/artifacts/PILOT-20261106-01"
    artifact = ROOT / "benchmark/artifacts/PI-CONTEXT-TRACE-20261106-01"
    artifact.mkdir(exist_ok=False)
    original = json.loads((source / "result.json").read_text())
    run = original["runs"][0]
    assert run["tool"] == "pi" and run["spec"]["config_id"] == "C-0023"
    oldroot = pathlib.Path(run["spec"]["runtime_root"])
    session = next((oldroot / "sessions").glob("*.jsonl"))
    session_before = sha256(session)
    stdout_path = source / "R-0001/stdout.jsonl"
    events = [json.loads(line) for line in stdout_path.read_text().splitlines()]
    messages = [e["message"] for e in events if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant" and e["message"].get("stopReason") == "toolUse"]
    assert len(messages) == 2
    saved = [r["message"] for r in map(json.loads, session.read_text().splitlines()) if r.get("type") == "message" and r.get("message", {}).get("role") == "assistant" and r["message"].get("stopReason") == "toolUse"]
    source_reasoning = [json.loads(c["thinkingSignature"]) for m in messages for c in m["content"] if c.get("type") == "thinking"]
    persisted_reasoning = [json.loads(c["thinkingSignature"]) for m in saved for c in m["content"] if c.get("type") == "thinking"]
    assert len(source_reasoning) == 2 and source_reasoning == persisted_reasoning
    shells = {
        "pwd && rg --files -g '!*__pycache__*' -g '*.py' -g 'pyproject.toml' -g 'pytest.ini' -g 'tox.ini' -g 'setup.cfg'",
        "git status --short",
        "find . -maxdepth 3 -type f -not -path '*/__pycache__/*' -print | sort",
        "find . -maxdepth 3 -type f \\( -name 'test*.py' -o -name '*_test.py' -o -name 'pyproject.toml' -o -name 'pytest.ini' -o -name 'tox.ini' -o -name 'setup.cfg' \\) -print | sort",
    }
    outputs = []
    for message in messages:
        items = []
        for block in message["content"]:
            if block["type"] == "thinking":
                items.append(json.loads(block["thinkingSignature"]))
            elif block["type"] == "text":
                signature = json.loads(block["textSignature"])
                items.append({"type": "message", "id": signature["id"], "role": "assistant", "phase": signature.get("phase"), "status": "completed",
                    "content": [{"type": "output_text", "text": block["text"], "annotations": []}]})
            elif block["type"] == "toolCall":
                args = block["arguments"]
                if block["name"] == "read":
                    assert args["path"] == str(oldroot / "project/intervals.py")
                else:
                    assert block["name"] == "bash" and args["command"] in shells and args.get("timeout") == 10
                call_id, item_id = block["id"].split("|")
                items.append({"type": "function_call", "id": item_id, "call_id": call_id, "name": block["name"], "arguments": json.dumps(args), "status": "completed"})
            else:
                raise ValueError("Unexpected recorded block")
        outputs.append(items)
    spec, root, nonce, command, cli = prepare(run["spec"], "C-0035", "P-01")
    # Mount the frozen synthetic pilot snapshot, not live user data, at the original read argument's path.
    insertion = command.index("--chdir")
    command[insertion:insertion] = ["--ro-bind", str(source / "R-0001/grader/snapshot"), str(oldroot / "project")]
    captures = []
    ledger = []
    checks = []
    class MockOpener:
        def open(self, request, timeout):
            body = json.loads(request.data)
            index = len(captures)
            assert index < 3
            reasoning = [i for i in body.get("input", []) if i.get("type") == "reasoning"]
            expected = source_reasoning[:index]
            calls = {i["call_id"] for i in body.get("input", []) if i.get("type") == "function_call"}
            results = {i["call_id"] for i in body.get("input", []) if i.get("type") == "function_call_output"}
            captures.append({"request_index": index + 1, "model": body.get("model"), "reasoning_items": [item_summary(i) for i in reasoning],
                "reasoning_whole_json_matches_original": reasoning == expected, "call_result_ids_match": calls == results,
                "input_types": [i.get("type") for i in body.get("input", [])],
                "broker_body_semantically_unchanged": hashed(json.dumps(body, sort_keys=True)) == ledger[index]["original_body_sha256"]})
            if index < 2:
                response = {"id": messages[index]["responseId"], "status": "completed", "model": body["model"], "output": outputs[index],
                            "usage": {"input_tokens": 1, "output_tokens": 1, "input_tokens_details": {"cached_tokens": 0}}}
                frames = [{"type": "response.created", "response": {"id": response["id"], "status": "in_progress"}}]
                for output_index, item in enumerate(outputs[index]):
                    frames.extend([{"type": "response.output_item.added", "output_index": output_index, "item": item},
                                   {"type": "response.output_item.done", "output_index": output_index, "item": item}])
                frames.append({"type": "response.completed", "response": response})
                data = b"".join(b"data: " + json.dumps(frame).encode() + b"\n\n" for frame in frames)
                result = io.BytesIO(data)
                result.code = 200
                result.headers = {"Content-Type": "text/event-stream"}
            else:
                result = io.BytesIO(b'{"error":{"message":"Intentional offline replay stop, not a provider error"}}')
                result.code = 418
                result.headers = {"Content-Type": "application/json"}
            return result

    pricing = json.loads((ROOT / "research/provider-pricing.json").read_text())
    server = Broker(str(root / "broker.sock"), handler("offline-trace-inert-key", nonce, ledger, threading.Lock(), pricing, time.monotonic() + 60,
        request_limit=3, output_limit=2048, serialize_requests=True))
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        with patch("model_smoke.urllib.request.build_opener", return_value=MockOpener()):
            execution = execute(command, root, 60)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        (root / "broker.sock").unlink(missing_ok=True)
    checks = {"two_reasoning_items_stdout_equal_session": source_reasoning == persisted_reasoning,
              "captured_three_mock_requests": len(captures) == 3,
              "original_session_unchanged": sha256(session) == session_before,
              "reasoning_replayed_without_changes": len(captures) == 3 and all(c["reasoning_whole_json_matches_original"] for c in captures),
              "tool_pairing_ok": all(c["call_result_ids_match"] for c in captures),
              "broker_kept_body_unchanged": all(c["broker_body_semantically_unchanged"] for c in captures)}
    summary = {"scope": "Offline replay of synthetic pilot assistant snapshots through pinned Pi/bridge/broker/mock opener; no provider calls or key read",
        "finished_at_utc": now(), "source_run": "R-0001", "source_result_sha256": sha256(source / "result.json"),
        "source_stdout_sha256": sha256(stdout_path), "source_session_sha256": session_before,
        "script_sha256": sha256(pathlib.Path(__file__)), "config_id": "C-0035", "binary_sha256": spec["binary_sha256"],
        "source_reasoning": [item_summary(i) for i in source_reasoning], "requests": captures, "checks": checks,
        "status": "pass" if all(checks.values()) else "failure", "exit_code": execution["exit_code"],
        "witness": execution["witness"], "provider_calls": 0,
        "limitations": ["SSE reconstructed from snapshots, not the original raw provider stream", "New cwd/session and tool outputs differ from original request context",
                        "Opaque ciphertext validity, gateway routing, account/key affinity cannot be verified offline", "HTTP 418 and usage 1/1 are intentional mock data, not model measurements"]}
    write(artifact / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
