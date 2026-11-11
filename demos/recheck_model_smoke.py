"""Chấm lại log đã có bằng parser sửa lỗi; không chạy agent/provider, không ghi đè kết quả cũ."""
import argparse
import json
import pathlib
import sys

sys.dont_write_bytecode = True
from model_smoke import ROOT, acceptance, now, sha256, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=pathlib.Path, required=True)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    source = args.result.resolve()
    target = args.artifact_dir.resolve()
    if not all(p.is_relative_to(ROOT / "demos/artifacts") for p in [source, target]):
        parser.error("Paths must be under demos/artifacts")
    original = json.loads(source.read_text())
    if not original.get("finished_at_utc"):
        parser.error("Only completed run artifacts may be re-evaluated")
    target.mkdir(parents=True, exist_ok=False)
    result = {"evaluated_at_utc": now(), "scope": "Offline re-evaluation of unchanged logs; no new CLI/provider run",
              "reason": "Codex final_message is last completed agent_message; progress must not be concatenated into final",
              "original_result": str(source.relative_to(ROOT)), "original_result_sha256": sha256(source),
              "evaluator_sha256": sha256(pathlib.Path(__file__)), "parser_sha256": sha256(ROOT / "demos/model_smoke.py"),
              "source_evidence": "E-0065", "runs": []}
    for run in original["runs"]:
        stdout_path = source.parent / (run["spec"]["config_id"] + ".stdout.jsonl")
        checks = {**run["checks"], **acceptance(run["spec"]["tool"], stdout_path.read_text())}
        required = ["successful_local_read_observed", "final_exact_marker", "fixture_unchanged", "isolated_network", "real_home_hidden", "provider_completed"]
        status = "pass" if run["exit_code"] == 0 and all(checks[k] for k in required) else "failure"
        result["runs"].append({"run_id": run["run_id"], "config_id": run["spec"]["config_id"],
                              "original_status": run["status"], "reevaluated_status": status, "checks": checks,
                              "stdout_sha256": sha256(stdout_path), "exit_code": run["exit_code"]})
    write(target / "evaluation.json", result)
    print(json.dumps({"artifact": str(target.relative_to(ROOT) / "evaluation.json"),
                      "statuses": [r["reevaluated_status"] for r in result["runs"]]}, indent=2))


if __name__ == "__main__":
    main()
