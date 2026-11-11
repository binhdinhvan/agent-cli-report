"""Offline postcheck retry89+44; never resume, probe or read credentials."""
from datetime import datetime
from decimal import Decimal
import csv
import json
import pathlib
import re
import subprocess

import retry_continue48 as retry

ART = retry.SUITE / "artifacts/BENCH45-RETRY-CONTINUE-20261110-01"
OUT = retry.ROOT / "research/artifacts/RETRY45-REVIEW-20261110-01"


def main():
    result = json.loads((ART / "result.json").read_text())
    plan = json.loads((ART / "plan.json").read_text())
    retry.cont.batch.check_dispatch_inputs(plan["input_sha256"], plan["resource_identity"])
    retry.predecessors()
    runs = result["runs"]
    assert [r["run_id"] for r in runs] == ["R-0134", "R-0135"]
    assert runs[0]["retry_of"] == "R-0089" and runs[0]["status"] == "success"
    assert runs[0]["grading"]["rubric"]["total"] == 10
    assert runs[0]["grading"]["changed_files"] == ["answer.json"]
    assert runs[1]["status"] == "infra_error" and runs[1]["validity"] == "pending_review"
    assert runs[1]["grading"]["changed_files"] == []
    assert len(result["plan"]) == 45 and sum(r["status"] == "not_run" for r in result["plan"]) == 43
    ledger = [q for r in runs for q in r["requests"]]
    assert len(ledger) == result["provider_requests"] == 7
    known, missing = retry.cont.batch.ledger_cost(ledger)
    assert known == Decimal("0.03844560") and missing == 1
    assert result["known_usage_estimate_usd"] == str(known)
    assert result["estimated_total_usd"] is None and result["benchmark_estimated_total_usd"] is None
    assert result["benchmark_known_cumulative_usd"] == "0.25185936"
    assert all(q.get("http_status") == 200 and q.get("terminal_type") == "response.completed" for q in ledger[:6])
    last = ledger[-1]
    assert last["error_type"] == "TimeoutError"
    assert all(key not in last for key in ("http_status", "terminal_type", "cost", "finished_at_utc"))
    gaps = [(datetime.fromisoformat(b["started_at_utc"]) - datetime.fromisoformat(a["finished_at_utc"])).total_seconds()
            for a, b in zip(ledger, ledger[1:])]
    assert len(gaps) == 6 and min(gaps) >= 30
    previous = json.loads((retry.PRIOR / "result.json").read_text())
    cross_batch_gap = (datetime.fromisoformat(ledger[0]["started_at_utc"]) - datetime.fromisoformat(previous["finished_at_utc"])).total_seconds()
    assert cross_batch_gap >= 30
    cleanup, durations = {}, {}
    for record in runs:
        execution = record["execution"]
        assert not execution["timed_out"] and not execution["output_limit_exceeded"]
        assert retry.cont.batch.native.isolated(execution) and record["grading"]["scope_ok"]
        assert not pathlib.Path("/proc", str(execution["supervisor_host_pid"])).exists()
        assert not (pathlib.Path(record["spec"]["runtime_root"]) / "broker.sock").exists()
        assert execution["broker_deadline_monotonic"] == execution["outer_started_monotonic"] + 900
        cleanup[record["run_id"]] = "PID/socket absent; isolation witness pass"
        durations[record["run_id"]] = execution["duration_ms"]
    for row in result["plan"][2:]:
        assert not (retry.cont.batch.native.RUNTIME / row["config_id"]).exists()
    assert all(q["deadline_remaining_seconds_at_dispatch"] >= 60 and q["effective_max_output_tokens"] == 2048 for q in ledger)
    with (retry.ROOT / "benchmark/runs-benchmark48.csv").open() as stream:
        indexed = list(csv.DictReader(stream))
    assert [r["run_id"] for r in indexed] == ["R-0039", "R-0087", "R-0088", "R-0089", "R-0134", "R-0135"]
    assert next(r for r in indexed if r["run_id"] == "R-0089")["status"] == "infra_error"
    state = json.loads(retry.STATE.read_text())
    assert len(state["benchmark48_paid_batches"]) == 3
    assert (state["next_pilot_run_start"], state["next_pilot_config_start"]) == (179, 280)
    git = {}
    for repo in ("opencode-v1", "opencode-v2", "pi", "codex"):
        output = subprocess.check_output(["git", "--no-optional-locks", "status", "--porcelain"], cwd=retry.ROOT.parent / repo, timeout=30)
        assert not output
        git[repo] = "clean"
    hashes = {}
    for path in ART.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert not re.search(rb"\bsk-[A-Za-z0-9_-]{24,}\b|Bearer\s+[A-Za-z0-9_.-]{24,}", data), str(path)
            hashes[str(path.relative_to(ART))] = retry.cont.batch.digest(path)
    freeze = subprocess.run(["python3", "-B", "benchmark/freeze_pilot.py", "--verify"], cwd=retry.ROOT,
                            capture_output=True, text=True, timeout=120)
    assert freeze.returncode == 0
    OUT.mkdir(parents=True, exist_ok=False)
    retry.cont.batch.native.write(OUT / "validation.json", {
        "status": "pass", "checked_at_utc": retry.cont.batch.native.now(), "batch": str(ART.relative_to(retry.ROOT)),
        "executed_attempts": 2, "new_unique_slots_attempted": 1, "remaining_unique_slots_not_run": 43,
        "retry": "R134 success/valid10/10 supplementary retry_ofR89; original R89infra_error unchanged",
        "stop": "R135Codex/B02 request1TimeoutError before HTTP/terminal/usage, no edits; no wall timeout; root cause unverified",
        "provider_requests": 7, "completed_with_usage": 6, "unpriced_requests": 1,
        "known_estimate_usd": str(known), "benchmark_cumulative_known_usd": "0.25185936",
        "benchmark_cumulative_unpriced": 3, "benchmark_total_charge_usd": None,
        "all_benchmark_attempts": 6, "all_benchmark_unique_slots_attempted": 5,
        "first_attempt_counts": {"success": 1, "failure": 1, "infra_error": 3},
        "supplementary_retry_counts": {"success": 1},
        "duration_ms": durations, "gaps_seconds": gaps, "all_gaps_ge30": True,
        "cross_batch_gap_seconds": cross_batch_gap,
        "minimum_remaining_seconds_at_dispatch": min(q["deadline_remaining_seconds_at_dispatch"] for q in ledger),
        "cleanup": cleanup, "unrun_runtime_roots_absent": True, "input_resource_hashes": "pass",
        "source_git_status": git, "frozen_pilot": freeze.stdout, "raw_artifact_sha256": hashes,
        "secret_pattern_scan": "heuristic pass; not a full publication/PII audit",
        "next_registry_ids": ["R-0179", "C-0280"], "new_provider_requests_by_audit": 0,
        "auto_retry_or_resume_authorized": False})
    print("PASS:retryR13410/10;R135provider timeout;7upstream/6completed/1unpriced;6gaps>=30;raw/hash/cleanup/Git/frozen")


if __name__ == "__main__":
    main()
