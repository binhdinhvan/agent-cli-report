"""Native suite48 adapter + LOCAL synthetic preflight. No paid mode or credential reads."""
import argparse
import copy
import csv
import io
import json
import os
import pathlib
import re
import selectors
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from unittest.mock import patch

from suite48_runtime import ROOT, SUITE, digest, grade, task_spec
from suite48_solutions import references, writer_source
from verify_suite48 import verify

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "demos"))
import model_smoke
from model_smoke import Broker, MODEL, BASE_URL, PacingState, handler, now, write
from preflight import RUNTIME, profile
from pilot import pilot_config, classify_run
from environment_profile import environment_profile
from timing_policy import timing_policy

SEAL = SUITE / "artifacts/PREP48-20261110-02"
ORDER = SUITE / "artifacts/DRAFT48-20261109-01/order.csv"
MARKER = "OFF48_NATIVE_APPLY_DONE"
NONCE = "offline-inert-local-token-never-a-provider-key"


def slot_mapping(rows):
    slots = [dict(row) for row in rows]
    if len({r["slot"] for r in slots}) != len(slots):
        raise ValueError("Duplicate draft slot")
    for row in slots:
        if row["status"] != "planned_not_run" or not re.fullmatch(r"D48-\d{3}", row["slot"]):
            raise ValueError("Draft slots only, not measured or allocated run IDs")
        task_spec(row["task_id"])
        if row["tool"] not in ("opencode-v1", "opencode-v2", "pi", "codex"):
            raise ValueError("Unknown CLI")
    return slots


def prepare(spec, config_id, task_id):
    if not re.fullmatch(r"OF48-[A-Za-z0-9-]+", config_id):
        raise ValueError("Offline namespace only; never reserve/reuse paid R/C IDs")
    spec = copy.deepcopy(spec)
    spec.update(config_id=config_id, runtime_root=str(RUNTIME / config_id), environment_revision="search-r2")
    root = pathlib.Path(spec["runtime_root"])
    root.mkdir(parents=True, exist_ok=False)
    for directory in ("home", "tmp", "xdg-config", "xdg-data", "xdg-cache", "xdg-state", "managed", "agent", "sessions", "codex-home"):
        (root / directory).mkdir()
    task = SUITE / task_id
    shutil.copytree(task / "fixture", root / "project")
    immutable = sorted(str(path.relative_to(task / "fixture")) for path in (task / "fixture").rglob("*")
        if path.is_file() and str(path.relative_to(task / "fixture")) not in task_spec(task_id)["allowed_changes"])
    write(root / "immutable.json", immutable)
    sources = {"inside.py": ROOT / "demos/model_smoke_inside.py", "proxy_headers.py": ROOT / "demos/proxy_headers.py",
        "suite48_native_inside.py": ROOT / "benchmark/suite48_native_inside.py"}
    for name, source in sources.items():
        (root / name).write_bytes(source.read_bytes())
    # Reuse pinned native settings; no shape/env guesses or edits to the frozen pilot.
    cli_args = pilot_config(spec, root, NONCE, (task / "prompt.txt").read_text())
    command, binary, env = profile(spec)
    for name in [*sources, "immutable.json", *("project/" + name for name in immutable)]:
        command += ["--ro-bind", str(root / name), str(root / name)]
    command += ["--setenv", "SMOKE_PROXY_TOKEN", NONCE, "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        "/usr/bin/python3", "-B", str(root / "suite48_native_inside.py"), str(root / "broker.sock"), json.dumps([binary, *cli_args])]
    return spec, root, command, [binary, *cli_args]


def execute(command, root, timeout=90):
    start = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
    streams = {process.stdout: bytearray(), process.stderr: bytearray()}
    selector = selectors.DefaultSelector()
    for stream in streams:
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ)
    timed_out, overflow = False, False
    try:
        while selector.get_map():
            remaining = start + timeout - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            for key, _ in selector.select(min(remaining, 0.25)):
                data = os.read(key.fileobj.fileno(), 65536)
                if not data:
                    selector.unregister(key.fileobj)
                else:
                    streams[key.fileobj].extend(data)
                    if sum(len(value) for value in streams.values()) > 16 * 1024 * 1024:
                        overflow = True
                        break
            if overflow:
                break
        if timed_out or overflow:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        selector.close()
        for stream in streams:
            stream.close()
    end = time.monotonic()
    native_clock = json.loads((root / "native-clock.json").read_text()) if (root / "native-clock.json").exists() else None
    return {"supervisor_host_pid": process.pid, "exit_code": process.returncode, "timed_out": timed_out,
        "output_limit_exceeded": overflow, "duration_ms": round((end - start) * 1000),
        "duration_boundary": "outer bwrap spawn through launcher/bridge exit; startup/teardown included",
        "outer_started_monotonic": start, "outer_finished_monotonic": end, "native_clock": native_clock,
        "stdout": bytes(streams[process.stdout]).decode(errors="replace"),
        "stderr": bytes(streams[process.stderr]).decode(errors="replace"),
        "witness": json.loads((root / "native-witness.json").read_text()) if (root / "native-witness.json").exists() else None}


def isolated(execution):
    w = execution["witness"]
    return bool(w and all(w["immutable_readonly"].values()) and all(w[k] for k in
        ("project_writable", "hidden_absent", "home_hidden", "provider_key_env_absent"))
        and w["net_namespace"] != os.readlink("/proc/self/ns/net"))


def event_acceptance(tool, text):
    events = []
    for line in text.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if tool.startswith("opencode"):
        tool_ok = any(e.get("type") == "tool_use" and e.get("part", {}).get("state", {}).get("status") == "completed"
            and MARKER in e.get("part", {}).get("state", {}).get("output", "") for e in events)
        parts = [e.get("part", {}) for e in events if e.get("type") == "text"]
        last = parts[-1].get("messageID") if parts else None
        final = "".join(p.get("text", "") for p in parts if p.get("messageID") == last)
    elif tool == "pi":
        tool_ok = any(e.get("type") == "tool_execution_end" and not e.get("isError") and MARKER in json.dumps(e.get("result")) for e in events)
        messages = [e["message"] for e in events if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant"]
        final = "".join(p.get("text", "") for p in (messages[-1].get("content", []) if messages else []) if p.get("type") == "text")
    else:
        tool_ok = any(e.get("type") == "item.completed" and e.get("item", {}).get("type") == "command_execution"
            and e["item"].get("exit_code") == 0 and MARKER in e["item"].get("aggregated_output", "") for e in events)
        messages = [e["item"].get("text", "") for e in events if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
        final = messages[-1] if messages else ""
    return {"native_tool_execution_observed": tool_ok, "final_marker": final.strip() == MARKER}


def sse(items, number, usage=True, terminal="response.completed"):
    response = {"id": f"resp_of48_{number}", "model": MODEL, "status": "in_progress"}
    events = [{"type": "response.created", "response": response}]
    for index, item in enumerate(items):
        events.append({"type": "response.output_item.added", "output_index": index,
            "item": {**item, "status": "in_progress", **({"arguments": ""} if item["type"] == "function_call" else {})}})
        if item["type"] == "function_call":
            events += [{"type": "response.function_call_arguments.delta", "item_id": item["id"], "output_index": index, "delta": item["arguments"]},
                {"type": "response.function_call_arguments.done", "item_id": item["id"], "output_index": index, "arguments": item["arguments"]}]
        elif item["type"] == "message":
            for content_index, part in enumerate(item["content"]):
                position = {"item_id": item["id"], "output_index": index, "content_index": content_index}
                events += [{"type": "response.content_part.added", **position, "part": {**part, "text": ""}},
                    {"type": "response.output_text.delta", **position, "delta": part["text"]},
                    {"type": "response.output_text.done", **position, "text": part["text"]},
                    {"type": "response.content_part.done", **position, "part": part}]
        events.append({"type": "response.output_item.done", "output_index": index, "item": item})
    completed = {**response, "status": "completed" if terminal == "response.completed" else "failed", "output": items}
    if usage:
        completed["usage"] = {"input_tokens": 100, "output_tokens": 10, "input_tokens_details": {"cached_tokens": 20}, "output_tokens_details": {"reasoning_tokens": 0}}
    events.append({"type": terminal, "response": completed})
    return b"".join(b"data: " + json.dumps(event).encode() + b"\n\n" for event in events)


class Response(io.BytesIO):
    code = 200
    headers = {"Content-Type": "text/event-stream", "x-request-id": "offline-synthetic-not-provider"}


class SyntheticProvider:
    """In-memory urllib opener replacement. There is no network client behind this object."""
    def __init__(self, tool, task_id):
        self.tool, self.task_id = tool, task_id
        self.captures, self.injected = [], False

    def open(self, request, timeout):
        if request.full_url != BASE_URL + "/responses" or timeout != 45:
            raise ValueError("Unexpected outbound URL/timeout even in synthetic mode")
        payload = json.loads(request.data)
        self.captures.append(payload)
        names = [t.get("name") for t in payload.get("tools", [])]
        tool_name = "shell" if self.tool == "opencode-v2" else "bash"
        ready = tool_name in names or (self.tool == "codex" and "additional_tools" in json.dumps(payload))
        if ready and not self.injected:
            code = writer_source(references()[self.task_id]) + "\nprint(" + repr(MARKER) + ")\n"
            command = "python3 -B -c " + shlex.quote(code)
            if self.tool == "codex":
                items = [{"type": "custom_tool_call", "id": "ctc_of48", "call_id": "call_of48", "status": "completed", "name": "exec",
                    "input": "const r = await tools.exec_command({cmd:" + json.dumps(command) + ",yield_time_ms:10000,max_output_tokens:2000}); text(r.output);"}]
            else:
                items = [{"type": "function_call", "id": "fc_of48", "call_id": "call_of48", "status": "completed", "name": tool_name,
                    "arguments": json.dumps({"command": command})}]
            self.injected = True
        else:
            items = [{"type": "message", "id": "msg_of48_" + str(len(self.captures)), "role": "assistant", "status": "completed",
                "content": [{"type": "output_text", "text": MARKER if self.injected else "OFF48_BOOTSTRAP", "annotations": []}]}]
        return Response(sse(items, len(self.captures)))


class VirtualPacing:
    """Fast policy exercise only; not evidence of real wall-clock30s spacing."""
    def __init__(self):
        self.offset = 0.0

    def clock(self):
        return time.monotonic() + self.offset

    def sleep(self, seconds):
        self.offset += seconds


def guarded_handler(ledger, all_requests, pacing, deadline, pricing, budget="16"):
    timing = timing_policy("paced-900")
    return handler("OFFLINE-INERT-NO-PROVIDER-KEY", NONCE, ledger, threading.Lock(), pricing, deadline,
        request_limit=timing["request_limit"], output_limit=timing["output_limit"], budget_limit=budget,
        budget_ledger=all_requests, stop_on_unknown=True, serialize_requests=True, min_interval_seconds=30,
        pacing_state=pacing, stop_on_provider_failure=True, minimum_request_window_seconds=timing["minimum_request_window_seconds"])


def run_preflight(artifact, selected_slots=None):
    verify(SEAL)
    env = environment_profile("search-r2")
    with ORDER.open() as stream:
        rows = slot_mapping(csv.DictReader(stream))
    selected = [row for row in rows if row["repetition"] == "1"]
    if selected_slots:
        if set(selected_slots) - {row["slot"] for row in selected}:
            raise ValueError("Only round1 draft slots allowed for preflight")
        selected = [row for row in selected if row["slot"] in selected_slots]
    specs = {s["tool"]: s for s in json.loads((ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())["releases"]}
    pricing = json.loads((ROOT / "research/provider-pricing.json").read_text())
    artifact.mkdir(parents=True, exist_ok=False)
    virtual = VirtualPacing()
    pacing, all_requests = PacingState(clock=virtual.clock, sleep=virtual.sleep), []
    result = {"mode": "offline-native-synthetic-preflight", "provider_requests": 0, "paid_runs_authorized": False,
        "actual_inference_charge_usd": None, "synthetic_usage_not_real_cost": True,
        "pacing_mode": "virtual30s, serialized; NOT actual30s native wall-gap acceptance",
        "environment_revision": "search-r2", "environment_manifest_sha256": env["manifest_sha256"],
        "timing_policy": timing_policy("paced-900"), "offline_outer_watchdog_seconds": 90,
        "planned": [{**row, "status": "not_run"} for row in selected], "runs": [], "started_at_utc": now()}
    for row in selected:
        run_dir = artifact / row["slot"]
        run_dir.mkdir()
        config_id = "OF48-" + artifact.name + "-" + row["slot"]
        spec, root, command, cli = prepare(specs[row["tool"]], config_id, row["task_id"])
        local_provider = SyntheticProvider(row["tool"], row["task_id"])
        ledger = []
        server = Broker(str(root / "broker.sock"), guarded_handler(ledger, all_requests, pacing, virtual.clock() + 900, pricing))
        os.chmod(root / "broker.sock", 0o600)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            # Both opener substitution and TCP denial fail closed. The bridge uses
            # AF_UNIX; native CLI networking is confined to its private namespace.
            with patch.object(model_smoke.urllib.request, "build_opener", return_value=local_provider), patch.object(
                    socket, "create_connection", side_effect=AssertionError("Offline adapter forbids TCP egress")):
                execution = execute(command, root)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
            (root / "broker.sock").unlink(missing_ok=True)
        acceptance = event_acceptance(row["tool"], execution["stdout"])
        for name in ("stdout", "stderr"):
            (run_dir / (name + (".jsonl" if name == "stdout" else ".txt"))).write_text(execution.pop(name).replace(NONCE, "[LOCAL-PROXY-TOKEN]"))
        grading = grade(root / "project", row["task_id"], run_dir / "grader")
        ok = isolated(execution) and not execution["output_limit_exceeded"] and all(acceptance.values())
        status = "offline_preflight_pass" if ok and classify_run(execution, True, grading, ledger) == "success" and local_provider.injected else "offline_preflight_failure"
        safe_config = {}
        for name in ("xdg-config/opencode/opencode.json", "agent/models.json", "codex-home/config.toml"):
            if (root / name).exists():
                safe_config[name] = (root / name).read_text().replace(NONCE, "[LOCAL-PROXY-TOKEN]")
        write(run_dir / "config.json", safe_config)
        write(run_dir / "synthetic-payloads.json", local_provider.captures)
        run = {"slot": row["slot"], "task_id": row["task_id"], "tool": row["tool"], "config_id": config_id,
            "spec": spec, "cli": cli, "status": status, "execution": execution, "event_acceptance": acceptance,
            "isolation_ok": isolated(execution), "grading": grading, "synthetic_ledger": ledger,
            "provider_requests": 0, "synthetic_calls": len(local_provider.captures), "paid_run_id": None,
            "supervisor_pid_absent": not pathlib.Path("/proc", str(execution["supervisor_host_pid"])).exists(),
            "broker_socket_absent": not (root / "broker.sock").exists()}
        write(run_dir / "result.json", run)
        result["runs"].append(run)
        next(p for p in result["planned"] if p["slot"] == row["slot"])["status"] = status
        write(artifact / "result.json", result)
        print(json.dumps({k: run[k] for k in ("slot", "task_id", "tool", "status", "synthetic_calls")}), flush=True)
        if status != "offline_preflight_pass":
            result["stop_reason"] = "offline_preflight_failure; no automatic retry"
            break
    result["finished_at_utc"] = now()
    result["status"] = "pass" if len(result["runs"]) == len(selected) and all(r["status"] == "offline_preflight_pass" for r in result["runs"]) else "failure"
    result["synthetic_calls"] = len(all_requests)
    sources = ["benchmark/suite48_native.py", "benchmark/suite48_native_inside.py", "benchmark/test_suite48_native.py",
        "benchmark/pilot.py", "demos/preflight.py", "demos/model_smoke.py", "demos/model_smoke_inside.py",
        "demos/proxy_headers.py", "demos/environment_profile.py", "demos/timing_policy.py"]
    result["source_sha256"] = {name: digest(ROOT / name) for name in sources}
    for name in sources:
        saved = artifact / "source" / name
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes((ROOT / name).read_bytes())
    result["artifact_sha256"] = {str(p.relative_to(artifact)): digest(p) for p in artifact.rglob("*") if p.is_file() and p != artifact / "result.json"}
    write(artifact / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-preflight", action="store_true")
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--slots", nargs="+")
    args = parser.parse_args()
    if not args.offline_preflight:
        parser.error("Only offline synthetic preflight is implemented; paid launch requires separate approval/protocol")
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / "artifacts") or not re.fullmatch(r"[A-Za-z0-9-]+", artifact.name):
        parser.error("Expected suite48 artifact directory with safe namespace")
    result = run_preflight(artifact, args.slots)
    print(json.dumps({"status": result["status"], "executed": len(result["runs"]), "provider_requests": 0, "paid_runs_authorized": False}))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
