"""Verify saved offline batch orchestration + disabled launch candidate; never dispatch."""
import argparse
import json
import pathlib

import batch48 as batch


def verify(artifact, candidate):
    artifact, candidate = pathlib.Path(artifact).resolve(), pathlib.Path(candidate).resolve()
    if not all(path.is_relative_to(batch.SUITE / "artifacts") for path in (artifact, candidate)):
        raise ValueError("Expected local suite48 artifacts")
    plan_path = candidate / "launch-plan.json"
    plan = json.loads(plan_path.read_text())
    batch.validate_plan(plan)
    disabled = json.loads((candidate / "approval-template.json").read_text())
    if disabled["launch_authorized"] is not False or disabled["plan_sha256"] != batch.digest(plan_path):
        raise ValueError("Candidate approval must remain explicitly DISABLED")
    result = json.loads((artifact / "result.json").read_text())
    if result["mode"] != "offline-batch48-synthetic" or not result["synthetic_usage"] or result["provider_requests"] != 0:
        raise ValueError("Only offline orchestration evidence accepted")
    expected = [row for row in plan["slots"] if row["repetition"] == "1"]
    if [r["slot"] for r in result["runs"]] != [r["slot"] for r in expected] or not result["all_slots_executed"]:
        raise ValueError("Expected full16case round1 orchestration acceptance")
    for record, row in zip(result["runs"], expected):
        if any(record[name] != row[name] for name in ("slot", "tool", "task_id")):
            raise ValueError("Slot mapping mismatch")
        if (record["status"] != "success" or not record["synthetic_usage"] or record["provider_requests"] != 0
                or record["run_id"] is not None or not record["config_id"].startswith("BP48-")):
            raise ValueError("Wrong offline status/namespace")
        execution = record["execution"]
        if execution["broker_deadline_monotonic"] != execution["outer_started_monotonic"] + 900:
            raise ValueError("Broker deadline and primary wall origin differ")
        native_clock = execution["native_clock"]
        if not (execution["outer_started_monotonic"] <= native_clock["started_monotonic"] <= native_clock["finished_monotonic"] <= execution["outer_finished_monotonic"]):
            raise ValueError("Native secondary clock not within outer primary")
        if not batch.native.isolated(execution) or not record["grading"]["pass"] or not all(record["preflight_events"].values()):
            raise ValueError("Isolation/grade/native tool marker acceptance failed")
        folder = artifact / row["slot"]
        if json.loads((folder / "grader/grading.json").read_text()) != record["grading"]:
            raise ValueError("Grading record differs")
        if not record["supervisor_pid_absent"] or not record["broker_socket_absent"]:
            raise ValueError("Cleanup failed at capture")
        for request in record["requests"]:
            if (request["terminal_type"] != "response.completed" or request["effective_max_output_tokens"] > 2048
                    or request["minimum_request_window_seconds"] != 60 or request["cost"]["estimated_cost_usd"] is None):
                raise ValueError("Synthetic ledger policy/usage mismatch")
    if result["synthetic_exchanges"] != sum(len(r["requests"]) for r in result["runs"]):
        raise ValueError("Batch synthetic ledger mismatch")
    return {"status": "pass", "offline_native_cases": 16, "synthetic_exchanges": result["synthetic_exchanges"],
        "provider_requests": 0, "approval_template_enabled": False, "run_ids_reserved": False,
        "plan_sha256": batch.digest(plan_path), "protocol_sha256": plan["protocol_sha256"],
        "note": "No paid requests or model task-solving evidence; virtual pacing, disabled launch approval"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--candidate", type=pathlib.Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.artifact_dir, args.candidate), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
