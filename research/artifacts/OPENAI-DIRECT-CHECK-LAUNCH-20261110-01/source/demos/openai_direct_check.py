"""Bounded OpenAI-direct catalog+one Responses SSE check; never expose credentials."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import signal
import stat
import time
import urllib.error
import urllib.request

from provider_probe import NoRedirect, now
from gemini_smoke5 import parse as parse_responses

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = "https://api.openai.com/v1"
MODEL = "gpt-6.1-sol"
KEY = ROOT / ".local/credentials/openai.key"
MARKER = "REPORT_OPENAI_DIRECT_OK"
SCOPE = "openai-direct-one-catalog-one-responses-no-retry"
PROFILE = ROOT / "research/model-profiles/openai-gpt-6.1-sol.json"
LIMIT = 4 * 1024 * 1024


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    return {str(p.relative_to(ROOT)): sha(p) for p in [pathlib.Path(__file__), ROOT / "demos/test_openai_direct_check.py",
        ROOT / "demos/OPENAI_DIRECT_CHECK.md", ROOT / "demos/provider_probe.py", ROOT / "demos/gemini_smoke5.py", PROFILE]}


def validate(approval):
    if (approval.get("authorized") is not True or approval.get("scope") != SCOPE or approval.get("provider") != BASE
            or approval.get("model") != MODEL or approval.get("max_generation_requests") != 1
            or approval.get("max_catalog_requests") != 1 or approval.get("retries_authorized") is not False
            or not approval.get("approved_by") or not approval.get("approved_at_utc")):
        raise PermissionError("Scoped OpenAI check approval required before credential/network")
    if approval.get("input_sha256") != inputs():
        raise ValueError("OpenAI check source/profile drift")


def credential(path=None):
    fd = os.open(KEY if path is None else path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("OpenAI key must be owner-controlled private regular file; content omitted")
        key = stream.read(16385).strip()
    if not key or len(key) > 16384 or any(c.isspace() for c in key):
        raise ValueError("Invalid OpenAI key file format; content omitted")
    return key


def redact(value, key):
    text = json.dumps(value, ensure_ascii=False, indent=2).replace(key, "[REDACTED]")
    return re.sub(r"\bsk-[A-Za-z0-9_.*-]{4,}", "[REDACTED-KEY]", text)


def payload():
    return {"model": MODEL, "store": False, "stream": True, "max_output_tokens": 1024,
            "reasoning": {"effort": "low"}, "service_tier": "default",
            "input": [{"role": "user", "content": "Return exactly " + MARKER + " without explanation."}]}


def run(artifact, key, opener, *, clock=time.monotonic, sleep=time.sleep):
    result = {"scope": SCOPE, "provider": BASE, "model": MODEL, "started_at_utc": now(),
        "requests": [], "plan": [{"stage": "catalog", "status": "not_run"}, {"stage": "generation", "status": "not_run"}],
        "estimated_cost_usd": None, "measured_charge_usd": None, "native_cli_execution": False,
        "cost_note": "published OpenAI rates recorded separately; raw usage retained; cachewrite/tier invoice not reconciled"}

    def save():
        (artifact / "result.json").write_text(redact(result, key) + "\n")

    last_end = None
    for position, stage in enumerate(("catalog", "generation")):
        if last_end is not None:
            sleep(max(0.0, 30 - (clock() - last_end)))
            if clock() - last_end < 30:
                raise ValueError("Pacing guard before OpenAI request")
        item = {"stage": stage, "started_at_utc": now(), "started_monotonic": clock(), "estimated_cost_usd": None}
        if stage == "generation":
            item.update(payload=payload(), usage=None)
        result["requests"].append(item)
        save()

        def deadline(_sig, _frame):
            raise TimeoutError("OpenAI check90s wall cap")

        previous = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, 90)
        try:
            request = urllib.request.Request(BASE + ("/models" if stage == "catalog" else "/responses"),
                data=None if stage == "catalog" else json.dumps(item["payload"]).encode(),
                method="GET" if stage == "catalog" else "POST", headers={"Authorization": "Bearer " + key,
                    "Content-Type": "application/json", "Accept": "application/json" if stage == "catalog" else "text/event-stream",
                    "User-Agent": "agent-cli-report-openai-direct-check"})
            try:
                response = opener.open(request, timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                item.update(http_status=response.code, content_type=response.headers.get("content-type", ""),
                            provider_request_id=response.headers.get("x-request-id"))
                if response.code != 200:
                    item["error_body"] = response.read(4096).decode("utf-8", errors="replace")
                    raise RuntimeError("OpenAI HTTP error; no retry/fallback")
                if stage == "catalog":
                    raw = response.read(LIMIT + 1)
                    if len(raw) > LIMIT:
                        raise ValueError("Catalog capture exceeds fixed cap")
                    models = json.loads(raw).get("data", [])
                    item.update(model_count=len(models), exact_model_present=any(m.get("id") == MODEL for m in models))
                    item["pass"] = item["exact_model_present"]
                else:
                    if "text/event-stream" not in item["content_type"]:
                        raise ValueError("Expected OpenAI SSE; no fallback")
                    # Reuse sealed Responses frame decoder, but validate this provider's marker independently.
                    parsed = parse_responses(response, item)
                    parsed["checks"]["marker_matches"] = parsed["text"].strip() == MARKER
                    parsed["pass"] = all(parsed["checks"].values())
                    item.update(parsed)
            item["status"] = "pass" if item["pass"] else "catalog_or_protocol_or_marker_or_usage_failure"
        except Exception as error:
            item.update(status="error", error_type=type(error).__name__, error=str(error))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
            item.update(finished_at_utc=now(), finished_monotonic=clock())
            item["duration_ms"] = round((item["finished_monotonic"] - item["started_monotonic"]) * 1000)
            last_end = item["finished_monotonic"]
        result["plan"][position]["status"] = item["status"]
        save()
        print(json.dumps({k: item.get(k) for k in ("stage", "status", "http_status", "duration_ms", "error_type")}), flush=True)
        if item["status"] != "pass":
            result["stop_reason"] = "first_failure_no_retry"
            break
    result.update(finished_at_utc=now(), provider_http_requests=len(result["requests"]),
        generation_requests=sum(r["stage"] == "generation" for r in result["requests"]),
        status="pass" if len(result["requests"]) == 2 and all(r["status"] == "pass" for r in result["requests"]) else "stopped")
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
        if sha(source) != expected:
            raise ValueError("Source changed after approval")
        dest = artifact / "source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
    (artifact / "approval.json").write_text(json.dumps(approval, ensure_ascii=False, indent=2) + "\n")
    key = credential()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    result = run(artifact, key, opener)
    print(json.dumps({"status": result["status"], "provider_http_requests": result["provider_http_requests"],
                      "generation_requests": result["generation_requests"], "estimated_cost_usd": None}), flush=True)


if __name__ == "__main__":
    main()
