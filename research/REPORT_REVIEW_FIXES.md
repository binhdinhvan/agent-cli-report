# Biên tập sau review mentor — 11/11/2026

## Thay đổi

- [REPORT.md](../REPORT.md): làm rõ ngày chốt phiên bản 06/11/2026; không đổi bốn pins hoặc benchmark.
- Thay các câu “chưa demo/chưa runtime” đã lỗi thời bằng trạng thái cuối cùng, phân biệt metadata, transcript, crash recovery, compaction plumbing và semantic retention.
- Thêm bảng tổng hợp sáu trục, sơ đồ hosting/shared service, demo Client với source/lệnh/output/validation, permission config và witness table, plugin before/after nguyên fixture, bảng đối chiếu yêu cầu và kết luận theo use case.
- Chuyển phần lịch sử vận hành khỏi report sang [EXPERIMENT_HISTORY.md](../EXPERIMENT_HISTORY.md), dẫn lại tài liệu gốc và mọi attempt; không xóa raw lịch sử.
- [BENCHMARK_FAIRNESS.md](BENCHMARK_FAIRNESS.md) và [script chỉ đọc](analyze_final_cohort.py): token/cache/output trên request theo 16 nhóm task/CLI, request/lượt, median pacing/native; phân biệt task correctness và terminal completion. Không suy nguyên nhân token hoặc CPU/provider compute time khi chưa đo.
- [SUBMISSION.md](../SUBMISSION.md): đường đọc bằng chứng, phạm vi file đi kèm, prerequisites ngoài workspace và cảnh báo nhạy cảm. Chưa publish hoặc tạo archive bàn giao; không gọi hướng dẫn này là bundle đã nghiệm thu.
- README/PLAN/versions có điều hướng và nhãn trạng thái cuối để không nhầm các mốc chuẩn bị với kết quả hiện tại.

## Kiểm tra đã thực hiện

Kiểm tra offline, không chạy native CLI/model hoặc đọc credential:

1. 241 local Markdown links/anchors trong REPORT, README, SUBMISSION, EXPERIMENT_HISTORY, PLAN, versions và fairness: tồn tại file/heading tương ứng; code fences cân bằng.
2. Hai block plugin trong report trùng nguyên bytes văn bản của fixtures sau khi bỏ newline cuối.
3. Session ID và các check trong API output excerpt khớp raw `NATIVE-CLIENT-20261111-01`.
4. Chạy `python3 -B research/analyze_final_cohort.py`: 48 unique slot, 46 success/2 failure, 278 upstream HTTP 200/completed, 16 nhóm × 3 lượt; không thay phân loại.
5. Đối chiếu đủ 16 dòng token/request trong fairness với giá trị tính từ raw, sai số chỉ do làm tròn một chữ số; aggregate input/request count/median end-to-end khớp audit cuối gốc.
6. Tìm lại các câu trạng thái cũ về Client, plugin port, permission approval, shared UI và “chưa có benchmark chính thức”: không còn trong report.

Đây là receipt kiểm tra biên tập và phép tính dẫn xuất, **không phải audit độc lập lại toàn bộ 48 lần thực thi**, không phải tái chạy 194 tests cũ, không xác minh lại mọi GitHub permalink qua mạng. Không sửa CSV/raw/audit receipt, fixture, tool source repo, service hoặc binary. Chờ người dùng review nội dung; quyết định chia sẻ/publish artifact vẫn riêng.

## Chỉnh sau review lần 2

- Lệnh Client dùng đường dẫn được quote và timestamp UTC có nanosecond, bỏ placeholder `<fresh-id>` gây shell redirection. Kiểm `bash -n` và chạy probe thay launcher bằng in argv: shell truyền đúng một giá trị `--artifact-dir`; không thực thi demo.
- Thêm nguyên trích đoạn subscribe/xử lý event từ runner (chỉ bỏ thụt lề ngoài), event `session.execution.succeeded` với session ID/created từ raw và thời gian UTC tương ứng. Không dựng output mới hoặc sửa script demo.
- Tách subagent completion khỏi shell completion; đọc source đúng pin của `SubagentJob.notify`/`SubagentCompletion.deliver` và dẫn permalink/file/dòng, không coi shell notifier thay thế subagent notifier.
- Thêm chú thích tổng chi phí tính trước làm tròn và giờ Việt Nam UTC+7 cho khoảng benchmark.
- Kiểm 246 local links/anchors trong tám tài liệu điều hướng/báo cáo: không thiếu file hoặc heading, code fences cân bằng. Cả 42 file target khác nhau được link từ REPORT đều tồn tại và resolve bên trong workspace, không dựa vào symlink ra repo source bên ngoài. Đây là kiểm tra tĩnh tính tương đối của đường dẫn, **chưa phải thử clone repository hoặc xác nhận gói bàn giao đã gửi đủ file**.
- Đối chiếu terminal event/timestamp với raw, subscribe với source và hai mốc benchmark UTC+7: đạt. Assertion so substring đầu tiên không tính thụt lề nên thất bại; kiểm lại sau dedent xác nhận trích đoạn khớp, không thay code để ép pass.

Không chạy lại native demo/benchmark, không gọi thêm inference hoặc đọc key; dữ liệu thực nghiệm và receipt gốc giữ nguyên. Phạm vi publish/bàn giao vẫn như SUBMISSION, chờ người dùng review.
