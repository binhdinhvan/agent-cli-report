# Google trực tiếp — smoke dừng ở request đầu

Model gửi `gemini-3.8-flash`, endpoint Google `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`, Chat Completions SSE. Key Google riêng chỉ được dùng trong process đã có approval, không qua Shopaikey và không ghi key vào artifact.

## Kết quả thật

- **1/5request đã gửi,0pass,4not_run.** UTC2026-11-10T15:20:39.709552Z–15:20:40.555913Z, **846ms**.
- Google trả **HTTP503**, `status=UNAVAILABLE` với thông báo:

  > This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.

- Đây là HTTP503 thực trên kết nối trực tiếp Google, khác brokerlocal503 trong sol và khác HTTP500 Shopaikey ở smoke trước. Lý do high demand là **provider-reported**, chưa phải phép kiểm độc lập về outage toàn hệ thống hoặc model identity/backend.
- Chưa có SSE generation hoàn tất, response model identity hoặc usage. Giá cũng pending: **estimated/measuredcostnull**,1unpriced. Không gán0/token0 hoặc kế thừa giá Shopaikey/sol.
- Theo scope đã duyệt, dừng ngay lỗi đầu; không retry, không mở4request còn lại, không chuyển endpoint/model/provider tự động. Không benchmark48 hoặc native4CLI/toolcalling acceptance.

## Audit và giới hạn

[Raw result](artifacts/GOOGLE-GEMINI-SMOKE5-20261110-01/result.json), [approval](approvals/GOOGLE-GEMINI-SMOKE5-20261110-01.json), [postcheck](../research/artifacts/GOOGLE-GEMINI-SMOKE5-REVIEW-20261110-01/validation.json).

Input/source snapshots khớp approval trước cập nhật trạng thái profile. Raw/hash/keymetadata600/priorraw/frozenSol/registry kiểm đạt; audit không đọc lại nội dung key hoặc gửi API. RegistryR222/C323 không đổi. Secret-pattern scan chỉ heuristic, không thay fullpublication/PII review.

Kết quả này chưa chứng minh Gemini ổn định hơn sol hoặc key/model/account đã qua nghiệm thu hoàn chỉnh. Mọi lượt tiếp theo cần quyết định mới; nhóm benchmark Google phải độc lập với Shopaikey/Sol.
