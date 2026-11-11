"""Explicit continuation of43 unattempted slots; no retry of R135 or automatic repeat."""
import argparse
import csv
from decimal import Decimal
import fcntl
import json
import os
import pathlib
import re

import retry_continue48 as previous

cont = previous.cont
ROOT, SUITE = previous.ROOT, previous.SUITE
STATE = previous.STATE
PRIOR = SUITE / "artifacts/BENCH45-RETRY-CONTINUE-20261110-01"
PROTOCOL = ROOT / "benchmark/PROTOCOL_CONTINUE43_R2.md"
SCOPE = "43-not-run-slots-only-no-retry-R135-rubric-r2"


def predecessors():
    previous.predecessors()
    audit = json.loads((ROOT / "research/artifacts/RETRY45-REVIEW-20261110-01/validation.json").read_text())
    for name, expected in audit["raw_artifact_sha256"].items():
        if cont.batch.digest(PRIOR / name) != expected:
            raise ValueError("Previous raw drift: " + name)
    result = json.loads((PRIOR / "result.json").read_text())
    if [r["run_id"] for r in result["runs"]] != ["R-0134", "R-0135"]:
        raise ValueError("Unexpected predecessor attempts")
    rows = []
    for old in result["plan"]:
        if old["status"] == "not_run":
            row = {k: v for k, v in old.items() if k not in ("run_id", "config_id", "retry_of")}
            row.update(attempt_kind="first_attempt_of_unrun_slot",
                continuation_of={k: old[k] for k in ("slot", "run_id", "config_id")})
            rows.append(row)
    if [r["slot"] for r in rows] != [f"D48-{n:03d}" for n in range(6, 49)]:
        raise ValueError("Only43 untouched slots; no retryR135")
    known = Decimal(result["prior_known_usd"]) + Decimal(result["known_usage_estimate_usd"])
    missing = result["prior_unpriced_requests"] + result["unpriced_requests"]
    if known != Decimal("0.25185936") or missing != 3:
        raise ValueError("Cost carry needs fresh review")
    return rows, str(known), missing


def make_plan():
    rows, known, missing = predecessors()
    state = json.loads(STATE.read_text())
    if len(state.get("benchmark48_paid_batches", [])) != 3:
        raise PermissionError("Exactly3predecessors required; no automatic continuation")
    files = [pathlib.Path(__file__), PROTOCOL, ROOT / "benchmark/test_continue43.py",
        ROOT / "benchmark/verify_continue43_regressions.py", ROOT / "benchmark/retry_continue48.py",
        ROOT / "benchmark/PROTOCOL_RETRY45_R2.md", ROOT / "research/artifacts/RETRY45-REVIEW-20261110-01/validation.json",
        ROOT / "research/artifacts/CONTINUE47-REVIEW-20261110-01/validation.json", PRIOR / "result.json",
        previous.PRIOR / "result.json"]
    return {"revision": "continuation43-r2", "scope": SCOPE, "launch_authorized": False,
        "protocol": str(PROTOCOL.relative_to(ROOT)), "rubric_revision": "b01-evidence-r2",
        "budget_estimate_usd": "16", "prior_known_usd": known, "prior_unpriced_requests": missing,
        "remaining_known_guard_usd": str(Decimal("16") - Decimal(known)), "invoice_cap": False,
        "benchmark_total_charge_usd": None,
        "input_sha256": {**cont.batch.inputs(), **cont.revision_inputs(),
                         **{str(p.relative_to(ROOT)): cont.batch.digest(p) for p in files}},
        "resource_identity": cont.batch.resource_identity(), "slots": rows,
        "proposed_run_start": state["next_pilot_run_start"], "proposed_config_start": state["next_pilot_config_start"],
        "model": cont.batch.native.MODEL, "provider": cont.batch.native.BASE_URL,
        "timing": cont.batch.native.timing_policy("paced-900"), "retry_policy": "none; no retryR135; no auto resume"}


def validate(plan_path, approval):
    plan_path = pathlib.Path(plan_path).resolve()
    if not plan_path.is_relative_to(SUITE / "artifacts"):
        raise ValueError("Local artifact plan required")
    plan = json.loads(plan_path.read_text())
    if plan != make_plan():
        raise ValueError("Plan/source/resource/registry/schedule drift")
    if (approval.get("launch_authorized") is not True or approval.get("plan_sha256") != cont.batch.digest(plan_path)
            or approval.get("scope") != SCOPE or approval.get("budget_estimate_usd") != "16"
            or approval.get("prior_unpriced_acknowledged") is not True or approval.get("retries_authorized") is not False
            or approval.get("rubric_revision") != "b01-evidence-r2"
            or not approval.get("approved_by") or not approval.get("approved_at_utc")):
        raise PermissionError("Explicit43suffix/no-retry/unknown/guard approval required")
    return plan


def reserve(plan, artifact):
    state = json.loads(STATE.read_text())
    if len(state.get("benchmark48_paid_batches", [])) != 3:
        raise PermissionError("Already reserved; no automatic repeat")
    if len(plan["slots"]) != 43 or any("retry_of" in row for row in plan["slots"]):
        raise ValueError("43unrun slots without retry required")
    if (state["next_pilot_run_start"], state["next_pilot_config_start"]) != (plan["proposed_run_start"], plan["proposed_config_start"]):
        raise ValueError("Registry moved")
    used_runs = {r["run_id"] for b in state["benchmark48_paid_batches"] for r in b["reserved"]}
    used_configs = {r["config_id"] for b in state["benchmark48_paid_batches"] for r in b["reserved"]}
    rows = []
    for offset, slot in enumerate(plan["slots"]):
        row = {**slot, "run_id": f"R-{plan['proposed_run_start'] + offset:04d}",
               "config_id": f"C-{plan['proposed_config_start'] + offset:04d}", "status": "not_run"}
        if (row["run_id"] in used_runs or row["config_id"] in used_configs
                or row["config_id"] in state.get("retired_config_ids", [])
                or (cont.batch.native.RUNTIME / row["config_id"]).exists()):
            raise ValueError("ID/runtime collision")
        for name in ("runs.csv", "runs-search-r2.csv", "runs-benchmark48.csv"):
            index = ROOT / "benchmark" / name
            if index.exists():
                with index.open() as stream:
                    if any(r.get("run_id") == row["run_id"] or r.get("config_id") == row["config_id"] for r in csv.DictReader(stream)):
                        raise ValueError("ID already indexed")
        rows.append(row)
    state["next_pilot_run_start"] += 43
    state["next_pilot_config_start"] += 43
    state["benchmark48_paid_batches"].append({"artifact": str(artifact.relative_to(ROOT)), "reserved": rows,
        "status": "continuation43_reserved", "protocol": str(PROTOCOL.relative_to(ROOT)),
        "rubric_revision": "b01-evidence-r2", "budget_estimate_usd": "16",
        "prior_known_usd": plan["prior_known_usd"], "prior_unpriced_requests": plan["prior_unpriced_requests"]})
    tmp = STATE.with_suffix(".json.continue43-tmp")
    with tmp.open("x") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, STATE)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare-plan", "offline-check", "paid"):
        mode.add_argument("--" + name, action="store_true")
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--plan", type=pathlib.Path)
    parser.add_argument("--approval", type=pathlib.Path)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / "artifacts") or not re.fullmatch(r"[A-Za-z0-9-]+", artifact.name):
        parser.error("Fresh safe suite artifact path required")
    if args.paid:
        if not args.plan or not args.approval:
            parser.error("Explicit plan/approval required")
        approval = json.loads(args.approval.read_text())
        plan = validate(args.plan, approval)
        with (ROOT / "research/.batch48-launch.lock").open("a") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            plan = validate(args.plan, approval)
            artifact.mkdir(parents=True, exist_ok=False)
            rows = reserve(plan, artifact)
            for name, value in (("plan", plan), ("approval", approval), ("reserved", rows)):
                cont.batch.native.write(artifact / (name + ".json"), value)
            cont.dispatch(artifact, rows, plan, paid=True, key=cont.batch.load_credential())
    else:
        plan = make_plan()
        artifact.mkdir(parents=True, exist_ok=False)
        cont.batch.native.write(artifact / "launch-plan.json", plan)
        if args.prepare_plan:
            cont.batch.native.write(artifact / "approval-template.json", {"launch_authorized": False,
                "plan_sha256": cont.batch.digest(artifact / "launch-plan.json"), "scope": SCOPE,
                "budget_estimate_usd": "16", "prior_unpriced_acknowledged": False,
                "retries_authorized": False, "rubric_revision": "b01-evidence-r2", "approved_by": None, "approved_at_utc": None})
        else:
            cases = {}
            for row in plan["slots"]:
                cases.setdefault((row["task_id"], row["tool"]), row)
            result = cont.dispatch(artifact, list(cases.values()), plan)
            if len(result["runs"]) != 16 or not result["all_slots_executed"] or any(r["status"] != "success" for r in result["runs"]):
                raise SystemExit(1)


if __name__ == "__main__":
    main()
