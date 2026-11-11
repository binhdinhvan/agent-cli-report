# Báo cáo so sánh OpenCode, Pi và Codex CLI

Workspace để nghiên cứu source, chạy demo và benchmark, sau đó viết báo cáo.

## Bản nộp hoàn chỉnh

**[OpenCode_Comparison_Report.pdf](OpenCode_Comparison_Report.pdf)** — **19 trang**, gồm 16 trang báo cáo chính và 3 trang phụ lục. Các link source/bằng chứng có thể nhấp; artifact nghiên cứu được pin tại commit `f2becc501cfc1b980b888402458bac81b8193370`, không trỏ về filesystem của máy xuất PDF. Đây là file duy nhất cần gửi mentor để đọc báo cáo; repository vẫn đi kèm để kiểm chứng raw/code.

**Repository public:** [binhdinhvan/agent-cli-report](https://github.com/binhdinhvan/agent-cli-report). Đọc [REPORT.md](REPORT.md), tải [APPENDIX.pdf](APPENDIX.pdf) và xem [hướng dẫn kiểm chứng](SUBMISSION.md). Credentials/binary/dependencies cục bộ không nằm trong Git; một raw lịch sử >100 MiB được lưu gzip lossless, xem [PUBLISHING.md](PUBLISHING.md).

**Phụ lục để nộp mentor:** [APPENDIX.pdf](APPENDIX.pdf) — 3 trang A4 với [ảnh mới Desktop/Chrome/TUI](demos/UI_RECAPTURE_RESULTS.md), log chức năng và biểu đồ benchmark. [HTML tự chứa](APPENDIX.html), [nguồn/cách tái tạo](research/APPENDIX_GUIDE.md). Chỉ chạy thêm lượt UI cách ly đã duyệt; không gọi model hoặc chạy lại benchmark, chưa ghép vào PDF chính.

**Bản đã biên tập sau review mentor:** xem [REPORT.md](REPORT.md). Giữ phiên bản chốt ngày **06/11/2026** và nguyên kết quả benchmark; đã đồng bộ trạng thái runtime, đưa demo/code và đối chiếu yêu cầu vào report. [Hướng dẫn bàn giao và kiểm chứng](SUBMISSION.md), [fairness/token/timing](research/BENCHMARK_FAIRNESS.md), [lịch sử thực nghiệm riêng](EXPERIMENT_HISTORY.md). Các khối lịch sử bên dưới không phải trạng thái hiện tại; repository public thay cho archive bàn giao riêng.

**Đã hoàn thành benchmark48 và bản tổng hợp báo cáo.** OpenAI trực tiếp/`gpt-6.1-sol`: **46success,2failure hợp lệ,48/48snapshotpass**, khôngtimeout/infra_error trongcohort. Medianv1/v2/Pi/Codex lần lượt228,15/200,20/164,23/139,63giây, gồm pacing. Guardestimate48lượt **$2,1470985**, không phải hóađơn; lịch sửusageunknown giữ nguyên.

- [Báo cáo chính](REPORT.md): so sánhsource sáutrục, v1/v2, phươngpháp, kếtquả vàlimitations.
- [Kết quả cuối +48row/raw](benchmark/suite48/OPENAI_BENCHMARK_FINAL.md), [audit](research/artifacts/OPENAI48-R3-FINAL-20261111-01/validation.json).
- [Phiênbản/sourcepins](research/versions.md), [evidenceindex](research/evidence.csv).

**Đã hoàn tất8/8hạng mục đề bài trong phạm vi nghiệm thu:** [bảng đối chiếu](research/REQUIREMENTS_ACCEPTANCE.md). Demo còn thiếu đã kiểm managed-service shell/subagent recovery và sideeffectcounter, resume-budget, permissionv1/configmigration, Client/SDKerror-timeout-interrupt và **TUI/Desktop/Web cùng session/servicePID** có ảnh native. [Kết quả vòng2](demos/NATIVE_COMPLETION_R2_RESULTS.md), [audit pass](research/artifacts/NATIVE-COMPLETION-R2-REVIEW-20261111-02/validation.json), [audit tài liệu](research/artifacts/NATIVE-COMPLETION-DOCUMENTS-20261111-02/validation.json).194tests đạt; inference scripted local, **0 API thật mới**; không modelquality/semanticmemory/exactly-once. Scope trảphí đóng, khôngretry hai benchmarkfailure; giới hạn Linuxheadless và SDKbuildprovenance ghi rõ.

<details>
<summary>Nhật ký chuẩn bị và các cohort trước — không phải trạng thái hiện tại</summary>

**Chạy lại bằng reasoning-r3 đã được duyệt:** [protocol](benchmark/PROTOCOL_OPENAI48_R3.md),185tests vànativeoffline đãđạt. Mộtđợt4smokethật→48benchmark nếuđủgate, giữguard16USD/IDs mới/khôngautoretry. Chưa có kết quả mới tại mốclaunch; không tạo jobtrùng từ cácmessagecontinue.

**Lỗi Codex mất `reasoning.context` đã sửa offline:** [revision3](benchmark/OPENAI_REASONING_FIX_R3.md) giữ nguyên native reasoning fields, chỉ chốt effortlow. **180 tests +16/16 native synthetic đạt**, gồm8ResponsesLiteexchanges cócontextall_turns. Chưa gọi thêmAPI/chạy lại benchmark; rawcũ vàngânsách giữ nguyên, live launcher cũ khôngtựdùngr3.

**Kết quả chạy lại: 3/4 CLI đạt smoke thật** (OpenCodev1,v2,Pi). Codex gặpHTTP400 vì **adapter làm mất `reasoning.context=all_turns`**, không phải lỗi cache hay bằng chứng provider chập chờn. **Benchmark vẫn0/48**. [Kết quả/audit](benchmark/suite48/OPENAI_RESULTS.md);9APIrequests,guardestimate$0,0372805/1unpriced,chargeunknown. Đãdừng,khôngauto retry.

**Chạy lại benchmark OpenAI bằng cache-costr2 đã được duyệt:** [protocol](benchmark/PROTOCOL_OPENAI48_R2.md),172tests và16/16nativeoffline đạt.4smokethật trước48benchmark, IDs mới; guard16USD khôngtăng, remainingguard$15,69757284saucarry/reserve. Khôngauto retry/fallback, rawcũgiữnguyên; chưa có kết quả đợt mới tại mốc launch.

**Gate tính phí cache đã sửa và nghiệm thu offline:** [revision2](benchmark/OPENAI_CACHE_FIX_R2.md), **168 tests +16/16 native synthetic** đạt, kể cả cache-write có giá trị dương và thiếu TTLbreakdown. Không tính trùng token; guard dùng mứcphícao hơn nếu TTLunknown, không coi là charge. **Chưa gọi thêm API/chạy lại benchmark**; dữ liệu cũ vàguard16USD giữ nguyên.

**Benchmark OpenAI chưa chạy (0/48):** native smoke v1 đã gọi tool thành công, cả2requestOpenAI200/completed, nhưng **gate tính phí của harness** chặn do cache-write chưa được estimator xử lý. Không phải bằng chứng provider chập chờn;3CLI smoke chưa chạy. [Kết quả](benchmark/suite48/OPENAI_RESULTS.md). Đã dừng, không tựretry; mới known$0,001576/1unpriced, tổngchargeunknown.

**Đã duyệt chạy benchmark OpenAI mới:** [protocol](benchmark/PROTOCOL_OPENAI48_R1.md), 149 tests offline và16/16 native synthetic đạt. Chạy4native smoke thật trước, chỉ khi đạt mới48slot; giữguard16USD gồm phísmoke vàcarrycũ, khôngretry/fallback/topup. Chưa có kết quả cohort mới tại mốc launch; không trộn provider.

**OpenAI trực tiếp đã qua kiểm tra tối thiểu:** `gpt-6.1-sol`, catalog và generation đều HTTP 200; request ngắn hoàn tất trong **4,38 giây**, usage 16 input/9 output. [Kết quả](demos/OPENAI_DIRECT_RESULTS.md), ước tính hậu kiểm **$0,000122**, chưa xác nhận hóa đơn. Scope đã dùng hết; chưa kiểm tool calling/native4CLI hoặc mở benchmark48, chưa kết luận ổn định dài hạn. Key không hiển thị; dữ liệu provider trước giữ nguyên.

**Provider trước: Google AI Studio trực tiếp.** [Smoke](demos/GOOGLE_GEMINI_RESULTS.md) dừng ngay request1: **HTTP503/UNAVAILABLE**, Google báo modelhighdemand,846ms.0pass/4not_run,usage/costnull. Khôngretry/fallback, chưa nghiệmthu native4CLI/benchmark48. Key giữquyền600, khônglộtrongartifact; dữ liệu Shopaikey/Sol giữ nguyên.

**5smoke Google đã được duyệt nhưng dừng ở lỗi đầu theo policy.** Approval riêng không mở retry/benchmark48; lượt mới cần quyết định riêng.

**Gemini trên Shopaikey:** [smoke5](demos/GEMINI_SMOKE5_RESULTS.md) dừng ngay request1 với **HTTP500/internal_error** trong676ms;0pass/4not_run,usage/costnull. Khôngretry/fallback, chưa mở48benchmark/native4CLI. User chọn chạy lại thành cohort mới, không nối2model; toàn bộ kết quả sol giữ nguyên.

**Hiện tại:** [continuation43](benchmark/suite48/BENCHMARK_RESULTS.md) dừng sau 2 slot: Pi/B-02 đạt, v2/B-02 timeout trước HTTP/usage. Tổng 8 attempts gồm 1 retry trên7/48slot unique; **41 slot chưa chạy**. Known0.28485816USD/4unpriced/totalchargeunknown. Giữ lỗi gốc và retry riêng; không tựretry/resume/top-up/probe. Source/demo tách khỏi benchmark trong `REPORT.md`.

**Yêu cầu “retry chạy tiếp” đã thực hiện theo [protocol](benchmark/PROTOCOL_RETRY45_R2.md)** và dừng theo stop policy. Lượt mới sau lỗi cần quyết định riêng; không đổi rubric/guard hoặc kết quả cũ.

**Yêu cầu “chạy tiếp” đã thực hiện theo [protocol continuation43](benchmark/PROTOCOL_CONTINUE43_R2.md)** và dừng theo policy; giữguard tổng16USD/rubricr2. Lượt mới cần quyết định riêng.

[So sánh source sáu trục](REPORT.md) đã có bản first-pass theo commit, gồm permission/sandbox, context/session, extension, background/loader v1-v2 và recovery consumer v2;124 evidence IDs đã kiểm cấu trúc. [Chuẩn bị demo offline](demos/OFFLINE_DEMO_PLAN.md) có acceptance matrix và fixture/tests cục bộ. Demo native security/resume/plugin port và subagent/background vẫn chưa nghiệm thu, không nâng source-only hoặc fixture tests thành runtime support.

## Nhật ký các mốc trước — không phải trạng thái hiện tại

**Batch Benchmark48 đầu đã dừng sau1/48slot**: R-0039/v1/B-01 infra_error/pending_review, request5TimeoutError trước HTTP/usage;47slot chưa chạy tại mốc đó. Known estimate0.06853344USD,1unpriced/totalunknown. [Kết quả và review rubric](benchmark/suite48/BENCHMARK_RESULTS.md). Các dòng “chưa launch” bên dưới giữ lịch sử chuẩn bị.

**Đã tổng kết pilot và khóa baseline offline** `search-r2 + paced-900`: [baseline/manifest/validator](benchmark/BASELINE.md), [mọi attempt và cohort P-02](benchmark/artifacts/PILOT-FREEZE-20261109-01/SUMMARY.md). Benchmark chính thức vẫn pending, không inference mới.

**Hướng48slot:** đã có [protocol/task/order/dự toán draft](benchmark/PROTOCOL_48_DRAFT.md), [fixture/grader44checks](benchmark/suite48/IMPLEMENTATION.md) và [native preflight16/16cặp task×CLI](benchmark/suite48/NATIVE_PREFLIGHT.md) với response giả cục bộ. Còn final protocol/budget/paid orchestration và duyệt launch; chưa gọi provider hoặc chạy benchmark trả phí.

**Cập nhật bộ điều phối:** [batch runner/launch candidate03](benchmark/suite48/BATCH_RUNNER.md) đã qua offline16/16case. Đã ghi nhận đồng ý guard16USD estimate/outer-wall để hoàn thiện runner; approval launch vẫn tắt, chưa gọi provider hoặc reserve paid IDs.

</details>

## Đề bài

1. So sánh OpenCode với Pi và Codex CLI theo: kiến trúc, vòng lặp agent, hệ thống tool, permission, quản lý context và khả năng mở rộng. Mọi nhận định kỹ thuật phải dẫn tới source code cụ thể.
2. So sánh OpenCode v1 với v2:
   - Cài song song bản 1.x cuối và bản 2.x mới nhất tại ngày chốt.
   - Kiểm chứng background service dùng chung cho TUI, desktop và web.
   - Viết script tạo session, gửi prompt và nhận event qua API/SDK mới.
   - So sánh permission object v1 với ordered rules allow/ask/deny v2.
   - Kiểm chứng subagent và shell chạy nền.
   - Port một plugin v1 sang v2.
   - Chạy cùng bộ task, đo tỉ lệ hoàn thành, token và thời gian.

Các phát biểu trong đề là nội dung cần kiểm chứng, không mặc định là kết luận.

## Bắt đầu ở đây

1. Đọc [PLAN.md](PLAN.md) và làm lần lượt các giai đoạn.
2. Xác minh rồi chốt phiên bản trong [research/versions.md](research/versions.md).
3. Ghi nhận định và bằng chứng vào [research/evidence.csv](research/evidence.csv).
4. Xem [pilot và mọiattempt](benchmark/PILOT_RESULTS.md), sau đó [protocol benchmark OpenAI đã chạy](benchmark/PROTOCOL_OPENAI48_R3.md); không lấy draft/planning làm trạng thái mới nhất.
5. Viết kết quả vào [REPORT.md](REPORT.md), chỉ dùng số liệu thực sự thu được.

## Source hiện có

Các đường dẫn tương đối tính từ workspace này:

| Tool | Source |
| --- | --- |
| OpenCode v1 | `../opencode-v1` |
| OpenCode v2 | `../opencode-v2` |
| Pi | `../pi` |
| Codex CLI | `../codex` |

Không cần clone thêm repo tool. Có thể cần project mẫu/fixture riêng để benchmark.

## Cấu trúc

- `PLAN.md`: kế hoạch và checklist nghiệm thu.
- `research/`: phiên bản, bản đồ source và bằng chứng.
- [research/isolation.md](research/isolation.md): phương án cách chạy/cách ly theo source và giới hạn kiểm chứng runtime.
- `demos/`: hướng dẫn chuẩn bị demo API, permission, background và plugin.
- [demos/SMOKE_TEST.md](demos/SMOKE_TEST.md): checklist chuẩn bị lịch sử; trạng thái smoke thật và benchmark cuối ở [kết quả OpenAI48](benchmark/suite48/OPENAI_BENCHMARK_FINAL.md).
- [demos/OFFLINE_API.md](demos/OFFLINE_API.md): kết quả HTTP auth/events/session metadata v1/v2 và giới hạn so với Client/SDK.
- [demos/PROVIDER_PROBE.md](demos/PROVIDER_PROBE.md): kiểm tra gateway/model bằng request tối thiểu, usage và giới hạn ngân sách chưa xác minh.
- `benchmark/`: protocol, task manifest, mẫu kết quả và nơi lưu log.
- `REPORT.md`: báo cáo tổng hợp với trạng thái runtime cuối cùng và các nhánh còn unverified.
- `AGENTS.md`: hướng dẫn cho coding agent làm việc tại workspace này.

Model cohort hoàn chỉnh **`gpt-6.1-sol` trên OpenAI trực tiếp**; dữ liệu model cũ đã xóa theo yêu cầu không phục hồi. [Pilot Shopaikey lịch sử](benchmark/PILOT_RESULTS.md) và [benchmark Shopaikey chưa đủ](benchmark/suite48/BENCHMARK_RESULTS.md) giữ riêng, không gộp với 48 OpenAI. Guard estimate không phải charge; raw failure/retry/unknown usage giữ nguyên. Phạm vi file công bố và khôi phục raw gzip ở [PUBLISHING.md](PUBLISHING.md).

Để chuyển sang làm việc:

```sh
cd /home/tts/Project/agent-cli-report
```
