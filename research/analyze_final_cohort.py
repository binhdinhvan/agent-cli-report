"""Read-only derived metrics for the fixed OpenAI48 r3 cohort; no API or key access."""
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "benchmark/suite48/artifacts/OPENAI48-R3-20261110-01/benchmark"
TOOLS = ("opencode-v1", "opencode-v2", "pi", "codex")


def summarize(runs):
    requests = [request for run in runs for request in run["requests"]]
    usage = [request["cost"]["usage"] for request in requests]
    return {
        "runs": len(runs),
        "requests": len(requests),
        "requests_per_run": len(requests) / len(runs),
        "input_per_request": sum(u["input_tokens"] for u in usage) / len(requests),
        "cache_read_per_request": sum(q["cost"]["cached_input_tokens"] for q in requests) / len(requests),
        "cache_write_per_request": sum(q["cost"]["cache_write_tokens"] for q in requests) / len(requests),
        "output_per_request": sum(u["output_tokens"] for u in usage) / len(requests),
        "median_e2e_seconds": statistics.median(r["execution"]["duration_ms"] / 1000 for r in runs),
        "median_pacing_seconds": statistics.median(sum(q["pacing_wait_seconds"] for q in r["requests"]) for r in runs),
        "median_native_seconds": statistics.median(r["execution"]["native_clock"]["duration_ms"] / 1000 for r in runs),
    }


def main():
    runs = []
    hashes = {}
    groups = defaultdict(list)
    for path in sorted(RAW.glob("D48-*/result.json")):
        data = path.read_bytes()
        run = json.loads(data)
        assert run["validity"] == "valid" and not run["synthetic_usage"]
        assert len(run["requests"]) == run["provider_requests"]
        assert all(q["http_status"] == 200 and q["terminal_type"] == "response.completed" for q in run["requests"])
        runs.append(run)
        groups[run["task_id"], run["tool"]].append(run)
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    assert len(runs) == 48 and len({r["slot"] for r in runs}) == 48
    assert sum(r["status"] == "success" for r in runs) == 46
    assert sum(r["provider_requests"] for r in runs) == 278
    assert len(groups) == 16 and all(len(group) == 3 for group in groups.values())
    print(json.dumps({
        "scope": "derived from existing raw; all 48 runs including two failures; no new experiment",
        "definitions": {
            "per_request": "ratio of summed reported tokens to upstream request count; not mean of run means",
            "pacing": "sum of logged pacing_wait_seconds per run; includes cross-run waits charged to that run",
            "native": "logged native_clock; includes its own model/tool waits and pacing; not CPU time",
            "timing": "medians computed separately; do not subtract medians to derive CLI overhead",
        },
        "tools": {tool: summarize([r for r in runs if r["tool"] == tool]) for tool in TOOLS},
        "tasks": {task: {tool: summarize(groups[task, tool]) for tool in TOOLS} for task in sorted({r["task_id"] for r in runs})},
        "source_sha256": hashes,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
