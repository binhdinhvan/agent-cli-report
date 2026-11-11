"""Explicit once-only continuation of47 not_run slots; offline default, no auto retry."""
import argparse
import contextlib
import csv
from decimal import Decimal
import fcntl
import json
import os
import pathlib
import re
from unittest.mock import patch

import batch48 as batch
import suite48_runtime as runtime

ROOT, SUITE = batch.ROOT, batch.SUITE
STATE = batch.STATE
PRIOR = SUITE / "artifacts/BENCH48-20261110-01"
REV = SUITE / "revisions/b01-evidence-r2"
PROTOCOL = ROOT / "benchmark/PROTOCOL_47_CONTINUE_R2.md"
SCOPE = "47-not-run-slots-continuation-no-retry-rubric-r2"


def prior_state():
    result = json.loads((PRIOR / "result.json").read_text())
    if len(result["runs"]) != 1 or result["runs"][0]["run_id"] != "R-0039":
        raise ValueError("Unexpected prior execution set")
    review = json.loads((ROOT / "research/artifacts/BENCH48-REVIEW-20261110-01/validation.json").read_text())
    for name, expected in review["raw_artifact_sha256"].items():
        if batch.digest(PRIOR / name) != expected:
            raise ValueError("Prior raw drift: " + name)
    rows = []
    for old in result["plan"]:
        if old["status"] == "not_run":
            row = {k: v for k, v in old.items() if k not in ("run_id", "config_id")}
            row["continuation_of"] = {k: old[k] for k in ("slot", "run_id", "config_id")}
            rows.append(row)
    if len(rows) != 47 or [r["slot"] for r in rows] != [f"D48-{n:03d}" for n in range(2, 49)]:
        raise ValueError("Only the original untouched suffix may continue")
    known = result["known_usage_estimate_usd"]
    unknown = result["unpriced_requests"]
    if Decimal(known) != Decimal("0.06853344") or unknown != 1:
        raise ValueError("Prior cost requires new reviewed decision")
    return rows, known, unknown


def revision_inputs():
    seal = json.loads((REV / "seal.json").read_text())
    actual = {str(p.relative_to(REV)): batch.digest(p) for p in REV.rglob("*") if p.is_file() and p.name != "seal.json"}
    if actual != seal["files_sha256"] or seal["changed_from_r1"] != ["B-01/hidden/acceptance.py"]:
        raise ValueError("Rubric seal/file set drift")
    for name, expected in actual.items():
        if name != "B-01/hidden/acceptance.py" and batch.digest(SUITE / name) != expected:
            raise ValueError("Unexpected fixture/prompt change")
    files = [REV / name for name in actual] + [REV / "seal.json", PROTOCOL, pathlib.Path(__file__),
        ROOT / "benchmark/seal_continue48.py", ROOT / "benchmark/rubric_b01_r2.py",
        ROOT / "benchmark/test_continue48.py", PRIOR / "result.json",
        ROOT / "research/artifacts/BENCH48-REVIEW-20261110-01/validation.json"]
    return {str(p.relative_to(ROOT)): batch.digest(p) for p in files}


def make_plan():
    rows, known, unknown = prior_state()
    state = json.loads(STATE.read_text())
    if len(state.get("benchmark48_paid_batches", [])) != 1:
        raise PermissionError("Exactly one predecessor required; no automatic second continuation")
    return {"revision": "continuation47-r2", "launch_authorized": False,
        "scope": SCOPE, "budget_estimate_usd": "16", "prior_known_usd": known,
        "prior_unpriced_requests": unknown, "remaining_known_guard_usd": str(Decimal("16") - Decimal(known)),
        "prior_missing_usage_policy": "explicit_continuation_total_remains_unknown",
        "protocol": str(PROTOCOL.relative_to(ROOT)), "rubric_revision": "b01-evidence-r2",
        "input_sha256": {**batch.inputs(), **revision_inputs()}, "resource_identity": batch.resource_identity(),
        "slots": rows, "proposed_run_start": state["next_pilot_run_start"],
        "proposed_config_start": state["next_pilot_config_start"],
        "model": batch.native.MODEL, "provider": batch.native.BASE_URL,
        "timing": batch.native.timing_policy("paced-900"), "invoice_cap": False}


def validate(plan_path, approval):
    plan_path = pathlib.Path(plan_path).resolve()
    if not plan_path.is_relative_to(SUITE / "artifacts"):
        raise ValueError("Local suite artifact plan required")
    plan = json.loads(plan_path.read_text())
    if plan != make_plan():
        raise ValueError("Plan/source/resource/registry/order drift; no credential read")
    if (approval.get("launch_authorized") is not True or approval.get("plan_sha256") != batch.digest(plan_path)
            or approval.get("scope") != SCOPE or approval.get("budget_estimate_usd") != "16"
            or approval.get("prior_unpriced_acknowledged") is not True
            or approval.get("rubric_revision") != "b01-evidence-r2"
            or not approval.get("approved_by") or not approval.get("approved_at_utc")):
        raise PermissionError("Explicit suffix/rubric/budget/unknown approval required")
    return plan


def reserve(plan, artifact):
    state = json.loads(STATE.read_text())
    if len(state.get("benchmark48_paid_batches", [])) != 1:
        raise PermissionError("Continuation already reserved")
    if (state["next_pilot_run_start"], state["next_pilot_config_start"]) != (plan["proposed_run_start"], plan["proposed_config_start"]):
        raise ValueError("Registry moved")
    used = {r["run_id"] for b in state["benchmark48_paid_batches"] for r in b["reserved"]}
    rows = []
    for offset, slot in enumerate(plan["slots"]):
        row = {**slot, "run_id": f"R-{plan['proposed_run_start'] + offset:04d}",
            "config_id": f"C-{plan['proposed_config_start'] + offset:04d}", "status": "not_run"}
        if row["run_id"] in used or (batch.native.RUNTIME / row["config_id"]).exists() or row["config_id"] in state.get("retired_config_ids", []):
            raise ValueError("ID/runtime collision")
        for name in ("runs.csv", "runs-search-r2.csv", "runs-benchmark48.csv"):
            path = ROOT / "benchmark" / name
            if path.exists():
                with path.open() as stream:
                    if any(r.get("run_id") == row["run_id"] or r.get("config_id") == row["config_id"] for r in csv.DictReader(stream)):
                        raise ValueError("ID already indexed")
        rows.append(row)
    state["next_pilot_run_start"] += len(rows)
    state["next_pilot_config_start"] += len(rows)
    state["benchmark48_paid_batches"].append({"artifact": str(artifact.relative_to(ROOT)), "reserved": rows,
        "status": "continuation_reserved_before_dispatch", "protocol": str(PROTOCOL.relative_to(ROOT)),
        "rubric_revision": "b01-evidence-r2", "budget_estimate_usd": "16", "prior_known_usd": plan["prior_known_usd"],
        "prior_unpriced_requests": plan["prior_unpriced_requests"]})
    tmp = STATE.with_suffix(".json.continue48-tmp")
    with tmp.open("x") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, STATE)
    return rows


@contextlib.contextmanager
def context(plan):
    remaining = Decimal(plan["remaining_known_guard_usd"])
    original_handler = batch.native.handler

    def handler(*args, **kwargs):
        if kwargs.get("budget_limit") != "16":
            raise ValueError("Unexpected inherited budget")
        kwargs["budget_limit"] = str(remaining)
        return original_handler(*args, **kwargs)

    with patch.object(batch, "SUITE", REV), patch.object(runtime, "SUITE", REV), patch.object(batch.native, "SUITE", REV), \
            patch.object(batch, "BUDGET", remaining), patch.object(batch.native, "handler", handler):
        yield


def dispatch(artifact, rows, plan, *, paid=False, key=None):
    with context(plan):
        result = batch.run_batch(artifact, rows, paid=paid, key=key,
            input_hashes=plan["input_sha256"], resources=plan["resource_identity"])
    result.update(protocol=plan["protocol"], rubric_revision=plan["rubric_revision"],
        prior_known_usd=plan["prior_known_usd"], prior_unpriced_requests=plan["prior_unpriced_requests"],
        remaining_known_guard_usd=plan["remaining_known_guard_usd"],
        benchmark_known_cumulative_usd=str(Decimal(plan["prior_known_usd"]) + Decimal(result["known_usage_estimate_usd"])) if paid else None,
        benchmark_estimated_total_usd=None, measured_charge_usd=None,
        cost_scope="continuation_only; benchmark cumulative includes predecessor; total unknown")
    batch.native.write(artifact / "result.json", result)
    return result


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
                batch.native.write(artifact / (name + ".json"), value)
            key = batch.load_credential()
            dispatch(artifact, rows, plan, paid=True, key=key)
    else:
        plan = make_plan()
        artifact.mkdir(parents=True, exist_ok=False)
        batch.native.write(artifact / "launch-plan.json", plan)
        if args.prepare_plan:
            batch.native.write(artifact / "approval-template.json", {"launch_authorized": False,
                "plan_sha256": batch.digest(artifact / "launch-plan.json"), "scope": SCOPE,
                "budget_estimate_usd": "16", "prior_unpriced_acknowledged": False,
                "rubric_revision": "b01-evidence-r2", "approved_by": None, "approved_at_utc": None})
        else:
            selected = {}
            for row in plan["slots"]:
                selected.setdefault((row["task_id"], row["tool"]), row)
            result = dispatch(artifact, list(selected.values()), plan)
            if len(result["runs"]) != 16 or not result["all_slots_executed"] or any(r["status"] != "success" for r in result["runs"]):
                raise SystemExit(1)


if __name__ == "__main__":
    main()
