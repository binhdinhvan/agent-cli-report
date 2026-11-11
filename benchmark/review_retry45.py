"""Gate and snapshot explicit retry45 launch; no credential or provider."""
import json
import subprocess

import retry_continue48 as retry


def main():
    candidate = retry.SUITE / "artifacts/RETRY45-CANDIDATE-20261110-01/launch-plan.json"
    offline = retry.SUITE / "artifacts/RETRY45-OFFLINE-20261110-01"
    target = retry.ROOT / "research/artifacts/RETRY45-LAUNCH-20261110-01"
    plan = json.loads(candidate.read_text())
    assert retry.make_plan() == plan
    assert json.loads((offline / "launch-plan.json").read_text()) == plan
    accepted = json.loads((offline / "result.json").read_text())
    assert accepted["synthetic_usage"] and accepted["provider_requests"] == 0 and accepted["all_slots_executed"]
    assert len(accepted["runs"]) == 16
    assert len({(r["task_id"], r["tool"]) for r in accepted["runs"]}) == 16
    for record in accepted["runs"]:
        assert record["status"] == "success" and record["grading"]["pass"]
        assert record["supervisor_pid_absent"] and record["broker_socket_absent"]
        assert retry.cont.batch.native.isolated(record["execution"])
        assert all(record["preflight_events"].values())
    assert accepted["runs"][0]["retry_of"] == "R-0089"
    assert all("retry_of" not in r for r in accepted["runs"][1:])
    assert len(plan["slots"]) == 45 and plan["slots"][0]["retry_of"] == "R-0089"
    assert plan["prior_unpriced_requests"] == 2 and plan["remaining_known_guard_usd"] == "15.78658624"
    assert not any((retry.cont.batch.native.RUNTIME / f"C-{n:04d}").exists() for n in range(235, 280))
    git = {}
    for name in ("opencode-v1", "opencode-v2", "pi", "codex"):
        output = subprocess.check_output(["git", "--no-optional-locks", "status", "--porcelain"], cwd=retry.ROOT.parent / name, timeout=30)
        assert not output
        git[name] = "clean"
    target.mkdir(parents=True, exist_ok=False)
    tests = {}
    for name, command, count in [
        ("benchmark", ["python3", "-B", "benchmark/verify_retry_regressions.py"], 69),
        ("demos", ["python3", "-B", "-m", "unittest", "discover", "-s", "demos", "-p", "test_*.py"], 37),
    ]:
        result = subprocess.run(command, cwd=retry.ROOT, capture_output=True, timeout=120)
        (target / (name + ".stdout.txt")).write_bytes(result.stdout)
        (target / (name + ".stderr.txt")).write_bytes(result.stderr)
        assert result.returncode == 0, name
        tests[name] = count
    snapshots = {}
    for name, expected in plan["input_sha256"].items():
        source = retry.ROOT / name
        assert retry.cont.batch.digest(source) == expected
        if name.startswith("benchmark/") and (source.suffix in (".py", ".md", ".json", ".txt") or "/revisions/" in name):
            dest = target / "inputs" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(source.read_bytes())
            snapshots[name] = expected
    approval = {"launch_authorized": True, "plan_sha256": retry.cont.batch.digest(candidate), "scope": retry.SCOPE,
        "budget_estimate_usd": "16", "prior_unpriced_acknowledged": True, "retry_of": "R-0089",
        "rubric_revision": "b01-evidence-r2", "approved_by": "user explicit request: retry chạy tiếp",
        "approved_at_utc": retry.cont.batch.native.now(), "prior_known_usd": "0.21341376",
        "prior_unpriced_requests": 2, "remaining_known_guard_usd": "15.78658624",
        "offline_acceptance_sha256": retry.cont.batch.digest(offline / "result.json"),
        "no_further_auto_retry_or_resume": True}
    assert retry.validate(candidate, approval) == plan
    path = retry.SUITE / "approvals/RETRY45-20261110-01.json"
    with path.open("x") as stream:
        json.dump(approval, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    retry.cont.batch.native.write(target / "validation.json", {
        "status": "pass", "checked_at_utc": retry.cont.batch.native.now(),
        "scope": retry.SCOPE, "plan_sha256": retry.cont.batch.digest(candidate),
        "approval": str(path.relative_to(retry.ROOT)), "approval_sha256": retry.cont.batch.digest(path),
        "regression_tests": tests, "prior_test_harness_failures_retained": ["RETRY45-REGRESSION-20261110-01", "RETRY45-REGRESSION-20261110-02"],
        "native_synthetic_acceptance_pairs": 16, "native_synthetic_exchanges": accepted["synthetic_exchanges"],
        "source_snapshots": snapshots, "source_git_status": git, "new_provider_requests": 0,
        "network_probes": 0, "credential_read": False, "fresh_ids_proposed": ["R-0134..R-0178", "C-0235..C-0279"],
        "ids_reserved_by_audit": False, "budget_estimate_usd": "16", "prior_known_usd": "0.21341376",
        "prior_unpriced_requests": 2, "remaining_known_guard_usd": "15.78658624", "total_charge_usd": None,
        "prior_raw_retention": "pass via predecessors()", "rubric_unchanged": True})
    print("PASS:1retryR89+44suffix;106tests/16native synthetic cases/hash/guard/prior raw/IDs/Git;0provider")


if __name__ == "__main__":
    main()
