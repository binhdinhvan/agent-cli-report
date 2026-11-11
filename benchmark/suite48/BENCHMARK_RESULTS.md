# Benchmark48 — batch đầu dừng, 2026-11-10

## Hiện tại: continuation43 dừng sau 2 slot

| Run / slot | Task / CLI | Status | Primary duration | Upstream | Known estimate USD |
| --- | --- | --- | ---: | ---: | ---: |
| R-0179 / D48-006 | B-02 / Pi | success / valid | 157222ms | 5 | 0.03299880 |
| R-0180 / D48-007 | B-02 / OpenCode v2 | infra_error / pending_review | 159194ms | 1 | unknown; known subtotal0 không phải miễn phí |

Theo [protocol continuation43](../PROTOCOL_CONTINUE43_R2.md), không retry slot đã chạy. Batch UTC14:33:54–14:39:13 đã dừng 2/43 slot, còn **41 slot chưa chạy**. [Raw](artifacts/BENCH43-CONTINUE-20261110-01/result.json), [audit](../../research/artifacts/CONTINUE43-REVIEW-20261110-01/validation.json).

- Pi chỉ sửa `pagination.py`, scope/public/hidden pass, CLIexit0. V2 request1 `TimeoutError` trước HTTP/terminal/usage, chưa sửa file; không có wall timeout, chưa xác minh root cause. Không coi đây là tool giải sai hoặc chứng minh upstream503.
- 6upstream/5HTTP200completed cóusage/1unpriced;5/5gap≥30s, kể cả xuyênCLI; reserve tối thiểu753.439768s≥60s. Audit input/resource/raw/frozen/Git/isolation/cleanup đạt,41unrun roots vắng.
- Known batch **0.03299880USD**; tổng benchmark **0.28485816USD known,4requestunpriced,totalchargeunknown**. Guard tổng16USD estimate không thay đổi; arithmetic remaining15.71514184USD không phải số dư hóa đơn hoặc quyền chạy tiếp.
- Tổng **8attempts trên7/48slot unique**: firstattempts2success/1failure/4infra, cộng1supplementaryretrysuccess;41not_run. Giữ nguyên rubric revisions, Pi/B01evidence caveat, R89infra và R134retry riêng; không xếp hạng từ mẫu này.
- ReserveR179–221/C280–322, đã chạyR179–180/C280–281;41cặp mới cònreserved/not_run. Next **R-0222/C-0323**, không tự retry/resume/probe.

## Lịch sử: retry v2 đạt, batch retry45 dừng tại Codex/B-02

Theo [protocol retry45](../PROTOCOL_RETRY45_R2.md), thực hiện1retryR89 rồi44slot chưa chạy. Batch dừng sau **2/45attempts**, còn **43slot unique chưa chạy**.

| Run / slot | Task / CLI | Status | Primary duration | Upstream | Known estimate USD |
| --- | --- | --- | ---: | ---: | ---: |
| R-0134 / D48-004 | B-01 / OpenCode v2, retry_ofR89 | success / valid,10/10 | 224706ms | 6 | 0.03844560 |
| R-0135 / D48-005 | B-02 / Codex | infra_error / pending_review | 73499ms | 1 | unknown; known subtotal0 không phải miễn phí |

- [Raw batch](artifacts/BENCH45-RETRY-CONTINUE-20261110-01/result.json), [audit](../../research/artifacts/RETRY45-REVIEW-20261110-01/validation.json). UTC14:17:00–14:22:01;7upstream/6HTTP200completed cóusage/1unpriced,6/6gap≥30s kể cảxuyênCLI; khôngwalltimeout. Scope/isolation/input-resource/raw/frozen/Git/cleanup đạt.
- Retryv2 chỉ tạoanswer.json,10/10 vàCLIexit0. **R89gốc vẫninfra_error**, retry supplementary không thay firstattempt hoặc independent repetition.
- Codex request1 `TimeoutError` trướcHTTP/terminal/usage, chưa sửa file; CLI báo stream disconnected/turn.failed. Không bằng chứng task sửa sai, upstream503 hoặc rootcause cụ thể. Không tựretry/resume.
- Batchknown0.03844560USD, tổngbenchmark **0.25185936USD known/3requestunpriced/totalchargeunknown**, không nhập pilot. Guard16USDkhônginvoicecap; arithmeticremaining15.74814064USDkhông phải số dư hoặc quyền chạy tiếp.
- Tổng **6attempts trên5/48unique slots**: firstattempts1success/1failure/3infra, cộng1supplementaryretrysuccess;43not_run. Giữ mọi attempt/revision/caveat rubric, không xếp hạng từ mẫu này.
- ReserveR134–178/C235–279, đã chạyR134–135/C235–236;43cặp mới cònreserved/not_run, counters tiếp theo **R-0179/C-0280**. Giữ nguyên IDs/data hai batch cũ.

## Lịch sử: continuation47 dừng sau3/47slot

Continuation theo [protocol r2](../PROTOCOL_47_CONTINUE_R2.md), không retryR39. **Toàn thiết kế có4/48slot đã thực hiện,44not_run:**1success,1failure theo sealed rubric,2infra_error/pending_review. R1/R2 có rubric khác, không coi đây là cohort đồng nhất hoặc đủ để xếp hạng.

| Run / slot | B-01 / CLI | Status / validity | Raw rubric | Duration primary | Upstream | Known estimate USD |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| R-0087 / D48-002 | Codex | success / valid | 10/10 | 124344ms | 4 | 0.11446704 |
| R-0088 / D48-003 | Pi | failure / valid theo r2 | 9/10 | 171830ms | 5 | 0.03041328 |
| R-0089 / D48-004 | OpenCode v2 | infra_error / pending_review | không có answer | 155949ms | 1 | unknown (known subtotal0 không phải miễn phí) |

- [Raw continuation](artifacts/BENCH47-CONTINUE-20261110-01/result.json), [audit](../../research/artifacts/CONTINUE47-REVIEW-20261110-01/validation.json). UTC13:56:28–14:04:04;10upstream,9HTTP200/completed cóusage,1unpriced;9/9gap≥30s, cả gap xuyênCLI. Không walltimeout; min remaining dispatch731.81528s≥reserve60s.
- **V2 request1 TimeoutError trước HTTP/terminal/usage**, chưa tool execution/chưa sửa file; CLIexit1. Local503latch chặn retry, không bằng chứng upstream503/overload hoặc rootcause mạng.44suffix not_run, không tự resume/retry.
- **Pi:** CLIexit0, scope/public pass,5giá trị đúng. Mất1điểm evidence mutation do thêm `aliases.py:canonical_name` bên cạnh `resolver.py:resolve`; sealed r2 chỉ nhận symbol sau ở mục này. Giữ failure/valid/raw9/10 theo protocol; ghi **rubric design caveat cần review**, không nói5đáp án sai, không regrade hoặc sửa rubric sau quan sát âm thầm.
- Known continuation **0.14488032USD**; cộng batch cũ benchmark known **0.21341376USD**, **2requestunpriced**, total/measuredcharge null. Pilot không nhập vào guard16USD; không invoicecap, không tăng guard. Remaining known arithmetic15.78658624USD **không phải số dư hóa đơn hoặc quyền tự chạy tiếp**.
- Reserve mớiR87–133/C188–234; đã chạyR87–89/C188–190.44cặp mới cònreserved/not_run;47cặp reserved cũ giữ nguyên. Counters tiếp theo **R-0134/C-0235**. Audit input/resource/fixture/binary/raw/frozen/Git/cleanup đạt; không job/ socket của3supervisor còn lại, unrunruntime roots vắng.

## Batch đầu R1 — giữ nguyên ghi nhận bên dưới

> Các số liệu phía dưới chỉ là batch đầu, không phải tổng hai batch. Nguyên nhân mạng vẫn user-reported; không retryR39 hoặc regrade raw9/10.

**1/48 slot đã thực hiện,47slot not_run; chưa có success hoặc dữ liệu để so sánh tool.** Theo stop policy, không tự retry/resume, không tăng budget/cap. Giữ nguyên protocol/fixture/grader/raw/CSV đã khóa.

| Run / slot | Task / CLI | Status / validity | Upstream | Duration primary | Known estimate USD |
| --- | --- | --- | ---: | ---: | ---: |
| R-0039 / D48-001 | B-01 / OpenCode v1 | infra_error / pending_review | 5 | 278237ms | 0.06853344 |

- [Raw batch](artifacts/BENCH48-20261110-01/result.json), [raw run](artifacts/BENCH48-20261110-01/D48-001/result.json), [CSV riêng](../runs-benchmark48.csv), [audit](../../research/artifacts/BENCH48-REVIEW-20261110-01/validation.json).
- Batch UTC03:13:10–03:17:49. CLI exit1, không wall timeout; watchdog/deadline chung900s đúng origin. Reserve tại dispatch còn≥734.670317s. **4/4gap≥30s**, outputcap2048/request/requestcount5≤8; không dừng vì wall/request/output/USD cap.

## Nguyên nhân stop quan sát được

Bốn request đầu HTTP200/response.completed và có usage. **Request5 `TimeoutError` trước khi có HTTP status/terminal/usage**, không có finished timestamp ở ledger. Chưa xác định gateway/provider/network root cause hoặc provider có nhận/xử lý request5 hay chưa.

CLI sau đó thấy503 với body `Batch stopped after provider failure; no upstream request sent.` tại [stdout dòng14](artifacts/BENCH48-20261110-01/D48-001/stdout.jsonl). Đây là broker local latch chặn native retry, **không phải bằng chứng upstream trả503/overload**. Ledger chỉ5upstream; quan sát ít nhất1local reject, số native retry nội bộ chính xác chưa được instrument, không tự đoán.

Known estimate batch **0.06853344USD**, **1request unpriced**, estimated total/measured charge **null**. Guard mới16USD chưa chạm theo known estimate nhưng usage thiếu vẫn phải stop. Không xem request thiếuusage là0 hoặc remainingestimate là số dư hóa đơn. Pilot known1.10640264USD và6requestunpriced tách riêng, không nhập vào batch benchmark này.

## Snapshot và rủi ro rubric — không kết luận tool giải sai

Agent chỉ tạo `answer.json`, scope và public schema pass. Snapshot raw hidden **9/10**, không CLI completion. Cả5giá trị nội dung (`default`, `precedence`, `alias_trace`, `cycle_error`, `mutation`) khớp oracle. Điểm mất thuộc evidence của `cycle_error`: câu trả lời có cả `aliases.py:canonical_name` và `aliases.py:ALIASES`, trong khi hidden allowlist chỉ nhận symbol đầu và yêu cầu **mọi reference đều nằm trong allowlist**.

`ALIASES` có thật và định nghĩa cycle graph; do đó có **rủi ro allowlist quá hẹp so với yêu cầu evidence hỗ trợ trong prompt**, không công khai cho agent. Ghi pending review riêng, không tự đổi9→10, không sửa sealed grader sau khi thấy kết quả, không nâng infra_error thành success hoặc task failure. Mọi sửa rubric cần quyết định/revision và chính sách xử lý lượt cũ công khai trước khi chạy tiếp.

## Registry và an toàn

48R/C đã được reserve nguyên tử trước dispatch: **R-0039–R-0086 / C-0140–C-0187**. ChỉR39/C140 được thực hiện;47cặp còn lại reserved/not_run, không tái sử dụng. Counters tiếp theo **R-0087/C-0188**, không có nghĩa đã chạy87lượt. Không tự launch lại48slot để né suffix chưa chạy.

Audit đạt input/source/protocol/fixture/binary/resource hash, snapshot/scope/public/score provenance, real pacing4gap, source Git sạch, supervisor PID/broker socket đã mất, unrun config roots vắng. Secret-pattern scan đạt nhưng không thay thế review publication/PII; không đọc key/gọi provider trong audit. Runner/source/CSV/raw không bị sửa khi postcheck.

**Bước an toàn tiếp:** review rubric B-01 offline và giữ request5/protocol evidence; chốt có đổi rubric/revision hay giữ nguyên trước khi xin quyết định continuation/retry. Không gửi thêm inference hoặc retry mù để thử provider.
# Cohort lịch sử Shopaikey — không gộp với OpenAI

**Benchmark hoàn chỉnh mới nằm ở [OPENAI_BENCHMARK_FINAL.md](OPENAI_BENCHMARK_FINAL.md):48/48OpenAI,46success/2failure hợp lệ.** Toàn bộ nội dung dưới đây giữ nguyên cho cohortShop trước, không thay provider/model hoặc cộng slot vào48OpenAI.
