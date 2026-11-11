"""Một request Responses SSE với input cố định; không retry, không chạy agent/tool."""

import argparse
import datetime
import hashlib
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.dont_write_bytecode = True
from provider_probe import BASE_URL, MODEL, NoRedirect, credential
from estimate_provider_cost import require_pricing


ROOT = pathlib.Path(__file__).resolve().parents[1]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    require_pricing(MODEL, BASE_URL)
    artifact.mkdir(parents=True, exist_ok=False)
    key = credential()
    marker = "REPORT_STREAM_OK"
    payload = {"model": MODEL, "store": False, "stream": True, "max_output_tokens": 128,
               "input": [{"role": "user", "content": "Return exactly REPORT_STREAM_OK without explanation."}]}
    result = {"started_at_utc": now(), "base_url": BASE_URL, "model": MODEL, "payload": payload,
              "scope": "Single provider SSE request with constant input; no agent or filesystem tool",
              "script_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__), ROOT / "demos/provider_probe.py"]},
              "events": [], "cost_usd": None}
    clock = time.monotonic()
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        request = urllib.request.Request(BASE_URL + "/responses", data=json.dumps(payload).encode(), method="POST",
                                         headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                                  "Accept": "text/event-stream", "User-Agent": "agent-cli-report-provider-probe"})
        try:
            response = opener.open(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            result["http_status"] = response.code
            result["content_type"] = response.headers.get("content-type")
            if response.code != 200:
                result["error_body"] = response.read(4096).decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {response.code}; no retry")
            if "text/event-stream" not in response.headers.get("content-type", ""):
                raise ValueError("Expected SSE content type")
            frames = []
            captured = 0
            for line in response:
                captured += len(line)
                if captured > 4 * 1024 * 1024 or time.monotonic() - clock > 90:
                    raise TimeoutError("SSE capture limit reached")
                value = line.decode("utf-8").rstrip("\r\n")
                if value.startswith("data:"):
                    frames.append(value[5:].lstrip(" "))
                elif not value and frames:
                    data = "\n".join(frames)
                    frames = []
                    if data == "[DONE]":
                        break
                    event = json.loads(data)
                    result["events"].append({"observed_at_utc": now(), "event": event})
                    if event.get("type") in {"response.completed", "response.failed", "response.incomplete"}:
                        result["terminal_response"] = event.get("response")
                        break
        events = [item["event"] for item in result["events"]]
        text = "".join(event.get("delta", "") for event in events if event.get("type") == "response.output_text.delta")
        terminal = result.get("terminal_response", {})
        result["checks"] = {"received_text_delta": bool(text), "marker_matches": text.strip() == marker,
                            "response_completed": terminal.get("status") == "completed"}
        result["status"] = "responses_stream_pass" if all(result["checks"].values()) else "responses_stream_failure"
    except Exception as error:
        result.update({"status": "probe_error", "error_type": type(error).__name__, "error": str(error)})
    result["finished_at_utc"] = now()
    result["duration_ms"] = round((time.monotonic() - clock) * 1000)
    encoded = json.dumps(result, ensure_ascii=False, indent=2).replace(key, "[REDACTED]")
    (artifact / "result.json").write_text(encoded + "\n")
    print(json.dumps({"status": result["status"], "event_count": len(result["events"]),
                      "artifact": str(artifact.relative_to(ROOT) / "result.json")}, indent=2))
    if result["status"] != "responses_stream_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
