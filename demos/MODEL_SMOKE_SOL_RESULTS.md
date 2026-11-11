# Smoke sol: kết quả và review protocol

Đợt `MODEL-SMOKE-SOL-20261106-01` ngày 2026-11-06: **ba CLI đạt luồng model → local read → final**, nhưng **không đạt pacing toàn đợt**. Không chạy pilot hoặc retry thêm.

| CLI | Config | Request | Estimate USD |
| --- | --- | ---: | ---: |
| OpenCode v1 1.19.5 | C-0045 | 3 | 0.05590704 |
| OpenCode v2 2.2.5 standalone | C-0046 | 3 | 0.02725800 |
| Codex 0.167.0 | C-0047 | 2 | 0.00857112 |
| Tổng | | 8 | **0.09173616** |

Giá user-reported; measured charge chưa biết. Tổng estimate dưới shared guard 0.50 USD; không có slot not_run, không thiếu usage. Cả 8 response HTTP 200/completed, đúng model field sol; cả ba CLI exit 0, có event đọc file thật, final đúng marker, fixture không đổi, không CLI error event hoặc timeout. stderr OpenCode rỗng; Codex chỉ ghi `Reading additional input from stdin...`.

## Lệch protocol cần giữ nguyên trong kết quả

Năm gap nội bộ từng CLI đều ≥30 giây. Hai gap chuyển CLI chỉ **1.571132 giây** (v1 → v2) và **1.271972 giây** (v2 → Codex). `demos/model_smoke.py:handler` khởi tạo `last_finished = None` mỗi broker mới; main tạo broker riêng từng CLI nên pacing bị reset dù budget ledger dùng chung. Đây là lỗi harness, không phải lỗi CLI/provider; không được trình bày là pacing30 toàn đợt đạt. Cần sửa và kiểm thử pacing xuyên broker trước nhóm trả phí tiếp theo; không tự chạy lại để che lệch protocol.

## Bằng chứng và giới hạn

- Raw protocol/result/stdout/stderr: [`artifacts/MODEL-SMOKE-SOL-20261106-01/`](artifacts/MODEL-SMOKE-SOL-20261106-01/), giữ nguyên.
- Review offline, hash từng file, cost từng CLI, timestamp từng gap và cleanup: [`../research/artifacts/SOL-SMOKE-REVIEW-20261106-01/validation.json`](../research/artifacts/SOL-SMOKE-REVIEW-20261106-01/validation.json).
- Hash source/protocol/pricing/binary khớp; acceptance tính lại từ stdout. Key scan không thấy key thật trong raw artifact; supervisor PID/socket broker không còn, không thấy process khớp runtime; bốn repo source tool sạch tại postcheck. Witness xác nhận network namespace/home riêng, key không ở agent.
- Đây là runtime-confirmed cho đúng ba release/binary/config đã lưu, không xếp hạng chất lượng/tốc độ/chi phí từ smoke. Source claim/permalink đã pin vẫn ở `../research/evidence.csv`; review này không tự nâng các evidence lịch sử đã rút.
- Pi có diagnostic sol/P-01 riêng, không cùng fixture marker hoặc cùng đợt smoke này. Không gọi bốn lượt là cùng bài kiểm tra; chưa có pilot sol 8 lượt, resume/shared-service GUI/Client/SDK runtime.

Protocol đã đóng băng `MODEL_SMOKE.md` không sửa ngược. Bước tiếp theo: sửa/test pacing xuyên CLI offline, rồi chốt ngân sách/settings pilot với người dùng; không tự khởi chạy pilot.

Cập nhật sau review: đã sửa và đạt 5 regression tests xuyên broker offline, cả bốn suite tổng 23 tests đạt; [`../research/PACING_FIX.md`](../research/PACING_FIX.md). Không sửa kết quả/protocol cũ hoặc gọi provider chạy lại. Gate tiếp theo là chốt budget/settings/protocol pilot; pacing live sau sửa chưa được kiểm chứng.
