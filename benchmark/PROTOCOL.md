# Protocol benchmark — chưa chốt

> **Candidate hiện tại:** [PROTOCOL_48_R1.md](PROTOCOL_48_R1.md), [batch runner/manifest03](suite48/BATCH_RUNNER.md). Đã thống nhất hướng48slot, guard16USD estimate và outer-wall; runner offline đạt16/16. Protocol/input bytes đã pin trong launch candidate, nhưng **chưa có approval dispatch**. Các draft/readiness ghi nhận phía dưới giữ theo thời điểm lịch sử, không tự bật launch.

> **Hướng hiện tại:48lượt** đã được người dùng chọn để chuẩn bị offline. [Protocol48 draft ngày09](PROTOCOL_48_DRAFT.md), [fixture/grader implementation và seal ngày10](suite48/IMPLEMENTATION.md). B-01–B-04 đã có fixture/acceptance seal và44reference/mutant checks đạt kỳ vọng; native CLI runner adapter, budget đề xuất16USD estimate và protocol cuối **chưa duyệt/nghiệm thu đủ**, không inference mới. Phương án72lượt không triển khai ở giai đoạn này.

> Cập nhật tiếp ngày10: [native adapter đã qua16/16preflight offline](suite48/NATIVE_PREFLIGHT.md) với40response giả,0provider requests. Virtual pacing và outer90s watchdog là điều kiện mock, không live acceptance/đổi cap900. Đề xuất primary duration outer launcher (exact native duration secondary) phải được duyệt vào final protocol. **Budget/protocol/paid entrypoint vẫn chưa được duyệt**, không inference mới; câu pending adapter trong ghi nhận trước giữ theo thời điểm lịch sử.

Pilot đã phủ tám cặp task/CLI qua **14 inference attempts**, không phải8/8 first-attempt; giữ mọi failure/retry và tách environment/timing revisions. [Tổng kết và baseline đã khóa offline](BASELINE.md): `search-r2 + paced-900`, P-01/P-02 v2 và seal. **Baseline frozen không phải benchmark protocol approved.** Chưa có benchmark chính thức hoặc quyền chạy inference mới; giá user-reported, sáu request pilot unpriced.

## Thiết kế

- Bốn cấu hình: OpenCode v1, OpenCode v2, Pi, Codex CLI.
- So sánh ba tool dùng OpenCode v2; phân tích v1/v2 riêng.
- Pilot thiết kế8cặp, thực tế14inference attempts +1launch-error không inference; không gộp vào kết quả chính thức.
- Thiết kế đang chuẩn bị:4task×4cấu hình×3lần=48slot, chưa launch.
- Phương án6task×4×3=72lượt không chọn ở giai đoạn này.
- Chốt quy mô và ngân sách trước khi chạy; không dừng chọn lọc theo kết quả.

## Task manifest

Mỗi task trong `tasks/` cần:

1. ID, mục tiêu và nhóm task.
2. Fixture repository, license và full commit SHA, hoặc fixture tự viết có version.
3. Prompt nguyên văn, không điều chỉnh riêng để giúp một tool.
4. Dependency setup, test command và acceptance tests chốt trước.
5. Timeout, giới hạn token/chi phí nếu công cụ cho phép.
6. Quyền filesystem/network và tài nguyên được truy cập.
7. Cách chuẩn bị workspace sạch và xác minh baseline.
8. Cách chấm, artifact cần lưu, điều kiện loại lượt do lỗi hạ tầng.

Nhóm đề xuất: hiểu code, sửa bug, thêm tính năng, refactor, context nhiều file, task tích hợp. Permission/background đặc thù chạy thành demo riêng nếu không tương đương giữa tool.

## Kiểm soát

- Cùng model/provider và generation settings khi cả bốn hỗ trợ. Không được thì tạo nhóm riêng và nêu confounder.
- Chấp nhận system prompt/tool definitions riêng của từng tool như một phần sản phẩm; lưu cấu hình, không giả định chúng giống nhau.
- Cùng fixture, prompt, timeout, mạng và permission policy tương đương.
- Session/workspace mới cho mỗi lượt; không để agent nhìn lời giải, log hay acceptance tests ẩn nếu thiết kế dùng hidden tests.
- Lưu patch và test output; không chấm qua lời tự nhận của agent.
- Xáo trộn thứ tự tool; lưu execution order.
- Không can thiệp thủ công trong benchmark chính. Nếu cần tương tác permission, quy định policy trước và ghi lại mọi lần.
- Không xóa lượt thất bại. Retry có ID riêng và liên kết lượt gốc.
- Provider/network/build setup errors tách khỏi agent failures theo quy tắc định trước.
- Cùng tên model không đủ để xác nhận tương đương: ghi exact ID/revision nếu có, endpoint và generation/reasoning settings; tách nhóm hoặc nêu giới hạn khi không xác minh được.
- Chốt tài nguyên máy, mức chạy đồng thời và giới hạn chi phí/token nếu hỗ trợ; ghi khác biệt không áp dụng đồng đều được.
- Lưu seed/thuật toán xáo trộn hoặc danh sách thứ tự chạy đã chốt. Không thay đổi thứ tự theo kết quả quan sát được.
- Đóng băng protocol sau pilot và trước lượt chính thức, có người duyệt, ngày và revision. Mọi thay đổi sau đó cần ghi lý do và quyết định chạy lại/tách nhóm.

## Định nghĩa chỉ số

- Success: acceptance criteria đạt trong timeout và không có can thiệp ngoài protocol.
- Completion rate: số lượt success / số lượt hợp lệ; công bố cả tử và mẫu, cùng số lượt loại và lý do.
- Duration: monotonic wall-clock từ khi gửi task đến trạng thái cuối; ghi timeout riêng. Nêu rõ thời gian startup có nằm trong phép đo không.
- Token: input/output/cache/reasoning theo nguồn usage thực tế. Tránh cộng double-count cached/reasoning khi chúng đã nằm trong input/output.
- Thiếu usage: để trống và ghi lý do; không thay bằng 0.
- Cache policy: ghi rõ cache lạnh/ấm hoặc không kiểm soát được; không trộn chúng mà không chú thích.
- Báo median và khoảng min–max cho thời gian/token; không chỉ thống kê success mà giấu chi phí các lượt thất bại.
- Mẫu nhỏ: kết quả mang tính mô tả, không khẳng định ưu thế thống kê.
- Task hiểu code dùng rubric chốt trước, ghi người/cách chấm; task sửa code dùng acceptance tests và ràng buộc hành vi. Không coi lời tự nhận của agent là kết quả chấm.
- Chốt việc tính startup, chờ permission, retry provider và acceptance tests vào duration hay đo riêng. Lưu thời điểm các pha cần thiết; không thay ranh giới đo giữa các tool.
- Đối chiếu định nghĩa usage theo tool/provider trước khi tổng hợp. Nếu không tương đương, tách chỉ số hoặc ghi rõ giới hạn thay vì cộng trực tiếp.

## Artifact

`runs.csv` là chỉ mục. Mỗi run nên có thư mục artifact riêng chứa metadata, stdout/event log đã lọc secret, patch, test output và usage gốc.

ID ổn định: evidence `E-0001`, run `R-0001`, config `C-0001`; không tái sử dụng ID. Raw logs ở `raw/<run_id>/` (giữ cục bộ, chưa mặc định an toàn để chia sẻ), artifact đã duyệt ở `artifacts/<run_id>/`. `artifact_path` trỏ tới bản đã duyệt. Không ghi đè lượt cũ khi retry.

Metadata lưu revision protocol, full SHA, model/settings, cấu hình an toàn và version/checksum của prompt, fixture, config, script kèm cách tìm bản gốc. Không lưu credential. Kiểm tra cả secret và dữ liệu cá nhân trước công bố.

Evidence status dùng trong nghiên cứu: `unverified`, `source-confirmed`, `runtime-confirmed`, `both`.
Run status đề xuất: `success`, `failure`, `timeout`, `infra_error`, `not_supported`.
Tính hợp lệ của run ghi ở `validity`: `valid`, `excluded`, `pending_review`.

## Quyết định còn thiếu

Baseline pilot đã khóa model/provider alias, config native từngCLI, search-r2, paced-900, pacing/caps/isolation và hai fixture v2. Các checkbox dưới đây là **quyết định/duyệt cho benchmark chính thức**, không phủ nhận pilot đã hoàn tất; chưa tự dùng lại budget3USD hoặc xem cấu hình native tương đương.

- [ ] Fixture và task cụ thể.
- [ ] Model/provider/reasoning settings.
- [ ] Budget/timeout và số lượt.
- [ ] Permission/network/cache policy.
- [ ] Cách thu usage và event của mỗi tool.
- [ ] Quy tắc xử lý infra error và retry.
- [ ] Người duyệt protocol và ngày đóng băng.
- [ ] Rubric theo nhóm task và cách chấm.
- [ ] Ranh giới duration, semantics usage và cách xử lý chỉ số không tương đương.
- [ ] Tài nguyên máy, mức chạy đồng thời, seed/danh sách thứ tự chạy.
- [ ] Tiêu chí exclusion, số retry tối đa và cách trình bày lượt gốc/retry.

Điều kiện đóng băng: pilot có kết quả hoặc blocker được xử lý công khai; các mục trên có quyết định cụ thể và task/acceptance tests không còn placeholder. Nếu chưa đáp ứng, chưa chạy benchmark chính thức.
