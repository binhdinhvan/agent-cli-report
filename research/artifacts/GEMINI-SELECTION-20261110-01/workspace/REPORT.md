# So sánh OpenCode, Pi và Codex CLI; OpenCode v1 và v2

> **Model được chọn cho bước tiếp theo: `gemini-3.8-flash`.** [Migration đang chuẩn bị](research/GEMINI_MIGRATION.md), chưa gọi API/kiểm runtime, chưa có giá Gemini. Các số liệu benchmark phía dưới vẫn hoàn toàn thuộc sol; không trộn model hoặc kết luận outage sol chỉ từ timeout.

> Bản nháp. Benchmark có 8 attempts qua 4 batch, gồm 1 retry; 7/48 slot unique đã thử, 41 chưa chạy. Hiện dừng vì infra_error; chưa đủ dữ liệu để xếp hạng. Giá user-reported, kết quả model cũ đã xóa/rút.

> **Hiện tại:** continuation43 dừng sau 2 slot: R179/Pi-B02 success, R180/v2-B02 timeout trước HTTP/usage, chưa sửa file. Còn 41 slot chưa chạy. Tổng known0.28485816USD/4unpriced/totalchargeunknown. Giữ các lỗi gốc và supplementary retry riêng; không tự retry/resume, nguyên nhân timeout chưa xác minh.

> [Protocol continuation43](benchmark/PROTOCOL_CONTINUE43_R2.md), [kết quả](benchmark/suite48/BENCHMARK_RESULTS.md), [audit](research/artifacts/CONTINUE43-REVIEW-20261110-01/validation.json). Guard tổng16USD estimate không phải invoice cap; pilot tách riêng.

> Yêu cầu “chạy tiếp” đã thực hiện; batch dừng theo stop policy. Lượt inference tiếp theo cần quyết định riêng, không đổi rubric/guard/caps hoặc kết quả cũ.

## 1. Tóm tắt kết quả hiện còn bằng chứng

- **Batch mới nhất:** R179/Pi-B02 success/valid157222ms, chỉsửapagination.py,scope/public/hiddenpass,5HTTP200completed; R180/v2-B02infra_error/pending_review159194ms,request1TimeoutError trướcHTTP/terminal/usage,chưasửafile,khôngwalltimeout. Batchknown0.03299880USD/1unpriced,5gap≥30s. Tổng8attempts gồm1retry trên7/48unique slots; firstattempts2success/1failure/4infra +1supplementaryretrysuccess,41slotchưachạy. [Audit](research/artifacts/CONTINUE43-REVIEW-20261110-01/validation.json).

- **Batch retry trước:** R134/v2-B01 success/valid10/10 (retry_ofR89),224706ms,6HTTP200/completed; R135/Codex-B02infra_error/pending_review,73499ms,1requestTimeoutError trướcHTTP/terminal/usage,khôngwalltimeout/chưasửafile. Batchknown0.03844560USD/1unpriced,6gap≥30s. Tại mốc đó tổng6attempts gồm1retry trên5unique48slot;43slotchưachạy. Không nângR89gốc thànhsuccess hoặc xếphạng từ mẫu này. [Audit](research/artifacts/RETRY45-REVIEW-20261110-01/validation.json).

- **Batch continuation trước:** R87Codex/B01success10/10; R88Pi/B01failuretheor2 9/10 do extra evidence mutation bịallowlistloại, cả5giátrịđúng; R89v2/B01infra_error/pending_review với1requestTimeoutError trướcHTTP/terminal/usage. Khi đợt đó dừng:3/47executed,44not_run;9gap≥30s,0walltimeout; batchknown0.14488032USD/1unpriced. Tổng tại mốc đó kểR39:4/48slot,1success/1failure/2infra,known0.21341376USD/2unpriced/chargeunknown. R1/R2khácrubric,khônggộpđểxếphạng. [Kết quả/giới hạn](benchmark/suite48/BENCHMARK_RESULTS.md), [audit](research/artifacts/CONTINUE47-REVIEW-20261110-01/validation.json).

- **Pilot đã tổng kết offline:** 14 inference attempts / 76 upstream requests; reviewed **8 success, 3 timeout, 3 infra_error**, thêm một launch-error không inference. Tám cặp task/CLI đều có success qua retry/revision khác nhau, **không phải8/8 first-attempt hoặc benchmark đồng nhất**. [Mọi attempt](benchmark/artifacts/PILOT-FREEZE-20261109-01/SUMMARY.md), [lịch sử đầy đủ](benchmark/PILOT_RESULTS.md).
- **P-02 R-0035–R-0038:** v2→v1→Codex→Pi, cùng `search-r2/paced-900`, cả bốn success/valid, scope/public/hidden pass. n=1/CLI, không randomized, native prompts/tools/reasoning khác; không xếp hạng hoặc suy causal. Duration đều dưới300s dù cap900, không quy success chỉ cho tăng cap. [Cohort/raw references](benchmark/artifacts/PILOT-FREEZE-20261109-01/summary.json).
- **Known estimate pilot1.10640264 USD**, sáu request unpriced nên total/measured charge null. Giá user-reported4.8/0.24/18 USD mỗi triệu input/cache/output token, chưa đối soát hóa đơn; không nhập smoke/diagnostic vào pilot. [Manifest/pricing](benchmark/artifacts/PILOT-FREEZE-20261109-01/baseline.json).
- **Baseline đã khóa offline:** `search-r2 + paced-900`, pins/config/fixture/seal/dependency/policy/source hashes và validator tại [BASELINE.md](benchmark/BASELINE.md). Benchmark đã chạy8attempts trên7slot qua4batch rồi dừng; hiện không được tự resume. Giữ raw/CSV, review override R-0009; snapshot pass nhưng CLI timeout vẫn là timeout.
- HTTP API offline v1/v2 đã có auth/SSE/session metadata qua restart; không suy resume hội thoại, GUI/shared-service hoặc Client/SDK runtime. [API offline](demos/OFFLINE_API.md).

<details>
<summary>Ghi nhận lịch sử theo từng thời điểm — không phải trạng thái hiện tại</summary>

- Metadata/version/checksum bốn binary vẫn giữ; không phải kết quả giải task.
- HTTP API offline v1/v2: auth/SSE/session metadata qua restart đã có artifact; chưa suy resume hội thoại/GUI/shared-service.
- **Sol diagnostic Pi/P-01:** 6 HTTP 200/completed, task/public/hidden đạt, chỉ fixture tạm thay đổi. Một lượt không chứng minh ổn định tổng quát hoặc ưu thế model/tool. [`benchmark/MODEL_COMPARE.md`](benchmark/MODEL_COMPARE.md).
- Smoke sol OpenCode v1/v2/Codex: **3/3 đạt chức năng**, 8/8 HTTP 200/completed, estimate **0.09173616 USD**. **Không đạt pacing toàn đợt** do hai gap chuyển CLI dưới 30 giây; lỗi harness cần sửa trước nhóm mới. [`demos/MODEL_SMOKE_SOL_RESULTS.md`](demos/MODEL_SMOKE_SOL_RESULTS.md). Chưa có pilot sol đủ 8 lượt.
- Giá input/cache/output user-reported 4.8/0.24/18 USD mỗi triệu token cho estimate **0.21496416 USD** của diagnostic Pi đã giữ; measured charge null. Ledger riêng [`benchmark/SOL_COST.md`](benchmark/SOL_COST.md), không sửa raw artifact.
- Pilot sol đã chạy và **dừng sau 1/8 lượt**: request2 HTTP 200 nhưng response.failed/provider overload, thiếu usage; bảy slot chưa chạy. Review R-0009 là infra_error/pending_review (raw classifier gán nhầm failure/valid), chưa sửa source; không kết luận Pi giải sai. Known subtotal 0.0280872 USD, tổng/charge unknown. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- Sau bản sửa offline, **single retry R-0017/Pi/P-01 đạt**, scope/public/hidden pass, 7/7 HTTP200/completed, sáu gap≥30 giây; estimate lượt0.07692480 USD, cumulative known pilot0.10501200 USD (total/charge unknown). Không mở bảy slot khác hoặc suy provider ổn định lâu dài. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- Continuation sau đó dừng **2/7**: Codex/P-01 đạt, v2/P-01 timeout300s gồm pacing, request cuối thiếu terminal/usage; năm slot chưa chạy. Pacing xuyên CLI30.003446s đạt, không overload message xác định; có môi trường glob/ripgrep lỗi nên chưa quy timeout cho chất lượng giải task. Cumulative known estimate **0.40389912 USD**, total/charge unknown (hai request unpriced). [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- Audit offline native tools xác nhận sandbox thiếu rg gây glob failure ở **cả v1/v2**, Pi shell không có rg, trong khi Codex có bản bundled. Đối chứng mount read-only rg có sẵn sửa được glob trong sandbox test; chưa áp dụng cho pilot hoặc suy toàn bộ timeout do dependency. Cần revision môi trường trước khi so sánh tiếp. [`research/SEARCH_ENVIRONMENT.md`](research/SEARCH_ENVIRONMENT.md).
- **search-r2 đã chuẩn hóa và đạt preflight offline**: cùng bytes/version rg15.2.0 cho cả bốn CLI, native search và writable/isolation pass, 37 tests đạt; chưa inference mới. Runner tag revision và chặn silent legacy→r2 continuation; không gộp kết quả cũ/mới như cùng điều kiện. [`research/ENVIRONMENT_R2_RESULTS.md`](research/ENVIRONMENT_R2_RESULTS.md).
- Inference recheck search-r2 sau đó **R-0025 infra_error/pending_review**: request đầu timeout trước HTTP status/usage, chưa tới task; 11 lần gọi tiếp bị chặn local, chỉ1 upstream. Không có bằng chứng upstream503/overload từ local503. Cumulative known0.40389912 USD, total/charge unknown với ba requestunpriced; r2 CSV riêng, không kết luận môi trường native đã sửa vẫn lỗi. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- Single retry search-r2 **R-0026 lặp timeout trước task**, chỉ1 upstream/11 localblocked; chưa xác định gateway/provider/network root cause. Cumulative known vẫn0.40389912 USD, total/charge unknown với **bốn** requestunpriced. Chưa mở năm slot hoặc chứng minh task support sau chuẩn hóa. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- Sau lần launch R-0027 lỗi trước inference (0upstream), khôi phục **R-0028 v2/P-01/search-r2 đạt**, scope/public/hidden pass, 7/7 completed/gap≥30s. Estimate lượt0.06716400 USD, cumulative known0.47106312 USD; total/charge vẫn unknown vì bốn request cũunpriced. Giữ cả failure lineage và tách r2/legacy, chưa đủ pilot đồng nhất môi trường hoặc chứng minh nguyên nhân timeout cũ. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- Finish search-r2 dừng **2/5**: **v1/P-01 đạt**; v2/P-02 **snapshot scope/public/hidden pass nhưng CLI timeout300s**, request cuối bắt đầu giây299.39 thiếu terminal/usage. Ba slot P02/v1,Codex,Pi chưa chạy. Pacing13gap≥30s; cumulative known **0.61870440 USD**, total/charge unknown với nămrequestunpriced. Không nâng snapshot pass thành CLI success hoặc suy provider overload. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- Retry **R-0034 v2/P-02 tiếp tục timeout300s, snapshot pass**, nativeglob completed trong call model thật; request cuối ở giây295.65 thiếu terminal/usage. Pacing≥180s trong cap300s. Known estimate mới0.07098192 USD, cumulative0.68968632 USD, total/charge unknown với sáu requestunpriced. Không nâng thành success/ẩn timeout hoặc chọn lọc retry; ba slot khác chưa chạy. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- **Timing revision paced-900 đã đạt offline**, áp chung cả bốn CLI: wall900s, reserve60s saupacing/no upstream khi sắp hết giờ, request/output/concurrency/USD guard không tăng. 48tests và config/isolation4/4 pass; chưa inference mới. Không gộp cap300/cap900 như cùng điều kiện hoặc bảo đảm provider/task success. [`research/PACED_900_RESULTS.md`](research/PACED_900_RESULTS.md).
- Sau đó **R-0035 v2/P-02 paced-900 acceptance đạt**, scope/public/hidden pass,7/7completed/gap≥30s,234718ms gồm pacing. Vì hoàn tất dưới300s, không quy thành công chỉ cho tăngcap; không nâng timeout cũ. Estimate0.07580592 USD,cumulativeknown0.76549224,totalchargeunknown(sáuunpriced). Ba slotP02khác chưa chạy, chưa có pilot đồng nhất8slot. [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).
- **Ba slot P-02 còn lại R-0036/v1, R-0037/Codex, R-0038/Pi đều đạt**, scope/public/hidden pass,20/20completed,19gap≥30s. Như vậy đủ tám cặp task/CLI có ít nhất một success, **không phải8/8first-attempt hoặc cùng environment/timing**; toànpilot14attempts/76upstream, giữmọifailure. P-02 cả4 cùngsearch-r2/paced900 nhưng nativeprompt/tools/reasoning khác. Cumulative known **1.10640264 USD**, totalchargeunknown(sáuunpriced). [`benchmark/PILOT_RESULTS.md`](benchmark/PILOT_RESULTS.md).

</details>

Theo yêu cầu, đã xóa artifact/log/result model cũ và các runtime thử liên quan; không còn dùng các số đo đó. Source/permalinks vẫn giữ, runtime evidence phụ thuộc dữ liệu đã rút được hạ về source-only. [`research/SOL_MIGRATION.md`](research/SOL_MIGRATION.md).

## 2. Phạm vi và phương pháp

- Phiên bản/full SHA: `research/versions.md`; không thay binary/source checkout hoặc service thật.
- OpenCode v2 đại diện OpenCode trong so sánh ba tool; bốn cấu hình thực nghiệm gồm cả v1.
- Provider/model hiện tại: `https://api.shopaikey.com/v1`, alias `gpt-6.1-sol`; backend revision/model gốc chưa xác minh.
- Giá user-reported, chưa đối soát hóa đơn; không áp giá model khác. Tách source-confirmed/runtime-confirmed/both/unverified, diagnostic/pilot/benchmark.

Nguồn metadata và API offline: [`demos/PREPARATION.md`](demos/PREPARATION.md), [`demos/OFFLINE_API.md`](demos/OFFLINE_API.md). Các source claim ở `research/evidence.csv`; không nâng thành runtime support của sol khi chưa thử.

**Chuẩn bị offline bổ sung:** recovery consumer source v2 đã truy tiếp ở4.4; [acceptance matrix](demos/OFFLINE_DEMO_PLAN.md) có fixture/tests success/error/cancel do nghiên cứu viết. Những unit tests này không phải native background/plugin/security demo. Client/SDK prompt, permission matrix, port plugin, GUI/shared-service và resume/compaction runtime vẫn chưa nghiệm thu.

## 3. So sánh ba tool

Các mục3.1–3.6 dưới đây là **đối chiếu source tại release đã pin**, không phải đánh giá tốc độ/chất lượng model hoặc proof mọi mode của sản phẩm. Pi/Codex đọc bằng `git show <release-SHA>:<file>`, không dùng HEAD development thay release. Mỗi mục chỉ kết luận trong nhánh code được dẫn; runtime security, resume/compaction quality và plugin compatibility còn cần demo riêng.

### 3.1. Kiến trúc

| Tool | Đường thực thi đã truy vết | Hệ quả khi sử dụng và giới hạn |
| --- | --- | --- |
| **OpenCode v2** | `ServerConnection.resolve` ưu tiên explicit server, sau đó standalone/disabled-service, cuối cùng managed service. `Standalone.start` spawn private `serve --stdio --port 0`; embedded SDK còn có đường `EmbeddedHost` + `host.fetch`. [E-0014](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/cli/src/services/server-connection.ts#L23-L58), [E-0015](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/cli/src/services/standalone.ts#L17-L58), [E-0053](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/sdk/src/promise.ts#L34-L68). | Phải chỉ rõ đang dùng managed service, private child hay embedded host; không gộp chúng thành một lifecycle. Standalone không tự cách ly config/data. Chưa chứng minh TUI/desktop/web cùng một service trong thực nghiệm này. |
| **Pi** | Trong `createAgentSession`, SDK dựng `Agent` với transcript hiện có và stream qua `modelRuntime`, rồi ghép `AgentSession` với session/settings/resource managers. [E-0077](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/sdk.ts#L403-L468). | Phân biệt lớp vòng lặp `Agent` với lớp coding-session quản lý môi trường/phiên. Đây là đường ghép SDK được đọc, không kết luận Pi không có server/mode khác hoặc đã nghiệm thu SDK runtime. |
| **Codex CLI** | Nhánh `exec` kiểm Git trust rồi khởi tạo `InProcessAppServerClient`. [E-0028](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/exec/src/lib.rs#L1018-L1033). | `exec` cũng có lớp app-server client; không nên mô tả là chỉ gọi model trực tiếp hoặc mặc nhiên bắt buộc remote server. Kết luận giới hạn ở nhánh `exec`, không phủ mọi TUI/daemon mode. |

**So sánh thực dụng:** xác định ranh giới client/server/session trước khi chọn cách tích hợp hay đo startup. Các đường trên khác cách ghép thành phần; source chưa cho phép kết luận tool nào nhanh/nhẹ/ổn định hơn.

### 3.2. Vòng lặp agent

| Tool | Quyết định tiếp tục ở đâu? | Bằng chứng |
| --- | --- | --- |
| **OpenCode v2** | `drain` lấy step sẵn sàng rồi gọi `runStep`; `runStep` kiểm compaction, chuẩn bị primary model request, gọi `steps.attempt`. Outcome `Completed` còn có `needsContinuation`, còn `Retry` đi qua retry policy/wait. | [E-0080: drain](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/runner/llm.ts#L209-L218), [E-0081: runStep](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/runner/llm.ts#L230-L326). |
| **Pi** | `runLoop` stream assistant, thực thi tool calls và đưa tool results vào context. Error/aborted kết thúc nhánh; steering/follow-up và explicit continuation có thể giữ vòng lặp hoạt động sau một response. | [E-0078: runLoop](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/agent/src/agent-loop.ts#L250-L329). |
| **Codex CLI** | `run_turn` nhận kết quả sampling rồi hợp `model_needs_follow_up` với pending input. Nhánh còn in-flight tool futures chờ `drain_in_flight` trước token-count event tương ứng. | [E-0083: run_turn](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/session/turn.rs#L594-L650), [E-0086: drain tools](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/session/turn.rs#L3560-L3578). |

**Hệ quả cho automation:** “provider đã hoàn tất một response”, “tool đã xong”, “agent/CLI đã kết thúc” và “acceptance đã đạt” là các mốc khác nhau. Vì vậy benchmark lưu terminal provider, CLI exit và supervisor grading riêng; không nâng snapshot pass thành success khi CLI chưa hoàn tất. Chưa có đối chứng runtime riêng cho mọi nhánh steering/compaction/retry, không dùng source flow để khẳng định retry tốt hơn hoặc tiết kiệm token hơn.

### 3.3. Hệ thống tool

| Tool | Cách tổ chức đã xác minh từ code | Hệ quả và giới hạn |
| --- | --- | --- |
| **OpenCode v2** | `definition` dựng model tool definition từ schema; `execute` đi qua input decode, tool implementation, output encode/normalize và chuẩn hóa foreign typed failure về `Tool.Error`. [E-0082](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/tool/runtime.ts#L21-L61). | Có ranh giới hợp đồng tool/implementation; cần đọc phần validation cụ thể trước khi kết luận mọi loại JSON Schema đều được enforce. Đây không phải permission engine hoặc bằng chứng OS sandbox. |
| **Pi** | `createCodingTools` tạo `read/bash/edit/write`; `createReadOnlyTools` tạo `read/grep/find/ls`; `createAllTools` là factory tập khác. [E-0079](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/tools/index.ts#L195-L223). | Không đồng nhất tập factory với inventory hiệu lực của mọi session: CLI còn parse tool allowlist. [E-0068](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/cli/args.ts#L151-L175). Tên “read-only” của factory không tự giới hạn filesystem ở mức OS. |
| **Codex CLI** | `ToolRouter` tạo `ToolInvocation` mang session/step/cancellation rồi dispatch qua registry; `tool_supports_parallel` đọc capability từng tool và mặc định false nếu thiếu. [E-0084](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/tools/router.rs#L390-L427), [E-0085](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/tools/router.rs#L260-L264). | Capability song song là có điều kiện, không phải mọi tool luôn parallel; không thay concurrency1 của thí nghiệm. Cần đọc handler/policy để đánh giá quyền và sandbox, không suy từ router. |

**Không so tool bằng số phần tử `tools` top-level đơn thuần:** nhánh Codex Responses Lite có thể đưa `additional_tools` vào `input` và đặt header tương ứng. [E-0060](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/client.rs#L1051-L1085), [E-0062](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/client.rs#L1580-L1608). Tool definitions, runtime dispatch và OS permissions phải được ghi riêng; chưa có bảng hiệu năng tool-call đồng nhất để xếp hạng.

### 3.4. Permission và sandbox

Ba lớp cần phân biệt: **cho phép gọi tool**, **hỏi/phê duyệt hành động**, và **hạn chế tài nguyên ở mức OS**. Không dùng tool allowlist, config home hoặc HTTP authentication thay cho OS sandbox.

| Tool | Đường kiểm quyền đã truy vết | Điều chưa được chứng minh |
| --- | --- | --- |
| **OpenCode v2** | Shell prepare resolve cwd/directories, `authorizeExternal`, rồi `permission.assert` trên parsed commands. Evaluator chọn rule khớp cuối; enforcement còn kiểm configured deny trước saved allows và đi qua hook/unattended policy. [E-0089](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/tool/plugin/shell.ts#L114-L149), [E-0087](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/permission.ts#L86-L100), [E-0088](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/permission.ts#L151-L201). | Có application-level policy không đồng nghĩa parser chặn mọi shell side effect hoặc tự cung cấp kernel sandbox. Chưa demo ask-approve/ask-reject/deny và hiệu lực saved approval. |
| **Pi** | Local shell operations mặc định gọi `spawn` với cwd/env và timeout/abort cleanup. Tool preparation có `beforeToolCall`; nếu callback trả `block`, tạo immediate error thay vì prepared call. [E-0090](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/tools/bash.ts#L95-L140), [E-0092](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/agent/src/agent-loop.ts#L719-L778). | Đây là local helper/hook path, không đủ kết luận Pi không có custom isolation hoặc mọi mode đều có approval mặc định. Hook chặn tool không phải OS-level filesystem/network confinement. |
| **Codex CLI** | Protocol tách `AskForApproval` khỏi `SandboxType`; approval có `Never`, backend type inventory có None/LinuxSeccomp/MacosSeatbelt/WindowsRestrictedToken/WindowsMxc. [E-0093](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/protocol/src/protocol.rs#L1146-L1169), [E-0094](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/protocol/src/sandbox.rs#L27-L45). | `Never` nghĩa là không hỏi, không có nghĩa tắt sandbox. Enum không chứng minh backend nào thật sự active, mức deny nào được enforce hay tương đương trên các OS. |

**Pi extension có đường can thiệp trước tool thật, không chỉ declaration:** `AgentSession` cài callback vào Agent ([E-0107](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/agent-session.ts#L668-L696)); `createLoopConfig` chuyển callback cho vòng lặp ([E-0108](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/agent/src/agent.ts#L476-L494)); extension emitter trả ngay khi handler báo block ([E-0091](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/extensions/runner.ts#L1249-L1267)). Đây vẫn là source wiring, chưa chạy extension demo.

**Hệ quả:** phải chọn approval policy và isolation policy riêng. Bwrap/read-only mounts của [harness thí nghiệm](benchmark/BASELINE.md) là lớp ngoài do nghiên cứu đặt, không được dùng làm bằng chứng ba tool có native sandbox tương đương. Chưa đủ dữ liệu để xếp hạng bảo mật hoặc kết luận một tool “an toàn nhất”.

### 3.5. Context và session

Phân biệt **history đã giữ**, **projection đưa vào model**, **checkpoint/summary**, và **execution đang chạy**. Chúng không đồng nghĩa chỉ vì cùng mang tên session/context.

| Tool | Cơ chế source đã xác minh | Hệ quả và giới hạn |
| --- | --- | --- |
| **OpenCode v2** | History phân biệt native compaction window và các boundary `latest`/`local`/model ref. Helper `replayable` kiểm providerID/model id và khả năng decode khi dùng model boundary; local boundary không replay native window. [E-0095](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/history.ts#L32-L53). | Projection phụ thuộc boundary/model, không suy summary/window dùng được lossless qua mọi model. Chưa runtime-test native compaction hoặc chất lượng context sau nén. |
| **Pi** | `buildContextEntries` theo active leaf path, chọn latest compaction và giữ range từ `firstKeptEntryId` cùng các entry sau compaction. `branch` chỉ xác minh entry và chuyển leaf pointer trong hàm đó. [E-0096](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/session-manager.ts#L476-L511), [E-0097](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/session-manager.ts#L1584-L1595). | Branch selection và model context là projection của history, không phải xóa mọi entry cũ. Chưa demo branch/resume CLI hoặc bảo đảm tiếp tục tool execution đang chạy. |
| **Codex CLI** | `ContextManager` giữ model items và retained context riêng; `conversation_history_snapshot` ghép shared items/review history/retained context/reviewer mode/revisions. [E-0098](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/context_manager/history.rs#L249-L279). | In-memory snapshot không tự chứng minh disk persistence, crash recovery hoặc khôi phục process/tool. Chưa đo chất lượng giữ ngữ cảnh hoặc token saving so với tool khác. |

Do đó chưa thể kết luận tool nào “nhớ tốt hơn” từ data model. Evidence session metadata qua restart ở4.2 vẫn chỉ là ID/title của session rỗng; hội thoại resume, model switch và compaction cần acceptance riêng. Không dùng số token/cache của một lượt để thay phép thử chất lượng context.

### 3.6. Khả năng mở rộng

| Tool | Bề mặt mở rộng tại pin | Giới hạn khi chọn/cải biến tích hợp |
| --- | --- | --- |
| **OpenCode v2** | Promise plugin có `id/setup(context)` và Cleanup; context cung cấp các domain. Tool domain có transform/reload/list/hook, editor add/update/remove. [E-0099](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/plugin/src/promise/plugin.ts#L27-L67), [E-0100](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/plugin/src/promise/tool.ts#L26-L72). | Contract có lifecycle và tool-editing surface; chưa nghiệm thu hook ordering/reload/disposal hoặc port module thực tế. |
| **Pi** | Extension API có `tool_call/tool_result/user_bash` handlers và `registerTool/registerCommand`. [E-0101](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/core/extensions/types.ts#L1685-L1705). | Có thể thiết kế tích hợp theo event/registration contract này; chưa chạy extension để chứng minh behavior hoặc isolation. Không mặc nhiên coi API giống OpenCode plugin. |
| **Codex CLI** | `RawPluginManifest` có fields skills/mcp_servers/apps/hooks/interface/extensions. [E-0102](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core-plugins/src/manifest.rs#L48-L73). | Đây là schema của manifest được đọc; không đủ suy mọi field được kích hoạt, không tương đương một JavaScript plugin function và không kết luận không có extension mechanism khác. |

**Khuyến nghị ở mức source:** chọn theo bề mặt cần mở rộng (tool/event/lifecycle hay manifest/skills/MCP), rồi kiểm loader/config/trust và runtime riêng. Tên “plugin” chung không phải compatibility contract giữa sản phẩm. Chưa cài/bật plugin, chưa port và chưa có kết quả demo; không gọi các mục đó là unsupported chỉ vì chưa thử.

## 4. OpenCode v1 so với v2

### 4.1. Kiến trúc và background service

- **v1 không mặc định đồng nghĩa “không có server”:** nhánh `run` không attach tạo SDK custom fetch gọi `Server.Default().app.fetch` trong process; đồng thời có `ServeCommand` mở listener và giữ process. [E-0008](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/cli/cmd/run.ts#L933-L951), [E-0044](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/cli/cmd/serve.ts#L6-L24).
- **v2 tách đường kết nối rõ:** explicit server, private standalone child và managed-service resolution là các nhánh riêng; embedded SDK còn có host riêng. [ServerConnection.resolve/E-0014](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/cli/src/services/server-connection.ts#L23-L58), [Standalone.start/E-0015](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/cli/src/services/standalone.ts#L17-L58), [PromiseSdk.create/E-0053](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/sdk/src/promise.ts#L34-L68).

Do đó mô tả khác biệt chính xác hơn là **cách resolve/host server và quản lý lifecycle**, không phải “v1 không server/v2 luôn daemon”. Source chỉ ra managed-service path; demo TUI/desktop/web thật cùng service, restart/recovery và resume execution vẫn **unverified**, chưa được phép tác động service thật để thử.

### 4.2. API/Client/SDK và demo

| Mặt tích hợp | Bằng chứng | Trạng thái và giới hạn |
| --- | --- | --- |
| HTTP create session v1/v2 | v1 `POST /session` trả trực tiếp `Session.Info`; v2 `POST /api/session` nhận `location` và trả envelope `data`. [E-0042 v1](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/server/routes/instance/httpapi/groups/session.ts#L203-L207), [E-0041 v2](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/protocol/src/groups/session.ts#L165-L185). | **both** cho nhánh create session rỗng của demo; không coi đổi prefix là đủ để migrate toàn API. |
| HTTP auth/events | [Event v1/E-0046](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/server/routes/instance/httpapi/handlers/event.ts#L25-L84), [event v2/E-0045](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/server/src/handlers/event.ts#L11-L33), [auth v1/E-0048](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/server/auth.ts#L17-L33), [auth v2/E-0047](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/server/src/middleware/authorization.ts#L20-L101) và [demo/log offline](demos/OFFLINE_API.md): đã kiểm auth, subscribe trước create và nhận event/session ID tương ứng. | Runtime giới hạn ở thao tác metadata, không phải streaming model completion, replay/reconnect hay permission allow/deny của tool. |
| Session qua restart | [E-0050 v1](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/session/session.ts#L667-L688), [E-0051 v2](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session.ts#L288-L338), runtime artifact trong evidence index. | **runtime-confirmed** cho giữ ID/title của session rỗng; không chứng minh restore transcript hoặc tiếp tục LLM/tool execution sau crash. |
| TypeScript Client v2 | Package exports tách Promise/Effect client và service entrypoints; `Service.discover` khác `ensure` có nhánh spawn. [E-0052](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/client/package.json#L18-L27), [E-0054](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/client/src/promise/service.ts#L18-L48). | **source-confirmed**, chưa cài/chạy TypeScript Client; HTTP Python demo không thay được nghiệm thu client library hoặc service lifecycle. |
| Embedded SDK v2 | `PromiseSdk.create` ghép `EmbeddedHost` với client dùng `host.fetch`, có aliases sessions/events và close/disposal. [E-0053](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/sdk/src/promise.ts#L34-L68). | **source-confirmed**, chưa runtime; không đánh đồng SDK embedded với network Client hoặc shared service. |

Mục4.2 còn thiếu end-to-end Client/SDK gửi prompt, terminal/error/cancel/usage và hội thoại resume. Các bằng chứng source mới không tự nâng các mục đó thành đạt.

### 4.3. Permission schema, precedence và defaults

| Tầng | OpenCode v1 | OpenCode v2 |
| --- | --- | --- |
| Schema cấu hình đã truy vết | Input permission nhận action hoặc object rule, có các key như read/edit/bash/task. [E-0066](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/core/src/v1/config/permission.ts#L5-L39). | Native `Rule` có action/resource/effect, `Ruleset` là array. [E-0067](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/schema/src/permission.ts#L56-L67). |
| Internal evaluator | Flatten rulesets, match permission/pattern, lấy rule cuối hoặc fallback ask; `ask` xét ruleset cùng approved, rồi deny/allow/pending deferred. [E-0103](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/permission/index.ts#L28-L106). | Match action/resource, lấy rule cuối hoặc fallback ask. `configured` ghép agent permissions trước session permissions, nhưng enforcement còn nhiều bước. [E-0087](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/permission.ts#L86-L100), [E-0088](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/permission.ts#L151-L201). |
| Base agent default, chưa user overlays | Wildcard allow với exceptions ask/deny; Build ghép defaults, built-in overrides rồi user permission. [E-0105](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/agent/agent.ts#L119-L152). | `Agent.Info.default` cũng có wildcard allow và exceptions ask cho env files/allow env.example. [E-0106](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/schema/src/agent.ts#L39-L52). |

**Hai điểm dễ hiểu sai:**

1. “Không rule khớp thì ask” là fallback của evaluator, **không phải** mọi thao tác mặc định đều ask: base defaults/config/agent/session có thể đã có rule khớp. Các defaults source ở bảng cũng không phải effective policy của benchmark đã override.
2. V2 không thể rút gọn toàn policy thành “rule cuối thắng” hoặc “hễ có deny là thắng”: trước hết chọn effective configured rule; nếu một resource bị configured deny thì trả deny **trước** saved allows. Sau đó mới xét saved rules, plugin evaluation và unattended settlement. Một deny cũ đã bị configured rule sau override khác với một configured deny còn hiệu lực.

Những kết luận trên là source-confirmed ở đúng pin, không phải demo permission runtime. Còn thiếu ask-approve/reject/deny, rule overlap trong môi trường thật, persistence/thời hạn saved approval và thử nạp config v1 vào v2. Không kết luận config cũ bất tương thích chỉ từ khác schema native.

### 4.4. Subagent và shell chạy nền

**Cả v1 và v2 đều có đường subagent chạy nền trong source tại pin.** Không mô tả background subagent là tính năng chỉ có ở v2.

| Đường thực thi | OpenCode v1 | OpenCode v2 |
| --- | --- | --- |
| Subagent | `background.start` đăng ký `runTask`; `runInBackground` gọi notify rồi trả trạng thái running/jobId. Foreground chờ completion hoặc promotion; interrupt có đường cancel. [E-0109](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/tool/task.ts#L284-L350). | `subagents.start` nhận recovery descriptor; background gọi `subagents.background` rồi trả child sessionID. Foreground `jobs.block`; interrupt gọi child interrupt và job cancel. [E-0111](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/tool/plugin/subagent.ts#L226-L262). |
| Completion | `notifyBackgroundResult` fork chờ job, inject completed/error; status khác trả void trong helper này. [E-0110](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/tool/task.ts#L256-L264). | Shell background đăng ký `notifyWhenDone` và trả shellID/output file; foreground cũng có nhánh được chuyển nền. Đây là source wiring, chưa kiểm thời điểm/độ tin cậy giao thông báo. [E-0112](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/tool/plugin/shell.ts#L193-L266). |
| Shell native background | Schema legacy shell đã đọc chỉ có `command/timeout/workdir`, không có `background` flag. Không suy mọi plugin/mode hay OS detach đều bị cấm. [E-0113](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/tool/shell/prompt.ts#L15-L26). | Shell có nhánh native background, timeout input mặc định 0 ở nhánh này (còn qua prepare), job kèm recovery descriptor; khác việc tự thêm `&` vào command. [E-0112](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/tool/plugin/shell.ts#L193-L266). |

V2 `pendingBackground` đọc persisted `JobTable`, trong khi `runningBackground` lọc live jobs từ state trong bộ nhớ ([E-0117](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/job.ts#L511-L537)). **Có recovery metadata/row không đồng nghĩa process hoặc model/tool execution sống nguyên trạng qua restart.**

**Recovery consumer đã đọc tiếp, vẫn source-only:**

- Shell job persisted ở trạng thái `running` được chuyển thành notice `cancelled` với nội dung server restarted; `recoverToolJob` gửi synthetic notice `resume: false`, rồi hoàn tất background record. Đây không phải tự chạy lại command hoặc bằng chứng OS process được giữ sống. [E-0118](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/execution/restart.ts#L102-L165).
- Subagent kiểm parent/child còn tồn tại và quan hệ đúng. Job đã kết thúc đi qua completion delivery; child còn running nhưng chưa active có thể được `prepareResume` rồi `execution.resume`, đăng ký lại background job và observer. Đây là resume session execution, **không phải phục hồi instruction pointer hoặc bảo đảm side effect chỉ xảy ra một lần**. [E-0119](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/execution/restart.ts#L167-L219).
- `countResume` tăng durable attempt counter; vượt `maxAttempts` (mặc định10) phát execution failure và release claim, còn trong budget ghi restart notice. Store giữ `time_suspended/resume_attempts` trong `SessionTable`. Không nhầm budget này với provider retry. [E-0120](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/execution/restart.ts#L34-L100), [E-0124](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/store.ts#L207-L263).
- Sweep nhận pending jobs, xử lý tool notices trước subagent rồi resume root sessions còn suspended/chưa active. **Activation tùy hosting:** Node boot gọi installer khi có `lifecycle`; `ServerFetch.make` có đường fork recovery riêng. Vì vậy không mặc định mọi `serve`/standalone/SDK có cùng điều kiện kích hoạt. [E-0121](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/session/execution/restart.ts#L221-L259), [E-0122](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/server/src/process.ts#L98-L113), [E-0123](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/server/src/fetch.ts#L41-L53).

Acceptance matrix và fixture cục bộ đã chuẩn bị tại [OFFLINE_DEMO_PLAN.md](demos/OFFLINE_DEMO_PLAN.md); test fixture không phải test recovery của OpenCode. Không chạy sweep vì có thể phát sinh model request.

**Trạng thái: source-confirmed, runtime demo vẫn pending.** Cần nghiệm thu start/return/progress/cancel, parent tiếp tục làm việc, parent/client disconnect và process restart riêng. Chưa bật/chạy subagent hay shell nền trong đợt đọc source này.

### 4.5. Plugin compatibility và port mẫu

Ở pin v1, `PluginInput` có SDK client/project/directory/worktree/serverUrl/BunShell và `Plugin` là function trả `Promise<Hooks>` ([E-0104](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/plugin/src/index.ts#L56-L79)). Entry contract Promise v2 là object `id/setup(context)` với Cleanup và các domain ([E-0099](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/plugin/src/promise/plugin.ts#L27-L67)). **Bề mặt contract khác nhau không tự chứng minh loader có/không có adapter tương thích cho một module cụ thể.**

**Đã truy tới loader, không chỉ so interface:**

- **V1:** `applyPlugin` thử `readV1Plugin` rồi gọi `.server(input, options)`; fallback deduplicate các export, nhận function hoặc object có `.server` function. Vì vậy mô tả loader v1 “chỉ nhận default function” là không đúng với đường đã đọc. [E-0114](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/plugin/index.ts#L88-L124).
- **V2:** đường config server module decode schema `default` object có `id` và function `effect` hoặc `setup`; lỗi decode báo yêu cầu definition đó. Nếu là `setup`, `loadServer` dùng `PluginPromise.fromPromise`. **Default function v1 nguyên dạng không thỏa schema ở đường nạp này**; không mở rộng kết luận sang mọi integration path. [E-0115](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/plugin/module.ts#L75-L187).
- Adapter Promise v2 gọi `setup(context2)` qua `acquireRelease` và cleanup nếu có; đây là bridge lifecycle Promise/Effect của contract v2, không phải tự chuyển `Promise<Hooks>` v1. [E-0116](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/plugin/src/promise/adapter.ts#L660-L672).

Port demo vẫn pending: cần map custom tool/hook và cleanup, rồi nạp plugin tối giản trong hai môi trường riêng, giữ cả lỗi và diff. **Chưa có runtime compatibility matrix hoặc port thành công.** Chưa tạo/cài/bật plugin hoặc đụng config/service người dùng. Đợt này chỉ dùng source local đã pin; không fetch tài liệu web do đang giữ yêu cầu không probe mạng.

### 4.6. Thay đổi khác có bằng chứng

Các khác biệt đã có căn cứ trong phạm vi này là hosting/API envelope ở4.1–4.2, native permission contract/enforcement ở4.3 và plugin contract surface ở4.5. Không xem chúng là changelog đầy đủ giữa hai release hoặc bằng chứng runtime cho mọi tính năng mới.

## 5. Thiết kế thực nghiệm

Fixture P-01/P-02 v2 và [baseline pilot](benchmark/BASELINE.md) được giữ nguyên. Benchmark chọn **4task×4CLI×3lần=48slot**: B-01hiểucode/B-02bug/B-03feature/B-04refactor, [protocol r1](benchmark/PROTOCOL_48_R1.md), fixture/acceptance seal và [batch runner/launch manifest](benchmark/suite48/BATCH_RUNNER.md). Guard16USD estimate đã được người dùng duyệt cho batch đầu, không invoice cap; primary outer-wall/secondary native clock và real pacing≥30s/concurrency1/cap900s/reserve60/request8/output2048 chốt trước chạy. Offline reference/mutant và synthetic/native tests là nghiệm thu harness, không kết quả model. Batch thật dừng1/48; hiện tạm hoãn theo yêu cầu người dùng, không tự resume/retry hoặc thay rubric đã khóa. Dự toán trước chạy từ P-02 chỉ là số học planning, không thay chi phí measured/unknown ởmục6.

## 6. Kết quả benchmark

**Batch thật đầu tiên đã dừng sau1/48slot:** R-0039/v1/B-01 infra_error/pending_review,5upstream/4completedcóusage; request5TimeoutError trước HTTPstatus/terminal/usage. 503native nhìn thấy là localbrokerlatch, không chứng minh upstream503. Duration278237ms/khôngwalltimeout,4gap≥30s. Known estimate0.06853344USD,1unpriced/totalchargeunknown;47not_run, không xếp hạng tool. Snapshot scope/public pass nhưng rawrubric9/10 vì extraevidence bịallowlistloại dù5giátrịđúng; cần reviewrubric riêng, không chấm lại hoặc đổistatusraw saukhi thấyresult. [Raw/audit/giới hạn](benchmark/suite48/BENCHMARK_RESULTS.md). Batch dừng, không retry/resume mới được duyệt.

<details>
<summary>Lịch sử chuẩn bị trước launch — không phải trạng thái hiện tại</summary>

**Bộ điều phối đã hoàn thiện và kiểm offline:**16/16case ở batch03,40synthetic exchanges,0provider requests. Protocol candidate/48input hashes/resource/order đã pin; guard16USD estimate và outer-wall được đồng ý, nhưng launch approval disabled, chưa reserve paid R/C IDs. [Nghiệm thu và giới hạn](benchmark/suite48/BATCH_RUNNER.md). Các cost trong synthetic ledger không phải phí thật, không nhập số liệu benchmark/pilot.

**Cập nhật chuẩn bị, không phải benchmark:** native adapter B-01–B-04 đã qua16/16task×CLI preflight offline,40synthetic exchanges,0provider requests. Một lượt mock-schema failure trước đó được giữ; không xóa retry hoặc coi đây là model giải task. [Artifact/giới hạn](benchmark/suite48/NATIVE_PREFLIGHT.md). Pacing dùng virtual clock; primary outer-wall duration còn cần duyệt trước paid launch, exact native duration được lưu riêng. Protocol/budget/paid orchestration vẫn pending.

Chưa có benchmark chính thức. CSV legacy `benchmark/runs.csv` giữ4 inference attempts; `benchmark/runs-search-r2.csv` có10 attempts với timing/group trong notes và đầy đủ metadata trong raw. Toànpilot14attempts phủ8cặp task/CLI cósuccess, không phải completionrate8/8đồngnhất; raw R-0009 classifier sai phải dùng review infra_error. Không gộp retry thành slot độc lập hoặc trộn environment/timing revisions để xếp hạng. Không đưa diagnostic/kết quả đã xóa vào completionrate/median/chi phí. Khi tổng hợp phải báo tử/mẫu, failure/retry/exclusion, duration cópacing/token/cache/reasoning, dữ liệu thiếu và artifact nguồn.

</details>

## 7. Hạn chế

Model/provider, system prompt/tool set, cache/reasoning, quota/mạng, fixture size, sample nhỏ và usage semantics khác nhau. Không quy khác biệt model/provider thành chất lượng tool từ một lượt.

## 8. Kết luận và khuyến nghị

Bốn CLI đã có lượt pilot thành công qua provider/model alias đã chọn, không chứng minh ổn định tổng quát hoặc ưu thế tool. Baseline pilot đã khóa; chỉ chạy benchmark sau khi bộ task, số lượt, budget và protocol được duyệt riêng. Các phần source/demo còn scaffold không được nâng thành kết luận từ pilot.
