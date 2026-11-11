# So sánh OpenCode, Pi và Codex CLI; OpenCode v1 và v2

> Bản nháp. Nhóm gpt-6.1-sol có giá user-reported; kết quả model cũ đã xóa/rút. Pilot đã tổng kết; benchmark thật dừng ở1attempt infra_error, chưa đủ bộ kết quả để so sánh. Không xem placeholder, source-only hoặc diagnostic một lượt là kết luận runtime đầy đủ.

> **Công việc hiện tại:** benchmark tạm hoãn theo yêu cầu, chờ người dùng yêu cầu chạy lại khi về nhà. Người dùng cho biết mạng công ty chặn kết nối; đây là thông tin user-reported, còn raw xác nhận TimeoutError trước HTTP/usage. Chuyển sang hoàn thiện source comparison offline, không probe/gọi provider. Batch thật đã có1attempt bịdừng, chưa có bộ kết quả benchmark đủ để so sánh.

## 1. Tóm tắt kết quả hiện còn bằng chứng

- **Pilot đã tổng kết offline:** 14 inference attempts / 76 upstream requests; reviewed **8 success, 3 timeout, 3 infra_error**, thêm một launch-error không inference. Tám cặp task/CLI đều có success qua retry/revision khác nhau, **không phải8/8 first-attempt hoặc benchmark đồng nhất**. [Mọi attempt](benchmark/artifacts/PILOT-FREEZE-20261109-01/SUMMARY.md), [lịch sử đầy đủ](benchmark/PILOT_RESULTS.md).
- **P-02 R-0035–R-0038:** v2→v1→Codex→Pi, cùng `search-r2/paced-900`, cả bốn success/valid, scope/public/hidden pass. n=1/CLI, không randomized, native prompts/tools/reasoning khác; không xếp hạng hoặc suy causal. Duration đều dưới300s dù cap900, không quy success chỉ cho tăng cap. [Cohort/raw references](benchmark/artifacts/PILOT-FREEZE-20261109-01/summary.json).
- **Known estimate pilot1.10640264 USD**, sáu request unpriced nên total/measured charge null. Giá user-reported4.8/0.24/18 USD mỗi triệu input/cache/output token, chưa đối soát hóa đơn; không nhập smoke/diagnostic vào pilot. [Manifest/pricing](benchmark/artifacts/PILOT-FREEZE-20261109-01/baseline.json).
- **Baseline đã khóa offline, benchmark chưa duyệt:** `search-r2 + paced-900`, pins/config/fixture/seal/dependency/policy/source hashes và validator tại [BASELINE.md](benchmark/BASELINE.md). Giữ raw/CSV, review override R-0009; snapshot pass nhưng CLI timeout vẫn là timeout. Không inference mới.
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

## 3. So sánh ba tool

Các mục3.1–3.3 dưới đây là **source-confirmed tại release đã pin**, không phải đánh giá tốc độ/chất lượng model hoặc proof mọi mode của sản phẩm. Pi/Codex đọc bằng `git show <release-SHA>:<file>`, không dùng HEAD development thay release. Permission/context/extension còn cần truy vết riêng, không suy từ kiến trúc.

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

**Chưa hoàn tất so sánh enforcement của ba tool.** Không dùng tool allowlist, config home hoặc HTTP authentication thay cho OS sandbox; phần source ở3.3 chỉ xác minh factory/runtime/dispatcher, không chứng minh mức độ an toàn tương đương.

### 3.5. Context và session

**Pending:** cần truy vết persistence/branching/compaction và ranh giới restore của cả ba tool. Session metadata offline ở4.2 không đủ chứng minh resume hội thoại hoặc khôi phục execution đang chạy.

### 3.6. Khả năng mở rộng

**Pending:** cần đối chiếu plugin/extension/MCP contract ở đúng commit và demo cách ly. Các hook/manager xuất hiện ở3.1–3.2 không đủ để kết luận plugin compatibility hoặc port thành công.

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
### 4.4. Subagent và shell chạy nền
### 4.5. Plugin compatibility và port mẫu
### 4.6. Thay đổi khác có bằng chứng

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
