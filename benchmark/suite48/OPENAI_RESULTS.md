# OpenAI trực tiếp — native smoke dừng trước benchmark

**Cập nhật cuối: benchmark đã chạy đủ48lượt**,46success/2failure hợp lệ,0timeout/infra_error; cả4CLI đãpasssmokethật r3. [Kết quả cuối](OPENAI_BENCHMARK_FINAL.md), [audit](../../research/artifacts/OPENAI48-R3-FINAL-20261111-01/validation.json). Nội dung bên dưới là lịch sử bootstrap/r1/r2, không phải trạng thái hiện tại; rawcũ giữ nguyên.

**Bản sửa reasoning r3 đã hoàn tất offline:** [adapter/thiết kế](../OPENAI_REASONING_FIX_R3.md) giữ nativecontext/summary/fields khác, chỉ chuẩn hóa effortlow; giữ header/protocol/cache-costr2 và mọi cap/guard. [Replay R277](../../research/artifacts/OPENAI-REASONING-R3-REPLAY-20261110-01/replay.json), [audit](../../research/artifacts/OPENAI-REASONING-R3-REVIEW-20261110-01/validation.json):180tests/16native synthetic/40exchanges đạt,8ResponsesLite giữcontext.0API/keyread/reserveID; không regrade hoặc sửaraw400. Chưa liveacceptance saufix/benchmark; cần freshlaunchplan/approval vàIDs mới.

## Lượt chạy lại cache-r2: 3 smoke pass, Codex bị adapter làm mất reasoning.context

Ngày2026-11-10,16:27:39–16:32:19UTC. R274/OpenCodev1, R275/OpenCodev2 và R276/Pi **đạt native smoke thật**: tool event và final marker đúng. Raw status `failure/valid` của ba lượt này là fixturegrader không được sửa file theo promptsmoke, **không phải smoke fail hoặc benchmark task failure**.

R277/Codex dừng ở HTTP400 `invalid_request_error/unsupported_value`: `X-OpenAI-Internal-Codex-Responses-Lite requires reasoning.context to be all_turns`. Native đã gửi `reasoning: {effort:low,context:all_turns}`, nhưng normalizer trong `openai48.py:context.request` thay cả object bằng `{effort:low}`, đồng thời giữ ResponsesLiteheader. Đây là lỗi tích hợp của harness; **không phải provider chập chờn hoặc cache-costr2 còn lỗi**. Bản sửa tiếp cần giữ nguyên các native reasoning fields khi chốt effort, không tự đổi protocol/header hoặc coi source-only fix là live pass.

Tổng9upstream: **8HTTP200/completed,1HTTP400**. Cache-costr2 định giá được toàn bộ8requestcóusage; guard estimate **$0,0372805**, gồm conservativeTTLupperbounds; khoảngtariff của phầnusageđãbáo$0,0207630…$0,0372805, **không gồmrequest400thiếuusage**.1unpriced mới, charge thựcunknown, không coi400miễnphí. GuardcumulativecóreserveR222 thành$0,33970766/remaining$15,66029234; historicalunknown tăng5→6, không tăngguard16.

**0/48benchmark đã chạy**, giữ48notrun và52IDs mới đãreserve R274…325/C375…426; nextR326/C427. Scopeđãđóng, khôngauto retry/fallback. [Raw](artifacts/OPENAI48-R2-20261110-01/result.json), [postcheckpass](../../research/artifacts/OPENAI48-R2-REVIEW-20261110-01/validation.json) giữraw/sourcehashes/priorproviders/frozenpilot, kiểmcleanup4CLI vàkeymetadata600; audit0API/keyread. Bằngchứng normalizer tại [source snapshot](artifacts/OPENAI48-R2-20261110-01/source/benchmark/openai48.py#L111-L120), hash pinned trongaudit. Các mốc dưới đây là lịch sử.

**Đã có bản sửa cache-cost r2 offline:** [thiết kế và công thức](../OPENAI_CACHE_FIX_R2.md), [replay raw cũ](../../research/artifacts/OPENAI-CACHE-R2-REPLAY-20261110-01/replay.json). Regression101benchmark +67demo đạt, gồm19testmới. Khi thiếu TTLbreakdown, dùng conservative12hguardestimate (không gọi là charge); missingusage thật vẫn chặn. Chưa chạy lại API hoặc sửa status/rawcostnull của lượt dưới đây.

[Native offline r2](artifacts/OPENAI48-CACHE-R2-OFFLINE-20261110-01/result.json) **16/16task×CLI,40synthetic exchanges** cópositivecachewrite3109/khôngTTLbreakdown đều đạt; [audit](../../research/artifacts/OPENAI-CACHE-R2-REVIEW-20261110-01/validation.json) xác nhận0providerrequests/keyread/reserveID, raw/source/frozen giữ nguyên. Đây không phải native smoke thật hoặc benchmark model; cần live plan/approval mới trước retry.

**Chưa có benchmark OpenAI chính thức: 0/48 lượt chạy, 48 not_run.** Ngày 2026-11-10, native smoke đầu tiên R-0222/C-0323/OpenCode v1 dừng sau 70.953 ms; ba CLI smoke còn lại chưa chạy. Không retry/fallback hoặc gọi thêm API.

## Điều thực sự xảy ra

- Hai upstream đều **HTTP 200 / `response.completed`**, model `gpt-6.1-sol`, tier `default`, reasoning `low`.
- Request1: 568 input/44 output, cache-write0; known estimate **$0,001576**.
- Request2: 3.112 input/32 output, cached0, **cache-write3.109**. Provider có usage đầy đủ; bộ estimate revision1 chủ động trả costnull khi cache-write khác0 để tránh đoán TTL/billing.
- Native `bash` đã chạy đúng lệnh, exit0 và in marker. Nhưng broker chặn request tiếp theo do prior costnull, trả **local HTTP400**, nên không có final assistant marker. HTTP400 này **không phải phản hồi OpenAI**.
- Shared dispatcher ghi `infra_error/pending_review`, lý do `usage_missing`; trong lượt này nhãn đó có nghĩa **không tính được cost**, không phải provider thiếu usage. Không sửa raw nhãn cũ.
- Fixture không đổi; hidden grader fail là dự kiến vì smoke yêu cầu không sửa file, **không phải model thất bại task benchmark**. Index append-only có slot `OAI-SMOKE-1`, repetition `smoke`; phải loại khỏi điểm benchmark.

## Nguyên nhân và hướng sửa offline

Lượt này dừng do **gate tính phí của harness do assistant cấu hình quá bảo thủ**, không phải bằng chứng OpenAI outage/chập chờn. Chưa thể nghiệm thu đầy đủ native smoke bốn CLI.

[Tài liệu cache chính thức](https://developers.openai.com/api/docs/guides/prompt-caching#monitor-cache-performance), đọc sau lượt chạy, mô tả cache-write là **nhóm token tách khỏi ordinary input/cached reads**, không phải phụ phí cộng chồng. TTL mặc định30m, có12h; usage có thể tách `cache_write_tokens_details.ttl_30m_tokens/ttl_12h_tokens`. Revision tiếp cần kiểm accounting/TTL (hoặc conservative upper estimate được ghi rõ), ghi effective cache settings và test guard trước khi gọi API. Raw lượt này không có breakdownTTL nên **không tự gán một giá duy nhất** hay dùng native CLI cost làm invoice.

Known mới $0,001576, **1 request chưa định giá**, charge thực unknown. Guard benchmark cộng carry trước thành known **$0,28655616 / 5 unpriced**; giữ tổng16USD, không tăng budget. Scope đã dừng; việc sửa offline không tự mở quyền chạy lại smoke/API.

## Bằng chứng

- [Summary raw](artifacts/OPENAI48-20261110-01/result.json), [native events](artifacts/OPENAI48-20261110-01/native-smoke/OAI-SMOKE-1/stdout.jsonl).
- [Postcheck pass](../../research/artifacts/OPENAI48-REVIEW-20261110-01/validation.json): raw/source hashes,52freshIDs, isolation/cleanup, keymetadata600; audit0API/khôngđọcnộidungkey, scansecret heuristic.
- IDs R-0222…0273/C-0323…0374 đã reserve, kể cả not_run; next R-0274/C-0375, không tái dùng. Provider khác và frozen pilot được giữ nguyên.
