# Provider gpt-6.1-sol — đã có bảng giá user-reported

Model thử mặc định hiện tại: `gpt-6.1-sol`, base URL `https://api.shopaikey.com/v1`. Exact ID có trong [catalog đã giữ](../benchmark/artifacts/MODEL-COMPARE-CATALOG-20261106-01/result.json). Một lượt Pi/P-01 với model này đã hoàn tất; xem [`../benchmark/MODEL_COMPARE.md`](../benchmark/MODEL_COMPARE.md). Alias/gateway không xác minh model gốc hoặc backend revision.

Kết quả model cũ đã xóa theo yêu cầu; không dùng lại token/cost/success cho sol. Giá input/cache/output hiện **4.8 / 0.24 / 18 USD mỗi triệu token**, user-reported tại [`../research/provider-pricing.json`](../research/provider-pricing.json), chưa đối soát charge. `require_pricing` vẫn chặn trước key/artifact nếu thiếu giá hoặc sai model/provider; hiện đã qua gate giá, không có nghĩa tự khởi chạy generation. [`../benchmark/SOL_COST.md`](../benchmark/SOL_COST.md) tính riêng lượt sol đã lưu, không API.

Scripts giữ lại: `provider_probe.py` (catalog hoặc tối đa hai Responses tool roundtrip), `provider_stream_probe.py` (một SSE request), `estimate_provider_cost.py` (chỉ tính từ artifact đã lưu). Chưa chạy provider-only probes mới sau cập nhật giá; không tự tiêu tiền để xác minh lại từ việc nhận bảng giá.

Key vẫn chỉ ở file private `.local/credentials/shopaikey.key`; không in/read bằng tool hiển thị, không ghi vào source/config mẫu/log. Khi được chạy, HTTP client không follow redirect hoặc kế thừa proxy môi trường, timeout/capture bounds như source script. Usage/giá báo cáo phải tách khỏi phí đã đối soát.
