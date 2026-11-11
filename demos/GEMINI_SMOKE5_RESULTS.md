# Gemini smoke5 — dừng ngay request đầu

Model gửi: `gemini-3.8-flash`; provider Shopaikey; thử `POST /v1/responses` với SSE, prompt marker cố định, outputcap256. Không chạy native CLI/tools/session hoặc benchmark.

- **1/5request đã gửi,0pass,4not_run.** UTC2026-11-10T14:59:58.876397Z–14:59:59.551962Z,676ms.
- Provider thực trả **HTTP500**, JSONerror `type=api_error`, `code=internal_error`, thông báo “An error occurred while processing the request, please try again later”. Đây không phải brokerlocal503 hoặc TimeoutError như các attempt sol trước.
- Chưa có SSE terminal/model identity/usage. Chưa chứng minh alias đúng backend, hỗ trợ Responses hay Gemini ổn định hơn sol; HTTP500 generic không xác định nguyên nhân model/provider/adapter.
- Theo protocol, dừng ở lỗi đầu, không retry hoặc thử ChatCompletions/Gemini native fallback. Không gọi model catalog hay endpoint phụ. Giá chưa có: **estimated/measuredcostnull**,1unpriced; không gán phí0 hoặc dùng giá sol.
- R/C registry vẫnR222/C323; smoke này dùng artifactIDriêng, không nhập8attemptsol hoặc benchmark48. Toànsolraw/pricing/frozen giữ nguyên. Native4CLI/benchmarkGemini vẫn chưa nghiệm thu.

[Protocol đã pin](GEMINI_SMOKE5.md), [raw](artifacts/GEMINI-SMOKE5-20261110-01/result.json), [postcheck](../research/artifacts/GEMINI-SMOKE5-REVIEW-20261110-01/validation.json). Input/source snapshots đúng approval trước cập nhật trạng thái profile; raw giữ hash, secret-pattern scan chỉ là heuristic, không thay publication/PII review.

Không tự mở lại4slot hoặc đổi protocol/model. Lượt mới cần quyết định riêng; nhóm benchmark model mới phải chạy lại thành cohort độc lập như người dùng yêu cầu.
