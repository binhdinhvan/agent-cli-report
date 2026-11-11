"""Probe tối thiểu provider riêng: catalog hoặc Responses tool roundtrip, không chạy agent."""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import stat
import time
import urllib.error
import urllib.request
from estimate_provider_cost import require_pricing


ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE_URL = "https://api.shopaikey.com/v1"
MODEL = "gpt-6.1-sol"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not forward a credential to a redirected origin.
        return None


def credential():
    path = ROOT / ".local/credentials/shopaikey.key"
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor) as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("Credential must be a private regular file owned by this user")
        key = handle.read().strip()
    if not key or any(char.isspace() for char in key):
        raise ValueError("Credential is empty or contains whitespace; value omitted")
    return key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["catalog", "responses"], required=True)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    if args.stage == "responses":
        require_pricing(MODEL, BASE_URL)
    artifact.mkdir(parents=True, exist_ok=False)
    key = credential()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    result = {"started_at_utc": now(), "base_url": BASE_URL, "model": MODEL, "stage": args.stage,
              "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              "requests": [], "cost_usd": None,
              "budget_note": "Price/unspent balance not verified; no dollar cost inferred from token counts.",
              "scope": "Provider-only constant inputs; no agent execution, filesystem tool, source code or real session sent."}

    def save():
        text = json.dumps(result, ensure_ascii=False, indent=2).replace(key, "[REDACTED]")
        (artifact / "result.json").write_text(text + "\n")

    def call(method, path, payload=None):
        if (method, path) not in {("GET", "/models"), ("POST", "/responses")}:
            raise ValueError("Request outside fixed probe endpoints")
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Authorization": "Bearer " + key, "Accept": "application/json", "User-Agent": "agent-cli-report-provider-probe"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(BASE_URL + path, data=body, headers=headers, method=method)
        item = {"method": method, "path": path, "started_at_utc": now(), "payload": payload}
        result["requests"].append(item)
        clock = time.monotonic()
        try:
            try:
                response = opener.open(request, timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                raw = response.read(4 * 1024 * 1024 + 1)
                if len(raw) > 4 * 1024 * 1024:
                    raise ValueError("Response exceeds probe capture limit")
                try:
                    decoded = json.loads(raw)
                except json.JSONDecodeError:
                    decoded = {"non_json_body": raw.decode("utf-8", errors="replace")[:1000]}
                item.update({"http_status": response.code,
                             "headers": {name: response.headers.get(name) for name in ("content-type", "x-request-id", "request-id") if response.headers.get(name)}})
                if path == "/models" and response.code == 200:
                    entries = decoded.get("data", [])
                    matches = [entry for entry in entries if entry.get("id") == MODEL]
                    item["response"] = {"model_count": len(entries), "matching_models": matches,
                                        "related_model_ids": [entry.get("id") for entry in entries if "luna" in entry.get("id", "").lower()]}
                else:
                    item["response"] = decoded
                return response.code, decoded
        finally:
            item["finished_at_utc"] = now()
            item["duration_ms"] = round((time.monotonic() - clock) * 1000)
            save()

    try:
        if args.stage == "catalog":
            status, data = call("GET", "/models")
            found = status == 200 and any(entry.get("id") == MODEL for entry in data.get("data", []))
            result["status"] = "catalog_model_found" if found else "catalog_unverified"
        else:
            # Fixed protocol: at most two generation requests, no automatic retry or fallback protocol.
            marker = "REPORT_PROVIDER_PROBE_OK"
            first = {
                "model": MODEL, "store": False, "stream": False, "max_output_tokens": 256,
                "input": [{"role": "user", "content": "Call report_echo exactly once with marker REPORT_PROVIDER_PROBE_OK. Do not call other tools."}],
                "tools": [{"type": "function", "name": "report_echo", "description": "Return the supplied marker. This is an inert protocol test, not a filesystem or shell tool.",
                           "parameters": {"type": "object", "properties": {"marker": {"type": "string"}}, "required": ["marker"], "additionalProperties": False}, "strict": True}],
                "tool_choice": {"type": "function", "name": "report_echo"},
            }
            status, response = call("POST", "/responses", first)
            if status != 200:
                raise RuntimeError(f"Responses first request returned HTTP {status}; no retry")
            output = response.get("output", [])
            calls = [item for item in output if item.get("type") == "function_call"]
            if len(calls) != 1 or calls[0].get("name") != "report_echo" or json.loads(calls[0]["arguments"]) != {"marker": marker}:
                raise ValueError("No single valid report_echo tool call; no continuation sent")
            result["tool_call_validated"] = True
            # Respond with a literal only. Model arguments are never used to access files or execute code.
            second = {"model": MODEL, "store": False, "stream": False, "max_output_tokens": 256,
                      "input": [*first["input"], *output,
                                {"type": "function_call_output", "call_id": calls[0]["call_id"], "output": marker},
                                {"role": "user", "content": "Return only the marker from the tool result, without explanation."}]}
            status, response = call("POST", "/responses", second)
            text = "".join(part.get("text", "") for item in response.get("output", []) if item.get("type") == "message"
                           for part in item.get("content", []) if part.get("type") == "output_text")
            result["roundtrip_marker_matches"] = text.strip() == marker
            result["status"] = "responses_tool_roundtrip_pass" if status == 200 and result["roundtrip_marker_matches"] else "responses_tool_roundtrip_failure"
    except Exception as error:
        result.update({"status": "probe_error", "error_type": type(error).__name__, "error": str(error).replace(key, "[REDACTED]")})
    result["finished_at_utc"] = now()
    save()
    print(json.dumps({"stage": args.stage, "status": result["status"], "requests": len(result["requests"]), "artifact": str(artifact.relative_to(ROOT) / "result.json")}, indent=2))
    if result["status"] not in {"catalog_model_found", "responses_tool_roundtrip_pass"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
