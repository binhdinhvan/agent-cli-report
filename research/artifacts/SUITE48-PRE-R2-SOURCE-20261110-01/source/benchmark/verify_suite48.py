"""Offline suite48 reference/mutant/self-test seal. Not a paid runner or benchmark."""
import argparse
import datetime
import json
import pathlib
import shutil
import tempfile

from suite48_runtime import ROOT, SUITE, digest, grade, passed, sandbox
from suite48_solutions import variants, writer_source


def expected_failure(task_id, label, grading):
    if grading["pass"] or not grading["scope_ok"]:
        return False
    hidden = grading["suites"]["hidden"]
    # Require a unittest failure/error report, not bwrap launch/import of the harness failing.
    meaningful = (hidden["exit_code"] == 1 and not hidden["timed_out"] and
                  not hidden["output_limit_exceeded"] and "Ran " in hidden["stderr"] and "FAILED (" in hidden["stderr"])
    if task_id == "B-01" and label.startswith(("wrong_value_", "wrong_evidence_")):
        meaningful = meaningful and grading["rubric"] is not None and grading["rubric"]["total"] == 9
    return meaningful


def build(artifact):
    artifact.mkdir(parents=True, exist_ok=False)
    result = {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Offline supervisor-authored reference/mutants; NOT native CLI/provider or benchmark results",
        "fixture_version": 1, "status": "pending", "paid_runs_authorized": False,
        "native_paid_runner_integration": "pending; this runner only applies trusted stdlib writers offline",
        "files_sha256": {}, "tasks": []}
    source = [ROOT / "benchmark/verify_suite48.py", ROOT / "benchmark/suite48_runtime.py",
        ROOT / "benchmark/suite48_entry.py", ROOT / "benchmark/suite48_solutions.py", ROOT / "benchmark/test_suite48.py"]
    for name in source:
        result["files_sha256"][str(name.relative_to(ROOT))] = digest(name)
    for task_id in ("B-01", "B-02", "B-03", "B-04"):
        task = SUITE / task_id
        for path in sorted(task.rglob("*")):
            if path.is_file():
                result["files_sha256"][str(path.relative_to(ROOT))] = digest(path)
        record = {"task_id": task_id, "checks": []}
        for label, files in variants(task_id).items():
            output = artifact / task_id / label
            output.mkdir(parents=True)
            with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="suite48-selftest-") as temporary:
                base = pathlib.Path(temporary)
                project = base / "project"
                shutil.copytree(task / "fixture", project)
                writer = output / "apply.py"
                writer.write_text(writer_source(files))
                execution = sandbox(project, task_id, "execute", writer)
                (output / "execution.json").write_text(json.dumps(execution, ensure_ascii=False, indent=2) + "\n")
                grading = grade(project, task_id, output / "grader")
            witness = execution["witness"]
            isolation = (witness and all(witness["readonly"].values()) and witness["hidden_absent"] and
                witness["real_home_absent"] and witness["net_namespace"] != execution["host_net_namespace"])
            if label == "reference":
                expected = grading["pass"]
            else:
                expected = expected_failure(task_id, label, grading)
                if label == "baseline" and task_id != "B-01":
                    expected = expected and passed(grading["suites"]["public"])
            check = {"variant": label, "writer_completed": passed(execution), "isolation_ok": bool(isolation),
                "scope_ok": grading["scope_ok"], "grading_pass": grading["pass"],
                "expectation_met": bool(passed(execution) and isolation and expected),
                "source": str((output / "grader/grading.json").relative_to(ROOT))}
            record["checks"].append(check)
            print(task_id, label, "PASS" if check["expectation_met"] else "FAIL", flush=True)
        record["status"] = "pass" if all(c["expectation_met"] for c in record["checks"]) else "failure"
        result["tasks"].append(record)
    result["status"] = "pass" if all(task["status"] == "pass" for task in result["tasks"]) else "failure"
    result["offline_variant_checks"] = sum(len(task["checks"]) for task in result["tasks"])
    result["artifact_sha256"] = {str(path.relative_to(artifact)): digest(path)
        for path in sorted(artifact.rglob("*")) if path.is_file()}
    (artifact / "preparation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def verify(artifact):
    seal = json.loads((artifact / "preparation.json").read_text())
    if seal["status"] != "pass":
        raise ValueError("Offline acceptance did not pass")
    for name, expected in seal["files_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("Sealed source/fixture drift: " + name)
    for task in seal["tasks"]:
        folder = SUITE / task["task_id"]
        actual = {str(path.relative_to(ROOT)) for path in folder.rglob("*") if path.is_file()}
        expected = {name for name in seal["files_sha256"] if name.startswith(str(folder.relative_to(ROOT)) + "/")}
        if actual != expected:
            raise ValueError("Sealed task file inventory drift")
    for name, expected in seal["artifact_sha256"].items():
        if digest(artifact / name) != expected:
            raise ValueError("Sealed offline artifact drift: " + name)
    if {str(path.relative_to(artifact)) for path in artifact.rglob("*") if path.is_file()} != set(seal["artifact_sha256"]) | {"preparation.json"}:
        raise ValueError("Sealed offline artifact inventory drift")
    for task in seal["tasks"]:
        for check in task["checks"]:
            outcome = json.loads((ROOT / check["source"]).read_text())
            if outcome["pass"] != check["grading_pass"] or not check["expectation_met"]:
                raise ValueError("Offline result drift")
    return seal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / "artifacts"):
        parser.error("Expected suite48 artifact path")
    result = verify(artifact) if args.verify else build(artifact)
    print(json.dumps({"status": result["status"], "offline_variant_checks": result["offline_variant_checks"],
        "paid_runs_authorized": False, "native_paid_runner_integration": result["native_paid_runner_integration"]}, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
