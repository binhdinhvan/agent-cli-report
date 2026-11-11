# Chọn gemini-3.8-flash — đang chuẩn bị, chưa gọi API

Người dùng yêu cầu đổi từ sol sang **`gemini-3.8-flash`** sau các batch timeout. Chọn model mới không tự chứng minh sol/provider đang outage: raw chỉ xác nhận nhiều `TimeoutError` trước HTTP/terminal/usage, trên cả v2 và Codex; root cause chưa xác minh.

## Đã làm offline

- Ghi profile riêng [`model-profiles/gemini-3.8-flash.json`](model-profiles/gemini-3.8-flash.json), giá/capabilities/protocol còn null/unverified. Giả định vẫn dùng Shopaikey hiện tại, cần xác nhận; không đổi hoặc đọc credential.
- Đánh dấu model được chọn trong [`experiment-state.json`](experiment-state.json), paid gates của model mới đóng. **Runner đã pin vẫn là sol**, chưa thay MODEL bằng search/replace hoặc sửa sealed source/config/pricing. Profile mới không phải runtime config đã nghiệm thu.
- Giữ nguyên toàn bộ sol raw/CSV/rubric/cost/usage thiếu/retry/ID. Không thực hiện cách xóa dữ liệu của lần migration lịch sử trước đây vì người dùng lần này không yêu cầu xóa.
- Nhóm Gemini sẽ có model/protocol/config/smoke/pilot và kết quả riêng. Không gọi 7slot sol +41slot Gemini là benchmark48 cùng model; retry khác model không phải same-condition retry.

## Gate còn thiếu trước gọi model trả phí

1. Xác nhận provider và API model ID; kiểm protocol/tool/SSE thực tế bằng phép thử có scope/budget riêng, không mặc định Gemini hỗ trợ cùng wire contract hay reasoning setting của sol.
2. Nhận giá **input/cache-read/output mỗi triệu token** đúng provider/model. Nếu không có cache rate cần chính sách tính phí rõ, không coi null là0 hoặc dùng giá sol4.8/0.24/18.
3. Viết profile/adapter revision riêng, kiểm offline native cả4CLI trước smoke thật. Không cài provider/plugin hoặc sửa service đang dùng để thử nhanh.
4. Chốt scope: **bộ48 mới cùng Gemini** (phù hợp nếu muốn so sánh đồng nhất) hoặc **chỉ41suffix nhưng báo nhóm Gemini riêng**. Giữ sol8attempts/7unique slots gồm1retry,41not_run, không đổi kết quả gốc.
5. Chốt ngân sách mới hoặc giữ trần16USD tổng với known cũ0.28485816USD/4unpriced (phần known arithmetic15.71514184USD, không phải số dư invoice). Không tự cấp thêm16USD hoặc mở paid batch từ yêu cầu chọn model.

## Bằng chứng đang giữ

- [`../benchmark/suite48/BENCHMARK_RESULTS.md`](../benchmark/suite48/BENCHMARK_RESULTS.md): kết quả sol và giới hạn rubric/model/provider.
- [`artifacts/CONTINUE43-REVIEW-20261110-01/validation.json`](artifacts/CONTINUE43-REVIEW-20261110-01/validation.json): postcheck gần nhất, raw hashes và registry nextR222/C323.
- [`provider-pricing.json`](provider-pricing.json) **chỉ dành cho sol**, giữ bytes để tái lập baseline. Không dùng file đó để estimate Gemini.

Đợt chuẩn bị này: **0provider requests/0network probes**, chưa nghiệm thu API compatibility hoặc chạy Gemini.
