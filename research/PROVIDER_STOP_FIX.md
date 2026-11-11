# Sửa classifier và chống burst sau lỗi provider

Theo yêu cầu người dùng: sửa phân loại sai và không dồn request khi provider quá tải. **Chỉ sửa/kiểm thử offline; không gửi generation mới, không retry pilot đã dừng.**

## Thay đổi

- `benchmark/pilot.py:classify_run`: HTTP 200 không đủ để đạt. `response.failed`, `response.incomplete`, thiếu terminal, lỗi transport, ledger rỗng hoặc usage không tính được đều là `infra_error`; validity đi cùng là `pending_review`. Hidden/public fail chỉ thành task `failure` khi transport/terminal/usage đã hợp lệ. Timeout/isolation vẫn giữ nhóm riêng theo logic runner.
- `demos/model_smoke.py:PacingState/handler`: dùng chung khóa serialize và mốc monotonic toàn batch. **Tối đa một request đang xử lý**, nghỉ ≥30 giây sau response trước trong cấu hình pilot/smoke đã chốt, cả khi chuyển CLI/task.
- Thêm latch `stop_on_provider_failure=True` trong cả runner smoke và pilot. HTTP không phải 200, terminal khác completed hoặc exception làm batch chuyển sang trạng thái dừng; **không tự backoff-retry lên provider**. Retry native/CLI kế tiếp nhận HTTP 503 **local**, không tạo upstream request mới, kể cả response lỗi có usage đầy đủ và chưa chạm budget. Batch không mở slot tiếp theo.
- Thiếu usage vẫn là điều kiện dừng độc lập; không coi lỗi miễn phí hoặc dựa subtotal thấp để tiếp tục. Summary lưu `provider_stop_reason` và `locally_blocked_after_provider_failure`.
- Local reject đọc bỏ body tối đa 2 MiB, timeout 5 giây, trước đóng kết nối để tránh race `BrokenPipe` khi client còn đang gửi POST. Không chuyển credential hoặc tự retry request lỗi.

Khóa có phạm vi **một batch/process**, không phải rate limiter toàn tài khoản: không kiểm soát request từ chương trình/người dùng khác hoặc các lần thử nội bộ của gateway. Không chạy song song nhiều batch trả phí. Chưa đủ bằng chứng để khẳng định overload do phía mình gửi đồng thời: đợt R-0009 chỉ hai upstream request tuần tự với gap 30.000943 giây.

## Kiểm thử và bằng chứng

30 tests đạt: `test_provider_stop.py` 4, `test_pilot.py` 9, `test_pacing.py` 5, `test_model_smoke.py` 7, `test_provider_pricing.py` 5. Test HTTP dùng loopback/Unix socket, synthetic key, mock opener; fake clock/sleep không phải số đo live.

- Hai client đồng thời qua **hai broker chung state**: active upstream tối đa 1, request sau đợi thêm 30 giây giả lập, không overlap.
- HTTP 200 + failed/incomplete, không terminal, HTTP 429/503, exception: request thứ hai và broker tiếp theo bị chặn local, chỉ một lần opener được gọi. Cases failed/incomplete có usage tính được, chứng minh latch độc lập với budget gate.
- Deadline, pacing xuyên broker, header/auth/secret filtering, budget, grader và config hồi quy vẫn đạt.
- Chấm lại R-0009 từ artifact đã lưu bằng classifier mới cho **infra_error**, không sửa raw JSON/CSV. Bản review cũ tiếp tục là override khi tổng hợp dataset lịch sử.

Logs/source hashes: [`artifacts/PROVIDER-STOP-FIX-20261106-02/validation.json`](artifacts/PROVIDER-STOP-FIX-20261106-02/validation.json). Lần test `...-01` được giữ riêng vì gặp race local reject; không xóa hoặc gọi nó là pass. Test pricing gate cũng đã tách CSV reader giả để không xung đột R-0009 thực; không sửa CSV thật.

Raw pilot và protocol `benchmark/PILOT_SOL.md rev1` giữ nguyên hash. Bản sửa là **offline-confirmed**, chưa chạy provider để nghiệm thu live. Trước lượt trả phí mới cần protocol revision mới và quyết định retry/slot/budget phù hợp; lỗi `rg` thiếu trong môi trường vẫn cần review riêng, không tự cài dependency hoặc coi là nguyên nhân overload.
