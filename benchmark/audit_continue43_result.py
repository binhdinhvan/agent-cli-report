"""Offline audit fourth benchmark batch; no API, key or retry."""
from datetime import datetime
from decimal import Decimal
import csv
import json
import pathlib
import re
import subprocess

import continue43 as stage

ART = stage.SUITE / "artifacts/BENCH43-CONTINUE-20261110-01"
OUT = stage.ROOT / "research/artifacts/CONTINUE43-REVIEW-20261110-01"


def main():
    result = json.loads((ART / "result.json").read_text())
    plan = json.loads((ART / "plan.json").read_text())
    stage.cont.batch.check_dispatch_inputs(plan["input_sha256"], plan["resource_identity"])
    stage.predecessors()
    runs = result["runs"]
    assert [r["run_id"] for r in runs] == ["R-0179", "R-0180"]
    assert runs[0]["status"] == "success" and runs[0]["grading"]["pass"]
    assert runs[0]["grading"]["changed_files"] == ["pagination.py"]
    assert all(runs[0]["grading"]["suites"][name]["exit_code"] == 0 for name in ("public", "hidden"))
    assert runs[1]["status"] == "infra_error" and runs[1]["validity"] == "pending_review"
    assert runs[1]["grading"]["changed_files"] == [] and not any("retry_of" in r for r in runs)
    assert len(result["plan"]) == 43 and sum(r["status"] == "not_run" for r in result["plan"]) == 41
    ledger = [q for r in runs for q in r["requests"]]
    assert len(ledger) == result["provider_requests"] == 6
    known, missing = stage.cont.batch.ledger_cost(ledger)
    assert known == Decimal("0.03299880") and missing == 1
    assert str(known) == result["known_usage_estimate_usd"]
    assert result["benchmark_known_cumulative_usd"] == "0.28485816"
    assert result["estimated_total_usd"] is None and result["benchmark_estimated_total_usd"] is None
    assert all(q.get("http_status") == 200 and q.get("terminal_type") == "response.completed" for q in ledger[:5])
    last = ledger[-1]
    assert last["error_type"] == "TimeoutError"
    assert all(key not in last for key in ("http_status", "terminal_type", "cost", "finished_at_utc"))
    gaps = [(datetime.fromisoformat(b["started_at_utc"]) - datetime.fromisoformat(a["finished_at_utc"])).total_seconds()
            for a, b in zip(ledger, ledger[1:])]
    assert len(gaps) == 5 and min(gaps) >= 30
    previous = json.loads((stage.PRIOR / "result.json").read_text())
    cross_batch_gap = (datetime.fromisoformat(ledger[0]["started_at_utc"]) - datetime.fromisoformat(previous["finished_at_utc"])).total_seconds()
    assert cross_batch_gap >= 30
    cleanup, durations = {}, {}
    for record in runs:
        execution = record["execution"]
        assert not execution["timed_out"] and not execution["output_limit_exceeded"]
        assert stage.cont.batch.native.isolated(execution) and record["grading"]["scope_ok"]
        assert execution["broker_deadline_monotonic"] == execution["outer_started_monotonic"] + 900
        assert not pathlib.Path("/proc", str(execution["supervisor_host_pid"])).exists()
        assert not (pathlib.Path(record["spec"]["runtime_root"]) / "broker.sock").exists()
        cleanup[record["run_id"]] = "supervisorPID/socket absent; isolation witness pass"
        durations[record["run_id"]] = execution["duration_ms"]
    assert all(not (stage.cont.batch.native.RUNTIME / row["config_id"]).exists() for row in result["plan"][2:])
    assert all(q["deadline_remaining_seconds_at_dispatch"] >= 60 and q["effective_max_output_tokens"] == 2048 for q in ledger)
    with (stage.ROOT / "benchmark/runs-benchmark48.csv").open() as stream:
        indexed = list(csv.DictReader(stream))
    assert [r["run_id"] for r in indexed] == ["R-0039", "R-0087", "R-0088", "R-0089", "R-0134", "R-0135", "R-0179", "R-0180"]
    state = json.loads(stage.STATE.read_text())
    assert len(state["benchmark48_paid_batches"]) == 4
    assert (state["next_pilot_run_start"], state["next_pilot_config_start"]) == (222, 323)
    git = {}
    for name in ("opencode-v1", "opencode-v2", "pi", "codex"):
        status = subprocess.check_output(["git", "--no-optional-locks", "status", "--porcelain"], cwd=stage.ROOT.parent / name, timeout=30)
        assert not status
        git[name] = "clean"
    hashes = {}
    for path in ART.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert not re.search(rb"\bsk-[A-Za-z0-9_-]{24,}\b|Bearer\s+[A-Za-z0-9_.-]{24,}", data), str(path)
            hashes[str(path.relative_to(ART))] = stage.cont.batch.digest(path)
    freeze = subprocess.run(["python3", "-B", "benchmark/freeze_pilot.py", "--verify"], cwd=stage.ROOT,
                            capture_output=True, text=True, timeout=120)
    assert freeze.returncode == 0
    OUT.mkdir(parents=True, exist_ok=False)
    stage.cont.batch.native.write(OUT / "validation.json", {
        "status": "pass", "checked_at_utc": stage.cont.batch.native.now(), "batch": str(ART.relative_to(stage.ROOT)),
        "executed_attempts": 2, "new_unique_slots_attempted": 2, "remaining_unique_slots_not_run": 41,
        "success": "R179Pi/B02scope/public/hidden pass; onlypagination.py changed; CLIexit0",
        "stop": "R180v2/B02request1TimeoutError before HTTP/terminal/usage, no edits; no walltimeout; rootcauseunverified",
        "provider_requests": 6, "completed_with_usage": 5, "unpriced_requests": 1, "known_estimate_usd": str(known),
        "benchmark_cumulative_known_usd": "0.28485816", "benchmark_cumulative_unpriced": 4, "total_charge_usd": None,
        "all_benchmark_attempts": 8, "all_benchmark_unique_slots_attempted": 7,
        "first_attempt_counts": {"success": 2, "failure": 1, "infra_error": 4}, "supplementary_retry_counts": {"success": 1},
        "duration_ms": durations, "gaps_seconds": gaps, "all_gaps_ge30": True, "cross_batch_gap_seconds": cross_batch_gap,
        "minimum_remaining_seconds_at_dispatch": min(q["deadline_remaining_seconds_at_dispatch"] for q in ledger),
        "cleanup": cleanup, "unrun_runtime_roots_absent": True, "input_resource_hashes": "pass",
        "source_git_status": git, "frozen_pilot": freeze.stdout, "raw_artifact_sha256": hashes,
        "secret_pattern_scan": "heuristic pass; not full publication/PII review", "next_registry_ids": ["R-0222", "C-0323"],
        "new_provider_requests_by_audit": 0, "auto_retry_or_resume_authorized": False})
    print("PASS:PiB02success/v2request1TimeoutError;6upstream/5completed/1unpriced;5gaps>=30;raw/hash/cleanup/Git/frozen")


if __name__ == "__main__":
    main()
