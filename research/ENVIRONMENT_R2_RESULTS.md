# search-r2 — chuẩn hóa hoàn tất, chưa chạy model

**Đã chuẩn hóa dependency cho thử nghiệm mới và nghiệm thu offline đủ bốn CLI.** Không cài dependency lên host, không thay binary/service/source/config người dùng; không chạy thêm pilot trả phí.

- Manifest: [`environment-profiles/search-r2.json`](environment-profiles/search-r2.json), protocol preflight [`../benchmark/ENVIRONMENT_R2.md`](../benchmark/ENVIRONMENT_R2.md).
- `rg` **15.2.0**, SHA-256 **e62198eb19b136b88c330af83647b5a962cb99b6b1f066758568f12de1974849**; bytes lấy từ release package Codex đã lưu và checksum, copy riêng vào private dependency dir. Mount **read-only**; lỗi checksum hoặc executable lạ khiến profile từ chối trước chạy.
- PATH nền có common bin. Codex vẫn prepend bản bundled theo native behavior, nhưng kiểm actual executable chứng minh **cùng bytes/version** với ba CLI còn lại. Không giả cùng đường dẫn hoặc sửa launcher native.
- Python policy giữ nguyên: dùng `python3`/stdlib hiện có, không thêm alias `python`; native shell cả bốn xác nhận điều kiện này. Không thay prompt/fixture/tool set của nhóm model.

## Kết quả offline

| Kiểm tra | Kết quả |
| --- | --- |
| Native glob + grep v1/v2 với settings pilot | Cả hai CLI completed, trả đúng fixture/match |
| Native bash/shell/exec cả bốn: rg --files + search | 4/4 pass |
| Hash/version executable rg và quyền chỉ đọc | 4/4 khớp/chỉ đọc |
| Writable/config/isolation preflight pilot | 4/4 preflight_pass |
| Regression/unit tests | **37 pass**, sáu suite |
| Source/protocol/manifest/binary/fixture hash, PID/socket, repo status | Pass |
| Generation/key read mới | **Không** |

Native tools được dispatch bởi **SSE giả local**, không model. Pi chỉ thử bash như baseline pilot, không bật grep native vốn không nằm trong tools pilot. File fixture read-only, project writable đúng chế độ pilot để native sandbox Codex có thể thiết lập; không bypass sandbox. Native audit cố ý dừng bằng local HTTP400 sau tool events, nên exit1 không phải tiêu chí fail tool.

Artifact cuối: [`SEARCH-R2-NATIVE-PREFLIGHT-20261109-03`](../demos/artifacts/SEARCH-R2-NATIVE-PREFLIGHT-20261109-03/result.json), C-0098–C-0101; [`SEARCH-R2-PREFLIGHT-20261109-01`](../benchmark/artifacts/SEARCH-R2-PREFLIGHT-20261109-01/result.json), C-0102–C-0105. Logs/source before/after/checksum/validation: [`SEARCH-R2-PREP-20261109-01`](artifacts/SEARCH-R2-PREP-20261109-01/validation.json).

Giữ cả hai native audit01/02 trước đó: Codex không chạy lệnh vì audit đã mount cả project read-only trong chế độ native workspace-write (`bwrap: Can't mkdir .../.git: Read-only file system`). Đây là lỗi **harness audit**, không dependency r2 hay model; lượt03 sửa mount đúng pilot, không đổi native sandbox policy. Không ghi đè kết quả lỗi hoặc lấy exit1 intentional mock stop làm benchmark failure.

## Phạm vi triển khai và so sánh

- `demos/environment_profile.py` kiểm manifest/hash, `demos/preflight.py:profile` áp mount/PATH theo `spec.environment_revision`. Thiếu revision giữ legacy để tái lập dữ liệu cũ.
- `benchmark/pilot.py` mặc định **search-r2** cho lượt mới; ghi revision và manifest hash vào batch/run/spec, snapshot cả helper profile. Legacy chỉ khi chỉ định tường minh. Chặn retry/continuation âm thầm từ chain legacy sang r2 trước key/artifact.
- Raw pilot/CSV/protocol/fixture legacy giữ nguyên. Kết quả cũ vẫn có hai request unpriced, cumulative charge unknown, known estimate0.40389912 USD không tự biến thành tổng phí.
- **Chưa chạy năm slot còn lại hoặc retry v2.** Chúng không thể được gộp cùng các slot legacy để gọi là tám slot cùng môi trường. Trước inference cần chốt group/protocol/ID và ngân sách phù hợp; muốn so sánh đồng nhất cần thực nghiệm cùng revision.
- Nghiệm thu này xác nhận dependency/native tools, không bảo đảm task success hoặc giải thích toàn bộ timeout/provider latency. Pacing/cap/permission/provider-stop không được nới.
