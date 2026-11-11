"""Audit riêng đợt offline: không gọi HTTP/provider hoặc native CLI/service."""

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/artifacts/OFFLINE-TASKS-20261110-01"
DOCS = ["README.md", "PLAN.md", "REPORT.md", "demos/README.md", "demos/OFFLINE_DEMO_PLAN.md"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, capture_output=True, timeout=120)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    checks = {}
    for name, args in {
        "evidence": [sys.executable, "-B", "research/validate_evidence.py"],
        "frozen": [sys.executable, "-B", "benchmark/freeze_pilot.py", "--verify"],
        "fixture_tests": [sys.executable, "-B", "-m", "unittest", "discover", "-s", "demos",
                          "-p", "test_background_fixture.py", "-v"],
    }.items():
        result = run(args)
        (OUT / (name + ".stdout.txt")).write_bytes(result.stdout)
        (OUT / (name + ".stderr.txt")).write_bytes(result.stderr)
        checks[name] = {"exit_code": result.returncode, "command": args}
        assert result.returncode == 0, name
    rows = list(csv.DictReader((ROOT / "research/evidence.csv").open()))
    index = {row["id"]: row for row in rows}
    links = []
    for name in DOCS:
        text = (ROOT / name).read_text()
        assert text.count("<details>") == text.count("</details>"), name
        for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
            evidence = re.match(r"(E-\d{4})(?:\b|:)", label)
            if evidence:
                assert index[evidence[1]]["permalink"] == target, (name, label)
            if "://" not in target and not target.startswith("#"):
                assert ((ROOT / name).parent / target.split("#", 1)[0]).exists(), (name, target)
            links.append({"document": name, "label": label, "target": target})
        # Heuristic trên docs được công bố; không đọc credential/private logs.
        assert not re.search(r"\bsk-[A-Za-z0-9_-]{24,}\b|Bearer\s+[A-Za-z0-9_.-]{24,}", text), name
    cases = re.findall(r"^\| ((?:BG|PL|PM|CT|SDK)-\d{2}) \|", (ROOT / DOCS[-1]).read_text(), re.M)
    assert len(cases) == len(set(cases)) == 15
    snapshots = []
    selected = [r for r in rows if 118 <= int(r["id"][2:]) <= 124]
    for path in sorted({r["file"] for r in selected}):
        row = next(r for r in selected if r["file"] == path)
        result = run(["git", "--no-optional-locks", "show", row["commit"] + ":" + path], ROOT.parent / "opencode-v2")
        assert result.returncode == 0
        dest = OUT / "source/opencode-v2" / row["commit"] / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(result.stdout)
        snapshots.append({"commit": row["commit"], "file": path, "snapshot": str(dest.relative_to(ROOT)), "sha256": sha(dest)})
    review = json.loads((ROOT / "research/artifacts/BENCH48-REVIEW-20261110-01/validation.json").read_text())
    batch = ROOT / "benchmark/suite48/artifacts/BENCH48-20261110-01"
    for path, expected in review["raw_artifact_sha256"].items():
        assert sha(batch / path) == expected, path
    state = json.loads((ROOT / "research/experiment-state.json").read_text())
    assert not state["paid_runs_ready"]
    assert not state["user_requested_benchmark_pause"]["new_inference_or_network_probe_authorized"]
    assert (state["next_pilot_run_start"], state["next_pilot_config_start"]) == (87, 188)
    git = {}
    for repo in ["opencode-v1", "opencode-v2", "pi", "codex"]:
        result = run(["git", "--no-optional-locks", "status", "--porcelain"], ROOT.parent / repo)
        assert result.returncode == 0 and not result.stdout, repo
        git[repo] = result.stdout.decode()
    files = DOCS + ["research/evidence.csv", "research/experiment-state.json",
                    "research/audit_offline_tasks.py", "demos/fixtures/background_worker.py",
                    "demos/test_background_fixture.py"]
    # Lưu code/doc revision riêng, không chỉ hash của file có thể đổi ở lượt sau.
    hashes = {}
    for name in files:
        dest = OUT / "workspace" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / name).read_bytes())
        hashes[name] = sha(dest)
    report = {
        "status": "pass", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Offline source and research fixture tests only; no native tool/plugin/service execution",
        "checks": checks, "evidence_count": len(rows), "new_ids": [r["id"] for r in selected],
        "sources": snapshots, "workspace_sha256": hashes, "links_checked": links,
        "acceptance_cases": cases, "native_demo_acceptance": "unverified",
        "source_git_status": git, "raw_benchmark_retention": "pass against prior review hashes",
        "new_provider_requests": 0, "network_probes": 0, "external_urls_fetched": False,
        "paid_gate": False, "next_registry_ids": ["R-0087", "C-0188"],
        "secret_scan": "heuristic docs only; not a full publication privacy audit",
        "limitations": ["6 tests cover research fixture only, not OpenCode background or recovery",
                         "Source validator checks locations/links, not runtime semantics or URL availability",
                         "Native plugin/permission/SDK/UI/context demos remain pending"],
    }
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PASS: offline recovery source, 6 fixture tests, 15 acceptance cases; links/frozen/raw/gates/Git")


if __name__ == "__main__":
    main()
