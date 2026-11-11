"""Suite48 orchestrator: offline acceptance by default; paid dispatch needs a pinned explicit authorization."""
import argparse
import contextlib
import copy
import csv
import fcntl
import json
import os
import pathlib
import platform
import re
import secrets
import selectors
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from decimal import Decimal
from unittest.mock import patch

import suite48_native as native
from suite48_runtime import ROOT, SUITE, digest, grade, task_spec
from verify_native48 import verify as native_verified

PROTOCOL = ROOT / "benchmark/PROTOCOL_48_R1.md"
STATE = ROOT / "research/experiment-state.json"
BUDGET = Decimal("16")


def resource_identity():
    return {"platform": platform.platform(), "cpu_count": os.cpu_count(),
        "cpu_model": next((line.split(":", 1)[1].strip() for line in pathlib.Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), None),
        "mem_total": pathlib.Path("/proc/meminfo").read_text().splitlines()[0],
        "cgroup": {name: (pathlib.Path("/sys/fs/cgroup") / name).read_text().strip()
            if (pathlib.Path("/sys/fs/cgroup") / name).exists() else None for name in ("cpu.max", "memory.max", "pids.max")},
        "cpu_exclusivity": "uncontrolled; background load not fixed"}


def inputs():
    native_verified(SUITE / "artifacts/NATIVE48-20261110-02")
    files = [PROTOCOL, pathlib.Path(__file__), ROOT / "benchmark/test_batch48.py",
        ROOT / "benchmark/verify_native48.py", ROOT / "benchmark/suite48_native.py",
        ROOT / "benchmark/suite48_native_inside.py", native.ORDER, native.SEAL / "preparation.json",
        ROOT / "research/provider-pricing.json", ROOT / "demos/provider_probe.py",
        ROOT / "demos/estimate_provider_cost.py", ROOT / "benchmark/artifacts/PILOT-FREEZE-20261109-01/baseline.json",
        SUITE / "artifacts/NATIVE48-20261110-02/result.json"]
    # Bind all transitive implementation/fixture/config-builder inputs already verified.
    seal = json.loads((native.SEAL / "preparation.json").read_text())
    files += [ROOT / name for name in seal["files_sha256"]]
    previous = json.loads((SUITE / "artifacts/NATIVE48-20261110-02/result.json").read_text())
    files += [ROOT / name for name in previous["source_sha256"]]
    baseline = json.loads((ROOT / "benchmark/artifacts/PILOT-FREEZE-20261109-01/baseline.json").read_text())
    for name, expected in baseline["input_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("Frozen baseline input drift: " + name)
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(set(files))}


def make_plan():
    with native.ORDER.open() as stream:
        slots = native.slot_mapping(csv.DictReader(stream))
    state = json.loads(STATE.read_text())
    return {"revision": "benchmark48-orchestrator-r1", "status": "candidate_not_launch_authorization",
        "launch_authorized": False, "budget_estimate_usd": "16", "invoice_cap": False,
        "protocol": str(PROTOCOL.relative_to(ROOT)), "protocol_sha256": digest(PROTOCOL),
        "input_sha256": inputs(), "resource_identity": resource_identity(),
        "model": native.MODEL, "provider": native.BASE_URL, "timing": native.timing_policy("paced-900"),
        "primary_duration": "outer bwrap spawn through launcher/bridge exit; broker deadline same monotonic origin",
        "native_duration": "secondary, inside wrapper subprocess clock",
        "slots": slots, "run_ids_reserved": False,
        "proposed_run_start": state["next_pilot_run_start"], "proposed_config_start": state["next_pilot_config_start"],
        "historical_pilot_cost_not_in_new_budget": {"known_usd": "1.10640264", "unpriced_requests": 6, "total_usd": None}}


def validate_plan(plan):
    current = make_plan()
    if plan != current:
        raise ValueError("Plan/source/order/resource/registry drift: re-plan and review; no credential read")


def validate_approval(plan_path, approval):
    plan_path = pathlib.Path(plan_path).resolve()
    if not plan_path.is_relative_to(SUITE / "artifacts"):
        raise ValueError("Plan must be a local suite48 artifact")
    plan = json.loads(plan_path.read_text())
    validate_plan(plan)
    if (approval.get("launch_authorized") is not True or approval.get("plan_sha256") != digest(plan_path)
            or approval.get("budget_estimate_usd") != "16" or not approval.get("approved_by")
            or not approval.get("approved_at_utc") or approval.get("scope") != "48-first-attempt-slots-no-auto-retry"):
        raise PermissionError("Explicit launch approval bound to this plan/budget/scope is required")
    return plan


def reserve(plan, artifact):
    """Caller holds batch lock, after approval/hash gates. Reserve even not_run IDs; never rewind."""
    state = json.loads(STATE.read_text())
    if state.get("benchmark48_paid_batches"):
        raise PermissionError("Paid batch already reserved; continuation/retry needs separate reviewed protocol")
    if (state["next_pilot_run_start"], state["next_pilot_config_start"]) != (plan["proposed_run_start"], plan["proposed_config_start"]):
        raise ValueError("Registry moved")
    rows = []
    for offset, slot in enumerate(plan["slots"]):
        row = {**slot, "run_id": f"R-{plan['proposed_run_start'] + offset:04d}",
            "config_id": f"C-{plan['proposed_config_start'] + offset:04d}", "status": "not_run"}
        if (native.RUNTIME / row["config_id"]).exists() or row["config_id"] in state.get("retired_config_ids", []):
            raise ValueError("Runtime/config ID collision")
        for index in (ROOT / "benchmark/runs.csv", ROOT / "benchmark/runs-search-r2.csv", ROOT / "benchmark/runs-benchmark48.csv"):
            if index.exists():
                with index.open() as stream:
                    if any(old.get("run_id") == row["run_id"] for old in csv.DictReader(stream)):
                        raise ValueError("Run ID already indexed")
        rows.append(row)
    state["next_pilot_run_start"] += len(rows)
    state["next_pilot_config_start"] += len(rows)
    state["benchmark48_paid_batches"] = [{"artifact": str(artifact.relative_to(ROOT)), "reserved": rows,
        "status": "reserved_before_dispatch", "budget_estimate_usd": "16"}]
    temporary = STATE.with_suffix(".json.batch48-tmp")
    with temporary.open("x") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, STATE)
    return rows


def prepare(spec, config_id, task_id, *, paid=False):
    if not re.fullmatch(r"C-\d{4,}" if paid else r"BP48-[A-Za-z0-9-]+", config_id):
        raise ValueError("Wrong paid/offline config namespace")
    spec = copy.deepcopy(spec)
    spec.update(config_id=config_id, runtime_root=str(native.RUNTIME / config_id), environment_revision="search-r2")
    root = pathlib.Path(spec["runtime_root"])
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    for directory in ("home", "tmp", "xdg-config", "xdg-data", "xdg-cache", "xdg-state", "managed", "agent", "sessions", "codex-home"):
        (root / directory).mkdir()
    task = SUITE / task_id
    shutil.copytree(task / "fixture", root / "project")
    immutable = sorted(str(path.relative_to(task / "fixture")) for path in (task / "fixture").rglob("*")
        if path.is_file() and str(path.relative_to(task / "fixture")) not in task_spec(task_id)["allowed_changes"])
    native.write(root / "immutable.json", immutable)
    copies = {"inside.py": ROOT / "demos/model_smoke_inside.py", "proxy_headers.py": ROOT / "demos/proxy_headers.py",
        "suite48_native_inside.py": ROOT / "benchmark/suite48_native_inside.py"}
    for name, source in copies.items():
        (root / name).write_bytes(source.read_bytes())
    nonce = secrets.token_hex(24)
    args = native.pilot_config(spec, root, nonce, (task / "prompt.txt").read_text())
    command, binary, _ = native.profile(spec)
    for name in [*copies, "immutable.json", *("project/" + name for name in immutable)]:
        command += ["--ro-bind", str(root / name), str(root / name)]
    command += ["--setenv", "SMOKE_PROXY_TOKEN", nonce, "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        "/usr/bin/python3", "-B", str(root / "suite48_native_inside.py"), str(root / "broker.sock"), json.dumps([binary, *args])]
    return spec, root, nonce, command, [binary, *args]


def execute(command, root, window, *, timeout=900):
    """Single monotonic origin sets both outer watchdog and broker deadline before spawn."""
    start = time.monotonic()
    window.update(origin=start, deadline=start + timeout, broker_deadline=start + 900)
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
            remaining = window["deadline"] - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            for key, _ in selector.select(min(remaining, 0.25)):
                data = os.read(key.fileobj.fileno(), 65536)
                if not data:
                    selector.unregister(key.fileobj)
                else:
                    streams[key.fileobj].extend(data)
                    if sum(map(len, streams.values())) > 16 * 1024 * 1024:
                        overflow = True
                        break
            if overflow:
                break
        if timed_out or overflow:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        selector.close()
        for stream in streams:
            stream.close()
    end = time.monotonic()
    return {"supervisor_host_pid": process.pid, "exit_code": process.returncode, "timed_out": timed_out,
        "output_limit_exceeded": overflow, "duration_ms": round((end - start) * 1000),
        "outer_started_monotonic": start, "outer_finished_monotonic": end, "broker_deadline_monotonic": window["broker_deadline"],
        "outer_watchdog_deadline_monotonic": window["deadline"],
        "native_clock": json.loads((root / "native-clock.json").read_text()) if (root / "native-clock.json").exists() else None,
        "witness": json.loads((root / "native-witness.json").read_text()) if (root / "native-witness.json").exists() else None,
        "stdout": bytes(streams[process.stdout]).decode(errors="replace"), "stderr": bytes(streams[process.stderr]).decode(errors="replace")}


def outcome(execution, grading, ledger, pacing):
    reasons = []
    if pacing.stop_reason:
        reasons.append(pacing.stop_reason)
    provider_bad = not ledger or any(q.get("http_status") != 200 or q.get("terminal_type") != "response.completed" or q.get("error_type") for q in ledger)
    missing = any(q.get("cost", {}).get("estimated_cost_usd") is None for q in ledger)
    if missing:
        reasons.append("usage_missing")
    if execution["output_limit_exceeded"] or not native.isolated(execution):
        return "infra_error", "pending_review", reasons + ["output_or_isolation"]
    # A timing-only local rejection may have no upstream at all; not a provider error.
    timing_only = pacing.stop_reason == "time_window_exhausted" and not missing and all(
        q.get("http_status") == 200 and q.get("terminal_type") == "response.completed" and not q.get("error_type") for q in ledger)
    if timing_only:
        return "timeout", "valid", reasons
    if not ledger and execution["timed_out"]:
        return "timeout", "valid", reasons + ["wall_cap_no_upstream"]
    if provider_bad or missing or pacing.stop_reason == "provider_failure":
        return "infra_error", "pending_review", reasons + ["provider_or_usage"]
    if execution["timed_out"]:
        return "timeout", "valid", reasons + ["wall_cap"]
    error_event = False
    for line in execution.get("stdout", "").splitlines():
        try:
            event = json.loads(line)
            error_event |= event.get("type") in ("error", "turn.failed") or bool(event.get("message", {}).get("errorMessage"))
        except (json.JSONDecodeError, AttributeError):
            pass
    if execution["exit_code"] != 0 or not grading["pass"] or error_event:
        return "failure", "valid", reasons + (["native_error_event"] if error_event else [])
    return "success", "valid", reasons


def ledger_cost(ledger):
    costs = [q.get("cost", {}).get("estimated_cost_usd") for q in ledger]
    return sum((Decimal(c) for c in costs if c is not None), Decimal(0)), sum(c is None for c in costs)


def check_dispatch_inputs(expected, resources):
    if expected is not None:
        for name, wanted in expected.items():
            if digest(ROOT / name) != wanted:
                raise ValueError("Input drift before/after slot: " + name)
    if resources is not None and resource_identity() != resources:
        raise ValueError("Host resource identity drift; batch must pause")


def run_batch(artifact, rows, *, paid=False, key=None, input_hashes=None, resources=None):
    """Internal dispatcher; CLI paid path must pass approval/lock/reservation first."""
    if paid and not key:
        raise PermissionError("Paid dispatch requires a credential loaded after authorization gates")
    if paid and (not input_hashes or not resources):
        raise PermissionError("Paid dispatch requires pinned per-slot input/resource gates")
    specs = {spec["tool"]: spec for spec in json.loads((ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())["releases"]}
    pricing = json.loads((ROOT / "research/provider-pricing.json").read_text())
    virtual = None if paid else native.VirtualPacing()
    pacing = native.PacingState() if paid else native.PacingState(clock=virtual.clock, sleep=virtual.sleep)
    all_requests = []
    result = {"mode": "benchmark48" if paid else "offline-batch48-synthetic", "started_at_utc": native.now(),
        "budget_estimate_usd": "16", "measured_charge_usd": None, "synthetic_usage": not paid,
        "provider_requests": 0, "plan": [{**row, "status": "not_run"} for row in rows], "runs": []}
    native.write(artifact / "result.json", result)
    for position, row in enumerate(rows):
        known, missing = ledger_cost(all_requests)
        if missing or known >= BUDGET or pacing.stop_reason:
            result["stop_reason"] = pacing.stop_reason or ("usage_missing" if missing else "estimate_guard")
            break
        dest = artifact / row["slot"]
        dest.mkdir()
        config_id = row["config_id"] if paid else "BP48-" + artifact.name + "-" + row["slot"]
        ledger, window, execution = [], {}, None
        try:
            check_dispatch_inputs(input_hashes, resources)
            spec, root, nonce, command, cli = prepare(specs[row["tool"]], config_id, row["task_id"], paid=paid)
            fake = None if paid else native.SyntheticProvider(row["tool"], row["task_id"])

            def factory(*args, **kwargs):
                if "deadline" not in window:
                    raise RuntimeError("No dispatch before monotonic run origin")
                deadline = window["broker_deadline"] if paid else window["broker_deadline"] + window["virtual_offset_at_origin"]
                cls = native.handler(key if paid else "OFFLINE-INERT-NO-PROVIDER-KEY", nonce, ledger, threading.Lock(), pricing, deadline,
                    request_limit=8, output_limit=2048, budget_limit="16", budget_ledger=all_requests, stop_on_unknown=True,
                    serialize_requests=True, min_interval_seconds=30, pacing_state=pacing, stop_on_provider_failure=True,
                    minimum_request_window_seconds=60)
                return cls(*args, **kwargs)

            server = native.Broker(str(root / "broker.sock"), factory)
            os.chmod(root / "broker.sock", 0o600)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                with contextlib.ExitStack() as stack:
                    if not paid:
                        stack.enter_context(patch.object(native.model_smoke.urllib.request, "build_opener", return_value=fake))
                        stack.enter_context(patch.object(socket, "create_connection", side_effect=AssertionError("Offline batch forbids TCP egress")))
                    window["virtual_offset_at_origin"] = 0 if paid else virtual.offset
                    execution = execute(command, root, window, timeout=900 if paid else 90)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                (root / "broker.sock").unlink(missing_ok=True)
            native_stdout = execution["stdout"]
            for name in ("stdout", "stderr"):
                text = execution.pop(name).replace(nonce, "[LOCAL-PROXY-TOKEN]")
                if key:
                    text = text.replace(key, "[REDACTED]")
                (dest / (name + (".jsonl" if name == "stdout" else ".txt"))).write_text(text)
            native.write(dest / "execution.json", execution)
            grading = grade(root / "project", row["task_id"], dest / "grader")
            check_dispatch_inputs(input_hashes, resources)
            if digest(pathlib.Path(spec["binary"])) != spec["binary_sha256"]:
                raise ValueError("Binary changed during attempt")
            native.environment_profile("search-r2")
            status, validity, reasons = outcome({**execution, "stdout": native_stdout}, grading, ledger, pacing)
            preflight_events = native.event_acceptance(row["tool"], native_stdout) if not paid else None
            if not paid and not all(preflight_events.values()):
                status, validity, reasons = "infra_error", "pending_review", reasons + ["synthetic_marker_missing"]
            config = {}
            for name in ("xdg-config/opencode/opencode.json", "agent/models.json", "codex-home/config.toml"):
                if (root / name).exists():
                    config[name] = (root / name).read_text().replace(nonce, "[LOCAL-PROXY-TOKEN]")
            native.write(dest / "config.json", config)
            if fake:
                native.write(dest / "synthetic-payloads.json", fake.captures)
            record = {**row, "config_id": config_id, "run_id": row.get("run_id") if paid else None,
                "spec": spec, "cli": cli, "status": status, "validity": validity, "reasons": reasons,
                "execution": execution, "grading": grading, "requests": ledger, "synthetic_usage": not paid,
                "preflight_events": preflight_events, "provider_requests": len(ledger) if paid else 0,
                "supervisor_pid_absent": not pathlib.Path("/proc", str(execution["supervisor_host_pid"])).exists(),
                "broker_socket_absent": not (root / "broker.sock").exists()}
        except Exception as error:
            record = {**row, "status": "infra_error", "validity": "pending_review", "error_type": type(error).__name__,
                "reasons": ["supervisor_prepare_execute_or_grader_exception"], "requests": ledger,
                "execution": execution, "provider_requests": len(ledger) if paid else 0, "synthetic_usage": not paid}
        native.write(dest / "result.json", record)
        if paid:
            index = ROOT / "benchmark/runs-benchmark48.csv"
            columns = ["run_id", "slot", "task_id", "tool", "config_id", "repetition", "status", "validity", "duration_ms", "known_estimated_cost_usd", "unpriced_requests", "artifact_path"]
            exists = index.exists()
            with index.open("a", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                if not exists:
                    writer.writeheader()
                known_run, unknown_run = ledger_cost(ledger)
                writer.writerow({**{name: record.get(name, "") for name in columns[:8]},
                    "duration_ms": (record.get("execution") or {}).get("duration_ms", ""),
                    "known_estimated_cost_usd": str(known_run), "unpriced_requests": unknown_run,
                    "artifact_path": str(dest.relative_to(ROOT))})
        result["runs"].append(record)
        result["plan"][position]["status"] = record["status"]
        native.write(artifact / "result.json", result)
        print(json.dumps({k: record.get(k) for k in ("slot", "tool", "task_id", "status", "validity", "provider_requests")}), flush=True)
        if record["status"] == "infra_error":
            result["stop_reason"] = "infra_error_no_automatic_retry"
            break
    known, missing = ledger_cost(all_requests)
    result.update(finished_at_utc=native.now(), provider_requests=len(all_requests) if paid else 0,
        synthetic_exchanges=0 if paid else len(all_requests), known_usage_estimate_usd=str(known),
        unpriced_requests=missing, estimated_total_usd=None if missing else str(known),
        all_slots_executed=all(row["status"] != "not_run" for row in result["plan"]))
    if missing or known >= BUDGET or pacing.stop_reason:
        result.setdefault("stop_reason", pacing.stop_reason or ("usage_missing" if missing else "estimate_guard"))
    native.write(artifact / "result.json", result)
    return result


def load_credential():
    # Imported only after the paid CLI's authorization/hash/lock/registry gates.
    from provider_probe import credential
    return credential()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-plan", action="store_true")
    mode.add_argument("--offline-check", action="store_true")
    mode.add_argument("--paid", action="store_true")
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--plan", type=pathlib.Path)
    parser.add_argument("--approval", type=pathlib.Path)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / "artifacts") or not re.fullmatch(r"[A-Za-z0-9-]+", artifact.name):
        parser.error("Expected fresh suite48 artifact path with safe namespace")
    if args.paid:
        if not args.plan or not args.approval:
            parser.error("Paid requires explicit --plan and --approval; no credential read")
        approval = json.loads(args.approval.read_text())
        plan = validate_approval(args.plan, approval)
        lock_path = ROOT / "research/.batch48-launch.lock"
        with lock_path.open("a") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            validate_approval(args.plan, approval)
            artifact.mkdir(parents=True, exist_ok=False)
            rows = reserve(plan, artifact)
            native.write(artifact / "plan.json", plan)
            native.write(artifact / "approval.json", approval)
            native.write(artifact / "reserved.json", rows)
            key = load_credential()
            run_batch(artifact, rows, paid=True, key=key, input_hashes=plan["input_sha256"], resources=plan["resource_identity"])
    elif args.prepare_plan:
        plan = make_plan()
        artifact.mkdir(parents=True, exist_ok=False)
        native.write(artifact / "launch-plan.json", plan)
        native.write(artifact / "approval-template.json", {"launch_authorized": False,
            "plan_sha256": digest(artifact / "launch-plan.json"), "budget_estimate_usd": "16",
            "scope": "48-first-attempt-slots-no-auto-retry", "approved_by": None, "approved_at_utc": None})
        print("Created launch candidate + DISABLED approval template; no IDs reserved or credential read")
    else:
        plan = make_plan()
        artifact.mkdir(parents=True, exist_ok=False)
        native.write(artifact / "plan.json", plan)
        result = run_batch(artifact, [row for row in plan["slots"] if row["repetition"] == "1"],
            input_hashes=plan["input_sha256"], resources=plan["resource_identity"])
        if not result["all_slots_executed"] or any(r["status"] != "success" for r in result["runs"]):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
