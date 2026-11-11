# Chuyển nhóm chuẩn bị sang gpt-6.1-sol

Theo yêu cầu người dùng ngày 2026-11-06: xóa kết quả chạy model cũ, chuẩn bị chuyển sang sol và chờ bảng giá mới. Đây là quyết định rút cả nhóm dữ liệu, không phải chọn lọc bỏ lượt xấu hoặc thay dữ liệu thiếu bằng 0. Các kết luận dựa riêng trên artifact đã xóa không còn được dùng.

## Đã xóa trong phạm vi project/thử nghiệm

- **57 thư mục** artifact/sandbox và **2 file output tạm**, tổng 1300 file, khoảng 162.7 MB trước xóa. Chỉ các đường dẫn chính xác đã kiểm kê; không xóa đệ quy thư mục source/binary/credential.
- Gồm provider probe/usage-cost ledgers/model smoke/re-evaluation/traces/native preflight/pilot/retry model cũ và các sandbox chứa session/config/db tương ứng.
- Xóa 5 dòng run cũ khỏi CSV; các protocol/result summaries cũ được rút hoặc viết lại thành trạng thái nhóm sol. Không giữ lại số đo/model-error tables cũ trong báo cáo hiện tại.
- 12 evidence có runtime artifact bị xóa được hạ về source-confirmed, bỏ runtime pointer; source claim/file/commit/permalink/ID giữ nguyên. Không tự nâng evidence đó thành sol runtime-confirmed.
- Retire R-0001–R-0008 và C-0005–C-0038/C-0040; ID không được tái sử dụng dù file đã xóa. Registry [`experiment-state.json`](experiment-state.json).

Manifest dọn dẹp chỉ giữ **danh sách đường dẫn/ID và kiểm tra tồn tại**, không lưu bản sao log/kết quả cũ: [`artifacts/SOL-MIGRATION-20261106-01/manifest.json`](artifacts/SOL-MIGRATION-20261106-01/manifest.json). Source helper khớp hash của lượt sol được snapshot trước đổi mặc định trong `preserved-sol-source/`; đó là source tái lập sol, không phải bản sao kết quả model cũ.

## Đã giữ nguyên

- API key file private, binary/release/checksum và bốn repo source tool; không thay checkout hoặc restart service đang dùng.
- Metadata/version/help và HTTP API offline không dùng model, gồm sandbox C-0001–C-0004.
- Fixture/task-history/public/hidden/seal/self-check P-01/P-02; đây là code/test nhân tạo, không phải kết quả model cũ.
- **Toàn bộ 10 file artifact gốc của sol** ở `benchmark/artifacts/MODEL-COMPARE-GPT61-20261106-01`, catalog sol và runtime C-0039. Giữ bit-for-bit, không sửa raw model fields hoặc hash lịch sử. Chỉ dùng quan sát riêng sol; không còn control để kết luận so sánh model.
- Lịch sử chat/tool logs do harness OpenCode quản lý **ngoài workspace/thư mục thử nghiệm** không bị sửa/xóa. Không can thiệp dữ liệu session thật hoặc giả vờ xóa được nội dung hội thoại đã gửi.

## Chuyển đổi cấu hình và chặn chi phí

- Nguồn model mặc định dùng chung `demos/provider_probe.py:MODEL` là **gpt-6.1-sol**. Model smoke/pilot/provider SSE helpers kế thừa giá trị này; native configs mới được tạo trong sandbox, không sửa cấu hình người dùng.
- Tại thời điểm chuyển đổi, `research/provider-pricing.json` có input/cache/output **null/pending**, không kế thừa giá cũ. Sau đó người dùng đã cung cấp giá sol, cập nhật dưới đây; estimate thiếu giá vẫn trả null, không giả bằng 0.
- Paid-entrypoints provider roundtrip/SSE/model smoke/pilot kiểm tra `require_pricing` **trước đọc key và trước tạo artifact generation**. Catalog-only và unit/mock/offline-preflight không tạo generation có phí.
- Tests dùng **giá giả lập cục bộ có nhãn unit test**, không lấy pending tariff hoặc tạo benchmark cost giả.
- Giữ pacing/header/sandbox/grader và logic source; helper trace phụ thuộc dataset đã rút bị vô hiệu hóa. Model smoke phải dùng config ID mới, pilot defaults chuyển khỏi ID đã retire.

## Trạng thái trước khi nhận giá

Tại cuối đợt chuyển đổi, Sol/Pi/P-01 có một diagnostic đã giữ, chưa có model smoke sol/OpenCode v1-v2/Codex hoặc pilot sol đủ 8 lượt. Chỉ chuẩn bị và kiểm tra offline, **không gọi thêm model/provider có phí**. Không tự nạp tiền.

Kiểm tra chuyển đổi: 5 tests pricing/retired-ID (gồm cả bốn paid-entrypoints), 6 tests bridge/smoke và 5 tests pilot/grader/pacing đều đạt. Sol preflight mới [`SOL-PREFLIGHT-20261106-01/result.json`](../benchmark/artifacts/SOL-PREFLIGHT-20261106-01/result.json) đủ bốn cấu hình load config/model/namespace/writable/test-isolation đạt, chỉ request mock; không suy inference runtime của bốn CLI đã đạt. C-0041–C-0044 nay đã dùng, ID offline tiếp theo phải mới.

## Giá được cung cấp sau chuyển đổi

Người dùng đã cung cấp input/cache/output **4.8/0.24/18 USD mỗi triệu token**; manifest hiện là user-reported, chưa invoice-confirmed. Gate đủ giá đã mở, nhưng không tự chạy model/pilot; `paid_runs_ready` vẫn false vì nhóm mới còn cần review/smoke. Estimate riêng từ diagnostic sol cũ **0.21496416 USD**, raw sol artifact không sửa, không gọi thêm API. [`../benchmark/SOL_COST.md`](../benchmark/SOL_COST.md).

Protocol/source khớp hash preflight offline rev2 đã snapshot trước cập nhật tài liệu giá tại `artifacts/SOL-PRICING-20261106-01/`; tài liệu pilot hiện rev3. Audit migration/validation cũ phản ánh trạng thái lúc chuyển đổi, không ghi đè để giả giá đã có từ đầu.
