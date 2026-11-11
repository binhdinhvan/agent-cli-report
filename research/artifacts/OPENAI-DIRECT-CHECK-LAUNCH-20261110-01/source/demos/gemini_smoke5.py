"""At most5 fixed provider-only Gemini SSE requests; explicit scoped unpriced approval."""
import argparse
import hashlib
import json
import pathlib
import signal
import time
import urllib.error
import urllib.request

from provider_probe import credential, NoRedirect, now

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = "gemini-3.8-flash"
BASE = "https://api.shopaikey.com/v1"
SCOPE = "gemini-provider-only-five-requests-unpriced-explicit-no-retry"
PROFILE = ROOT / "research/model-profiles/gemini-3.8-flash.json"
MARKER = "REPORT_GEMINI_SMOKE_OK"
LIMIT = 4 * 1024 * 1024


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    return {str(p.relative_to(ROOT)): sha(p) for p in [pathlib.Path(__file__), ROOT / "demos/test_gemini_smoke5.py",
        ROOT / "demos/GEMINI_SMOKE5.md", ROOT / "demos/provider_probe.py", PROFILE]}


def validate(approval):
    if (approval.get("authorized") is not True or approval.get("scope") != SCOPE or approval.get("model") != MODEL
            or approval.get("provider") != BASE or approval.get("max_requests") != 5
            or approval.get("allow_unpriced_for_this_smoke_only") is not True
            or not approval.get("approved_by") or not approval.get("approved_at_utc")):
        raise PermissionError("Explicit five-request unpriced smoke approval required; no credential read")
    if approval.get("input_sha256") != inputs():
        raise ValueError("Smoke source/profile drift")


def payload():
    return {"model": MODEL, "store": False, "stream": True, "max_output_tokens": 256,
        "input": [{"role": "user", "content": "Return exactly " + MARKER + " without explanation."}]}


def parse(response, captured_state=None):
    events, frame, captured, terminal = [], [], 0, None
    captured_state = {} if captured_state is None else captured_state
    captured_state["events"] = events  # Retain partial stream if iterator raises/timeout.
    for line in response:
        captured += len(line)
        captured_state["captured_response_bytes"] = captured
        if captured > LIMIT:
            raise ValueError("SSE capture exceeds fixed limit")
        text = line.decode("utf-8").rstrip("\r\n")
        if text.startswith("data:"):
            frame.append(text[5:].lstrip(" "))
            captured_state["partial_sse_frame"] = list(frame)
        elif not text and frame:
            data, frame = "\n".join(frame), []
            captured_state["partial_sse_frame"] = []
            if data == "[DONE]":
                break
            event = json.loads(data)
            events.append({"observed_at_utc": now(), "event": event})
            if event.get("type") in ("response.completed", "response.failed", "response.incomplete"):
                terminal = event
                break
    text = "".join(r["event"].get("delta", "") for r in events if r["event"].get("type") == "response.output_text.delta")
    output = (terminal or {}).get("response", {})
    if not text:
        text = "".join(part.get("text", "") for item in output.get("output", []) if item.get("type") == "message"
                       for part in item.get("content", []) if part.get("type") == "output_text")
    usage = output.get("usage")
    valid_usage = isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens"))
    checks = {"response_completed": (terminal or {}).get("type") == "response.completed" and output.get("status") == "completed",
              "marker_matches": text.strip() == MARKER, "usage_input_output_present": valid_usage}
    return {"events": events, "captured_response_bytes": captured, "terminal_type": (terminal or {}).get("type"),
            "response_model": output.get("model"), "usage": usage, "text": text, "checks": checks,
            "pass": all(checks.values())}


def run(artifact, key, opener, *, clock=time.monotonic, sleep=time.sleep):
    result = {"scope": SCOPE, "model": MODEL, "provider": BASE, "protocol": "responses-sse",
        "started_at_utc": now(), "planned_requests": 5, "max_output_tokens": 256,
        "native_cli_execution": False, "estimated_cost_usd": None, "measured_charge_usd": None,
        "cost_status": "explicit user-approved unpriced smoke; rates pending, no sol rates used",
        "requests": [], "plan": [{"request_index": n, "status": "not_run"} for n in range(1, 6)]}

    def save():
        text = json.dumps(result, ensure_ascii=False, indent=2).replace(key, "[REDACTED]")
        (artifact / "result.json").write_text(text + "\n")

    last_end = None
    for index in range(1, 6):
        if last_end is not None:
            wait = max(0.0, 30 - (clock() - last_end))
            if wait:
                sleep(wait)
            if clock() - last_end < 30:
                raise ValueError("Pacing clock failed before request")
        item = {"request_index": index, "started_at_utc": now(), "started_monotonic": clock(),
            "payload": payload(), "estimated_cost_usd": None, "usage": None}
        result["requests"].append(item)
        save()  # intent preserved even if request fails

        def deadline(_signum, _frame):
            raise TimeoutError("Fixed90s smoke request wall cap")

        old_handler = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, 90)
        try:
            request = urllib.request.Request(BASE + "/responses", data=json.dumps(item["payload"]).encode(), method="POST",
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                         "Accept": "text/event-stream", "User-Agent": "agent-cli-report-gemini-smoke5"})
            try:
                response = opener.open(request, timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                item.update(http_status=response.code, content_type=response.headers.get("content-type", ""))
                if response.code != 200:
                    item["error_body"] = response.read(4096).decode("utf-8", errors="replace")
                    raise RuntimeError("HTTP error; no retry or fallback")
                if "text/event-stream" not in item["content_type"]:
                    raise ValueError("Expected SSE response; no fallback")
                item.update(parse(response, item))
            item["status"] = "pass" if item["pass"] else "protocol_or_marker_or_usage_failure"
        except Exception as error:
            item.update(status="error", error_type=type(error).__name__, error=str(error).replace(key, "[REDACTED]"))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
            item.update(finished_at_utc=now(), finished_monotonic=clock())
            item["duration_ms"] = round((item["finished_monotonic"] - item["started_monotonic"]) * 1000)
            last_end = item["finished_monotonic"]
        result["plan"][index - 1]["status"] = item["status"]
        save()
        print(json.dumps({k: item.get(k) for k in ("request_index", "status", "http_status", "duration_ms", "error_type")}), flush=True)
        if item["status"] != "pass":
            result["stop_reason"] = "first_failure_no_retry"
            break
    result.update(finished_at_utc=now(), upstream_requests=len(result["requests"]),
        passes=sum(r["status"] == "pass" for r in result["requests"]),
        not_run=5 - len(result["requests"]), status="pass" if len(result["requests"]) == 5 and all(r["status"] == "pass" for r in result["requests"]) else "stopped")
    result["unpriced_requests"] = len(result["requests"])
    result["usage_reported_requests"] = sum(isinstance(r.get("usage"), dict) for r in result["requests"])
    result["token_totals"] = {name: sum(r["usage"][name] for r in result["requests"])
        if all(isinstance(r.get("usage"), dict) and type(r["usage"].get(name)) is int for r in result["requests"]) else None
        for name in ("input_tokens", "output_tokens")}
    save()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", type=pathlib.Path, required=True)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    approval = json.loads(args.approval.read_text())
    validate(approval)
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Fresh demos artifact directory required")
    artifact.mkdir(parents=True, exist_ok=False)
    for name, expected in approval["input_sha256"].items():
        source = ROOT / name
        assert sha(source) == expected
        dest = artifact / "source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
    (artifact / "approval.json").write_text(json.dumps(approval, ensure_ascii=False, indent=2) + "\n")
    key = credential()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    result = run(artifact, key, opener)
    print(json.dumps({"status": result["status"], "passes": result["passes"], "upstream_requests": result["upstream_requests"],
        "not_run": result["not_run"], "estimated_cost_usd": None, "artifact": str(artifact.relative_to(ROOT))}), flush=True)


if __name__ == "__main__":
    main()
