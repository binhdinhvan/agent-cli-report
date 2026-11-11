"""Pilot 8 lượt có budget toàn đợt; --offline-preflight không credential/Internet."""
import argparse
import copy
import csv
import datetime
import difflib
import hashlib
import http.server
import json
import os
import pathlib
import platform
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "demos"))
from model_smoke import Broker, MODEL, BASE_URL, config, handler, profile, sha256, write, now, RUNTIME, PacingState
from provider_probe import credential
from estimate_provider_cost import require_pricing
from preflight import ensure_fresh_id
from verify_pilot_fixtures import sandbox

ORDER = [("P-01", "pi"), ("P-01", "codex"), ("P-01", "opencode-v2"), ("P-01", "opencode-v1"),
         ("P-02", "opencode-v2"), ("P-02", "opencode-v1"), ("P-02", "codex"), ("P-02", "pi")]
SEAL = ROOT / "benchmark/artifacts/PILOT-PREP-20261106-02/preparation.json"


def sealed():
    seal = json.loads(SEAL.read_text())
    if seal["status"] != "pass":
        raise ValueError("Fixture preparation did not pass")
    for task in seal["tasks"]:
        base = ROOT / "benchmark/tasks" / task["task_id"]
        for path, digest in task["files"].items():
            if sha256(base / path) != digest:
                raise ValueError("Fixture seal changed: " + str(base / path))
    return seal


def pilot_config(spec, root, nonce, prompt):
    args = config(spec, root, nonce)
    args[-1] = prompt
    tool = spec["tool"]
    if tool.startswith("opencode"):
        path = root / "xdg-config/opencode/opencode.json"
        cfg = json.loads(path.read_text())
        if tool == "opencode-v1":
            cfg["small_model"] = "openai/" + MODEL
            cfg["provider"]["openai"]["models"][MODEL]["limit"]["output"] = 2048
            cfg["permission"] = {"*": "deny", **{action: "allow" for action in ["read", "edit", "glob", "grep", "list", "bash"]}}
        else:
            cfg["providers"]["shopaikey"]["models"][MODEL]["limit"]["output"] = 2048
            cfg["permissions"] = [{"action": "*", "resource": "*", "effect": "deny"},
                *[{"action": action, "resource": "*", "effect": "allow"} for action in ["read", "edit", "glob", "grep", "shell", "execute"]]]
        write(path, cfg)
    elif tool == "pi":
        path = root / "agent/models.json"
        cfg = json.loads(path.read_text())
        cfg["providers"]["shopaikey"]["models"][0]["maxTokens"] = 2048
        write(path, cfg)
        args[args.index("--tools") + 1] = "read,bash,edit,write"
        args[-1:-1] = ["--thinking", "off"]
    else:
        path = root / "codex-home/config.toml"
        path.write_text(path.read_text().replace('sandbox_mode = "read-only"', 'sandbox_mode = "workspace-write"'))
    return args


def prepare(original, config_id, task_id):
    ensure_fresh_id(config_id)
    spec = copy.deepcopy(original)
    spec["config_id"] = config_id
    root = RUNTIME / config_id
    root.mkdir(exist_ok=False)
    spec["runtime_root"] = str(root)
    for directory in ["home", "tmp", "xdg-config", "xdg-data", "xdg-cache", "xdg-state", "managed", "agent", "sessions", "codex-home"]:
        (root / directory).mkdir()
    task = ROOT / "benchmark/tasks" / task_id
    shutil.copytree(task / "fixture", root / "project")
    for source in [ROOT / "demos/model_smoke_inside.py", ROOT / "demos/proxy_headers.py", ROOT / "benchmark/pilot_inside.py"]:
        target = root / ("inside.py" if source.name == "model_smoke_inside.py" else source.name)
        target.write_bytes(source.read_bytes())
    nonce = secrets.token_hex(24)
    args = pilot_config(spec, root, nonce, (task / "prompt.txt").read_text().strip())
    command, binary, env = profile(spec)
    for name in ["inside.py", "proxy_headers.py", "pilot_inside.py", "project/test_public.py"]:
        command += ["--ro-bind", str(root / name), str(root / name)]
    command += ["--setenv", "SMOKE_PROXY_TOKEN", nonce, "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
                "/usr/bin/python3", str(root / "pilot_inside.py"), str(root / "broker.sock"), json.dumps([binary, *args])]
    return spec, root, nonce, command, [binary, *args]


def execute(command, root, timeout):
    start = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    if len(stdout) + len(stderr) > 16 * 1024 * 1024:
        raise RuntimeError("Pilot output capture exceeds limit")
    witness_path = root / "pilot-witness.json"
    witness = json.loads(witness_path.read_text()) if witness_path.exists() else {}
    return {"supervisor_host_pid": process.pid, "exit_code": process.returncode, "timed_out": timed_out,
            "duration_ms": round((time.monotonic() - start) * 1000), "witness": witness,
            "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")}


def grade(project, task_id, target):
    task = ROOT / "benchmark/tasks" / task_id
    manifest = json.loads((task / "task.json").read_text())
    target.mkdir(exist_ok=False)
    snapshot = target / "snapshot"
    snapshot.mkdir()
    invalid = []
    for directory, dirs, files in os.walk(project, followlinks=False):
        for name in list(dirs):
            path = pathlib.Path(directory) / name
            if path.is_symlink():
                invalid.append(str(path.relative_to(project)))
                dirs.remove(name)
            elif name == "__pycache__":
                dirs.remove(name)
        for name in files:
            path = pathlib.Path(directory) / name
            relative = path.relative_to(project)
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
                invalid.append(str(relative))
                continue
            if len(list(snapshot.rglob("*"))) > 32:
                invalid.append("file_count_limit")
                break
            # Do not follow a symlink replaced between traversal and open.
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as handle:
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    invalid.append(str(relative))
                    continue
                data = handle.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                invalid.append(str(relative))
                continue
            destination = snapshot / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    baseline = {str(p.relative_to(task / "fixture")): p.read_bytes() for p in (task / "fixture").rglob("*") if p.is_file()}
    actual = {str(p.relative_to(snapshot)): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()}
    changed = sorted(p for p in set(baseline) | set(actual) if baseline.get(p) != actual.get(p))
    scope_ok = not invalid and set(actual) == set(baseline) and set(changed) <= set(manifest["allowed_modified_files"])
    patches = []
    for name in changed:
        patches.extend(difflib.unified_diff(baseline.get(name, b"").decode(errors="replace").splitlines(True),
            actual.get(name, b"").decode(errors="replace").splitlines(True), fromfile="before/" + name, tofile="after/" + name))
    (target / "patch.diff").write_text("".join(patches))
    start = time.monotonic()
    outcomes = {suite: sandbox(snapshot, task / "acceptance.py", suite) for suite in ["public", "hidden"]}
    report = {"scope_ok": scope_ok, "changed_files": changed, "invalid_paths": invalid,
              "snapshot_sha256": {str(p.relative_to(snapshot)): sha256(p) for p in snapshot.rglob("*") if p.is_file()},
              "suites": outcomes, "duration_ms": round((time.monotonic() - start) * 1000),
              "pass": scope_ok and all(not r["timed_out"] and r["exit_code"] == 0 for r in outcomes.values())}
    write(target / "grading.json", report)
    return report


def pending_cost(requests):
    return any(r.get("cost", {}).get("estimated_cost_usd") is None for r in requests)


def known_cost(requests):
    return sum((Decimal(r["cost"]["estimated_cost_usd"]) for r in requests if r.get("cost", {}).get("estimated_cost_usd") is not None), Decimal(0))


def budget_guard(value):
    try:
        budget = Decimal(value)
    except Exception as error:
        raise argparse.ArgumentTypeError("Budget must be positive and finite") from error
    if not budget.is_finite() or budget <= 0:
        raise argparse.ArgumentTypeError("Budget must be positive and finite")
    return budget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--offline-preflight", action="store_true")
    parser.add_argument("--config-start", type=int)
    parser.add_argument("--retry-run", type=pathlib.Path)
    parser.add_argument("--run-start", type=int, default=9)
    parser.add_argument("--request-gap-seconds", type=int, choices=[0, 30], default=30)
    parser.add_argument("--budget-usd", type=budget_guard, default=Decimal("1"))
    parser.add_argument("--protocol-file", type=pathlib.Path)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "benchmark/artifacts"):
        parser.error("Invalid artifact")
    seal = sealed()
    retry = None
    prior_known_cost = Decimal(0)
    prior_unknown_count = 0
    if args.retry_run:
        retry_path = args.retry_run.resolve()
        if args.offline_preflight or not retry_path.is_relative_to(ROOT / "benchmark/artifacts") or args.config_start is None:
            parser.error("Retry needs a benchmark run artifact and explicit fresh config ID")
        retry = json.loads(retry_path.read_text())
        prior_batch = json.loads((retry_path.parent.parent / "result.json").read_text())
        if not prior_batch.get("finished_at_utc") or retry["status"] == "success":
            parser.error("Only a failed run from a completed batch can be retried")
        prior_known_cost = Decimal(prior_batch.get("prior_known_usage_estimated_cost_usd", "0")) + known_cost([q for r in prior_batch["runs"] for q in r["provider_requests"]])
        prior_unknown_count = prior_batch.get("prior_unpriced_request_count", 0) + sum(q.get("cost", {}).get("estimated_cost_usd") is None for r in prior_batch["runs"] for q in r["provider_requests"])
        if prior_known_cost >= args.budget_usd:
            parser.error("Known prior estimate already reached budget")
    if not args.offline_preflight:
        with (ROOT / "benchmark/runs.csv").open(newline="") as handle:
            used_ids = {r["run_id"] for r in csv.DictReader(handle)}
        state_path = ROOT / "research/experiment-state.json"
        if state_path.exists():
            used_ids.update(json.loads(state_path.read_text()).get("retired_run_ids", []))
        planned_count = 1 if retry else len(ORDER)
        if any(f"R-{n:04d}" in used_ids for n in range(args.run_start, args.run_start + planned_count)):
            parser.error("Run IDs already exist; choose fresh --run-start")
    pricing = None if args.offline_preflight else require_pricing(MODEL, BASE_URL)
    artifact.mkdir(parents=True, exist_ok=False)
    preparation = json.loads((ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())
    specs = {s["tool"]: s for s in preparation["releases"]}
    # Offline mode never opens credential file and never creates an Internet client.
    key = None if args.offline_preflight else credential()
    all_requests = []
    pacing_state = PacingState()
    plan = [(retry["task_id"], retry["tool"])] if retry else (ORDER[:4] if args.offline_preflight else ORDER)
    budget_remaining = str(args.budget_usd - prior_known_cost)
    hashes = {str(p.relative_to(ROOT)): sha256(p) for p in [pathlib.Path(__file__), ROOT / "benchmark/pilot_inside.py",
        ROOT / "demos/model_smoke.py", ROOT / "demos/model_smoke_inside.py", ROOT / "demos/proxy_headers.py", ROOT / "benchmark/verify_pilot_fixtures.py"]}
    protocol_name = "PILOT.md"
    protocol_file = ROOT / "benchmark" / protocol_name
    if args.protocol_file:
        protocol_file = args.protocol_file.resolve()
        if protocol_file.parent != ROOT / "benchmark" or protocol_file.suffix != ".md" or not protocol_file.is_file():
            parser.error("Protocol must be an existing Markdown file directly under benchmark")
        protocol_name = protocol_file.name
    result = {"protocol": protocol_name + (" rev3" if protocol_name == "PILOT.md" else " rev1"), "mode": "offline-preflight" if args.offline_preflight else "pilot",
              "started_at_utc": now(), "budget_approved_usd_estimate": None, "budget_guard_usd_estimate": str(args.budget_usd), "script_sha256": hashes,
              "model": MODEL, "provider": BASE_URL,
              "pricing_sha256": sha256(ROOT / "research/provider-pricing.json") if pricing else None,
              "request_gap_seconds_after_response": args.request_gap_seconds,
              "fixture_seal": str(SEAL.relative_to(ROOT)), "fixture_seal_sha256": sha256(SEAL),
              "protocol_sha256": sha256(protocol_file), "prior_known_usage_estimated_cost_usd": str(prior_known_cost),
              "prior_unpriced_request_count": prior_unknown_count, "remaining_known_estimate_guard_usd": budget_remaining,
              "environment": {"platform": platform.platform(), "python": platform.python_version(), "cpu_count": os.cpu_count(),
                              "cpu_model": next((l.split(":", 1)[1].strip() for l in pathlib.Path("/proc/cpuinfo").read_text().splitlines() if l.startswith("model name")), None),
                              "mem_total": pathlib.Path("/proc/meminfo").read_text().splitlines()[0]},
              "plan": [{"task": t, "tool": tool, "status": "not_run"} for t, tool in plan], "runs": []}
    if retry:
        result["retry_of"] = str(retry_path.relative_to(ROOT))
        result["prior_unknown_cost_note"] = "Explicit user-requested single retry after prior stop; unpriced requests remain unknown, not zero; guard uses known estimates only"
    write(artifact / "protocol.json", result)
    for position, (task_id, tool) in enumerate(plan, 1):
        if pending_cost(all_requests) or known_cost(all_requests) >= Decimal(budget_remaining):
            result["stop_reason"] = "usage_missing" if pending_cost(all_requests) else "budget_guard"
            break
        first_config = args.config_start if args.config_start is not None else (41 if args.offline_preflight else 49)
        config_id = f"C-{first_config + position - 1:04d}"
        spec, root, nonce, command, cli = prepare(specs[tool], config_id, task_id)
        run_id = f"PREFLIGHT-{position:02d}" if args.offline_preflight else f"R-{args.run_start + position - 1:04d}"
        run_dir = artifact / run_id
        run_dir.mkdir()
        ledger = []
        captured = []
        if args.offline_preflight:
            class Capture(http.server.BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    captured.append({"model": payload.get("model"), "stream": payload.get("stream"),
                        "reasoning": payload.get("reasoning"), "max_output_tokens": payload.get("max_output_tokens"),
                        "header_names": sorted(self.headers.keys()), "responses_lite": self.headers.get("x-openai-internal-codex-responses-lite"),
                        "tools": [t.get("name") for t in payload.get("tools", [])],
                        "input_types": [i.get("type") for i in payload.get("input", [])]})
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error":{"message":"Intentional offline preflight stop"}}')
            request_handler = Capture
        else:
            request_handler = handler(key, nonce, ledger, threading.Lock(), pricing, time.monotonic() + 300,
                request_limit=8, output_limit=2048, budget_limit=budget_remaining, budget_ledger=all_requests, stop_on_unknown=True,
                serialize_requests=True, min_interval_seconds=args.request_gap_seconds, pacing_state=pacing_state)
        server = Broker(str(root / "broker.sock"), request_handler)
        os.chmod(root / "broker.sock", 0o600)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        started = now()
        try:
            execution = execute(command, root, 60 if args.offline_preflight else 300)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
            (root / "broker.sock").unlink(missing_ok=True)
        for name in ["stdout", "stderr"]:
            text = execution.pop(name).replace(nonce, "[PROXY-TOKEN]")
            if key:
                text = text.replace(key, "[REDACTED]")
            (run_dir / (name + (".jsonl" if name == "stdout" else ".txt"))).write_text(text)
        isolation_ok = bool(execution["witness"]) and all(execution["witness"].get(k) for k in ["project_writable", "public_test_read_only", "hidden_grader_absent", "real_home_hidden"])
        isolation_ok = isolation_ok and execution["witness"].get("net_namespace") != os.readlink("/proc/self/ns/net")
        grading = grade(root / "project", task_id, run_dir / "grader")
        if args.offline_preflight:
            status = "preflight_pass" if isolation_ok and captured and all(r["model"] == MODEL and r["stream"] is True for r in captured) else "preflight_failure"
        elif not isolation_ok:
            status = "infra_error"
        elif execution["timed_out"]:
            status = "timeout"
        elif any(q.get("http_status") != 200 or q.get("error_type") for q in ledger):
            status = "infra_error"
        elif execution["exit_code"] != 0 or not grading["pass"]:
            status = "failure"
        else:
            status = "success"
        safe_config = {}
        for path in [root / "xdg-config/opencode/opencode.json", root / "agent/models.json", root / "codex-home/config.toml"]:
            if path.exists():
                safe_config[str(path.relative_to(root))] = path.read_text().replace(nonce, "[PROXY-TOKEN]")
        write(run_dir / "config.json", safe_config)
        run = {"run_id": run_id, "task_id": task_id, "tool": tool, "spec": spec, "cli": cli,
               "started_at_utc": started, "finished_at_utc": now(), "status": status, "validity": "valid" if status in ["success", "failure", "timeout"] else "pending_review",
               "generation_group": "codex-explicit-none" if tool == "codex" else "capability-reasoning-off-no-forced-wire-value",
               "execution": execution, "isolation_ok": isolation_ok, "grading": grading,
               "provider_requests": ledger, "offline_request_metadata": captured, "retry_of": retry["run_id"] if retry else None}
        write(run_dir / "result.json", run)
        result["runs"].append(run)
        result["plan"][position - 1]["status"] = status
        write(artifact / "result.json", result)
        print(json.dumps({"tool": tool, "task": task_id, "config": config_id, "status": status, "requests": len(ledger) if key else len(captured)}), flush=True)
        if not isolation_ok or status == "preflight_failure":
            result["stop_reason"] = "preflight_or_isolation_failure"
            break
    result["finished_at_utc"] = now()
    result["known_usage_estimated_cost_usd"] = str(known_cost(all_requests))
    result["estimated_total_usd"] = None if pending_cost(all_requests) else str(known_cost(all_requests))
    result["cumulative_known_usage_estimated_cost_usd"] = str(prior_known_cost + known_cost(all_requests))
    result["cumulative_estimated_total_usd"] = None if prior_unknown_count or pending_cost(all_requests) else result["cumulative_known_usage_estimated_cost_usd"]
    if pending_cost(all_requests):
        result["stop_reason"] = "usage_missing"
    result["measured_charge_usd"] = None
    result["all_planned_runs_completed"] = all(p["status"] != "not_run" for p in result["plan"])
    write(artifact / "result.json", result)
    if not args.offline_preflight:
        index = ROOT / "benchmark/runs.csv"
        with index.open(newline="") as handle:
            columns = next(csv.reader(handle))
        with index.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            for position, run in enumerate(result["runs"], 1):
                requests = run["provider_requests"]
                writer.writerow({"run_id": run["run_id"], "task_id": run["task_id"], "tool": run["tool"],
                    "version": run["spec"]["version"], "commit": run["spec"]["commit"], "model": MODEL, "provider": BASE_URL,
                    "config_id": run["spec"]["config_id"], "repetition": 1, "execution_order": position,
                    "started_at_utc": run["started_at_utc"], "duration_ms": run["execution"]["duration_ms"], "status": run["status"],
                    "validity": run["validity"], "cost_usd": "" if pending_cost(requests) else str(known_cost(requests)),
                    "retry_of": run["retry_of"] or "",
                    "usage_source": "provider ledger; user-reported rates; estimate only", "artifact_path": str((artifact / run["run_id"]).relative_to(ROOT)),
                    "notes": "pilot only; fixture v2; full metrics in result.json; not invoice-confirmed"})


if __name__ == "__main__":
    main()
