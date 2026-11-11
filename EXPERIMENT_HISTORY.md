# Lịch sử thực nghiệm và thay đổi protocol

Tài liệu này gom lịch sử trước khi hoàn tất báo cáo ngày 11/11/2026. **Không dùng các trạng thái tại mốc cũ làm trạng thái hiện tại.** Kết quả cuối ở [REPORT.md](REPORT.md); raw, failure, retry và audit cũ giữ nguyên tại các đường dẫn dưới đây.

## 1. Cohort cuối: OpenAI trực tiếp, reasoning-r3

- [Protocol r3](benchmark/PROTOCOL_OPENAI48_R3.md), [launch audit](research/artifacts/OPENAI48-R3-LAUNCH-20261110-01/validation.json): 185 regression tests, 16 native synthetic cases; bốn native smoke thật là gate trước benchmark.
- Đã hoàn tất 48/48 slot hợp lệ, 46 success/2 failure; 48 snapshot pass. Không retry hai failure để nâng điểm. [Kết quả cuối và raw](benchmark/suite48/OPENAI_BENCHMARK_FINAL.md), [audit cuối](research/artifacts/OPENAI48-R3-FINAL-20261111-01/validation.json).
- Guard estimate benchmark $2,1470985; tổng r3 gồm smoke $2,2430601. Cộng carry/reserve lịch sử thành $2,58276776; không phải hóa đơn, sáu request unpriced lịch sử vẫn unknown.

## 2. OpenAI: lỗi bootstrap và các revision trước r3

| Mốc lịch sử | Quan sát và quyết định | Tài liệu gốc |
| --- | --- | --- |
| Direct check | Catalog/generation HTTP 200, marker đúng; chưa chứng minh native tool calling hoặc ổn định dài hạn | [Direct results](demos/OPENAI_DIRECT_RESULTS.md) |
| r1 smoke | V1 gọi tool được, nhưng cache-write 3109 làm estimator trả cost null; broker chặn local 400. Một smoke đã chạy, benchmark chưa mở | [OpenAI history](benchmark/suite48/OPENAI_RESULTS.md), [audit r1](research/artifacts/OPENAI48-REVIEW-20261110-01/validation.json) |
| Cache-cost r2 | Tách ordinary/cache-read/cache-write; thiếu TTL dùng conservative upper bound. 168 regression tests và 16 native synthetic cases đạt trước live launch | [Thiết kế](benchmark/OPENAI_CACHE_FIX_R2.md), [audit](research/artifacts/OPENAI-CACHE-R2-REVIEW-20261110-01/validation.json) |
| r2 smoke | V1/v2/Pi đạt chức năng; Codex HTTP 400 do harness bỏ `reasoning.context=all_turns` nhưng giữ Responses Lite header. Chưa mở benchmark | [Kết quả](benchmark/suite48/OPENAI_RESULTS.md), [audit r2](research/artifacts/OPENAI48-R2-REVIEW-20261110-01/validation.json) |
| Reasoning r3 offline | Giữ native reasoning fields, chỉ override effort; 180 regression tests và 16 native synthetic cases đạt trước launch mới | [Thiết kế/replay](benchmark/OPENAI_REASONING_FIX_R3.md), [audit](research/artifacts/OPENAI-REASONING-R3-REVIEW-20261110-01/validation.json) |

Các lỗi trên không được tính thành lỗi giải task của cohort cuối. Các raw status và supplementary smoke retries không bị ghi đè.

## 3. Các provider smoke không thuộc cohort cuối

- Shopaikey/Gemini: request đầu trả HTTP 500/internal_error, usage/cost null; dừng theo policy, không mở benchmark. [Kết quả](demos/GEMINI_SMOKE5_RESULTS.md).
- Google AI Studio trực tiếp: request đầu trả HTTP 503/UNAVAILABLE, provider báo high demand; không có successful generation hoặc native CLI acceptance. [Kết quả](demos/GOOGLE_GEMINI_RESULTS.md).
- Không suy global outage, model quality hoặc cùng backend chỉ từ lỗi hay alias model.

## 4. Pilot Shopaikey và chuẩn hóa môi trường

[PILOT_RESULTS.md](benchmark/PILOT_RESULTS.md) giữ diễn tiến và mọi attempt; [frozen summary](benchmark/artifacts/PILOT-FREEZE-20261109-01/SUMMARY.md) giữ phân loại reviewed. Các mốc chính:

1. Diagnostic Pi/P-01 có 6 HTTP 200/completed, public/hidden pass; smoke v1/v2/Codex đạt chức năng nhưng hai gap chuyển CLI dưới 30 giây. [Diagnostic](benchmark/MODEL_COMPARE.md), [smoke](demos/MODEL_SMOKE_SOL_RESULTS.md), [pacing fix](research/PACING_FIX.md).
2. R-0009 dừng do provider terminal failed/usage thiếu; classifier raw gán sai, review là infra_error/pending_review. Bản sửa latch/classifier giữ nguyên raw. R-0017 retry riêng đạt; không biến thành first-attempt success. [Provider stop fix](research/PROVIDER_STOP_FIX.md).
3. Continuation có Codex success và v2 timeout trước completion. Audit tái hiện thiếu `rg` ở sandbox v1/v2/Pi; chuẩn hóa search-r2 bằng cùng bytes `rg` mount read-only cho bốn CLI, không cài host. [Chẩn đoán](research/SEARCH_ENVIRONMENT.md), [environment r2](research/ENVIRONMENT_R2_RESULTS.md).
4. R-0025/R-0026 timeout trước task; probe không auth chỉ chứng minh kết nối cơ bản tại thời điểm đo, không xác định root cause. R-0027 launch lỗi trước inference do thiếu thư mục cha; R-0028 là lời gọi khôi phục và đạt. [Network](research/PROVIDER_NETWORK.md).
5. R-0030/R-0034 có snapshot đúng nhưng timeout 300 giây; không nâng thành success. Chuyển timing policy sang paced-900 cho cả bốn CLI, không tăng request/output/USD guard. [Timing revision](research/PACED_900_RESULTS.md), [policy](benchmark/TIMING_POLICY_R2.md).
6. R-0035–R-0038 P-02 đều đạt, nhưng duration dưới 300 giây nên không quy thành công chỉ cho tăng cap. Toàn pilot có 14 inference attempts/76 upstream: reviewed 8 success, 3 timeout, 3 infra_error; thêm một launch error không inference. Tám cặp task/CLI có ít nhất một success qua revision/retry, **không phải 8/8 first-attempt trong cùng điều kiện**.

Known estimate pilot $1,10640264; sáu request unpriced nên total/charge unknown. Giá Shopaikey user-reported chỉ áp cohort đó. [Pricing ledger](benchmark/SOL_COST.md), [baseline](benchmark/BASELINE.md).

## 5. Benchmark Shopaikey chưa hoàn chỉnh

[Ledger và kết quả đầy đủ](benchmark/suite48/BENCHMARK_RESULTS.md) giữ 8 attempts trên 7 unique slot, gồm một supplementary retry; 41 slot chưa chạy. Không gộp mẫu này với OpenAI48.

- R-0039: v1/B-01 infra_error; giữ lỗi gốc.
- R-0087/R-0088/R-0089: Codex success, Pi failure theo rubric r2 do extra evidence mutation, v2 infra_error trước HTTP/usage. [Audit](research/artifacts/CONTINUE47-REVIEW-20261110-01/validation.json).
- R-0134/R-0135: retry v2/B-01 đạt, Codex/B-02 infra_error; không nâng R-0089 gốc thành success. [Audit](research/artifacts/RETRY45-REVIEW-20261110-01/validation.json).
- R-0179/R-0180: Pi/B-02 success, v2/B-02 timeout trước HTTP/usage, không wall timeout. Known estimate cộng dồn $0,28485816; bốn request unpriced, charge unknown. [Audit](research/artifacts/CONTINUE43-REVIEW-20261110-01/validation.json).

Lịch sử bộ điều phối trước paid launch ở [batch runner](benchmark/suite48/BATCH_RUNNER.md), [native preflight](benchmark/suite48/NATIVE_PREFLIGHT.md). Synthetic exchanges/virtual pacing không được tính thành kết quả model hoặc phí thật.

## 6. Demo native và trạng thái cuối

- [Vòng 1](demos/NATIVE_RUNTIME_RESULTS.md) giữ các attempt lỗi envelope, plugin routing, compaction fixture và recovery stdio không notice; không được sửa ngược thành pass.
- [Vòng 2](demos/NATIVE_COMPLETION_R2_RESULTS.md) kiểm managed recovery/budget, v1 API approval/background flag, legacy permission, Client/SDK failures và shared UI. Lỗi readiness của harness được sửa; raw budget controller có assertion error được giữ và reviewed độc lập.
- Các demo dùng scripted local SSE, không chứng minh semantic memory, model quality hoặc exactly-once. [Acceptance cuối](research/REQUIREMENTS_ACCEPTANCE.md).

## 7. Dữ liệu đã rút

Artifact/log/result model cũ được xóa theo yêu cầu trước đây; runtime claim phụ thuộc được hạ về source-only. Không phục hồi hoặc dùng lại số đo đó. [Phạm vi cleanup](research/SOL_MIGRATION.md). Nhật ký chi tiết các quyết định cũ vẫn ở [PLAN.md](PLAN.md); trạng thái chính thức đọc từ báo cáo và acceptance cuối.
