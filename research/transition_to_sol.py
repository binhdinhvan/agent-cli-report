"""Data migration after explicit result deletion; no model/network/credential access."""
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/artifacts/SOL-MIGRATION-20261106-01"


def main():
    manifest = json.loads((AUDIT / "manifest.json").read_text())
    if (ROOT / "research/experiment-state.json").exists():
        raise SystemExit("Migration already recorded; do not reset new sol evidence/IDs")
    assert manifest["status"] in {"deleted", "migration_prepared"}
    assert all(not pathlib.Path(e["path"]).exists() for e in manifest["delete_targets"])
    evidence_path = ROOT / "research/evidence.csv"
    with evidence_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        rows = list(reader)
    withdrawn = []
    for row in rows:
        artifact = row["runtime_artifact"]
        if artifact and not (ROOT / artifact).is_file():
            old = row["evidence_status"]
            row["evidence_status"] = "source-confirmed" if old == "both" else "unverified"
            row["runtime_artifact"] = ""
            withdrawn.append(row["id"])
        if int(row["id"][2:]) >= 55 and not row["runtime_artifact"]:
            row["limitations"] = "Chỉ giữ bằng chứng source; runtime model cũ đã xóa theo yêu cầu; không suy runtime support của sol từ source"
    with evidence_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    runs_path = ROOT / "benchmark/runs.csv"
    with runs_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        run_columns = reader.fieldnames
        run_rows = list(reader)
    if any(r["model"] != "gpt-6-luna" for r in run_rows):
        raise RuntimeError("Non-luna run found: do not discard a sol/user run")
    with runs_path.open("w", newline="") as handle:
        csv.DictWriter(handle, fieldnames=run_columns, lineterminator="\n").writeheader()
    state = {"active_model": "gpt-6.1-sol", "provider_base_url": "https://api.shopaikey.com/v1",
             "pricing_status": "pending_user_rates", "paid_runs_ready": False,
             "retired_run_ids": [f"R-{n:04d}" for n in range(1, 9)],
             "retired_config_ids": [f"C-{n:04d}" for n in [*range(5, 39), 40]],
             "next_pilot_run_start": 9, "next_offline_config_start": 41,
             "next_smoke_config_start": 45, "next_pilot_config_start": 49,
             "preserved_sol_config_id": "C-0039",
             "note": "Retired IDs remain reserved after user-authorized deletion; no old run outcomes or logs retained in this registry"}
    (ROOT / "research/experiment-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    (AUDIT / "evidence-withdrawal.json").write_text(json.dumps({"downgraded_evidence_ids": withdrawn,
        "reason": "Runtime artifacts withdrawn at user request; source/permalinks retained", "removed_csv_rows": len(run_rows)}, ensure_ascii=False, indent=2) + "\n")
    manifest["status"] = "migration_prepared"
    (AUDIT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"active_model": state["active_model"], "pricing_status": state["pricing_status"],
        "withdrawn_runtime_evidence": len(withdrawn), "old_csv_rows_removed": len(run_rows), "paid_requests": 0}, indent=2))


if __name__ == "__main__":
    main()
