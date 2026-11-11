# OpenAI trực tiếp — kết quả kiểm tối thiểu

**Pass, runtime-confirmed trong phạm vi một request ngắn**, ngày 2026-11-10, 15:54:06–15:54:41 UTC. Provider `https://api.openai.com/v1`, model `gpt-6.1-sol`.

| Kiểm tra | Kết quả |
|---|---|
| `GET /models` | HTTP 200, 1.288 ms; có exact model ID trong 96 model |
| `POST /responses`, SSE | HTTP 200, 4.377 ms; `response.completed` |
| Marker | Đúng `REPORT_OPENAI_DIRECT_OK` |
| Usage | 16 input + 9 output = 25 token; cached/cache-write/reasoning đều 0 |
| Service tier | Gửi và nhận `default` |
| Pacing | Gap 30,00018 giây; không retry hoặc fallback |

Tổng cộng **2 HTTP request, 1 generation**. Request dùng `reasoning.effort=low`, output cap 1.024; chỉ nhận output item `message`, không kiểm tool calling hoặc native CLI.

## Chi phí

Ước tính hậu kiểm theo [bảng giá OpenAI](https://developers.openai.com/api/docs/pricing), standard short context: `(16 × $2 + 9 × $10) / 1.000.000 = $0,000122`. Đây là **derived estimate, không phải số tiền đã xác nhận trên hóa đơn**; không gồm phụ phí không được báo. Raw `estimated_cost_usd` và `measured_charge_usd` vẫn `null`, không sửa raw sau khi chạy, không dùng giá Shopaikey.

## Bằng chứng và giới hạn

- [Raw result](artifacts/OPENAI-DIRECT-CHECK-20261110-01/result.json), approval và source/profile snapshots được giữ nguyên.
- [Postcheck](../research/artifacts/OPENAI-DIRECT-CHECK-REVIEW-20261110-01/validation.json) pass: hashes/raw/source, metadata key 600, gap, dữ liệu provider trước, frozen pilot và registry R-0222/C-0323; không gọi thêm API. Scan secret chỉ là heuristic, không thay thế audit công bố đầy đủ.
- Key chỉ được runtime đã duyệt dùng nội bộ, không hiển thị; audit chỉ kiểm metadata.
- Một marker pass **không chứng minh ổn định dài hạn**, chất lượng giải task, tool calling hoặc tương thích bốn CLI. Alias cùng tên trên Shopaikey không chứng minh cùng backend/settings.
- Scope kiểm tối thiểu đã dùng hết. Không mở native4CLI, retry hay benchmark48; các bước đó cần protocol/acceptance và quyết định riêng. Cohort OpenAI phải tách khỏi kết quả provider trước.
