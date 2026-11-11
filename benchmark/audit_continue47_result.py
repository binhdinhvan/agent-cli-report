"""Read-only paid continuation postcheck. No API, credential, retry or native execution."""
from collections import Counter
from datetime import datetime
from decimal import Decimal
import csv
import json
import pathlib
import re
import subprocess

import continue48 as cont

ART = cont.SUITE / "artifacts/BENCH47-CONTINUE-20261110-01"
OUT = cont.ROOT / "research/artifacts/CONTINUE47-REVIEW-20261110-01"


def main():
    result = json.loads((ART / "result.json").read_text())
    plan = json.loads((ART / "plan.json").read_text())
    cont.batch.check_dispatch_inputs(plan["input_sha256"], plan["resource_identity"])
    cont.prior_state()  # prior raw hashes, no mutation
    records = result["runs"]
    assert [r["run_id"] for r in records] == ["R-0087", "R-0088", "R-0089"]
    assert [r["status"] for r in records] == ["success", "failure", "infra_error"]
    assert len(result["plan"]) == 47
    assert sum(row["status"] == "not_run" for row in result["plan"]) == 44
    ledger = [q for r in records for q in r["requests"]]
    assert len(ledger) == result["provider_requests"] == 10
    known, missing = cont.batch.ledger_cost(ledger)
    assert str(known) == result["known_usage_estimate_usd"] == "0.14488032"
    assert missing == result["unpriced_requests"] == 1
    assert Decimal(result["prior_known_usd"]) + known == Decimal("0.21341376")
    assert result["estimated_total_usd"] is None and result["benchmark_estimated_total_usd"] is None
    assert all(q.get("http_status") == 200 and q.get("terminal_type") == "response.completed" for q in ledger[:9])
    assert ledger[-1]["error_type"] == "TimeoutError"
    assert all(name not in ledger[-1] for name in ("http_status", "terminal_type", "cost", "finished_at_utc"))
    gaps = [(datetime.fromisoformat(b["started_at_utc"]) - datetime.fromisoformat(a["finished_at_utc"])).total_seconds()
            for a, b in zip(ledger, ledger[1:])]
    assert len(gaps) == 9 and min(gaps) >= 30
    old = json.loads((cont.PRIOR / "result.json").read_text())
    cross_batch_gap = (datetime.fromisoformat(ledger[0]["started_at_utc"]) - datetime.fromisoformat(old["finished_at_utc"])).total_seconds()
    assert cross_batch_gap >= 30
    assert all(q["effective_max_output_tokens"] == 2048 and q["deadline_remaining_seconds_at_dispatch"] >= 60 for q in ledger)
    cleanup, clocks = {}, {}
    for record in records:
        execution = record["execution"]
        assert not execution["timed_out"] and not execution["output_limit_exceeded"]
        assert cont.batch.native.isolated(execution)
        assert not pathlib.Path("/proc", str(execution["supervisor_host_pid"])).exists()
        assert not (pathlib.Path(record["spec"]["runtime_root"]) / "broker.sock").exists()
        assert execution["broker_deadline_monotonic"] == execution["outer_started_monotonic"] + 900
        cleanup[record["run_id"]] = "supervisor PID/socket absent; isolation witness pass"
        clocks[record["run_id"]] = execution["duration_ms"]
        assert record["grading"]["scope_ok"]
    for row in result["plan"][3:]:
        assert not (cont.batch.native.RUNTIME / row["config_id"]).exists()
    answer = json.loads((ART / "D48-003/grader/snapshot/answer.json").read_text())
    assert answer["default"]["value"] == 12
    assert answer["precedence"]["value"] == ["cli", "env", "config", "defaults"]
    assert answer["alias_trace"]["value"] == ["quick", "short", "timeout"]
    assert answer["cycle_error"]["type"] == "ValueError" and answer["cycle_error"]["message"] == "alias cycle: loop_a"
    assert answer["mutation"]["value"] is False
    assert answer["mutation"]["evidence"] == ["resolver.py:resolve", "aliases.py:canonical_name"]
    assert records[1]["grading"]["rubric"]["total"] == 9
    assert records[1]["grading"]["suites"]["public"]["exit_code"] == 0
    stdout = (ART / "D48-004/stdout.jsonl").read_text()
    assert "Batch stopped after provider failure; no upstream request sent." in stdout
    with (cont.ROOT / "benchmark/runs-benchmark48.csv").open() as stream:
        indexed = list(csv.DictReader(stream))
    assert [r["run_id"] for r in indexed] == ["R-0039", "R-0087", "R-0088", "R-0089"]
    state = json.loads(cont.STATE.read_text())
    assert len(state["benchmark48_paid_batches"]) == 2
    assert (state["next_pilot_run_start"], state["next_pilot_config_start"]) == (134, 235)
    git = {}
    for repo in ("opencode-v1", "opencode-v2", "pi", "codex"):
        status = subprocess.check_output(["git", "--no-optional-locks", "status", "--porcelain"], cwd=cont.ROOT.parent / repo, timeout=30)
        assert not status
        git[repo] = "clean"
    raw_hashes = {}
    for path in ART.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert not re.search(rb"\bsk-[A-Za-z0-9_-]{24,}\b|Bearer\s+[A-Za-z0-9_.-]{24,}", data), str(path)
            raw_hashes[str(path.relative_to(ART))] = cont.batch.digest(path)
    frozen = subprocess.run(["python3", "-B", "benchmark/freeze_pilot.py", "--verify"], cwd=cont.ROOT,
                            capture_output=True, text=True, timeout=120)
    assert frozen.returncode == 0
    OUT.mkdir(parents=True, exist_ok=False)
    report = {"status": "pass", "checked_at_utc": cont.batch.native.now(),
        "batch": str(ART.relative_to(cont.ROOT)), "executed_slots": 3, "not_run_slots": 44,
        "counts": dict(Counter(r["status"] for r in records)), "duration_ms": clocks,
        "upstream_requests": 10, "completed_with_usage": 9, "unpriced_requests": 1,
        "known_estimate_usd": str(known), "benchmark_cumulative_known_usd": "0.21341376",
        "benchmark_cumulative_unpriced": 2, "benchmark_total_charge_usd": None,
        "stop": "R89 request1 TimeoutError before HTTP/terminal/usage; no wall timeout; local503 latch is not upstream503",
        "pi_r88": "raw failure/valid under r2; all5content values correct; mutation extra canonical_name rejected by allowlist; design-review caveat, no regrade",
        "gaps_seconds": gaps, "all_gaps_ge30": True, "cross_batch_gap_seconds": cross_batch_gap,
        "minimum_remaining_seconds_at_dispatch": min(q["deadline_remaining_seconds_at_dispatch"] for q in ledger),
        "cleanup": cleanup, "unrun_runtime_roots_absent": True,
        "input_resource_hashes": "pass", "source_git_status": git, "frozen_pilot": frozen.stdout,
        "raw_artifact_sha256": raw_hashes, "secret_pattern_scan": "heuristic pass; not full publication/PII review",
        "next_registry_ids": ["R-0134", "C-0235"], "new_provider_requests_by_audit": 0,
        "auto_retry_or_resume_authorized": False}
    cont.batch.native.write(OUT / "validation.json", report)
    print("PASS:3attempts/10upstream/9completed/1unpriced;9gaps>=30s;raw/hash/resource/cleanup/Git/frozen verified")


if __name__ == "__main__":
    main()
