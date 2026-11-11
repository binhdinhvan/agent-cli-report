"""One-off diagnostic: runtime-only model override; no edits to client/proxy/fixture sources."""
import datetime
import hashlib
import json
import os
import pathlib
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "benchmark"))
import pilot as p
import model_smoke as smoke
from provider_probe import credential

ARTIFACT = pathlib.Path(__file__).resolve().parent
MODEL = "gpt-6.1-sol"
OLD_MODEL = "gpt-6-luna"


def main():
    if (ARTIFACT / "protocol.json").exists():
        raise RuntimeError("Do not overwrite/repeat this diagnostic artifact")
    p.sealed()
    previous_dir = ROOT / "benchmark/artifacts/PILOT-PACED-20261106-02/R-0004"
    previous = json.loads((previous_dir / "result.json").read_text())
    assert previous["tool"] == "pi" and previous["task_id"] == "P-01"
    source_paths = [ROOT / "benchmark/pilot.py", ROOT / "benchmark/pilot_inside.py", ROOT / "demos/model_smoke.py",
                    ROOT / "demos/model_smoke_inside.py", ROOT / "demos/proxy_headers.py"]
    source_hashes = {str(path.relative_to(ROOT)): p.sha256(path) for path in source_paths}
    # In-memory changes only. Wire/config changes only the model ID/name.
    smoke.MODEL = MODEL
    p.MODEL = MODEL
    def unknown_price(usage, pricing):
        return {"usage": usage, "estimated_cost_usd": None,
                "reason": "gpt-6.1-sol pricing unverified; do not reuse gpt-6-luna rates"}
    smoke.estimate = unknown_price
    spec, root, nonce, command, cli = p.prepare(previous["spec"], "C-0039", "P-01")
    safe_config = (root / "agent/models.json").read_text().replace(nonce, "[PROXY-TOKEN]")
    original_config = json.loads((previous_dir / "config.json").read_text())["agent/models.json"]
    config_equal = json.loads(safe_config.replace(MODEL, OLD_MODEL)) == json.loads(original_config)
    cli_equal = [arg.replace("C-0039", "C-0038").replace(MODEL, OLD_MODEL) for arg in cli] == previous["cli"]
    assert config_equal and cli_equal
    protocol = {"comparison_id": "MODEL-COMPARE-01", "mode": "diagnostic, not pilot or benchmark result",
        "started_at_utc": p.now(), "comparison_against": "R-0004", "tool": "pi", "task_id": "P-01",
        "model": MODEL, "previous_model": OLD_MODEL, "provider": smoke.BASE_URL, "config_id": "C-0039",
        "model_catalog_artifact": "benchmark/artifacts/MODEL-COMPARE-CATALOG-20261106-01/result.json",
        "native_config_equal_except_model": config_equal, "cli_equal_except_model_and_new_runtime": cli_equal,
        "prompt": cli[-1], "prompt_sha256": p.sha256(ROOT / "benchmark/tasks/P-01/prompt.txt"),
        "fixture_seal_sha256": p.sha256(p.SEAL), "source_sha256": source_hashes, "diagnostic_script_sha256": p.sha256(pathlib.Path(__file__)),
        "request_cap": 8, "max_output_tokens_requested_cap": 2048, "timeout_seconds": 300,
        "request_gap_seconds_after_response": 30,
        "pricing_status": "Unknown for new model; user explicitly requested one bounded test after pricing warning",
        "estimated_cost_usd": None, "measured_charge_usd": None,
        "budget_limit_note": "Existing USD guard cannot be calculated for new model without its rates; request/token/time bounds only, no account top-up",
        "safety": "No source/client/proxy fixes, no existing configs changed, only a fresh synthetic task workspace; no other pilot slots",
        "scope_note": "New model has native model-dependent behavior; one fresh session cannot establish provider-wide reliability"}
    p.write(ARTIFACT / "protocol.json", protocol)
    p.write(ARTIFACT / "config.json", {"agent/models.json": safe_config})
    key = credential()
    ledger = []
    base = smoke.handler(key, nonce, ledger, threading.Lock(), {}, time.monotonic() + 300,
        request_limit=8, output_limit=2048, budget_limit="1", serialize_requests=True,
        min_interval_seconds=30, stop_on_unknown=False)
    class DiagnosticHandler(base):
        def handle_post(self):
            # Unknown prices are not zero; permit the explicitly requested bounded diagnostic,
            # but never forward another request after an upstream error or missing usage.
            for request in ledger:
                usage = request.get("cost", {}).get("usage") or {}
                details = usage.get("input_tokens_details") or {}
                values = [usage.get("input_tokens"), usage.get("output_tokens"), details.get("cached_tokens")]
                if request.get("http_status") != 200 or request.get("terminal_type") != "response.completed" or not all(type(v) is int and v >= 0 for v in values):
                    self.send_error(400, "Diagnostic stopped after upstream error or missing usage; no further provider requests")
                    return
            super().handle_post()
    server = p.Broker(str(root / "broker.sock"), DiagnosticHandler)
    os.chmod(root / "broker.sock", 0o600)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        execution = p.execute(command, root, 300)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        (root / "broker.sock").unlink(missing_ok=True)
    for name in ["stdout", "stderr"]:
        (ARTIFACT / (name + (".jsonl" if name == "stdout" else ".txt"))).write_text(
            execution.pop(name).replace(key, "[REDACTED]").replace(nonce, "[PROXY-TOKEN]"))
    grading = p.grade(root / "project", "P-01", ARTIFACT / "grader")
    events = []
    for line in (ARTIFACT / "stdout.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    assistant_ends = [e["message"] for e in events if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant"]
    final_stop_reason = assistant_ends[-1].get("stopReason") if assistant_ends else None
    gaps = [(datetime.datetime.fromisoformat(b["started_at_utc"]) - datetime.datetime.fromisoformat(a["finished_at_utc"])).total_seconds()
            for a, b in zip(ledger, ledger[1:]) if a.get("finished_at_utc") and b.get("started_at_utc")]
    encrypted_error = any("encrypted conversation context could not be validated" in r.get("error_body_excerpt", "").lower() for r in ledger)
    upstream_error = any(r.get("http_status") != 200 or r.get("error_type") for r in ledger)
    result = {**protocol, "finished_at_utc": p.now(), "spec": spec, "cli": cli, "execution": execution,
        "provider_requests": ledger, "grading": grading, "observed_gaps_seconds": gaps,
        "final_stop_reason": final_stop_reason,
        "encrypted_context_error_observed": encrypted_error, "upstream_error_observed": upstream_error,
        "task_completed": execution["exit_code"] == 0 and not execution["timed_out"] and grading["pass"] and not upstream_error and final_stop_reason == "stop",
        "source_code_unchanged": all(p.sha256(ROOT / path) == digest for path, digest in source_hashes.items()),
        "supervisor_absent": not pathlib.Path("/proc", str(execution["supervisor_host_pid"])).exists(),
        "broker_socket_absent": not (root / "broker.sock").exists()}
    encoded = json.dumps(result, ensure_ascii=False, indent=2).replace(key, "[REDACTED]")
    (ARTIFACT / "result.json").write_text(encoded + "\n")
    assert result["source_code_unchanged"]
    assert all(key.encode() not in path.read_bytes() for path in ARTIFACT.rglob("*") if path.is_file())
    print(json.dumps({"model": MODEL, "requests": len(ledger), "http_statuses": [r.get("http_status") for r in ledger],
        "encrypted_context_error_observed": encrypted_error, "task_completed": result["task_completed"],
        "timed_out": execution["timed_out"], "source_code_unchanged": True, "estimated_cost_usd": None}, indent=2))


if __name__ == "__main__":
    main()
