# paced-900 — sửa chính sách thời gian, nghiệm thu offline

> Cập nhật mới nhất: **R-0036/v1, R-0037/Codex, R-0038/Pi P-02 đều đạt**, hoàn tất các slot pilot được yêu cầu; cùngR-0035 v2/P-02 đủ4CLI trênsearch-r2/paced900. Xem [`../benchmark/PILOT_RESULTS.md`](../benchmark/PILOT_RESULTS.md) cho coverage/retry/chi phí; phần dưới giữ ghi nhận nghiệm thu offline vàsingleacceptance tại thời điểm đó.

> Cập nhật sau nghiệm thu offline: **R-0035 v2/P-02 đã đạt live**, scope/public/hidden pass, 7/7completed,234718ms gồm pacing; estimate0.07580592 USD. Hoàn tất dưới300s nên không chứng minh riêng tăngcap gây success; reserve edge guard không kích hoạt live. Raw/review tại [`../benchmark/PILOT_RESULTS.md`](../benchmark/PILOT_RESULTS.md); cap300 cũ không đổi, ba slot khác chưa chạy.

**Đã đổi chính sách chung cho cả bốn CLI, không chỉ nới cap riêng v2.** Mục tiêu là tránh cắt final do pacing chiếm phần lớn cap300s và tránh mở request khi sắp hết giờ; không thể bảo đảm mọi provider/model/task sẽ thành công.

| Điều kiện | Chính sách mới |
| --- | --- |
| Timing revision | **paced-900** |
| Wall cap mỗi lượt, gồm pacing | **900 giây (15 phút)** |
| Reserve tại quyết định dispatch, tính sau pacing | **60 giây** |
| Pacing/concurrency | **30 giây / 1 upstream active** |
| Request/output cap | **8 / ≤2048 requested output token**, không tăng |
| Guard USD/provider-failure latch/isolation | Giữ nguyên |

Trước khi sleep, broker tính đủ cả gap và reserve. Không đủ thì trả local408/latch `time_window_exhausted`, không tạo upstream/ledger entry mới; sau parse/budget còn kiểm lại reserve. Local timing stop được đếm riêng với provider failure; run có isolation hợp lệ vẫn ghi timeout, không task failure. Không loại pacing khỏi duration sau chạy hoặc sửa raw timeout cũ thành success.

Cap900 vẫn hữu hạn. Reserve60 không phải dự đoán thời gian provider chắc chắn cần: request SSE có thể lâu hơn nếu còn stream, mạng/provider có thể lỗi. Broker socket45s/bridge90s không đổi. Không cung cấp API key hoặc mở Internet cho agent để đạt task.

## Kết quả nghiệm thu

- **48 tests offline đạt**, gồm fake-clock HTTP regression tại giây310 (legacy300 chặn, paced900 cho phép), trước deadline900 (chặn trước opener), pacing sẽ ăn mất reserve (chặn trước sleep), native retry sau timing stop (chặn local, không provider failure), cross-policy history gate.
- **4/4 CLI config/writable/isolation preflight pass**, C-0124–C-0127. Preflight chỉ local mock400, không key/provider/inference. Metadata từng batch/run cùng900s/60s/8request/2048output/pacing30, không branch riêng CLI.
- Hash source/protocol/dependency/binary/fixture, PID/socket/source Git postcheck đạt. Old raw/CSV giữ nguyên: legacy4 rows, search-r2 sáu rows tại thời điểm audit.

Protocol [`../benchmark/TIMING_POLICY_R2.md`](../benchmark/TIMING_POLICY_R2.md), raw [`PACED-900-PREFLIGHT-20261109-01/result.json`](../benchmark/artifacts/PACED-900-PREFLIGHT-20261109-01/result.json), logs/source before/after/validation [`PACED-900-PREP-20261109-01`](artifacts/PACED-900-PREP-20261109-01/validation.json).

## Sử dụng và giới hạn nhóm

`benchmark/pilot.py` mặc định paced-900 cho lượt mới; `--timing-policy legacy-300` tái lập policy cũ. Lưu `timing_policy`, `timing_limits`, experiment group vào batch/run/CSV notes. Retry từ cap300 cần **`--recheck-timing` và protocol riêng**, không âm thầm continuation hoặc đổi cả môi trường cùng lúc. Kết quả cap300/cap900 **không gộp như cùng điều kiện**, dù đều search-r2.

Không đổi search-r2/rg, binary/model/provider/native settings/tools, prompt/fixture/seal/grader hoặc Python policy; không cài pytest/alias, không tăng token/request/USD cap để kéo kết quả qua test.

**Chưa gọi inference mới hoặc chạy ba slot còn lại.** Known estimate vẫn0.68968632 USD, sáu request lịch sử unpriced/totalchargeunknown. Chính sách mới là **offline-confirmed**, cần một lượt nghiệm thu trả phí riêng nếu người dùng yêu cầu; không tự retry lặp cho đến khi gặp success.
