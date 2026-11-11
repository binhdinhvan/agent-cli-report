"""Verify saved native LOCAL preflight without invoking a CLI/provider or reading keys."""
import argparse
import csv
import json
import pathlib

from suite48_native import ROOT, SUITE, ORDER, SEAL, digest, isolated, slot_mapping
from verify_suite48 import verify as verify_fixtures
from plan48 import build as planned_outputs


def verify(artifact):
    artifact = pathlib.Path(artifact).resolve()
    if not artifact.is_relative_to(SUITE / "artifacts"):
        raise ValueError("Expected suite48 artifact directory")
    data = json.loads((artifact / "result.json").read_text())
    if (data["mode"] != "offline-native-synthetic-preflight" or data["status"] != "pass"
            or data["provider_requests"] != 0 or data["paid_runs_authorized"]
            or not data["synthetic_usage_not_real_cost"]):
        raise ValueError("Only successful LOCAL native preflight is accepted")
    verify_fixtures(SEAL)
    draft = SUITE / "artifacts/DRAFT48-20261109-01"
    for name, output in planned_outputs().items():
        if (draft / name).read_text() != output:
            raise ValueError("Draft48 order/planning drift")
    for name, expected in data["source_sha256"].items():
        if digest(ROOT / name) != expected or digest(artifact / "source" / name) != expected:
            raise ValueError("Native source/snapshot drift: " + name)
    for name, expected in data["artifact_sha256"].items():
        if digest(artifact / name) != expected:
            raise ValueError("Native artifact drift: " + name)
    inventory = {str(path.relative_to(artifact)) for path in artifact.rglob("*") if path.is_file()}
    if inventory != set(data["artifact_sha256"]) | {"result.json"}:
        raise ValueError("Native artifact inventory drift")
    with ORDER.open() as stream:
        selected = [row for row in slot_mapping(csv.DictReader(stream)) if row["repetition"] == "1"]
    if [r["slot"] for r in data["runs"]] != [r["slot"] for r in selected] or len(data["runs"]) != 16:
        raise ValueError("Expected complete round1 preflight in frozen order, not selected successes")
    for run, row in zip(data["runs"], selected):
        execution = run["execution"]
        if any(run[key] != row[key] for key in ("tool", "task_id", "slot")):
            raise ValueError("Slot/task/CLI mapping mismatch")
        if (run["status"] != "offline_preflight_pass" or run["provider_requests"] != 0 or run["paid_run_id"] is not None
                or not run["config_id"].startswith("OF48-") or not run["isolation_ok"] or not isolated(execution)):
            raise ValueError("Invalid offline native status/isolation/ID mapping")
        if execution["exit_code"] != 0 or execution["timed_out"] or execution["output_limit_exceeded"]:
            raise ValueError("Native CLI did not finish normally")
        clock = execution["native_clock"]
        if not (execution["outer_started_monotonic"] <= clock["started_monotonic"] <= clock["finished_monotonic"] <= execution["outer_finished_monotonic"]):
            raise ValueError("Native/outer monotonic duration boundaries mismatch")
        if not all(run["event_acceptance"].values()) or not run["grading"]["pass"]:
            raise ValueError("Missing native tool/final/grading acceptance")
        folder = artifact / run["slot"]
        if json.loads((folder / "grader/grading.json").read_text()) != run["grading"]:
            raise ValueError("Duplicated grading record differs")
        prompt = (SUITE / run["task_id"] / "prompt.txt").read_text()
        if run["cli"][-1] != prompt:
            raise ValueError("Native prompt bytes differ from task")
        ledger = run["synthetic_ledger"]
        if len(ledger) != run["synthetic_calls"] or not 1 <= len(ledger) <= 8:
            raise ValueError("Synthetic request count mismatch/cap")
        for q in ledger:
            if (q["http_status"] != 200 or q["terminal_type"] != "response.completed"
                    or q["effective_max_output_tokens"] > 2048 or q["min_interval_seconds"] != 30
                    or q["minimum_request_window_seconds"] != 60 or q["deadline_remaining_seconds_at_dispatch"] < 60
                    or q["cost"]["estimated_cost_usd"] is None):
                raise ValueError("Synthetic broker policy/usage failed")
        if not run["broker_socket_absent"] or not run["supervisor_pid_absent"]:
            raise ValueError("Native cleanup failed at capture time")
    if data["synthetic_calls"] != sum(r["synthetic_calls"] for r in data["runs"]):
        raise ValueError("Synthetic batch ledger mismatch")
    return {"status": "pass", "native_task_cli_pairs": 16, "synthetic_calls": data["synthetic_calls"],
        "provider_requests": 0, "paid_runs_authorized": False,
        "limitations": ["Synthetic reference injection is not model solving or provider compatibility acceptance",
            "Virtual30s pacing tests policy arithmetic, not real wall gaps",
            "Outer launcher and exact native subprocess durations kept separately; final protocol must choose primary boundary",
            "R/C allocation, paid budget and final protocol approval still pending; no paid entrypoint here"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.artifact_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
