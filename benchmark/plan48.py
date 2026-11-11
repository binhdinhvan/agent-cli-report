"""Soạn order/dự toán 48 slot offline từ pilot; không chạy model hoặc reserve run IDs."""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_CEILING
import csv
import hashlib
import io
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmark/suite48"
DEFAULT = SUITE / "artifacts/DRAFT48-20261109-01"
SEED = "agent-cli-report-suite48-draft-r1-20261109"
SUMMARY = "benchmark/artifacts/PILOT-FREEZE-20261109-01/summary.json"
BASELINE = "benchmark/artifacts/PILOT-FREEZE-20261109-01/baseline.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shuffled(values, label):
    # Fully specified SHA-256 ordering, independent of Python random versions.
    return sorted(values, key=lambda value: (hashlib.sha256(
        (SEED + "|" + label + "|" + value).encode("utf-8")).hexdigest(), value))


def make_order(manifest):
    rows = []
    for repetition in range(1, manifest["repetitions"] + 1):
        tasks = shuffled([t["id"] for t in manifest["tasks"]], f"tasks-{repetition}")
        tools = shuffled(manifest["tools"], f"tools-{repetition}")
        for block, task in enumerate(tasks):
            rotated = tools[block:] + tools[:block]
            for position, tool in enumerate(rotated, 1):
                rows.append({"slot": f"D48-{len(rows) + 1:03d}", "repetition": repetition,
                    "block": (repetition - 1) * 4 + block + 1, "task_id": task,
                    "position_in_block": position, "tool": tool,
                    "status": "planned_not_run"})
    validate_order(rows, manifest)
    return rows


def validate_order(rows, manifest):
    tasks = {t["id"] for t in manifest["tasks"]}
    tools = set(manifest["tools"])
    if len(tasks) != 4 or len(tools) != 4 or manifest["repetitions"] != 3 or len(rows) != 48:
        raise ValueError("Expected exactly 4 tasks x 4 tools x 3 repetitions")
    if len({r["slot"] for r in rows}) != 48 or any(r["status"] != "planned_not_run" for r in rows):
        raise ValueError("Unique draft slots only; never use draft as measured results")
    counts = Counter((r["repetition"], r["task_id"], r["tool"]) for r in rows)
    expected = {(rep, task, tool) for rep in range(1, 4) for task in tasks for tool in tools}
    if set(counts) != expected or any(value != 1 for value in counts.values()):
        raise ValueError("Missing/duplicate task-tool-repetition")
    positions = Counter((r["tool"], r["position_in_block"]) for r in rows)
    if any(positions[(tool, pos)] != 3 for tool in tools for pos in range(1, 5)):
        raise ValueError("Tool positions must balance across 12 blocks")


def estimate(summary):
    cohort = [next(r for r in summary["runs"] if r["run_id"] == rid)
              for rid in summary["p02_cohort_execution_order"]]
    if len(cohort) != 4 or len({r["tool"] for r in cohort}) != 4:
        raise ValueError("Expected all-four P-02 cohort")
    if any(r["unpriced_requests"] or r["reviewed_status"] != "success" or
           r["environment_revision"] != "search-r2" or r["timing_policy"] != "paced-900" for r in cohort):
        raise ValueError("Expected priced successful search-r2/paced-900 cohort")
    costs = [Decimal(r["known_usage_estimated_cost_usd"]) for r in cohort]
    base = sum(costs) / Decimal(4) * Decimal(48)
    scenarios = [{"multiplier": factor, "estimated_usd": str(base * factor)} for factor in (1, 2, 3)]
    return {"source": SUMMARY, "source_run_ids": [r["run_id"] for r in cohort],
        "source_cohort_cost_usd": str(sum(costs)), "observed_mean_cost_per_run_usd": str(sum(costs) / 4),
        "method": "12 runs per CLI times its single observed P-02 cost; algebraically cohort mean x48",
        "scenarios": scenarios,
        "proposed_new_estimate_guard_usd": str((base * 3).to_integral_value(rounding=ROUND_CEILING)),
        "budget_approved_usd": None, "measured_benchmark_cost_usd": None,
        "historical_pilot_known_cost_usd_not_in_new_budget": summary["known_usage_estimated_cost_usd"],
        "historical_pilot_unpriced_requests": summary["unpriced_requests"],
        "historical_total_charge_usd": None,
        "maximum_planned_upstream_requests": 48 * 8,
        "requested_output_token_cap_sum": 48 * 8 * 2048,
        "output_only_cost_if_every_request_hits_cap_usd": str(Decimal(48 * 8 * 2048) * Decimal(18) / 1000000),
        "input_cost_included_in_output_only_illustration": False,
        "agent_wall_caps_sum_seconds": 48 * 900,
        "limitations": ["Scenarios are planning arithmetic, NOT measured benchmark results or confidence bounds",
            "n=1 priced P-02/tool; new tasks, native settings, cache and provider latency differ",
            "Includes neither guaranteed upper cost bound nor invoice cap; input cost can exceed proposal",
            "Unknown historical usage is not extrapolated or set to zero; pilot and new budget separate",
            "Soft guard may stop before48slots; completion is not guaranteed; no automatic top-up/retry",
            "12 hours is sum of agent caps, excludes grader/setup/operator pauses, not predicted runtime"]}


def build():
    manifest = json.loads((SUITE / "manifest.json").read_text())
    summary = json.loads((ROOT / SUMMARY).read_text())
    baseline = json.loads((ROOT / BASELINE).read_text())
    pricing = json.loads((ROOT / "research/provider-pricing.json").read_text())
    if pricing != baseline["pricing"] or pricing["output"] != "18":
        raise ValueError("Pricing changed; draft estimate must be reviewed")
    if manifest["status"] != "specification_only_not_ready_for_paid_runs":
        raise ValueError("This generator only handles the unapproved draft")
    for task in manifest["tasks"]:
        if not task["pending"] or not (SUITE / task["prompt"]).is_file():
            raise ValueError("Missing prompt or explicit readiness gates")
    order = make_order(manifest)
    files = ["benchmark/suite48/manifest.json", SUMMARY, BASELINE,
        "research/provider-pricing.json", "benchmark/plan48.py", "benchmark/test_plan48.py",
        "benchmark/PROTOCOL_48_DRAFT.md", "benchmark/suite48/README.md"]
    files += ["benchmark/suite48/" + task["prompt"] for task in manifest["tasks"]]
    planning = {"revision": "suite48-draft-r1", "status": "draft_not_approved_no_inference",
        "selected_design": "4 tasks x4 CLIs x3 repetitions", "planned_slots": 48,
        "run_ids_reserved": False, "paid_runs_authorized": False,
        "fixture_acceptance_ready": False, "protocol_frozen": False,
        "order_algorithm": "SHA-256-sort seed|tasks-N|id and seed|tools-N|id; rotate tool permutation by task block offset0..3 each round",
        "order_seed": SEED, "cache_policy": "uncontrolled, including repetitions; sessions/workspaces fresh",
        "position_balance": "each CLI appears3times in each position across12blocks; per-task balance not exact with3reps",
        "estimate": estimate(summary), "input_sha256": {name: sha(ROOT / name) for name in files},
        "pending": ["fixture/reference/mutant implementation and offline acceptance/seal",
            "grader and isolated runner integration; readonly/source scope for all four task types",
            "host resource snapshot before launch; no real session/service",
            "review/approve budget and final protocol; assign fresh R/C IDs only at launch"]}
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(order[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(order)
    return {"planning.json": json.dumps(planning, ensure_ascii=False, indent=2) + "\n", "order.csv": stream.getvalue()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    target = args.output_dir.resolve()
    if not target.is_relative_to(SUITE / "artifacts"):
        parser.error("Expected suite48 draft artifact directory")
    outputs = build()
    if args.verify:
        if any((target / name).read_text() != content for name, content in outputs.items()):
            raise ValueError("Draft inputs/output drift; create a reviewed new draft revision")
        print("PASS: draft48 order, estimate and input hashes; no paid execution")
    else:
        target.mkdir(parents=True, exist_ok=False)
        for name, content in outputs.items():
            (target / name).write_text(content)
        print("Created offline draft48 order/estimate; not benchmark results")


if __name__ == "__main__":
    main()
