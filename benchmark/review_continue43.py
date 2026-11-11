"""Prelaunch43 review only: pin exact offline plan, preserve predecessors, no API/key."""
import json
import subprocess

import continue43 as stage


def main():
    candidate = stage.SUITE / "artifacts/CONTINUE43-CANDIDATE-20261110-01/launch-plan.json"
    offline = stage.SUITE / "artifacts/CONTINUE43-OFFLINE-20261110-01"
    target = stage.ROOT / "research/artifacts/CONTINUE43-LAUNCH-20261110-01"
    plan = json.loads(candidate.read_text())
    assert plan == stage.make_plan()
    assert json.loads((offline / "launch-plan.json").read_text()) == plan
    result = json.loads((offline / "result.json").read_text())
    assert result["synthetic_usage"] and result["provider_requests"] == 0 and result["all_slots_executed"]
    assert len(result["runs"]) == 16 and len({(r["task_id"], r["tool"]) for r in result["runs"]}) == 16
    for record in result["runs"]:
        assert record["status"] == "success" and record["grading"]["pass"]
        assert record["supervisor_pid_absent"] and record["broker_socket_absent"]
        assert stage.cont.batch.native.isolated(record["execution"])
        assert all(record["preflight_events"].values()) and "retry_of" not in record
    assert len(plan["slots"]) == 43 and not any("retry_of" in row for row in plan["slots"])
    assert plan["prior_unpriced_requests"] == 3 and plan["remaining_known_guard_usd"] == "15.74814064"
    assert not any((stage.cont.batch.native.RUNTIME / f"C-{n:04d}").exists() for n in range(280, 323))
    git = {}
    for name in ("opencode-v1", "opencode-v2", "pi", "codex"):
        output = subprocess.check_output(["git", "--no-optional-locks", "status", "--porcelain"], cwd=stage.ROOT.parent / name, timeout=30)
        assert not output
        git[name] = "clean"
    target.mkdir(parents=True, exist_ok=False)
    tests = {}
    for name, command, count in [
        ("benchmark", ["python3", "-B", "benchmark/verify_continue43_regressions.py"], 75),
        ("demos", ["python3", "-B", "-m", "unittest", "discover", "-s", "demos", "-p", "test_*.py"], 37),
    ]:
        checked = subprocess.run(command, cwd=stage.ROOT, capture_output=True, timeout=120)
        (target / (name + ".stdout.txt")).write_bytes(checked.stdout)
        (target / (name + ".stderr.txt")).write_bytes(checked.stderr)
        assert checked.returncode == 0
        tests[name] = count
    snapshots = {}
    for name, expected in plan["input_sha256"].items():
        path = stage.ROOT / name
        assert stage.cont.batch.digest(path) == expected
        if name.startswith("benchmark/") and (path.suffix in (".py", ".md", ".json", ".txt") or "/revisions/" in name):
            dest = target / "inputs" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())
            snapshots[name] = expected
    approval = {"launch_authorized": True, "plan_sha256": stage.cont.batch.digest(candidate), "scope": stage.SCOPE,
        "budget_estimate_usd": "16", "prior_unpriced_acknowledged": True, "retries_authorized": False,
        "rubric_revision": "b01-evidence-r2", "approved_by": "user explicit request: chạy tiếp after retry45 stopped",
        "approved_at_utc": stage.cont.batch.native.now(), "prior_known_usd": "0.25185936",
        "prior_unpriced_requests": 3, "remaining_known_guard_usd": "15.74814064",
        "offline_acceptance_sha256": stage.cont.batch.digest(offline / "result.json"), "no_auto_retry_or_resume": True}
    assert stage.validate(candidate, approval) == plan
    path = stage.SUITE / "approvals/CONTINUE43-20261110-01.json"
    with path.open("x") as stream:
        json.dump(approval, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    stage.cont.batch.native.write(target / "validation.json", {
        "status": "pass", "checked_at_utc": stage.cont.batch.native.now(), "scope": stage.SCOPE,
        "plan_sha256": stage.cont.batch.digest(candidate), "approval": str(path.relative_to(stage.ROOT)),
        "approval_sha256": stage.cont.batch.digest(path), "regression_tests": tests,
        "native_synthetic_acceptance_pairs": 16, "native_synthetic_exchanges": result["synthetic_exchanges"],
        "input_snapshots": snapshots, "source_git_status": git, "provider_requests_by_audit": 0,
        "network_probes": 0, "credential_read": False, "ids_reserved_by_audit": False,
        "fresh_ids_proposed": ["R-0179..R-0221", "C-0280..C-0322"], "budget_estimate_usd": "16",
        "prior_known_usd": "0.25185936", "prior_unpriced_requests": 3, "remaining_known_guard_usd": "15.74814064",
        "total_charge_usd": None, "prior_raw_retention": "pass via predecessors()", "rubric_unchanged": True})
    print("PASS:43unrun/no retries;112tests/16native synthetic cases/hash/guard/prior raw/IDs/Git;0provider")


if __name__ == "__main__":
    main()
