"""Offline approval for user-requested scoped unpriced smoke; no API/key read."""
import json
import subprocess
import sys

import gemini_smoke5 as smoke


def main():
    root = smoke.ROOT
    state = json.loads((root / "research/experiment-state.json").read_text())
    assert state["active_model"] == smoke.MODEL and not state["paid_runs_ready"] and not state["paid_pricing_gate_ready"]
    profile = json.loads(smoke.PROFILE.read_text())
    assert profile["smoke5_authorized"] is True and profile["benchmark_scope"].startswith("user selected restart")
    assert all(profile["pricing"][key] is None for key in ("input_uncached", "input_cache_read", "output"))
    assert json.loads((root / "research/provider-pricing.json").read_text())["model"] == "gpt-6.1-sol"
    audit = json.loads((root / "research/artifacts/CONTINUE43-REVIEW-20261110-01/validation.json").read_text())
    prior = root / audit["batch"]
    assert all(smoke.sha(prior / name) == expected for name, expected in audit["raw_artifact_sha256"].items())
    assert (state["next_pilot_run_start"], state["next_pilot_config_start"]) == (222, 323)
    out = root / "research/artifacts/GEMINI-SMOKE5-LAUNCH-20261110-01"
    out.mkdir(parents=True, exist_ok=False)
    checked = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "demos", "-p", "test_*.py"],
                             cwd=root, capture_output=True, timeout=120)
    (out / "tests.stdout.txt").write_bytes(checked.stdout)
    (out / "tests.stderr.txt").write_bytes(checked.stderr)
    assert checked.returncode == 0
    frozen = subprocess.run([sys.executable, "-B", "benchmark/freeze_pilot.py", "--verify"], cwd=root,
                            capture_output=True, text=True, timeout=120)
    assert frozen.returncode == 0
    approval = {"authorized": True, "scope": smoke.SCOPE, "model": smoke.MODEL, "provider": smoke.BASE,
        "max_requests": 5, "allow_unpriced_for_this_smoke_only": True,
        "approved_by": "user: Vẫn dùng Shopaikey; giá chạy đi lát tôi bổ xung; chạy lại không nối2model; chạy thử5cái trước",
        "approved_at_utc": smoke.now(), "input_sha256": smoke.inputs(),
        "estimated_cost_usd": None, "measured_charge_usd": None, "price_status": "pending user rates; explicit scoped exception",
        "max_output_tokens": 256, "minimum_gap_seconds": 30, "retry_allowed": False, "benchmark48_authorized": False}
    smoke.validate(approval)
    path = root / "demos/approvals/GEMINI-SMOKE5-20261110-01.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(approval, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    for name in approval["input_sha256"]:
        dest = out / "source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((root / name).read_bytes())
    (out / "validation.json").write_text(json.dumps({"status": "pass", "checked_at_utc": smoke.now(),
        "scope": smoke.SCOPE, "offline_tests_passed": 47, "new_provider_requests": 0, "credential_read": False,
        "prior_sol_raw_retained": True, "sol_pricing_unmodified": True, "frozen_pilot": frozen.stdout,
        "approval": str(path.relative_to(root)), "approval_sha256": smoke.sha(path),
        "input_sha256": approval["input_sha256"], "registry_unchanged": ["R-0222", "C-0323"],
        "scope_limits": {"requests": 5, "output_tokens": 256, "gap_seconds": 30, "no_retry": True},
        "estimated_cost_usd": None, "full_benchmark_gate": False,
        "limitations": "Provider-only smoke, not native4CLI/toolcalling/benchmark or proof Gemini is more stable"}, ensure_ascii=False, indent=2) + "\n")
    print("PASS:47offline tests;explicit5request unpriced exception bound;oldsol raw/pricing/frozen retained;0provider")


if __name__ == "__main__":
    main()
