"""Smoke read-only bốn CLI; broker host giữ credential, bwrap giữ net namespace riêng."""
import argparse
import copy
import hashlib
import http.server
import json
import os
import pathlib
import secrets
import signal
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from decimal import Decimal

sys.dont_write_bytecode = True
from preflight import ROOT, RUNTIME, now, profile, sha256, ensure_fresh_id
from provider_probe import BASE_URL, MODEL, NoRedirect, credential
from estimate_provider_cost import estimate, require_pricing
from proxy_headers import REQUEST_HEADERS, RESPONSE_HEADERS, protocol_headers

PROMPT = "Use a local tool to read smoke-marker.txt in the current working directory. Do not modify any file. Reply with only the complete marker found in that file."
MARKER = "SMOKE_LOCAL_READ_7c28e36bd41a"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


class Broker(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = False
    block_on_close = True


def pacing_delay(previous_end, interval, current, deadline):
    delay = 0 if previous_end is None else max(0, previous_end + interval - current)
    if current + delay >= deadline:
        raise TimeoutError("Proxy pacing deadline reached")
    return delay


class PacingState:
    """One monotonic clock/serialization boundary for the whole experiment batch."""

    def __init__(self, *, clock=None, sleep=None):
        self.lock = threading.Lock()
        self.last_finished = None
        self.stop_reason = None
        self.blocked_requests = 0
        self.clock = time.monotonic if clock is None else clock
        self.sleep = time.sleep if sleep is None else sleep


def handler(key, nonce, ledger, lock, pricing, deadline, *, request_limit=4, output_limit=512,
            budget_limit="0.0625", budget_ledger=None, stop_on_unknown=False, serialize_requests=False,
            min_interval_seconds=0, pacing_state=None, stop_on_provider_failure=False):
    if min_interval_seconds < 0 or (min_interval_seconds and not serialize_requests):
        raise ValueError("Pacing requires nonnegative interval and serialized requests")
    if stop_on_provider_failure and not serialize_requests:
        raise ValueError("Provider failure stop requires serialized requests")
    all_requests = ledger if budget_ledger is None else budget_ledger
    pacing = PacingState() if pacing_state is None else pacing_state
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, *args):
            pass

        def do_POST(self):
            if serialize_requests:
                with pacing.lock:
                    if stop_on_provider_failure and pacing.stop_reason:
                        pacing.blocked_requests += 1
                        self.send_error(503, "Batch stopped after provider failure; no upstream request sent")
                        return
                    previous_count = len(ledger)
                    try:
                        delay = pacing_delay(pacing.last_finished, min_interval_seconds, pacing.clock(), deadline)
                        before_wait = pacing.clock()
                        if delay:
                            # Intentional user-requested rate pacing, not job-status polling.
                            pacing.sleep(delay)
                        self._pacing_wait_seconds = pacing.clock() - before_wait
                        self.handle_post()
                    except TimeoutError:
                        self.send_error(408, "Proxy pacing deadline reached; no upstream request sent")
                    finally:
                        pacing.last_finished = pacing.clock()
                        if stop_on_provider_failure and len(ledger) > previous_count:
                            item = ledger[-1]
                            if (item.get("http_status") != 200 or item.get("terminal_type") != "response.completed"
                                    or item.get("error_type")):
                                pacing.stop_reason = "provider_failure"
            else:
                self.handle_post()

        def handle_post(self):
            if self.path != "/v1/responses" or self.headers.get("Authorization") != "Bearer " + nonce:
                self.send_error(403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2 * 1024 * 1024:
                    raise ValueError("body_limit")
                payload = json.loads(self.rfile.read(length))
                forwarded_headers = protocol_headers(self.headers, REQUEST_HEADERS)
                if payload.get("model") != MODEL or payload.get("stream") is not True:
                    raise ValueError("model_or_stream_rejected")
                with lock:
                    costs = [item.get("cost", {}).get("estimated_cost_usd") for item in all_requests]
                    if stop_on_unknown and any(c is None for c in costs):
                        raise ValueError("budget_unknown_prior_request")
                    if len(ledger) >= request_limit or time.monotonic() >= deadline or sum(Decimal(c) for c in costs if c is not None) >= Decimal(budget_limit):
                        raise ValueError("run_guard_limit")
                    item = {"started_at_utc": now(), "request_index": len(ledger) + 1,
                            "original_body_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
                            "requested_max_output_tokens": payload.get("max_output_tokens"),
                            "model": payload["model"], "tool_names": [t.get("name") for t in payload.get("tools", [])],
                            "forwarded_protocol_header_names": sorted(forwarded_headers),
                            "responses_lite": forwarded_headers.get("x-openai-internal-codex-responses-lite"),
                            "input_types": [i.get("type") for i in payload.get("input", []) if isinstance(i, dict)],
                            "previous_response_id_present": "previous_response_id" in payload}
                    item["generation_settings"] = {k: payload[k] for k in ["reasoning", "temperature", "top_p", "text"] if k in payload}
                    item["min_interval_seconds"] = min_interval_seconds
                    item["pacing_wait_seconds"] = round(getattr(self, "_pacing_wait_seconds", 0), 6)
                    ledger.append(item)
                    if all_requests is not ledger:
                        all_requests.append(item)
                payload["max_output_tokens"] = min(payload.get("max_output_tokens") or output_limit, output_limit)
                payload["store"] = False
                item["effective_max_output_tokens"] = payload["max_output_tokens"]
                body = json.dumps(payload).encode()
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
                forwarded_headers.update({"Authorization": "Bearer " + key, "Content-Type": "application/json", "Accept": "text/event-stream"})
                request = urllib.request.Request(BASE_URL + "/responses", data=body, method="POST",
                    headers=forwarded_headers)
                try:
                    response = opener.open(request, timeout=45)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    item["http_status"] = response.code
                    self.send_response(response.code)
                    self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                    response_headers = protocol_headers(response.headers, RESPONSE_HEADERS)
                    item["response_protocol_header_names"] = sorted(response_headers)
                    for name, value in response_headers.items():
                        self.send_header(name, value.replace(key, "[REDACTED]"))
                    item["provider_request_id"] = response_headers.get("x-request-id", response_headers.get("request-id"))
                    self.end_headers()
                    count = 0
                    frames = []
                    connected = True
                    for line in response:
                        count += len(line)
                        if count > 4 * 1024 * 1024 or time.monotonic() > deadline:
                            raise TimeoutError("response_guard_limit")
                        # Credential never comes from the provider into sandbox or artifact.
                        clean = line.replace(key.encode(), b"[REDACTED]")
                        if response.code >= 400:
                            item["error_body_excerpt"] = (item.get("error_body_excerpt", "") + clean.decode("utf-8", errors="replace"))[:4096]
                        if connected:
                            try:
                                self.wfile.write(clean)
                                self.wfile.flush()
                            except (BrokenPipeError, ConnectionResetError):
                                connected = False
                        if line.startswith(b"data:"):
                            frames.append(line[5:].strip())
                        elif not line.strip() and frames:
                            data = b"\n".join(frames)
                            frames = []
                            if data == b"[DONE]":
                                break
                            event = json.loads(data)
                            if event.get("type") in {"response.completed", "response.failed", "response.incomplete"}:
                                terminal = event.get("response", {})
                                item.update({"terminal_type": event["type"], "response_model": terminal.get("model"),
                                             "cost": estimate(terminal.get("usage"), pricing)})
                                break
                    item["captured_response_bytes"] = count
                    item["finished_at_utc"] = now()
            except Exception as error:
                if "item" in locals():
                    item["error_type"] = type(error).__name__
                else:
                    self.send_error(400, "Rejected by smoke broker")
    return Handler


def config(spec, root, nonce):
    base = "http://127.0.0.1:8765/v1"
    common_model = {"name": MODEL, "limit": {"context": 128000, "output": 512}}
    if spec["tool"] == "opencode-v1":
        settings = {"$schema": "https://opencode.ai/config.json", "model": "openai/" + MODEL, "small_model": "openai/" + MODEL,
            "provider": {"openai": {"npm": "@ai-sdk/openai", "options": {"baseURL": base, "apiKey": nonce},
                "models": {MODEL: {**common_model, "reasoning": False, "tool_call": True}}}}}
        write(root / "xdg-config/opencode/opencode.json", settings)
        return ["run", "--format", "json", "--model", "openai/" + MODEL, PROMPT]
    if spec["tool"] == "opencode-v2":
        settings = {"$schema": "https://opencode.ai/config.json", "model": "shopaikey/" + MODEL,
            "providers": {"shopaikey": {"name": "Smoke broker", "package": "@opencode/ai/providers/openai-compatible/responses",
                "settings": {"baseURL": base, "apiKey": nonce},
                "models": {MODEL: {**common_model, "modelID": MODEL, "capabilities": {
                    "tools": True, "input": ["text"], "output": ["text"], "reasoning": {"supported": False}}}}}}}
        write(root / "xdg-config/opencode/opencode.json", settings)
        return ["run", "--standalone", "--format", "json", "--model", "shopaikey/" + MODEL, PROMPT]
    if spec["tool"] == "pi":
        write(root / "agent/models.json", {"providers": {"shopaikey": {"baseUrl": base, "apiKey": nonce,
              "api": "openai-responses", "models": [{"id": MODEL, "name": MODEL, "reasoning": False,
              "input": ["text"], "contextWindow": 128000, "maxTokens": 512}]}}})
        return ["--print", "--mode", "json", "--provider", "shopaikey", "--model", MODEL, "--tools", "read",
                "--no-extensions", "--no-mcp", "--no-skills", "--no-prompt-templates", "--no-themes", "--no-context-files", PROMPT]
    (root / "codex-home/config.toml").write_text(f'''model = "{MODEL}"
model_provider = "shopaikey"
approval_policy = "never"
sandbox_mode = "read-only"
model_reasoning_effort = "none"
[model_providers.shopaikey]
name = "Smoke broker"
base_url = "{base}"
env_key = "SMOKE_PROXY_TOKEN"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
''')
    return ["exec", "--json", "--skip-git-repo-check", PROMPT]


def acceptance(tool, stdout):
    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if tool.startswith("opencode"):
        tools = [e for e in events if e.get("type") == "tool_use" and e.get("part", {}).get("state", {}).get("status") == "completed"
                 and MARKER in e.get("part", {}).get("state", {}).get("output", "")]
        text_parts = [e.get("part", {}) for e in events if e.get("type") == "text"]
        final_message = text_parts[-1].get("messageID") if text_parts else None
        final = "".join(p.get("text", "") for p in text_parts if final_message is None or p.get("messageID") == final_message)
    elif tool == "pi":
        tools = [e for e in events if e.get("type") == "tool_execution_end" and not e.get("isError") and MARKER in json.dumps(e.get("result"))]
        messages = [e["message"] for e in events if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant"]
        final = "".join(c.get("text", "") for c in (messages[-1].get("content", []) if messages else []) if c.get("type") == "text")
    else:
        tools = [e for e in events if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "command_execution"
                 and e["item"].get("exit_code") == 0 and MARKER in e["item"].get("aggregated_output", "")]
        messages = [e["item"].get("text", "") for e in events if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
        # Match Codex's final_message: each completed agent message replaces the prior one.
        # Earlier items can be progress commentary, not part of the final answer.
        final = messages[-1] if messages else ""
    return {"json_event_count": len(events), "successful_local_read_observed": bool(tools), "final_exact_marker": final.strip() == MARKER,
            "cli_error_event_observed": any(e.get("type") == "error" for e in events),
            "final_text": final, "successful_read_events": tools}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--retry-failed", type=pathlib.Path)
    parser.add_argument("--config-start", type=int, required=True)
    parser.add_argument("--tools", nargs="+", choices=["opencode-v1", "opencode-v2", "pi", "codex"])
    parser.add_argument("--budget-usd", default="0.50")
    parser.add_argument("--request-gap-seconds", type=int, choices=[0, 30], default=30)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Invalid artifact directory")
    budget = Decimal(args.budget_usd)
    if not budget.is_finite() or budget <= 0:
        parser.error("Budget must be positive and finite")
    prior = None
    if args.retry_failed:
        prior_path = args.retry_failed.resolve()
        if not prior_path.is_relative_to(ROOT / "demos/artifacts"):
            parser.error("Retry source must be an artifact")
        prior = json.loads(prior_path.read_text())
        if not prior.get("finished_at_utc") or args.config_start < 9:
            parser.error("Retry requires completed artifact and fresh config IDs")
    pricing = require_pricing(MODEL, BASE_URL)
    artifact.mkdir(parents=True, exist_ok=False)
    key = credential()
    specs = json.loads((ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())["releases"]
    if args.tools:
        specs = [s for s in specs if s["tool"] in args.tools]
    if prior:
        failed = {r["spec"]["tool"] for r in prior["runs"] if r["status"] != "pass"}
        specs = [s for s in specs if s["tool"] in failed]
    all_requests = []
    pacing_state = PacingState()
    result = {"protocol": "MODEL_SMOKE.md sol rev1", "started_at_utc": now(), "prompt": PROMPT, "marker": MARKER,
              "model": MODEL, "provider": BASE_URL, "budget_guard_usd_estimate": str(budget),
              "pricing_sha256": sha256(ROOT / "research/provider-pricing.json"), "protocol_sha256": sha256(ROOT / "demos/MODEL_SMOKE.md"),
              "request_gap_seconds_after_response": args.request_gap_seconds,
              "plan": [{"tool": s["tool"], "status": "not_run"} for s in specs],
              "script_sha256": {p.name: sha256(p) for p in [pathlib.Path(__file__), ROOT / "demos/model_smoke_inside.py", ROOT / "demos/proxy_headers.py"]}, "runs": []}
    if prior:
        result["retry_of"] = str(prior_path.relative_to(ROOT))
    write(artifact / "protocol.json", result)
    for index, original in enumerate(specs, args.config_start):
        if pacing_state.stop_reason:
            result["stop_reason"] = pacing_state.stop_reason
            break
        costs = [q.get("cost", {}).get("estimated_cost_usd") for q in all_requests]
        if any(c is None for c in costs) or sum((Decimal(c) for c in costs), Decimal(0)) >= budget:
            result["stop_reason"] = "usage_missing" if any(c is None for c in costs) else "budget_guard"
            break
        spec = copy.deepcopy(original)
        spec["config_id"] = f"C-{index:04d}"
        ensure_fresh_id(spec["config_id"])
        root = RUNTIME / spec["config_id"]
        root.mkdir(exist_ok=False)
        spec["runtime_root"] = str(root)
        for directory in ["home", "tmp", "project", "xdg-config", "xdg-data", "xdg-cache", "xdg-state", "managed", "agent", "sessions", "codex-home"]:
            (root / directory).mkdir()
        fixture = root / "project/smoke-marker.txt"
        fixture.write_text(MARKER + "\n")
        inside = root / "inside.py"
        inside.write_bytes((ROOT / "demos/model_smoke_inside.py").read_bytes())
        header_module = root / "proxy_headers.py"
        header_module.write_bytes((ROOT / "demos/proxy_headers.py").read_bytes())
        nonce = secrets.token_hex(24)
        arguments = config(spec, root, nonce)
        command, binary, env = profile(spec)
        # Outer OS enforcement: fixture read-only, even if a CLI permission is permissive.
        command += ["--ro-bind", str(root / "project"), str(root / "project"),
                    "--ro-bind", str(inside), str(inside), "--ro-bind", str(header_module), str(header_module),
                    "--setenv", "SMOKE_PROXY_TOKEN", nonce]
        cli = [binary, *arguments]
        command += ["/usr/bin/python3", str(inside), str(root / "broker.sock"), json.dumps(cli)]
        ledger = []
        deadline = time.monotonic() + 180
        server = Broker(str(root / "broker.sock"), handler(key, nonce, ledger, threading.Lock(), pricing, deadline,
            budget_limit=str(budget), budget_ledger=all_requests, stop_on_unknown=True,
            serialize_requests=True, min_interval_seconds=args.request_gap_seconds, pacing_state=pacing_state,
            stop_on_provider_failure=True))
        os.chmod(root / "broker.sock", 0o600)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        run = {"run_id": f"MODEL-SMOKE-{index-4:02d}", "spec": spec, "cli": cli, "started_at_utc": now(), "provider_requests": ledger}
        if prior:
            run["retry_of"] = next(r["run_id"] for r in prior["runs"] if r["spec"]["tool"] == spec["tool"])
        start = time.monotonic()
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
            run["supervisor_host_pid"] = process.pid
            try:
                stdout, stderr = process.communicate(timeout=180)
                run["timed_out"] = False
            except subprocess.TimeoutExpired:
                run["timed_out"] = True
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            run["exit_code"] = process.returncode
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
            (root / "broker.sock").unlink(missing_ok=True)
        run["duration_ms"] = round((time.monotonic() - start) * 1000)
        run["finished_at_utc"] = now()
        stdout = stdout.decode("utf-8", errors="replace").replace(key, "[REDACTED]").replace(nonce, "[PROXY-TOKEN]")
        stderr = stderr.decode("utf-8", errors="replace").replace(key, "[REDACTED]").replace(nonce, "[PROXY-TOKEN]")
        (artifact / (spec["config_id"] + ".stdout.jsonl")).write_text(stdout)
        (artifact / (spec["config_id"] + ".stderr.txt")).write_text(stderr)
        run["checks"] = acceptance(spec["tool"], stdout)
        witness = json.loads((root / "witness.json").read_text()) if (root / "witness.json").exists() else {}
        run["isolation"] = witness
        checks = run["checks"]
        checks["fixture_unchanged"] = fixture.read_text() == MARKER + "\n"
        checks["isolated_network"] = witness.get("net_namespace") != os.readlink("/proc/self/ns/net") and bool(witness)
        checks["real_home_hidden"] = witness.get("real_home_hidden", False)
        checks["provider_completed"] = any(r.get("terminal_type") == "response.completed" for r in ledger)
        checks["all_provider_requests_completed"] = bool(ledger) and all(q.get("http_status") == 200 and q.get("terminal_type") == "response.completed" and not q.get("error_type") for q in ledger)
        run["status"] = "pass" if run["exit_code"] == 0 and all(checks[k] for k in ["successful_local_read_observed", "final_exact_marker", "fixture_unchanged", "isolated_network", "real_home_hidden", "provider_completed"]) else "failure"
        if checks["cli_error_event_observed"] or not checks["all_provider_requests_completed"]:
            run["status"] = "failure"
        run["failure_layer"] = "provider_or_harness" if not checks["all_provider_requests_completed"] else (None if run["status"] == "pass" else "cli_or_task_pending_review")
        result["runs"].append(run)
        result["plan"][index - args.config_start]["status"] = run["status"]
        write(artifact / "result.json", result)
        print(json.dumps({"tool": spec["tool"], "status": run["status"], "exit_code": run["exit_code"], "requests": len(ledger)}), flush=True)
    result["finished_at_utc"] = now()
    costs = [r.get("cost", {}).get("estimated_cost_usd") for run in result["runs"] for r in run["provider_requests"]]
    result["estimated_total_usd"] = str(sum(Decimal(c) for c in costs)) if costs and all(c is not None for c in costs) else None
    known = [Decimal(c) for c in costs if c is not None]
    result["known_usage_estimated_cost_usd"] = str(sum(known)) if known else None
    if any(c is None for c in costs):
        result["stop_reason"] = "usage_missing"
    result["all_planned_runs_completed"] = all(p["status"] != "not_run" for p in result["plan"])
    result["measured_charge_usd"] = None
    result["provider_stop_reason"] = pacing_state.stop_reason
    result["locally_blocked_after_provider_failure"] = pacing_state.blocked_requests
    write(artifact / "result.json", result)


if __name__ == "__main__":
    main()
