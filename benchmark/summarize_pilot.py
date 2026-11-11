"""Tổng hợp artifact pilot đã kết thúc; không model, key, retry hoặc sửa log gốc."""
import argparse
from collections import Counter
from decimal import Decimal
import datetime
import json
import pathlib
import sys

sys.dont_write_bytecode = True


def total(usages, key, parent=None):
    values = [(u.get(parent) or {}).get(key) if parent else u.get(key) for u in usages]
    return sum(values) if values and all(type(v) is int for v in values) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=pathlib.Path, required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    source, target = args.result.resolve(), args.output_dir.resolve()
    if not all(p.is_relative_to(root / "benchmark/artifacts") for p in [source, target]):
        parser.error("Expected benchmark artifact paths")
    data = json.loads(source.read_text())
    if data.get("mode") != "pilot" or not data.get("finished_at_utc"):
        parser.error("Only completed model pilot results may be summarized")
    target.mkdir(parents=True, exist_ok=False)
    rows = []
    for run in data["runs"]:
        requests = run["provider_requests"]
        usages = [q.get("cost", {}).get("usage") or {} for q in requests]
        costs = [q.get("cost", {}).get("estimated_cost_usd") for q in requests]
        counts = Counter(str(q.get("http_status", "no_http_status")) for q in requests)
        gaps = []
        for previous, current in zip(requests, requests[1:]):
            before, after = previous.get("finished_at_utc"), current.get("started_at_utc")
            seconds = (datetime.datetime.fromisoformat(after) - datetime.datetime.fromisoformat(before)).total_seconds() if before and after else None
            gaps.append({"request_index": current["request_index"], "seconds_after_previous_response": seconds})
        configured_gap = data.get("request_gap_seconds_after_response", 0)
        rows.append({"run_id": run["run_id"], "task_id": run["task_id"], "tool": run["tool"],
            "status": run["status"], "validity": run["validity"], "generation_group": run["generation_group"],
            "agent_duration_ms": run["execution"]["duration_ms"], "grader_duration_ms": run["grading"]["duration_ms"],
            "isolation_ok": run["isolation_ok"], "source_scope_ok": run["grading"]["scope_ok"],
            "public_exit": run["grading"]["suites"]["public"]["exit_code"],
            "hidden_exit": run["grading"]["suites"]["hidden"]["exit_code"],
            "provider_requests": len(requests), "http_counts": dict(counts),
            "configured_request_gap_seconds": configured_gap, "observed_gaps": gaps,
            "known_gaps_satisfy_policy": all(g["seconds_after_previous_response"] is not None and g["seconds_after_previous_response"] >= configured_gap - 0.001 for g in gaps) if gaps else None,
            "input_tokens": total(usages, "input_tokens"), "output_tokens": total(usages, "output_tokens"),
            "cached_input_tokens": total(usages, "cached_tokens", "input_tokens_details"),
            "reasoning_tokens": total(usages, "reasoning_tokens", "output_tokens_details"),
            "estimated_cost_usd": str(sum(Decimal(c) for c in costs)) if costs and all(c is not None for c in costs) else None,
            "wire_reasoning_values": [q.get("generation_settings", {}).get("reasoning") for q in requests]})
    result = {"source": str(source.relative_to(root)), "scope": "Pilot descriptive summary, not benchmark ranking",
              "planned": len(data["plan"]), "executed": len(rows), "success": sum(r["status"] == "success" for r in rows),
              "not_run": sum(p["status"] == "not_run" for p in data["plan"]),
              "stop_reason": data.get("stop_reason"), "known_usage_estimated_cost_usd": data.get("known_usage_estimated_cost_usd"),
              "estimated_total_usd": data.get("estimated_total_usd"), "measured_charge_usd": None, "runs": rows,
              "prior_unpriced_request_count": data.get("prior_unpriced_request_count"),
              "cumulative_known_usage_estimated_cost_usd": data.get("cumulative_known_usage_estimated_cost_usd"),
              "cumulative_estimated_total_usd": data.get("cumulative_estimated_total_usd"),
              "limitations": ["Rates user-reported, usage provider-reported, charge not invoice-confirmed",
                              "Native generation groups differ; do not rank tools from pilot",
                              "Missing usage/cache/reasoning remain null, not zero",
                              "Runtime spec status/timestamps inherited from release preparation; use per-run status/timestamps"]}
    (target / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
