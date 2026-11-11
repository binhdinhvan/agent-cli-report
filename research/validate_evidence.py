"""Kiểm tra cấu trúc evidence và source locations chỉ đọc; không chứng minh claim đúng."""

import csv
import pathlib
import re
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOS = {
    "OpenCode v1": ("opencode-v1", "anomalyco/opencode"),
    "OpenCode v2": ("opencode-v2", "anomalyco/opencode"),
    "Pi": ("pi", "earendil-works/pi"),
    "Codex CLI": ("codex", "openai/codex"),
}


def main():
    with (ROOT / "research/evidence.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen = set()
    sources = {}
    errors = []
    for row in rows:
        try:
            assert None not in row and all(value is not None for value in row.values()), "sai số cột CSV"
            assert re.fullmatch(r"E-\d{4}", row["id"]) and row["id"] not in seen, "ID sai hoặc trùng"
            seen.add(row["id"])
            assert re.fullmatch(r"[0-9a-f]{40}", row["commit"]), "SHA không đầy đủ"
            assert row["file"] == row["file"].strip(), "path có khoảng trắng thừa"
            folder, remote = REPOS[row["tool"]]
            key = (folder, row["commit"], row["file"])
            if key not in sources:
                result = subprocess.run(
                    ["git", "--no-optional-locks", "-C", str(ROOT.parent / folder),
                     "show", row["commit"] + ":" + row["file"]],
                    capture_output=True, text=True, timeout=30,
                )
                assert result.returncode == 0, "không đọc được file tại commit"
                sources[key] = result.stdout.splitlines()
            start, end = int(row["line_start"]), int(row["line_end"])
            assert 1 <= start <= end <= len(sources[key]), "range dòng ngoài source"
            anchor = f"#L{start}" + (f"-L{end}" if end != start else "")
            expected = f"https://github.com/{remote}/blob/{row['commit']}/{row['file']}{anchor}"
            assert row["permalink"] == expected, "permalink không khớp commit/path/range"
            assert row["evidence_status"] in {"source-confirmed", "runtime-confirmed", "both", "unverified"}, "status không hợp lệ"
            if row["evidence_status"] in {"runtime-confirmed", "both"}:
                artifact = ROOT / row["runtime_artifact"]
                assert row["runtime_artifact"] and artifact.is_file(), "thiếu runtime artifact"
        except (AssertionError, KeyError, ValueError, subprocess.TimeoutExpired) as error:
            errors.append(f"{row.get('id', '?')}: {error}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(rows)} evidence IDs; commit/file/line ranges và permalinks hợp lệ.")
    print("Không kiểm chứng semantics claim, URL availability hoặc runtime bằng phép kiểm tra này.")


if __name__ == "__main__":
    main()
