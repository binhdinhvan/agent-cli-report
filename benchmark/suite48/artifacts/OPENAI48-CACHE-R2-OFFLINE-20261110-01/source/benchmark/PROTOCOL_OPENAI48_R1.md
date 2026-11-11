# Benchmark48 OpenAI trực tiếp — revision 1

Người dùng yêu cầu “chạy benmark đi” sau kiểm tối thiểu OpenAI pass. Chạy cohort **OpenAI-direct mới** `gpt-6.1-sol`, không tiếp 41 slot Sol/Shopaikey và không gộp điểm giữa provider. Giữ bốn binary/commit đã pin, fixture/prompt/rubric `b01-evidence-r2`, order 4 task × 4 CLI × 3 lần, `search-r2`, `paced-900`. Không sửa sealed runner/fixture/pricing hoặc raw cũ.

## Gates và phạm vi

1. Offline unit/regression và native synthetic 16 task×CLI phải pass với adapter mới.
2. Native smoke thật bốn CLI, mỗi CLI tối đa 8 upstream/output2.048/wall900; prompt chỉ yêu cầu chạy lệnh in marker rồi trả marker, không đưa lời giải fixture. Bắt buộc native tool event, final marker, isolation, HTTP200/completed và usage đầy đủ. Không tính điểm smoke như benchmark; grader fixture trong smoke không có ý nghĩa nghiệm thu.
3. Chỉ khi cả bốn smoke đạt mới chạy 48 slot chính thức. Giữ concurrency1, gap≥30s xuyên cả smoke/benchmark, socket45s, wall900s/attempt tính từ outer bwrap spawn đến bridge exit, reserve60s, tối đa8upstream/attempt/output2.048. Native clock là secondary. Giới hạn là cap chứ không dự báo runtime.
4. Không retry upstream, không fallback protocol/provider/model, không auto-resume hoặc top-up. Lỗi infra/provider/usage thiếu dừng batch; task failure/timeout hợp lệ được giữ và có thể tiếp slot sau. Native retry cục bộ bị broker latch chặn sau lỗi, không phát sinh upstream retry.

## Provider/settings và chi phí

Broker host gọi riêng `https://api.openai.com/v1/responses`, SSE/storefalse, **reasoning low/service_tier default** áp dụng thống nhất và ghi effective settings; giữ native tool schema và protocol headers. Các CLI dùng custom local provider/nonce, không nhận key thật. Config native cũng đặt low: v1 model options, v2 model settings/body, Pi thinkinglow, Codex model_reasoning_effortlow. Không tái dùng none/off của cohort cũ. Context cap giữ128K để không đổi baseline; output2.048 gồm reasoning.

Giá lấy từ profile OpenAI riêng: input2/cached0.10/output10USD/M, standard short context. Giữ usage đầy đủ; cache-write khác0, input>272K hoặc usage không hợp lệ → costnull và dừng để review, không đoán billing. Estimate không phải invoice; không xác nhận phụ phí/accountbalance. Không dùng bảng giá Shopaikey. Guard **tổng16USD known estimate**, carry0.28485816USD của benchmark cũ +0.000122USD check OpenAI; smoke và cohort mới cùng trừ vào phần còn lại15.71501984USD. Bốn request unpriced cũ vẫn unknown, không đặt0; không mang điểm/kết quả cũ vào cohort mới. Historical pilot1.10640264USD/6unpriced nằm ngoài guard benchmark như trước. Không tự tăng ngân sách.

Approval bind plan/source/profile/resource/registry; reserve **52 R/C IDs mới** dưới lock (4 smoke +48 benchmark), giữ mọi ID reserved/not_run cũ. Credential loader private600 chỉ chạy sau gates; không hiển thị key, redacts full/partial key trên response/artifact. Fresh isolated workspace/session/config/service cho mỗi attempt, không sửa source repo/tool binary hay service thật. Giữ raw config/usage/errors/grading/attempts và source snapshots. Thiếu usage khác0; failure môi trường khác task failure.

## Nguồn settings

- [OpenAI model card](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [pricing](https://developers.openai.com/api/docs/pricing), profile `research/model-profiles/openai-gpt-6.1-sol.json`.
- [v2 providers](https://opencode.ai/v2/docs/providers): model `settings`, `body`, capabilities và runtime Responses; config isolation kế thừa runner đã nghiệm thu.
- v2 pinned `9bbb8ce18c80f099e0e448775f59d965ead40a21`: [`open-responses.ts`, reasoning mapping](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/ai/src/protocols/open-responses.ts#L842-L845).
- v1 pinned `810c0eba1a7348036f8bdf61e6632d0c36c6876c`: [`provider-options.ts`, reasoning conversion](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/core/src/v1/config/provider-options.ts#L45-L51).
- Pi pinned `f9a26365568127461c47a07a37dcb42c140a3ac5`: `packages/ai/src/api/openai-responses.ts`, `streamSimpleOpenAIResponses`/reasoningEffort. URL upstream lấy từ metadata source đã pin, không suy từ tên thư mục.

Native synthetic không chứng minh provider hỗ trợ; smoke thật không chứng minh ổn định dài hạn hoặc chất lượng benchmark. Gates/status của từng giai đoạn báo riêng.
