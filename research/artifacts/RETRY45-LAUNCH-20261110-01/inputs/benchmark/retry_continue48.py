"""One explicit retry of R89 then44 untouched slots; never repeat automatically."""
import argparse
import csv
from decimal import Decimal
import fcntl
import json
import os
import pathlib
import re

import continue48 as cont

ROOT, SUITE = cont.ROOT, cont.SUITE
STATE = cont.STATE
PRIOR = SUITE / "artifacts/BENCH47-CONTINUE-20261110-01"
PROTOCOL = ROOT / "benchmark/PROTOCOL_RETRY45_R2.md"
SCOPE = "one-retry-R0089-then44-not-run-no-auto-retry-rubric-r2"


def predecessors():
    cont.prior_state()
    audit_path = ROOT / "research/artifacts/CONTINUE47-REVIEW-20261110-01/validation.json"
    audit = json.loads(audit_path.read_text())
    for name, expected in audit["raw_artifact_sha256"].items():
        if cont.batch.digest(PRIOR / name) != expected:
            raise ValueError("Predecessor raw drift: " + name)
    result = json.loads((PRIOR / "result.json").read_text())
    if [r["run_id"] for r in result["runs"]] != ["R-0087", "R-0088", "R-0089"]:
        raise ValueError("Unexpected predecessor attempts")
    if result["runs"][-1]["status"] != "infra_error":
        raise ValueError("R89 must remain original infra_error")
    source = next(r for r in result["plan"] if r["run_id"] == "R-0089")
    retry = {k: v for k, v in source.items() if k not in ("run_id", "config_id")}
    retry.update(status="not_run", retry_of="R-0089", attempt_kind="explicit_retry",
        continuation_of={k: source[k] for k in ("slot", "run_id", "config_id")})
    suffix = []
    for old in result["plan"]:
        if old["status"] == "not_run":
            row = {k: v for k, v in old.items() if k not in ("run_id", "config_id")}
            row.update(attempt_kind="first_attempt_of_unrun_slot",
                continuation_of={k: old[k] for k in ("slot", "run_id", "config_id")})
            suffix.append(row)
    if [r["slot"] for r in suffix] != [f"D48-{n:03d}" for n in range(5, 49)]:
        raise ValueError("Only44 untouched slots may follow retry")
    old = json.loads((cont.PRIOR / "result.json").read_text())
    known = Decimal(old["known_usage_estimate_usd"]) + Decimal(result["known_usage_estimate_usd"])
    missing = old["unpriced_requests"] + result["unpriced_requests"]
    if known != Decimal("0.21341376") or missing != 2:
        raise ValueError("Unexpected carry; review new decision")
    return [retry, *suffix], str(known), missing


def make_plan():
    rows, known, unknown = predecessors()
    state = json.loads(STATE.read_text())
    if len(state.get("benchmark48_paid_batches", [])) != 2:
        raise PermissionError("Exactly two predecessors required; no automatic repeat")
    files = [pathlib.Path(__file__), ROOT / "benchmark/test_retry_continue48.py", ROOT / "benchmark/verify_retry_regressions.py", PROTOCOL,
        ROOT / "benchmark/PROTOCOL_47_CONTINUE_R2.md", PRIOR / "result.json",
        ROOT / "research/artifacts/CONTINUE47-REVIEW-20261110-01/validation.json"]
    return {"revision": "explicit-retry89-then44-r2", "launch_authorized": False, "scope": SCOPE,
        "protocol": str(PROTOCOL.relative_to(ROOT)), "rubric_revision": "b01-evidence-r2",
        "prior_known_usd": known, "prior_unpriced_requests": unknown,
        "remaining_known_guard_usd": str(Decimal("16") - Decimal(known)), "budget_estimate_usd": "16",
        "invoice_cap": False, "benchmark_total_charge_usd": None,
        "input_sha256": {**cont.batch.inputs(), **cont.revision_inputs(),
                         **{str(p.relative_to(ROOT)): cont.batch.digest(p) for p in files}},
        "resource_identity": cont.batch.resource_identity(), "slots": rows,
        "proposed_run_start": state["next_pilot_run_start"], "proposed_config_start": state["next_pilot_config_start"],
        "model": cont.batch.native.MODEL, "provider": cont.batch.native.BASE_URL,
        "timing": cont.batch.native.timing_policy("paced-900"),
        "retry_policy": "R89 once supplementary; old infra status preserved; no further automatic retry"}


def validate(plan_path, approval):
    plan_path = pathlib.Path(plan_path).resolve()
    if not plan_path.is_relative_to(SUITE / "artifacts"):
        raise ValueError("Local artifact plan required")
    plan = json.loads(plan_path.read_text())
    if plan != make_plan():
        raise ValueError("Plan/source/resource/registry/schedule drift; no key read")
    if (approval.get("launch_authorized") is not True or approval.get("plan_sha256") != cont.batch.digest(plan_path)
            or approval.get("scope") != SCOPE or approval.get("budget_estimate_usd") != "16"
            or approval.get("prior_unpriced_acknowledged") is not True or approval.get("retry_of") != "R-0089"
            or approval.get("rubric_revision") != "b01-evidence-r2"
            or not approval.get("approved_by") or not approval.get("approved_at_utc")):
        raise PermissionError("Explicit retry+suffix/unknown/guard/plan approval required")
    return plan


def reserve(plan, artifact):
    state = json.loads(STATE.read_text())
    if len(state.get("benchmark48_paid_batches", [])) != 2:
        raise PermissionError("Already reserved, no automatic repeat")
    if len(plan["slots"]) != 45 or plan["slots"][0].get("retry_of") != "R-0089":
        raise ValueError("Exactly one retry then44 slots required")
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
    state["next_pilot_run_start"] += 45
    state["next_pilot_config_start"] += 45
    state["benchmark48_paid_batches"].append({"artifact": str(artifact.relative_to(ROOT)), "reserved": rows,
        "status": "explicit_retry89_then44_reserved", "protocol": str(PROTOCOL.relative_to(ROOT)),
        "rubric_revision": "b01-evidence-r2", "budget_estimate_usd": "16",
        "prior_known_usd": plan["prior_known_usd"], "prior_unpriced_requests": plan["prior_unpriced_requests"]})
    tmp = STATE.with_suffix(".json.retry45-tmp")
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
            key = cont.batch.load_credential()
            cont.dispatch(artifact, rows, plan, paid=True, key=key)
    else:
        plan = make_plan()
        artifact.mkdir(parents=True, exist_ok=False)
        cont.batch.native.write(artifact / "launch-plan.json", plan)
        if args.prepare_plan:
            cont.batch.native.write(artifact / "approval-template.json", {"launch_authorized": False,
                "plan_sha256": cont.batch.digest(artifact / "launch-plan.json"), "scope": SCOPE,
                "budget_estimate_usd": "16", "prior_unpriced_acknowledged": False,
                "retry_of": "R-0089", "rubric_revision": "b01-evidence-r2", "approved_by": None, "approved_at_utc": None})
        else:
            cases = {}
            for row in plan["slots"]:
                cases.setdefault((row["task_id"], row["tool"]), row)
            result = cont.dispatch(artifact, list(cases.values()), plan)
            if len(result["runs"]) != 16 or not result["all_slots_executed"] or any(r["status"] != "success" for r in result["runs"]):
                raise SystemExit(1)


if __name__ == "__main__":
    main()
