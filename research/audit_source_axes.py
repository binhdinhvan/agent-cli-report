"""Audit offline: snapshot source E87–117, links và retention; không chạy tool native."""

import csv
import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "research/artifacts/SOURCE-REPORT-AXES-20261110-02"
REPOS = {"OpenCode v1": "opencode-v1", "OpenCode v2": "opencode-v2",
         "Pi": "pi", "Codex CLI": "codex"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, timeout=120)


def main():
    # Không ghi đè revision audit cũ.
    OUT.mkdir(parents=True, exist_ok=False)
    checks = {}
    for name, args in {
        "evidence_validator": ["python3", "-B", "research/validate_evidence.py"],
        "frozen_pilot": ["python3", "-B", "benchmark/freeze_pilot.py", "--verify"],
    }.items():
        checks[name] = run(args).decode()
    rows = list(csv.DictReader((ROOT / "research/evidence.csv").open()))
    selected = [row for row in rows if 87 <= int(row["id"][2:]) <= 117]
    sources = {}
    for row in selected:
        repo = REPOS[row["tool"]]
        key = (repo, row["commit"], row["file"])
        if key in sources:
            continue
        data = run(["git", "--no-optional-locks", "show", row["commit"] + ":" + row["file"]], ROOT.parent / repo)
        dest = OUT / "source" / repo / row["commit"] / row["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        sources[key] = {"repo": repo, "commit": row["commit"], "file": row["file"],
                        "snapshot": str(dest.relative_to(ROOT)), "sha256": digest(data)}
    previous = json.loads((ROOT / "research/artifacts/BENCH48-REVIEW-20261110-01/validation.json").read_text())
    retained = previous["raw_artifact_sha256"]
    batch_root = ROOT / "benchmark/suite48/artifacts/BENCH48-20261110-01"
    assert all(digest((batch_root / name).read_bytes()) == sha for name, sha in retained.items())
    state = json.loads((ROOT / "research/experiment-state.json").read_text())
    assert not state["paid_runs_ready"]
    assert not state["user_requested_benchmark_pause"]["new_inference_or_network_probe_authorized"]
    assert state["next_pilot_run_start"] == 87
    assert state["next_pilot_config_start"] == 188
    links = []
    for name in ["README.md", "PLAN.md", "REPORT.md"]:
        text = (ROOT / name).read_text()
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            assert (ROOT / path).exists(), (name, path)
            links.append({"document": name, "target": target})
    statuses = {repo: run(["git", "--no-optional-locks", "status", "--porcelain"], ROOT.parent / repo).decode()
                for repo in REPOS.values()}
    assert not any(statuses.values()), "Source repo có thay đổi; không tự xóa hoặc revert"
    report = {
        "scope": "Đọc pinned source offline; không provider/network/native binary/plugin/service",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_ids_total": len(rows), "audited_ids": [r["id"] for r in selected],
        "checks": checks, "sources": list(sources.values()), "source_git_status": statuses,
        "raw_benchmark_root": str(batch_root.relative_to(ROOT)),
        "raw_benchmark_retained": retained, "local_links_checked": links,
        "previous_attempt": "SOURCE-REPORT-AXES-20261110-01 incomplete: audit relative-path error; snapshots retained",
        "external_urls_fetched": False, "new_provider_requests": 0, "network_probes": 0,
        "paused_gate_checked": True, "next_registry_ids": ["R-0087", "C-0188"],
        "manual_review": "Đã đọc các nhánh được dẫn; claim mới source-confirmed; không phải runtime acceptance",
        "limitations": ["Validator kiểm cấu trúc không chứng minh semantics hoặc URL availability",
                         "Chưa trace hết recovery consumer; chưa demo disconnect/restart/plugin port",
                         "Không kiểm process/service đang dùng; chỉ kiểm gates offline"],
        "document_sha256": {name: digest((ROOT / name).read_bytes()) for name in
                            ["README.md", "PLAN.md", "REPORT.md", "research/evidence.csv",
                             "research/experiment-state.json", "research/audit_source_axes.py"]},
    }
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"PASS: {len(selected)} evidence rows, {len(sources)} pinned snapshots; frozen/raw/link/gates/Git checks")


if __name__ == "__main__":
    main()
