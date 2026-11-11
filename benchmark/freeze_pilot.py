"""Tổng hợp toàn pilot và khóa baseline offline; không gọi CLI/provider hoặc đọc key."""
import argparse
from collections import Counter
import csv
from decimal import Decimal
import hashlib
import json
import pathlib

from summarize_pilot import total

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "benchmark/artifacts/PILOT-FREEZE-20261109-01"
REVIEW = "research/artifacts/SOL-PILOT-REVIEW-20261106-01/validation.json"
LAUNCH = "research/artifacts/SEARCH-R2-LAUNCH-RECOVERY-20261109-01/launch-failure.json"
COHORT = ["R-0035", "R-0036", "R-0037", "R-0038"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reviewed(run, review):
    if run["run_id"] != review["run_id"]:
        return run["status"], run["validity"]
    if (run["status"], run["validity"]) != (review["raw_status"], review["raw_validity"]):
        raise ValueError("Review no longer matches raw status")
    return review["reviewed_status"], review["reviewed_validity"]


def cost_summary(requests):
    costs = [q.get("cost", {}).get("estimated_cost_usd") for q in requests]
    known = sum((Decimal(c) for c in costs if c is not None), Decimal(0))
    missing = sum(c is None for c in costs)
    return {"known_usage_estimated_cost_usd": str(known), "unpriced_requests": missing,
            "estimated_total_usd": None if missing else str(known), "measured_charge_usd": None}


def build(root=ROOT):
    inputs, batches, runs, requests, seen = {}, {}, [], [], set()

    def pin(path):
        path = pathlib.Path(path)
        if path.is_absolute():
            path = path.relative_to(root)
        inputs[str(path)] = sha(root / path)

    def load(path):
        pin(path)
        return json.loads((root / path).read_text())

    review = load(REVIEW)
    # Bind the override to the reviewed bytes, not only the historical run ID.
    review_root = pathlib.Path("benchmark/artifacts/PILOT-SOL-20261106-01")
    for name, digest in review["raw_artifact_sha256"].items():
        pin(review_root / name)
        if inputs[str(review_root / name)] != digest:
            raise ValueError("Reviewed raw artifact changed: " + name)
    for index in ["benchmark/runs.csv", "benchmark/runs-search-r2.csv"]:
        pin(index)
        with (root / index).open() as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            folder = pathlib.Path(row["artifact_path"])
            run = load(folder / "result.json")
            rid = run["run_id"]
            if rid != row["run_id"] or rid in seen:
                raise ValueError("Duplicate or mismatched run ID: " + rid)
            seen.add(rid)
            batch_path = str(folder.parent / "result.json")
            if batch_path not in batches:
                batches[batch_path] = load(batch_path)
            batch = batches[batch_path]
            if batch.get("mode") != "pilot" or not batch.get("finished_at_utc"):
                raise ValueError("Unfinished/non-pilot batch")
            if run not in batch["runs"]:
                raise ValueError("Run differs from parent batch")
            for artifact in sorted((root / folder).rglob("*")):
                if artifact.is_file():
                    pin(artifact)
            status, validity = reviewed(run, review)
            qs = run["provider_requests"]
            usages = [q.get("cost", {}).get("usage") or {} for q in qs]
            requests.extend(qs)
            runs.append({"run_id": rid, "task_id": run["task_id"], "tool": run["tool"],
                "raw_status": run["status"], "raw_validity": run["validity"],
                "reviewed_status": status, "reviewed_validity": validity,
                "review_override": REVIEW if rid == review["run_id"] else None,
                "source": str(folder / "result.json"), "batch": batch_path,
                "retry_of": run.get("retry_of"), "timing_recheck_of": batch.get("timing_recheck_of"),
                "environment_revision": run.get("environment_revision", "legacy"),
                "timing_policy": batch.get("timing_policy", "legacy-300"),
                "generation_group": run["generation_group"],
                "duration_ms_including_pacing": run["execution"]["duration_ms"],
                "scope_public_hidden_pass": run["grading"]["pass"],
                "upstream_requests": len(qs), **cost_summary(qs),
                "input_tokens": total(usages, "input_tokens"),
                "output_tokens": total(usages, "output_tokens"),
                "cached_input_tokens": total(usages, "cached_tokens", "input_tokens_details"),
                "reasoning_tokens": total(usages, "reasoning_tokens", "output_tokens_details"),
                "wire_reasoning_values": [q.get("generation_settings", {}).get("reasoning") for q in qs]})
    coverage = sorted({(r["task_id"], r["tool"]) for r in runs if r["reviewed_status"] == "success"})
    cohort = [next(r for r in runs if r["run_id"] == rid) for rid in COHORT]
    if any(r["environment_revision"] != "search-r2" or r["timing_policy"] != "paced-900" for r in cohort):
        raise ValueError("P-02 cohort is not homogeneous in environment/timing")
    launch = load(LAUNCH)
    summary = {"scope": "Tổng hợp pilot mô tả; không phải benchmark hoặc xếp hạng",
        "inference_attempts": len(runs), "upstream_requests": len(requests),
        "reviewed_status_counts": dict(Counter(r["reviewed_status"] for r in runs)),
        "raw_status_counts": dict(Counter(r["raw_status"] for r in runs)),
        "coverage_pairs": [list(pair) for pair in coverage], "coverage_pair_count": len(coverage),
        **cost_summary(requests), "launch_errors_without_inference": [{"source": LAUNCH, "record": launch}],
        "runs": runs, "p02_cohort_execution_order": COHORT,
        "p02_cohort_known_estimate_usd": str(sum(Decimal(r["known_usage_estimated_cost_usd"]) for r in cohort)),
        "limitations": ["Coverage không phải 8/8 first-attempt success; không gộp revision để xếp hạng",
            "Giữ toàn bộ retry/failure; snapshot pass không nâng CLI timeout thành success",
            "Usage thiếu là null, không phải 0; giá user-reported, charge chưa đối soát",
            "n=1/CLI ở P-02; thứ tự không randomized; native prompts/tools/reasoning khác nhau",
            "Backend revision và cache không kiểm soát; không suy causal từ cap900 hoặc duration"]}
    pins = []
    for row in cohort:
        run = json.loads((root / row["source"]).read_text())
        spec = run["spec"]
        binary = pathlib.Path(spec["binary"])
        if sha(binary) != spec["binary_sha256"]:
            raise ValueError("Binary drift: " + row["tool"])
        pin(binary)
        config = str(pathlib.Path(row["source"]).parent / "config.json")
        pins.append({"tool": row["tool"], "version": spec["version"], "tag": spec["tag"],
            "commit": spec["commit"], "binary_sha256": spec["binary_sha256"],
            "config_reference": config, "config_sha256": inputs[config],
            "native_generation_group": row["generation_group"],
            "wire_reasoning_values": row["wire_reasoning_values"]})
    seal_path = "benchmark/artifacts/PILOT-PREP-20261106-02/preparation.json"
    seal = load(seal_path)
    for task in seal["tasks"]:
        for name, digest in task["files"].items():
            path = "benchmark/tasks/" + task["task_id"] + "/" + name
            pin(path)
            if inputs[path] != digest:
                raise ValueError("Fixture drift: " + path)
    env = load("research/environment-profiles/search-r2.json")
    pin(pathlib.Path(env["common_bin"]) / "rg")
    if inputs[str(pathlib.Path(env["common_bin"]) / "rg")] != env["executables"]["rg"]["sha256"]:
        raise ValueError("Dependency drift")
    # Pin both current workspace implementation and the launch snapshots actually used.
    source_paths = set()
    for batch in batches.values():
        source_paths.update(batch["script_sha256"])
    source_paths.update(["benchmark/freeze_pilot.py", "benchmark/summarize_pilot.py",
        "benchmark/test_freeze_pilot.py", "demos/timing_policy.py",
        "benchmark/BASELINE.md",
        "benchmark/TIMING_POLICY_R2.md", "benchmark/ENVIRONMENT_R2.md",
        "benchmark/PILOT_PACED_900_COMPLETE.md", "benchmark/PILOT_PACED_900_RECHECK.md"])
    for name in sorted(source_paths):
        pin(name)
    for folder in ["PACED-900-COMPLETE-LAUNCH-20261109-01", "PACED-900-RECHECK-LAUNCH-20261109-01"]:
        for path in sorted((root / "research/artifacts" / folder).rglob("*")):
            if path.is_file():
                pin(path)
    for label, row in [("RECHECK", cohort[0]), ("COMPLETE", cohort[-1])]:
        batch = batches[row["batch"]]
        snapshot = pathlib.Path("research/artifacts") / f"PACED-900-{label}-LAUNCH-20261109-01/source"
        for name, digest in batch["script_sha256"].items():
            saved = snapshot / name
            pin(saved)
            if inputs[str(saved)] != digest:
                raise ValueError("Launch snapshot differs from executed source: " + name)
        for name, digest in [("research/environment-profiles/search-r2.json", batch["environment_manifest_sha256"]),
                             (seal_path, batch["fixture_seal_sha256"]),
                             ("research/provider-pricing.json", batch["pricing_sha256"]),
                             (f"benchmark/PILOT_PACED_900_{label}.md", batch["protocol_sha256"])]:
            pin(name)
            if inputs[name] != digest:
                raise ValueError("Executed policy/input drift: " + name)
        audit_path = f"research/artifacts/PACED-900-{label}-REVIEW-20261109-01/validation.json"
        audit = load(audit_path)
        batch_folder = pathlib.Path(row["batch"]).parent
        for name, digest in audit["raw_artifact_sha256"].items():
            path = batch_folder / name
            pin(path)
            if inputs[str(path)] != digest:
                raise ValueError("Audited raw drift: " + str(path))
    latest = batches[cohort[-1]["batch"]]
    baseline = {"baseline_revision": "pilot-search-r2-paced-900-20261109-r1", "date": "2026-11-09",
        "scope": "Baseline pilot frozen offline; benchmark protocol pending; no paid authorization",
        "benchmark_protocol_approved": False, "paid_runs_authorized": False,
        "model": latest["model"], "provider": latest["provider"],
        "protocol_transport": "Responses SSE qua broker/bridge cách ly",
        "environment_profile": env, "host_environment_at_run": latest["environment"],
        "timing_policy": latest["timing_policy"], "timing_limits": latest["timing_limits"],
        "concurrency": 1, "gap_seconds_after_response_including_cross_cli": 30,
        "provider_failure_or_missing_usage": "stop batch; block local native retries; preserve raw",
        "insufficient_reserve": "local408/time_window_exhausted; no upstream; not provider overload",
        "pilot_guard_usd_estimate": "3", "guard_is_invoice_cap": False,
        "pricing": load("research/provider-pricing.json"), "pins": pins,
        "fixtures": [{"task_id": t["task_id"], "version": t["fixture_version"], "files": t["files"]} for t in seal["tasks"]],
        "fixture_seal": seal_path, "grading": "CLI completion + scope + public + hidden; grader outside agent",
        "isolation": "bwrap private network/home/XDG/session; host key broker; dependencies/public read-only; source writable; hidden absent",
        "native_settings_equivalent": False, "backend_revision": None, "cache_control": "uncontrolled",
        "pending_benchmark": ["4/6 task và acceptance/rubric", "48/72 lượt và budget mới",
            "duyệt protocol chính thức", "order/seed", "duration/usage/exclusion/retry rules và tài nguyên máy"],
        "input_sha256": dict(sorted(inputs.items()))}
    return summary, baseline


def render(summary):
    lines = ["# Tổng kết pilot đã khóa", "", "Không phải benchmark chính thức hoặc xếp hạng tool.", "",
        f"- {summary['inference_attempts']} inference attempts / {summary['upstream_requests']} upstream requests; 1 launch-error riêng, không inference.",
        f"- Reviewed: {summary['reviewed_status_counts']}; coverage {summary['coverage_pair_count']} cặp có success, không phải 8/8 first-attempt.",
        f"- Known estimate **{summary['known_usage_estimated_cost_usd']} USD**; {summary['unpriced_requests']} request unpriced; total/charge **unknown**.", "",
        "## Mọi inference attempt (thứ tự CSV legacy rồi search-r2)", "",
        "| Run | Task / CLI | Environment / timing | Raw → reviewed | Requests | ms gồm pacing | Known USD / unpriced |",
        "| --- | --- | --- | --- | ---: | ---: | --- |"]
    for r in summary["runs"]:
        lines.append(f"| {r['run_id']} | {r['task_id']} / {r['tool']} | {r['environment_revision']} / {r['timing_policy']} | {r['raw_status']}/{r['raw_validity']} → {r['reviewed_status']}/{r['reviewed_validity']} | {r['upstream_requests']} | {r['duration_ms_including_pacing']} | {r['known_usage_estimated_cost_usd']} / {r['unpriced_requests']} |")
    lines.extend(["", "## P-02: search-r2 / paced-900", "", "Thứ tự thực tế v2 → v1 → Codex → Pi; n=1/CLI, không randomized. Mọi lượt success/valid, scope/public/hidden pass; native settings không tương đương.", "",
        "| Run / CLI | Requests | ms gồm pacing | Estimate USD |",
        "| --- | ---: | ---: | ---: |"])
    for rid in summary["p02_cohort_execution_order"]:
        r = next(r for r in summary["runs"] if r["run_id"] == rid)
        lines.append(f"| {rid} / {r['tool']} | {r['upstream_requests']} | {r['duration_ms_including_pacing']} | {r['known_usage_estimated_cost_usd']} |")
    lines.extend(["", f"Tổng cohort {summary['p02_cohort_known_estimate_usd']} USD, không phải tổng pilot.", "",
        "Nguồn, lineage/review override, token/cache/reasoning (null khi thiếu): `summary.json`; pins/config/fixture/source hashes: `baseline.json`.", "",
        *["- " + text for text in summary["limitations"]], ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    target = args.output_dir.resolve()
    if not target.is_relative_to(ROOT / "benchmark/artifacts"):
        parser.error("Expected benchmark artifact directory")
    summary, baseline = build()
    outputs = {"summary.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        "baseline.json": json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
        "SUMMARY.md": render(summary)}
    if args.verify:
        for name, content in outputs.items():
            if (target / name).read_text() != content:
                raise ValueError("Frozen output/input drift: " + name)
        print("PASS: frozen outputs, ledger, review, fixture/dependency/binary and source hashes; offline only")
    else:
        target.mkdir(parents=True, exist_ok=False)
        for name, content in outputs.items():
            (target / name).write_text(content)
        print("Created offline pilot summary/baseline: " + str(target.relative_to(ROOT)))


if __name__ == "__main__":
    main()
