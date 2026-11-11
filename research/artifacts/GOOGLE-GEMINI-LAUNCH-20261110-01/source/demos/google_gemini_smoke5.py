"""Google-direct Chat Completions smoke; preparation default, explicit scoped approval to run."""
import argparse
import hashlib
import json
import os
import pathlib
import signal
import stat
import time
import urllib.error
import urllib.request

from provider_probe import NoRedirect, now

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = "gemini-3.8-flash"
BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"
URL = BASE + "chat/completions"
KEY = ROOT / ".local/credentials/google-ai.key"
PROFILE = ROOT / "research/model-profiles/google-gemini-3.8-flash.json"
SCOPE = "google-direct-chat-sse-five-unpriced-no-retry"
MARKER = "REPORT_GOOGLE_GEMINI_SMOKE_OK"
LIMIT = 4 * 1024 * 1024


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    files = [pathlib.Path(__file__), ROOT / "demos/test_google_gemini_smoke5.py", ROOT / "demos/GOOGLE_GEMINI.md",
             ROOT / "demos/provider_probe.py", PROFILE]
    return {str(p.relative_to(ROOT)): sha(p) for p in files}


def validate(approval):
    if (approval.get("authorized") is not True or approval.get("scope") != SCOPE or approval.get("model") != MODEL
            or approval.get("provider") != BASE or approval.get("max_requests") != 5
            or approval.get("allow_unpriced_for_this_smoke_only") is not True
            or approval.get("retries_authorized") is not False
            or not approval.get("approved_by") or not approval.get("approved_at_utc")):
        raise PermissionError("Separate Google-direct5request approval required before credential/network")
    if approval.get("input_sha256") != inputs():
        raise ValueError("Google-direct source/profile drift")


def credential(path=None):
    fd = os.open(KEY if path is None else path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("Google key must be owner-controlled private regular file; content omitted")
        key = stream.read(16385).strip()
    if not key or len(key) > 16384 or any(c.isspace() for c in key):
        raise ValueError("Invalid Google key file format; content omitted")
    return key


def payload():
    return {"model": MODEL, "stream": True, "stream_options": {"include_usage": True}, "max_tokens": 256,
            "messages": [{"role": "user", "content": "Return exactly " + MARKER + " without explanation."}]}


def parse(response, captured=None):
    captured = {} if captured is None else captured
    events, frame, size, pieces, usage, finish, model, done = [], [], 0, [], None, None, None, False
    captured["events"] = events
    for line in response:
        size += len(line)
        captured["captured_response_bytes"] = size
        if size > LIMIT:
            raise ValueError("Google SSE capture exceeds limit")
        text = line.decode("utf-8").rstrip("\r\n")
        if text.startswith("data:"):
            frame.append(text[5:].lstrip(" "))
            captured["partial_sse_frame"] = list(frame)
        elif not text and frame:
            value, frame = "\n".join(frame), []
            captured["partial_sse_frame"] = []
            if value == "[DONE]":
                done = True
                break
            event = json.loads(value)
            events.append({"observed_at_utc": now(), "event": event})
            if event.get("error"):
                raise ValueError("Google stream error event")
            model = event.get("model", model)
            if event.get("usage") is not None:
                usage = event["usage"]
            for choice in event.get("choices", []):
                if choice.get("index", 0) != 0:
                    continue
                content = choice.get("delta", {}).get("content")
                if content is not None:
                    if not isinstance(content, str):
                        raise ValueError("Expected text content in chat delta")
                    pieces.append(content)
                if choice.get("finish_reason") is not None:
                    finish = choice["finish_reason"]
    text = "".join(pieces)
    valid_usage = isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("prompt_tokens", "completion_tokens"))
    checks = {"marker_matches": text.strip() == MARKER, "finish_reason_stop": finish == "stop", "usage_present": valid_usage}
    return {"events": events, "captured_response_bytes": size, "text": text, "response_model": model,
            "usage": usage, "finish_reason": finish, "done_received": done, "checks": checks, "pass": all(checks.values())}


def run(artifact, key, opener, *, clock=time.monotonic, sleep=time.sleep):
    result = {"scope": SCOPE, "model": MODEL, "provider": BASE, "endpoint": URL, "protocol": "chat-completions-sse",
        "started_at_utc": now(), "planned_requests": 5, "max_tokens": 256, "native_cli_execution": False,
        "estimated_cost_usd": None, "measured_charge_usd": None, "requests": [],
        "plan": [{"request_index": n, "status": "not_run"} for n in range(1, 6)]}

    def save():
        (artifact / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2).replace(key, "[REDACTED]") + "\n")

    last_end = None
    for index in range(1, 6):
        if last_end is not None:
            sleep(max(0.0, 30 - (clock() - last_end)))
            if clock() - last_end < 30:
                raise ValueError("Pacing guard before Google dispatch")
        item = {"request_index": index, "payload": payload(), "started_at_utc": now(), "started_monotonic": clock(),
                "usage": None, "estimated_cost_usd": None}
        result["requests"].append(item)
        save()

        def deadline(_sig, _frame):
            raise TimeoutError("Google smoke90s wall cap")

        previous = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, 90)
        try:
            request = urllib.request.Request(URL, data=json.dumps(item["payload"]).encode(), method="POST",
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "Accept": "text/event-stream",
                         "User-Agent": "agent-cli-report-google-direct-smoke5"})
            try:
                response = opener.open(request, timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                item.update(http_status=response.code, content_type=response.headers.get("content-type", ""))
                if response.code != 200:
                    item["error_body"] = response.read(4096).decode("utf-8", errors="replace")
                    raise RuntimeError("Google HTTP error; no retry/fallback")
                if "text/event-stream" not in item["content_type"]:
                    raise ValueError("Expected Google SSE; no fallback")
                item.update(parse(response, item))
            item["status"] = "pass" if item["pass"] else "protocol_or_marker_or_usage_failure"
        except Exception as error:
            item.update(status="error", error_type=type(error).__name__, error=str(error).replace(key, "[REDACTED]"))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
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
        passes=sum(r["status"] == "pass" for r in result["requests"]), not_run=5 - len(result["requests"]),
        status="pass" if len(result["requests"]) == 5 and all(r["status"] == "pass" for r in result["requests"]) else "stopped",
        unpriced_requests=len(result["requests"]))
    result["token_totals"] = {name: sum(r["usage"][name] for r in result["requests"])
        if all(isinstance(r.get("usage"), dict) and type(r["usage"].get(name)) is int for r in result["requests"]) else None
        for name in ("prompt_tokens", "completion_tokens")}
    save()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--approval", type=pathlib.Path)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Fresh demos artifact directory required")
    if args.prepare_plan:
        artifact.mkdir(parents=True, exist_ok=False)
        plan = {"scope": SCOPE, "model": MODEL, "provider": BASE, "endpoint": URL, "max_requests": 5,
                "input_sha256": inputs(), "generation_authorized": False, "estimated_cost_usd": None}
        (artifact / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
        template = {"authorized": False, "scope": SCOPE, "model": MODEL, "provider": BASE, "max_requests": 5,
                    "input_sha256": inputs(), "retries_authorized": False, "allow_unpriced_for_this_smoke_only": False,
                    "approved_by": None, "approved_at_utc": None}
        (artifact / "approval-template.json").write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n")
        print("Prepared Google-direct plan + disabled approval; no credential/network")
        return
    if not args.approval:
        parser.error("Run requires separate Google-direct approval")
    approval = json.loads(args.approval.read_text())
    validate(approval)
    artifact.mkdir(parents=True, exist_ok=False)
    for name, expected in approval["input_sha256"].items():
        source = ROOT / name
        if sha(source) != expected:
            raise ValueError("Input changed after approval")
        dest = artifact / "source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
    (artifact / "approval.json").write_text(json.dumps(approval, ensure_ascii=False, indent=2) + "\n")
    key = credential()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    result = run(artifact, key, opener)
    print(json.dumps({"status": result["status"], "passes": result["passes"], "requests": result["upstream_requests"],
                      "not_run": result["not_run"], "estimated_cost_usd": None}), flush=True)


if __name__ == "__main__":
    main()
