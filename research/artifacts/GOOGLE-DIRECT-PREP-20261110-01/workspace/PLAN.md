# Kế hoạch hoàn thiện báo cáo

## Mục tiêu

**Google direct đã chuẩn bị offline:** user đã lưu `.local/credentials/google-ai.key`; chỉ kiểmmetadata, siếtquyền664→600 qua descriptor, khôngđọc/hiểnthịnộidungkey. ChọnproviderGoogle với ChatCompletions endpoint riêng, không sửa Shopaikey code/raw. [Profile/adapter](demos/GOOGLE_GEMINI.md) và plan disabled tại `demos/artifacts/GOOGLE-GEMINI-PREP-20261110-01/`;58offline tests đạt. **0Google API calls**, chưa xác minh key/model/account và native4CLI. Cần scopedapproval5Google trướcgeneration; benchmark48 vẫnchưamở. Audit `research/artifacts/GOOGLE-DIRECT-PREP-20261110-01/validation.json`. Các mốc Shopaikey/Sol bên dưới là lịch sử.

**Mới nhất — Gemini smoke dừng:**1/5requesttrực tiếpShopAikey`/responses` trảHTTP500/internal_error trong676ms,0pass/4not_run; chưausage hoặcmodelidentity,costnull. Khôngretry/fallback hoặc mở48benchmark. [Kết quả](demos/GEMINI_SMOKE5_RESULTS.md), audit`research/artifacts/GEMINI-SMOKE5-REVIEW-20261110-01/validation.json` giữraw/source/pricing/frozenSol/registryR222C323. KhôngkếtluậnGeminihaySoloutage/khônghỗtrợprotocol chỉtừlỗi500generic; native4CLI/toolcalling/benchmarkGemini chưa nghiệmthu. Các đoạn chuẩn bị bên dưới giữ lịch sử.

**Yêu cầu Gemini mới:** user xác nhận Shopaikey, **chạy lại thành cohort mới, không nối2model**, cho phép **5lượt thử trước, giá bổ sung sau**. Chuẩn bị provider-only [smoke5](demos/GEMINI_SMOKE5.md):5requesttốiđa/ResponsesSSE/output256/gap30/khôngretry; không dùngnativeCLI/session/tool hoặc mở48benchmark.47offline tests đạt; approval bind exceptiongiá scope5, estimated/measuredcostnull, khônggiásol. Audit `research/artifacts/GEMINI-SMOKE5-LAUNCH-20261110-01/validation.json`; solraw/pricing/frozen/IDs giữ nguyên. BenchmarkGemini đầy đủ vẫn cần adapter/smoke/protocol/budget riêng.

**Ưu tiên mới:** người dùng yêu cầu chọn `gemini-3.8-flash` thay sol. Đã tạo profile/model-selection riêng, giá/capabilities/protocol pending, paid gates đóng; xem [`research/GEMINI_MIGRATION.md`](research/GEMINI_MIGRATION.md). Chưa gọi API/probe hoặc sửa sealedsolrunner/pricing/baseline. Giữ solraw/failure/retry/usageunknown/IDs; chưa xác nhận rootcause timeout. Cần giáinput/cache/output, xác nhận provider và scopeGemini48mới hay41suffix tách nhóm; không tự tăng ngân sách hoặc trộn kết quả model.

**Trạng thái mới nhất:** continuation43 đã dừng2/43slot: R179/Pi-B02success157222ms (chỉpagination.py đổi,scope/public/hiddenpass), R180/v2-B02infra_error/pending_review159194ms (request1TimeoutError trướcHTTPusage,chưasửafile,khôngwalltimeout).41slotchưachạy. Tổngbenchmark8attempts/7unique48slot gồm1retry; known0.28485816USD/4unpriced/chargeunknown. Audit `research/artifacts/CONTINUE43-REVIEW-20261110-01/validation.json` đạt5gap≥30s/input-resource/raw/frozen/Git/isolation/cleanup; nextR222/C323. Không tựretry/resume/probe, lượt mới cần quyết định riêng. Các đoạn launch/kết quả cũ bên dưới là lịch sử.

**Yêu cầu mới “chạy tiếp”:** chuẩn bị43slot chưa chạy D48-006…048, **không retryR135** hoặc lượt đã chạy. Protocol `benchmark/PROTOCOL_CONTINUE43_R2.md`; giữrubricr2/guard16USD, carryknown0.25185936USD/3unpriced/totalunknown, remainingknown15.74814064USD.112regressiontests đạt (75benchmark+37demos; legacyfixedIDtests cáchly khỏiCSVthật, khôngsửa sealedcode). Nativeoffline/launchgates đangchuẩnbị. Lỗi mới sẽstop, khôngautor retry/resume.

**Gates continuation43 đã đạt:**16/16native synthetic task×CLI (0provider),112regressiontests, plan/priorraw/hash/resource/rubricr2/freshIDs/Git/cleanup kiểmđạt. Approval bound43slotkhôngretry vàguard16/carry3unpriced; audit `research/artifacts/CONTINUE43-LAUNCH-20261110-01/validation.json`. Runnerreserve dựkiếnR179–221/C280–322 dưới lock; chưa có kết quả mới vàkhôngtáidùngIDcũ.

**Trạng thái mới nhất — batch retry45 đã dừng:** R-0134/v2/B-01 retry củaR89 **success/valid10/10**,6requestcompleted,224706ms. Sau đóR-0135/Codex/B-02 **infra_error/pending_review**,1requestTimeoutError trướcHTTP/usage, chưa sửa file,73499ms/khôngwalltimeout. Dừng2/45attempts;43slot unique chưa chạy, không tựretry/resume. GiữR89infra_errorgốc,khôngthayfirstattemptbằngretrysuccess. Tổng6attempts/5unique48slot,known0.25185936USD/3unpriced/chargeunknown. Audit `research/artifacts/RETRY45-REVIEW-20261110-01/validation.json`:6gap≥30s/input-resource/raw/frozen/Git/cleanupđạt; nextR179/C280. Các đoạn launch/hold cũ phía dưới là lịch sử.

**Yêu cầu mới:** người dùng nói “retry chạy tiếp”; chuẩn bị đúng1retryR89/v2-B01 rồi44slot chưa chạy theo `benchmark/PROTOCOL_RETRY45_R2.md`. Không rerunCodex/Pi/R39, không sửa rubricr2, giữguard16USD gồm priorknown0.21341376USD/2unpriced (remainingknown15.78658624USD, totalunknown).106regressiontests pass sau cáchlylegacy fixedIDtest khỏiCSV thật; giữ2lỗi testharness metadata ởRETRY45-REGRESSION01/02, khôngsửa sealedcode/raw. Nativeoffline acceptance/launch gates đangchuẩnbị; không auto retry saulỗimới.

**Gates retry45 đã đạt:**16/16native synthetic task×CLI (0provider),106regressiontests, manifest/priorraw/rubricr2/hash/resource/freshIDs/Git kiểm đạt. Approval bind đúng1retryR89+44suffix và guard16/carryunknown; audit `research/artifacts/RETRY45-LAUNCH-20261110-01/validation.json`. Dự kiến reserveR134–178/C235–279 dưới lock khi dispatch, không tái dùng IDs cũ. Chưa có kết quả paid batch mới.

**Điều hướng hiện tại:** continuation47 theo yêu cầu đã dừng sau3slot: R87Codexsuccess, R88Pifailure9/10theosealedr2 (5giá trịđúng; caveatevidence mutation), R89v2infra_error/TimeoutError trướcHTTPusage.44suffixnot_run. Không retry/resume/topup; cần quyết định mới trước inference. Tổngbenchmark4/48slot,known0.21341376USD/2unpriced/totalchargeunknown, guard16USDkhônginvoicecap. Audit `research/artifacts/CONTINUE47-REVIEW-20261110-01/validation.json`:9gap≥30s/inputhash/resource/raw/frozen/Git/cleanupđạt; nextR134/C235. Nguyên nhân mạng vẫn user-reported; không đổi service/plugin thật hoặc probe mạng.

**Continuation launch gates đã đạt:** rubric r2 seal riêng chỉ thay B01hidden;8rubric cases đạt kỳ vọng;101regression tests pass và16/16native task×CLI synthetic acceptance (0provider). Manifest/approval bound suffix47, guard còn15.93146656USD known-estimate, prior1unpriced giữtotalunknown, IDs mới dự kiếnR87–133/C188–234. Audit `research/artifacts/CONTINUE47-LAUNCH-20261110-01/validation.json`; chỉ runner reserve dưới lock khi paid launch, chưa dùng lại47IDs cũ. Lần này dừng theo stop policy, không auto retry/resume.

**Đã làm offline2026-11-10:** bổ sung REPORT3.1kiếntrúc/3.2agentloop/3.3toolsvà4.1v1-v2serverlifecycle/4.2HTTP-Client-embeddedSDK; giữ permission/context/extension và runtime demo còn pending. Thêm E-0077–E-0086(source-confirmed), validator86evidence IDs đạt commit/file/line/permalink, không gọi đó là86runtime tests. Snapshot source đúng release + reviewclaim/link/secretpattern/raw/frozen/Git sạch tại `research/artifacts/SOURCE-REPORT-20261110-02/validation.json`. Zero provider/networkprobe/nativebinary calls; nextR87/C188 và rawR39 giữ nguyên. Mạng công ty là user-reported; chờ user về nhà/yêu cầu rõ mới xét chạy lại. Bước source tiếp theo: permission/sandbox enforcement, context/session và extension contract, không đụng service/plugin đang dùng.

**Đợt source tiếp theo:** đã viết REPORT3.4permission/sandbox,3.5context/session,3.6extension và4.3v1-v2schema/precedence/defaults,4.5plugincontract/giới hạn port; thêm E-0087–E-0108(source-confirmed). Đây là first-pass đối chiếu code theo nhánh, **không** nghiệm thu OS security/resume/compaction quality hoặc plugin runtime. V2 evaluatorlastmatchkhácconfigured-deny/savedallow policy; fallbackaskkhácbaseagentdefault. Pi hookblock cósourcewiringnhưngkhôngOSisolation; CodexapprovalNeverkhácSandboxType. Không plugin/service/network/providerchanges; benchmark vẫnđợiyêucầu củauser. Các checklist runtime/demo chưa đạt giữ unchecked.

So sánh OpenCode v2 với Pi và Codex CLI theo sáu trục; đối chiếu OpenCode v1/v2 bằng source và demo; đo hiệu quả trên cùng bộ task với bốn cấu hình.

**Source background/loader:** REPORT4.4 xác minh v1 **đã có** background subagent; v2 có native shell background và phân biệt persisted job rows với live execution. REPORT4.5 truy loader v1 fallback exports và v2 default id/effect-or-setup cùng Promise cleanup adapter. Thêm E-0109–E-0117; tổng117 evidence IDs kiểm cấu trúc. Audit chung E-0087–E-0117 tại `research/artifacts/SOURCE-REPORT-AXES-20261110-02/validation.json`; giữ revision01 lỗi đường dẫn tương đối trong audit script, không phải lỗi source/runtime tool. Demo plugin port/disconnect/restart vẫn pending; chưa nạp plugin hoặc chạy subagent/provider.

Phân biệt rõ: đọc được từ source, đã kiểm chứng runtime, và chưa kiểm chứng.

### Ưu tiên offline theo yêu cầu mới

Người dùng yêu cầu làm các task chưa cần API trước. Không coi đây là quyền resume benchmark/provider hoặc restart/nạp plugin. Đã truy recovery consumer v2 và activation gates (E-0118–E-0124), chuẩn bị [`demos/OFFLINE_DEMO_PLAN.md`](demos/OFFLINE_DEMO_PLAN.md) với15 acceptance cases và fixture worker bounded. Unit tests của fixture chỉ kiểm code nghiên cứu, không nghiệm thu native background của OpenCode. Audit: `research/artifacts/OFFLINE-TASKS-20261110-01/validation.json`.

- [x] Truy persisted background rows tới consumer recovery và phân biệt shell cancellation/subagent resume trong source v2.
- [x] Lập acceptance matrix background/plugin/permission/context/SDK, requirements isolation/artifacts/cleanup và ranh giới cần inference.
- [x] Tạo fixture success/error/cancel và unit tests cục bộ; chưa đưa vào native tool.
- [ ] Truy toàn bộ hosting callers và recovery v1 tương ứng; không kết luận v1 không hỗ trợ.
- [ ] Viết/nghiệm thu native offline demo runner với egress bị chặn và transport synthetic có nhãn trước khi nạp plugin/restart test service.
- [ ] Chạy các native demo, ảnh UI thật, nghiệm thu resume/compaction và port plugin; hiện vẫn pending.

Các ghi nhận theo ngày bên dưới giữ lịch sử. Checkbox rộng như full smoke/isolation/GUI vẫn pending dù metadata, native search và các prompt smoke cụ thể đã đạt; không đánh dấu hoàn thành toàn bộ chỉ từ một nhánh.

`README.md` là trang giới thiệu và điều hướng; `REPORT.md` là báo cáo cuối. Không biến checklist hoặc giả thuyết trong đề bài thành kết luận khi chưa có bằng chứng.

## 1. Chốt phiên bản và môi trường

- [x] Kiểm tra upstream: bản OpenCode 1.x cuối và 2.x mới nhất tại ngày chốt.
- [x] Chọn tag/commit cụ thể của Pi và Codex; không cập nhật trong thực nghiệm.
- [ ] Ghi OS, CPU/RAM, runtime, model/provider và cấu hình.
- [x] Ghi trạng thái Git, remote nguồn (không suy ra lịch sử clone) và cách gọi binary riêng vào `research/versions.md`; metadata đã chạy, prompt smoke còn thiếu.
- [x] Xác định nơi đặt fixture smoke và môi trường cách ly: `/tmp/opencode/agent-cli-report/smoke/<config_id>/`; fixture benchmark chính thức vẫn phải chốt ở giai đoạn 5.
- [x] Chốt chính sách release: ưu tiên stable; nếu dùng prerelease/development snapshot phải ghi lý do và giới hạn so sánh.
- [x] Hiểu “1.x cuối” và “2.x mới nhất” là release phù hợp chính sách tại ngày chốt, ghi rõ ngày và nguồn upstream.
- [ ] Nếu cần cập nhật source local, ghi phương án và xin phép trước khi fetch/checkout/build/cài dependencies; không thay đổi snapshot đang nghiên cứu ngoài quyết định đã ghi nhận.

Đầu ra: bảng version/commit có thể tái tạo. Không cần clone lại các tool nếu repo hiện có đủ source/tag.

Điều kiện hoàn thành: mỗi cấu hình có full commit SHA, nguồn xác minh, Git status, cách chạy dự kiến và danh sách phần chưa xác minh. Cách chạy thực tế phải được xác nhận ở smoke test trước pilot.

Model hiện tại: `gpt-6.1-sol`, provider `https://api.shopaikey.com/v1`. Kết quả/log/runtime model cũ đã xóa; giữ diagnostic sol/Pi, metadata/API offline và fixture/source evidence. Đã có giá user-reported input/cache/output 4.8/0.24/18 USD mỗi triệu token. Estimate offline của diagnostic sol đã giữ: 0.21496416 USD, charge chưa đối soát; không gọi thêm API từ cập nhật giá. Xem `benchmark/SOL_COST.md`.

## 2. Lập bản đồ source và bằng chứng

Giữ source guards về header Responses Lite và parser final/progress theo E-0060–E-0065. Runtime traces cũ đã rút, evidence còn source-only; không dùng để khẳng định Codex/sol đã chạy. Unit tests offline không thay runtime model.

Trạng thái sol: diagnostic Pi/P-01 hoàn tất với 6 HTTP 200/completed và public/hidden tests đạt; smoke OpenCode v1/v2/Codex đã đạt chức năng đọc marker. Chưa có pilot đủ 8 lượt; không kế thừa trạng thái của model đã rút.

Smoke ba CLI (v1 → v2 standalone → Codex), C-0045–C-0047 đã kết thúc: 3/3 đạt chức năng, 8/8 HTTP 200/completed, estimate 0.09173616 USD dưới shared guard 0.50. **Pacing toàn đợt không đạt**: năm gap nội bộ ≥30 giây, hai gap chuyển CLI chỉ 1.571132/1.271972 giây do handler reset trạng thái mỗi broker. Giữ raw/protocol nguyên; cần sửa/test pacing xuyên CLI offline trước lượt trả phí mới. Hash/key scan/PID/socket/source Git postcheck đạt; không mở pilot hoặc tự retry. Review: `demos/MODEL_SMOKE_SOL_RESULTS.md`.

Truy vết sáu trục:

Pacing đã sửa offline sau smoke: state/lock dùng chung toàn batch trong smoke và pilot; 5 tests xuyên broker mới + 7 smoke + 6 pilot + 5 pricing đạt (23 tổng). Source trước sửa/raw smoke giữ nguyên; chưa gọi provider lại. Xem `research/PACING_FIX.md`. Hold lượt trả phí tiếp theo ở bước chốt budget/settings/protocol pilot, không còn ở bước thiếu bản sửa offline.

Người dùng tiếp tục duyệt **pilot 8 lượt/guard chung 3 USD estimate/pacing30**. Đã chốt `benchmark/PILOT_SOL.md rev1`, sửa runner nhận `--budget-usd` và cho pacing full batch, 24 tests offline đạt; preflight C-0057–C-0060 đủ bốn CLI đạt, không provider. Source/protocol/fixture/binary hash và fresh IDs R-0009–R-0016/C-0049–C-0056 kiểm tra đạt, snapshot ở `research/artifacts/SOL-PILOT-LAUNCH-20261106-01/`. Đã khởi chạy background `PILOT-SOL-20261106-01` (shell `sh_1b0305998001145CS3mzi2qPDd`), đang chờ hoàn tất; không benchmark chính thức hoặc tự retry. Budget không phải trần hóa đơn cứng; thiếu usage/chạm guard dừng trước request/lượt sau.

Đợt trên **đã kết thúc, dừng 1/8**: R-0009 Pi/P-01 đọc source nhưng chưa sửa; request2 HTTP 200/`response.failed`, thông báo provider overload/thiếu usage. Guard dừng, bảy slot not_run, native retry bị chặn local; hai upstream request, gap30.000943 giây. Known subtotal 0.0280872 USD, tổng/charge unknown. Raw gán nhầm failure/valid vì classifier bỏ terminal failed; review là **infra_error/pending_review**, không dùng làm task failure. Còn lỗi môi trường rg missing. Hash/key scan/PID/socket/Git postcheck đạt; không tự retry. `benchmark/PILOT_RESULTS.md` và `research/artifacts/SOL-PILOT-REVIEW-20261106-01/validation.json`. Cần sửa/test classifier và review tools/PATH trước đợt mới.

Theo yêu cầu sửa và tránh burst: đã tách `classify_run` kiểm terminal/usage/empty ledger, latch provider failure toàn batch trong cả smoke/pilot để chặn retry/CLI tiếp theo tại local ngay cả lỗi có usage. Khóa serialize chung batch/pacing30 giữ nguyên. **30 tests offline đạt**, gồm hai client đồng thời/two-broker và chấm lại R-0009 thành infra_error; raw/CSV/protocol không sửa. Lần test race BrokenPipe giữ riêng, đã sửa local reject bounded-drain. Chưa gọi thêm API; bản sửa live chưa nghiệm thu. Xem `research/PROVIDER_STOP_FIX.md`; còn review tools/PATH và quyết định chạy tiếp/protocol revision trước lượt trả phí mới.

Người dùng yêu cầu chạy lại pilot để kiểm tra bản sửa: chốt **single retry Pi/P-01 R-0017/C-0069**, retry_of R-0009, protocol `benchmark/PILOT_SOL_RETRY.md rev1`; không mở bảy slot còn lại trong bước kiểm tra này. Giữ guard 3 USD tính known subtotal cũ 0.0280872 (remaining2.9719128), một request cũ unpriced giữ unknown; pacing30/1 upstream active/cap300s-8request-2048output. Launch audit xác nhận 30 tests/source hashes, fixture/binary/fresh ID/Git sạch; inventory cùng sandbox profile có Python/bash/find/ls, rg vẫn thiếu, giữ điều kiện retry không cài thêm. Snapshot `research/artifacts/SOL-PILOT-RETRY-LAUNCH-20261106-01/`. Đã khởi chạy background `sh_1b03be8ff001W5v2iol6Z58KDy`, đang chờ hoàn tất, chưa có kết luận.

Retry trên đã hoàn tất **R-0017 success/valid**: Pi/P-01 chỉ sửa intervals.py, scope/public/hidden pass, 7/7 HTTP200/completed, sáu gap≥30.000974 giây, exit0/không timeout. Estimate lượt0.07692480 USD, cumulative known pilot0.10501200 USD; total/charge unknown vì request cũ thiếu usage. Hash/key scan/PID/socket/Git postcheck đạt. Không mở bảy slot còn lại, chưa chứng minh pacing live xuyên CLI hoặc provider-failure latch live. `benchmark/PILOT_RESULTS.md`, review `research/artifacts/SOL-PILOT-RETRY-REVIEW-20261106-01/validation.json`.

Người dùng xác nhận mở **bảy slot còn lại**, không chạy lại Pi/P-01: protocol `benchmark/PILOT_SOL_CONTINUE.md rev1`, R-0018–R-0024/C-0070–C-0076. Thêm `--continue-after` kiểm single retry đã success, kế thừa known0.10501200 USD và một request unknown; remaining known guard2.89498800 USD trong tổng3. Giữ concurrency1/pacing30 xuyên CLI/cap300s-8request-2048output, provider lỗi thì latch dừng/no upstream retry. **32 tests offline đạt**, source/fixture/binary/chain hashes/fresh IDs/Git kiểm tra đạt, snapshot `research/artifacts/SOL-PILOT-CONTINUE-LAUNCH-20261106-01/`. Đã khởi chạy background `sh_1b0472bc1001TNnLE4QfFxMKj5`, đang chờ hoàn tất; chưa có kết quả continuation, không benchmark chính thức hoặc tự retry.

Continuation đã dừng **2/7**: R-0018 Codex/P-01 success (scope/public/hidden pass, 5 requests); R-0019 v2/P-01 timeout300s gồm pacing, chưa sửa source, request5 HTTP200 nhưng thiếu terminal/usage/TimeoutError. 5 slot chưa chạy. 9/9 gap≥30s, xuyên CLI30.003446s (runtime-confirmed); latch provider_failure/usage_missing dừng, không overload message xác định. V2 glob lỗi ripgrep, fallback read/find được; cần review environment/latency, không task-wrong conclusion. Known estimate đợt0.29888712 USD, cumulative0.40389912 USD; hai request unpriced nên total/charge unknown. Hash/key scan/PID/socket/process/Git postcheck đạt, raw/protocol giữ nguyên, không tự retry/tăng cap/mở slot. `benchmark/PILOT_RESULTS.md`, review `research/artifacts/SOL-PILOT-CONTINUE-REVIEW-20261106-01/validation.json`.

Theo yêu cầu xác minh môi trường, audit offline ngày2026-11-09 **đã tái hiện glob failure cả v1/v2**, native bash Pi không có rg; Codex có rg15.2.0 đi kèm. Đối chứng mount read-only rg sẵn có chỉ trong sandbox test mới khiến glob v1/v2 trả đúng fixture và Pi shell chạy rg được. Không cài dependency/đổi pilot/gọi provider. Mock đầu v1 bị lặp local sau tool events, giữ raw; bản bounded mock C-0081–C-0084 và control C-0085–C-0088 đủ bằng chứng tool, exit1 là intentional local400. Hash/binary/fixture/raw/PID/socket/source Git postcheck đạt. **Không nên chạy năm slot với nguyên environment cũ**; chốt revision dependency/preflight trước khi trả phí, tách nhóm hoặc chạy lại để so sánh đồng nhất. Chưa chứng minh thiếu rg là toàn bộ nguyên nhân timeout. `research/SEARCH_ENVIRONMENT.md`, review `research/artifacts/SEARCH-ENV-REVIEW-20261109-01/validation.json`.

Người dùng đồng ý chuẩn hóa: **search-r2 đã hoàn tất offline**. rg15.2.0 cùng SHA-256 cho bốn native CLI, mount read-only private dependency dir, không host install/thay tool binary; Python3 policy giữ nguyên. Native glob+grep v1/v2 và shell rg files/search cả bốn pass; writable/config/isolation preflight4/4, **37 tests pass**. Runner pilot mặc định r2, tag manifest/revision và chặn silent cross-env retry/continue; legacy raw/CSV giữ nguyên. Hai audit đầu Codex vướng projectRO không khớp workspace-write, đã sửa harness mount ở lượt03, giữ log. Chưa inference/năm slot mới; cần chốt group/protocol trước paid, không gộp legacy+r2. `research/ENVIRONMENT_R2_RESULTS.md`, validation `research/artifacts/SEARCH-R2-PREP-20261109-01/validation.json`.

Người dùng yêu cầu chạy lại sau chuẩn hóa: chốt **single recheck OpenCode v2/P-01 R-0025/C-0114** trên search-r2, nhóm mới `search-r2-environment-recheck`, đối chiếu R-0019 nhưng không gộp cùng legacy. Protocol `benchmark/PILOT_SEARCH_R2_RECHECK.md rev1`, ghi inference r2 vào CSV riêng, cờ explicit để không bypass silent cross-env guard. Giữ cap300s/8request/2048output/pacing30/concurrency1/failure latch; guard3 USD kế thừa known0.40389912, remaining2.59610088, hai request cũ unpriced giữ unknown. **38 tests offline pass**, hash fixture/dependency/binary/source/legacyraw/freshIDs/Git đạt, snapshot `research/artifacts/SEARCH-R2-RECHECK-LAUNCH-20261109-01/`. Đã khởi chạy background `sh_1be39c8360017HBRy58QV9YoaR`, đang chờ hoàn tất; không mở các slot còn lại hoặc tự retry.

R-0025 search-r2 recheck đã kết thúc **infra_error/pending_review**: request đầu không tool schema, TimeoutError trước HTTP status/usage, chưa tới task/glob/chưa sửa source. Chỉ1 upstream, **11 request tiếp bị chặn local**; local503 không phải provider overload evidence. Cumulative known estimate0.40389912 USD không đổi, ba requestunpriced/totalchargeunknown; raw subtotal0 lượt này không phải miễn phí. Hash/manifest/dependency/binary/chain/keyscan/PID/socket/Git postcheck đạt, CSV r2 riêng/legacygiữnguyên. Không mở năm slot hoặc tự retry. `benchmark/PILOT_RESULTS.md`, review `research/artifacts/SEARCH-R2-RECHECK-REVIEW-20261109-01/validation.json`.

Người dùng yêu cầu retry rõ ràng sau R-0025: chốt **R-0026/C-0115 v2/P-01 search-r2**, session mới, single retry_of R-0025; không mở năm slot. Protocol `benchmark/PILOT_SEARCH_R2_RETRY.md rev1`, giữ settings/cap300s/8request/2048output/pacing30/concurrency1/provider-failure latch. Guard3 USD carry known0.40389912, remaining2.59610088, ba request cũunpriced. Offline gates xác nhận runner đã test38 không đổi, same-env/dependency/fixture/binary/lineage hashes/freshIDs/Git đạt; snapshot `research/artifacts/SEARCH-R2-RETRY-LAUNCH-20261109-01/`. Đã khởi chạy background `sh_1be41bde6001QQO0cILbx3Cd6p`, đang chờ hoàn tất; chưa có kết luận, không tự retry thêm.

R-0026 đã kết thúc **infra_error/pending_review**, lặp R-0025: request đầu TimeoutError trước HTTP status/usage/tool execution, source chưa đổi; chỉ1 upstream và11 localblocked, không supervisor300s timeout. Local503 không phải upstream overload evidence. Known cumulative0.40389912 USD không đổi, bốnrequestunpriced/totalchargeunknown. Hash/manifest/dependency/fixture/binary/lineage/keyscan/PID/socket/Git đạt, r2CSV riêng cóR25/R26, legacy giữ nguyên. Không tự retry hoặc năm slot; nên chẩn đoán đường kết nối/timeout trước paidtiếp. `benchmark/PILOT_RESULTS.md`, review `research/artifacts/SEARCH-R2-RETRY-REVIEW-20261109-01/validation.json`.

Theo yêu cầu check mạng, đã kiểm **host direct/no-proxy giống broker**, không key/auth/generation: DNSapi→IPv4, TCP443/TLS1.3/chứng chỉCAhostnameverified; GET/models401 vàGET/200, dưới1s mỗi probe. **Không thấy chặn mạng cơ bản tại thời điểm kiểm**; không suy authenticatedResponses/backend hoạt động hoặc loại lỗi mạng thoáng qua trước đó. Chưa xác định rootcause TimeoutError, không retry/pilot thêm. `research/PROVIDER_NETWORK.md`, raw `demos/artifacts/PROVIDER-NETWORK-20261109-01/result.json`.

Người dùng yêu cầu check mạng lại: artifact mới `PROVIDER-NETWORK-20261109-02` cùng script, DNS7ms/cùngIPv4, TCP50ms/TCP+TLSverified103ms, models401/55ms/root200/57ms. Kết nối cơ bản vẫn đạt; không key/auth/generation hoặc retry/pilot. AuthenticatedResponses/backend chưa kiểm chứng, không kết luận rootcause timeout.

Người dùng yêu cầu gọi lại sau networkchecks: chốt single **R-0027/C-0116 v2/P-01 search-r2 retry_of R-0026**, protocol `benchmark/PILOT_SEARCH_R2_RETRY_02.md rev1`, không mở năm slot. Giữ cap/settings/pacing/guard3 USD; known0.40389912, remaining2.59610088, bốnrequestunpriced. Launch offline gates same-tested-source/environment/fixture/dependency/binary/lineage/freshIDs/Git đạt, snapshot `research/artifacts/SEARCH-R2-RETRY-LAUNCH-20261109-02/`. Đã khởi chạy background `sh_1c09bcd55001q0cuTHFuFd9yWN`, đang chờ hoàn tất; không tự retry thêm.

Launch R-0027 lỗi **FileNotFoundError vì runtime parent /tmp bị mất**, trước broker/CLI nên **0 upstream/no inference**; artifact chỉ protocol, giữ raw và IDreserved. Sửa đúng1 dòng prepare.mkdir parents=True/exist_ok=False, regression chứng minh tạo parent khi thiếu và không overwrite sandbox. **39 tests pass**, validation `research/artifacts/SEARCH-R2-LAUNCH-RECOVERY-20261109-01/`. Khôi phục lời gọi đã được người dùng yêu cầu bằng **R-0028/C-0117**, lineage inference vẫnR-0026, protocol `benchmark/PILOT_SEARCH_R2_RETRY_03.md rev1`; không thêm retry sau một inference lỗi. Giữ env/cap/pacing/guard/costunknown cũ, không mở năm slot. Đã khởi chạy background `sh_1c09e9b0d0016P6tBZSpRVMyS6`, đang chờ hoàn tất; chưa có kết luận.

R-0028 đã hoàn tất **success/valid** trênsearch-r2: v2/P-01 chỉ sửa intervals.py, scope/public/hidden pass, 7/7 HTTP200/completed, sáu gap≥30.000791s, exit0/không timeout, duration217097ms gồm pacing. Agent tự fallback python→python3 sauhai exit127, không glob/grep live. Estimate0.06716400 USD, cumulativeknown0.47106312 USD, bốnunpriced/totalchargeunknown. Hash/keyscan/PID/socket/Git/rawpostcheck đạt; r2CSV riêng lỗi cũgiữ nguyên; R27vẫnlauncherror0upstream. Không mở năm slot hoặc gộp legacy+r2. `benchmark/PILOT_RESULTS.md`, review `research/artifacts/SEARCH-R2-RETRY-REVIEW-20261109-03/validation.json`.

Người dùng yêu cầu chạy nốt: chốt **năm slot search-r2 R-0029–R-0033/C-0118–C-0122**, P01v1→P02v2→P02v1→P02Codex→P02Pi; không chạy lại ba slotP01đãcókếtquả/không gộp legacy+r2. Protocol `benchmark/PILOT_SEARCH_R2_FINISH.md rev1`, selector `--finish-after R28` kiểm source success/env và carry known0.47106312+4unpriced, remaining2.52893688 trong guard3. Giữ cap/pacing/concurrency/latch/noautorretry, CSVr2riêng. **41 tests offline pass**, exactplan/fixture/dependency/binary/chainraw/freshIDs/Git đạt; snapshot `research/artifacts/SEARCH-R2-FINISH-LAUNCH-20261109-01/`. Đã khởi chạy background `sh_1c0a62406001oBiR1fC56ftc5c`, đang chờ hoàn tất; không benchmark chính thức/auto retry.

Đợt finish đã dừng **2/5**: R-0029 v1/P01 success, scope/public/hidden pass,7completed; R-0030 v2/P02 **snapshot scope/public/hidden pass nhưng CLI timeout300s**, request7 bắt đầu299.393594s/HTTP200 rồi BrokenPipeError/missingterminalusage. Giữ timeout không upgrade success/không coi sửa sai; không toolerror/ripgrep error trong log đã đọc. 13/13gap≥30s/xuyênCLI30.000826s. **Ba slot P02/v1,Codex,Pi not_run**, không tựretry/tăngcap/mởtiếp. Knownđợt0.14764128,cumulative0.61870440 USD, nămrequestunpriced/totalchargeunknown. Hash/keyscan/PID/socket/Git/rawpostcheck đạt; `benchmark/PILOT_RESULTS.md`, review `research/artifacts/SEARCH-R2-FINISH-REVIEW-20261109-01/validation.json`.

Người dùng yêu cầu thử lại: chốt single **R-0034/C-0123 v2/P02 search-r2 retry_of R-0030**, protocol `benchmark/PILOT_SEARCH_R2_P02_RETRY.md rev1`. Giữ300s gồm pacing/8request/2048output/concurrency1/latch vàsettingsfixture; không mở ba slot khác, không upgrade timeoutcũ. Guard3 USD carryknown0.61870440+5unpriced, remaining2.38129560. Offline launch gates same-tested-runner/env/fixture/dependency/binary/chainraw/freshIDs/Git đạt, snapshot `research/artifacts/SEARCH-R2-P02-RETRY-LAUNCH-20261109-01/`. Đã khởi chạy background `sh_1c0b2ef82001XYQoxkfOcGu3BJ`, đang chờ hoàn tất; không tự retry thêm.

R-0034 đã kết thúc **timeout/valid300041ms**, lặp R30: snapshot chỉscheduler.py đổi/scope/public/hidden pass, nhưng CLI chưa completion. 7upstream/6completed; request7 bắt đầu295.647861s/HTTP200/TimeoutError/missingterminalusage. 6gap≥30s (≥180s dànhpacing), **nativeglob livecompleted**, agentfallback python/pytest thiếu→python3/unittest exit0. Knownlượt0.07098192,cumulative0.68968632 USD, sáuunpriced/totalchargeunknown. Hash/keyscan/PID/socket/Git/rawpostcheck đạt; ba slotP02/v1,Codex,Pi chưa chạy, không retry/tăngcapâmthầm. `benchmark/PILOT_RESULTS.md`, review `research/artifacts/SEARCH-R2-P02-RETRY-REVIEW-20261109-01/validation.json`. Không nên retry nguyên điều kiện chỉ để lấy success; đổi timeoutpolicy cần revisionnhómnhấtquán.

Người dùng đồng ý đổi timingpolicy thay vì retry nguyên điều kiện: **paced-900 đã sửa/nghiệm thu offline** chung cả bốn CLI (wall900s gồm pacing, reserve60s saupacing, concurrency1/gap30/request8/output2048 không tăng). Broker chặn local408/latch time_window_exhausted trước opener nếu thiếureserve, không quy providerfailure; kiểm lại sauparse. Runner tag policy/limits/group và chặn silent cap300→900 continuation/retry, recheck cầncờexplicit+protocolriêng. **48 tests pass, preflight config/writable/isolation4/4 pass**, C124–127; hash/key-free/PID/socket/Git/rawCSVpostcheck đạt. Sourcebefore/after và validation `research/artifacts/PACED-900-PREP-20261109-01/`, docs `research/PACED_900_RESULTS.md`, protocol `benchmark/TIMING_POLICY_R2.md`. **Chưa inference mới/ba slot**, không bảo đảm provider/task chắc chắn success; known0.68968632 USD/sáuunpriced giữ nguyên.

Người dùng đồng ý chạy policy mới: chốt **single R-0035/C-0136 v2/P02/search-r2/paced-900**, timingrecheck_of R34, nhómriêng không gộpcap300. Protocol `benchmark/PILOT_PACED_900_RECHECK.md rev1`, cap900s/reserve60/gap30/concurrency1/request8/output2048/latch giữ USDguard3; carryknown0.68968632+6unpriced/remaining2.31031368. Offline gates source48tests/hashfixturedependencybinary/chainraw/freshIDs/Git đạt; snapshot `research/artifacts/PACED-900-RECHECK-LAUNCH-20261109-01/`. Đã khởi chạy background `sh_1c0cba008001njQ0dqhTfdNobd`, đang chờ hoàn tất; không ba slot khác/auto retry.

R-0035 paced900 nghiệmthu đã hoàn tất **success/valid v2/P02**: chỉscheduler.py đổi/scope/public/hidden pass, 7/7HTTP200completed, gap≥30.001173s, duration234718ms gồm pacing, exit0khôngtimeout. Minremainingdispatch671.370163s/reserve60 giữ, timingguardkhôngkíchhoạtlive. Hoàn tấtdưới300s nên **không kết luận riêngtăngcaplànguyênnhânđạt**. Estimate0.07580592 USD,cumulativeknown0.76549224,sáuunpriced/totalchargeunknown. Hash/keyscan/PID/socket/Git/rawpostcheck đạt, timeoutcũgiữ nguyên/táchgroup. Ba slotP02/v1,Codex,Pi chưa chạy; `benchmark/PILOT_RESULTS.md`, review `research/artifacts/PACED-900-RECHECK-REVIEW-20261109-01/validation.json`.

Người dùng yêu cầu chạy nốt: chốt **ba slot P02 v1→Codex→Pi R-0036–R-0038/C-0137–C-0139**, cùng search-r2/paced900 vớiR35; không rerunv2/khônggộpP01legacycap300. Protocol `benchmark/PILOT_PACED_900_COMPLETE.md rev1`, selector `--complete-after` kiểm sourceR35success/env/timing; carryknown0.76549224+6unpriced, remaining2.23450776 trongguard3. Giữ900s/reserve60/pacing30/concurrency1/request8/output2048/latch/noautorretry. **50tests offline pass**, exactplan/fixture/dependency/binary/chainraw/freshIDs/Git đạt; snapshot `research/artifacts/PACED-900-COMPLETE-LAUNCH-20261109-01/`. Đã khởi chạy background `sh_1c0d3b272001r9rAJbOKMtOWhY`, đang chờ hoàn tất; không tự retry/benchmark.

Đợt ba slot cuối **đã hoàn tất3/3 success/valid**: R36v1/P02(7requests),R37Codex/P02(6),R38Pi/P02(7); chỉscheduler.py đổi/scope/public/hidden pass, exit0/khôngtimeout,20/20HTTP200completed,19gap≥30s/xuyênCLI30.008372/30.000807s/reserve≥633.66s. Estimateđợt0.34091040 USD, cumulativepilotknown **1.10640264 USD**, sáuunpriced/totalchargeunknown. Hash/keyscan/PID/socket/Git/chainrawpostcheck đạt. **Đủ8cặp taskCLI cóít nhất1success**,14inferenceattempts/76upstream, giữallfailure/retry; không 8/8firstattempt hoặcbenchmarkđồngnhấtrevision. P02cả4 cùngsearchr2/paced900; P01khácenv/timing phải tách. Không chạy thêm; `benchmark/PILOT_RESULTS.md`, review `research/artifacts/PACED-900-COMPLETE-REVIEW-20261109-01/validation.json`.

| Trục | Câu hỏi |
| --- | --- |
| Kiến trúc | Entry point, process, client/server, persistence và lifecycle? |
| Agent loop | Nhận prompt, gọi model, tool dispatch, cập nhật history, tiếp tục/dừng thế nào? |
| Tool | Schema, registry, lựa chọn tool, concurrency, kết quả và lỗi? |
| Permission | Load config, rule precedence, hỏi quyền, sandbox và giới hạn thực thi? |
| Context | History, token budget, truncate/compact, resume và instructions? |
| Mở rộng | Plugin/extension, hooks, MCP, custom tools và API/SDK? |

Điểm bắt đầu đọc, chưa phải kết luận về implementation:

- OpenCode v1: `../opencode-v1/packages/opencode/src` và các package liên quan.
- OpenCode v2: `../opencode-v2/packages/{core,server,protocol,client,sdk,plugin,tui}`.
- Pi: `../pi/packages/{agent,coding-agent,ai,mcp}`.
- Codex: `../codex/codex-rs/{cli,core,tools,execpolicy,sandboxing,app-server,plugin}`.

- [x] Mỗi trục có evidence source first-pass cho ba tool trong REPORT3.1–3.6; chưa phải audit đầy đủ mọi implementation branch hoặc runtime demo.
- [ ] Mỗi nhận định có commit, file, dòng/symbol, permalink và giới hạn kết luận.
- [x] Phân biệt permission policy/tool hook/approval với OS confinement; chưa chứng minh native security tương đương giữa tool/OS.
- [ ] Chỉ rõ nhánh code thực sự được bật trong cấu hình thử nghiệm.
- [ ] Ghi cả trường hợp phủ định/giới hạn và phạm vi tìm kiếm; không suy ra không hỗ trợ chỉ từ việc chưa tìm thấy symbol.

Đầu ra: `research/evidence.csv`.

Điều kiện hoàn thành: sáu trục có evidence cho ba tool; các nhận định v1/v2 có evidence riêng. Mỗi kết luận nêu trạng thái `source-confirmed`, `runtime-confirmed`, `both` hoặc `unverified` và không vượt quá phạm vi bằng chứng.

## 3. Cài và kiểm chứng OpenCode v1/v2 song song

- [x] Xác định cách gọi riêng từng phiên bản, không ghi đè binary hiện có. Đã tải/checksum và chạy metadata từ payload riêng; xem `demos/PREPARATION.md`.
- [ ] Xác minh cơ chế cách ly config, data, plugin, service và endpoint.
- [ ] Smoke test: khởi động, tạo session, prompt, tool call, mở lại session.
- [ ] Truy vết v2 service discovery/lifecycle và client connection.
- [ ] Kiểm chứng TUI, desktop, web: PID, endpoint, session quan sát được.
- [ ] Phân biệt shared-service, standalone và dev mode.
- [x] Trước khi chạy, đọc source tối thiểu để xác minh cách gọi, config/data/service isolation; không chờ đến sau pilot mới xác minh. Đã có phương án source-only tại `research/isolation.md`; runtime và các root còn thiếu vẫn chưa nghiệm thu.
- [x] Lập hướng dẫn cách ly cho cả Pi và Codex trước khi smoke test bốn cấu hình. Đã có profile metadata offline và witness; profile dùng model/network còn phải chốt.
- [ ] Xác minh cấu hình thử không dùng config, session, plugin directory hoặc service của môi trường thật bằng đường dẫn hiệu lực và bằng chứng quan sát phù hợp.
- [ ] Ghi PID, endpoint, thư mục dữ liệu và tài nguyên do từng lần thử tạo ra; không suy ra cách ly chỉ từ config mẫu.
- [ ] Có hướng dẫn dừng/dọn theo đúng PID và đường dẫn đã ghi nhận, chỉ tác động tài nguyên thử nghiệm; không dừng service đang dùng hoặc xóa rộng.

Tiến độ bổ sung: `demos/OFFLINE_API.md` đã kiểm chứng HTTP auth, SSE trước create, tạo/read/list session rỗng và metadata qua process restart cho v1/v2 trong sandbox offline. V2 stdin EOF exit 0; v1 dừng bằng SIGTERM. Chưa có prompt/tool/resume hội thoại, shared-service hoặc client GUI; không nghiệm thu smoke đầy đủ từ lượt này.

Đầu ra: hướng dẫn tái tạo, log đã lọc nhạy cảm, bằng chứng source/runtime. Nếu không chạy được một client, nêu rõ thay vì tuyên bố đã kiểm chứng toàn bộ.

Điều kiện sẵn sàng pilot: cả bốn cấu hình chạy smoke test thành công trong môi trường cách ly, có log và thu được trạng thái kết thúc. Nếu một cấu hình bị chặn, ghi blocker và điều chỉnh kế hoạch công khai; không âm thầm bỏ cấu hình khỏi so sánh.

## 4. Demo bắt buộc

### API/SDK

- [x] Kết nối đúng endpoint/authentication cho HTTP v1/v2 trong sandbox offline; xem `demos/OFFLINE_API.md`. Client/embedded SDK còn chưa chạy.
- [ ] Đăng ký event trước khi gửi prompt để tránh mất event đầu.
- [ ] Tạo session, gửi prompt, nhận event, xác định kết thúc/lỗi.
- [ ] Xuất transcript, thời gian và usage nếu có.
- [x] Đối chiếu source contract v1/v2 và phân biệt HTTP/Client/embedded SDK trong REPORT4.2; Client/SDK runtime prompt còn pending.
- [ ] Kiểm tra lỗi xác thực nếu endpoint có auth, timeout, mất kết nối và hủy; ghi rõ trạng thái cuối cùng quan sát được và trường hợp ngoài phạm vi.

### Permission

- [x] Đọc source schema/evaluator và configured/saved-rule layers của v1/v2; defaults source khác fallbackask và khác effective runtime policy.
- [ ] Kiểm tra allow, ask-approve, ask-reject, deny.
- [ ] Kiểm tra các rule chồng lấn và thứ tự ưu tiên.
- [ ] Kiểm tra khả năng đọc config v1 ở v2 và thay đổi default liên quan.
- [ ] Kiểm tra hành vi khi không có rule khớp và phạm vi/thời hạn áp dụng quyết định approve/reject theo implementation.

### Subagent và shell nền

- [ ] Kiểm tra start, trả quyền điều khiển, progress/result.
- [ ] Parent tiếp tục làm việc khi task nền còn chạy.
- [ ] Kiểm tra lỗi và hủy bằng tác vụ ngắn, an toàn.
- [ ] Ghi rõ persistence/restart semantics nếu thực sự kiểm chứng.
- [x] Đối chiếu source background subagent v1/v2 và shell schema ở REPORT4.4; runtime comparison vẫn pending.
- [ ] Ghi hành vi khi parent kết thúc hoặc client ngắt kết nối; chỉ kết luận persistence/restart semantics nếu có phép thử riêng.

### Port plugin

- [ ] Tạo plugin v1 tối giản với custom tool có output xác định.
- [ ] Xác nhận chạy được trên v1.
- [ ] Thử nạp trên v2 trong môi trường riêng và ghi nhận lỗi/khả năng tương thích.
- [ ] Port sang v2, giữ cùng hành vi.
- [ ] Lưu before/after, diff, thay đổi contract và hướng dẫn chạy.
- [ ] Phân loại lỗi do contract/API, dependency, runtime hoặc config; không coi mọi lỗi nạp plugin là bằng chứng bất tương thích API.

Đầu ra: scripts/config/log tại `demos/`, không chứa credential.

Điều kiện hoàn thành: mỗi demo có version/config, lệnh chạy, kết quả mong đợi/thực tế, evidence IDs và giới hạn. Trường hợp không chạy được hoặc chưa thử phải được ghi rõ, không đánh dấu đạt.

## 5. Benchmark

**Batch thật đã kết thúc, dừng1/48slot:** R-0039/D48-001/v1/B01 **infra_error/pending_review**, CLIexit1khôngwalltimeout278237ms;5upstream/4HTTP200completedcóusage, request5TimeoutErrortrướcHTTP/terminal/usage. Local503latch chặnnativeretrykhôngupstream503;4gap≥30s/reserve≥734.67s. Knownbatch0.06853344USD/1unpriced/totalchargeunknown,47not_run; không retry/resume/topup. Snapshot chỉanswer.json/scope/publicpass/rawrubric9/10;5giátrịđúngnhưngextraALIASESevidence bịhiddenallowlistloại, **rubricdesignpendingreview**, khôngsửa sealedgrader/rawscore/CSVstatusposthoc. Audit `research/artifacts/BENCH48-REVIEW-20261110-01/validation.json`, [kết quả](benchmark/suite48/BENCHMARK_RESULTS.md). Hash/binary/fixture/resource/Git/PID/socket/secretpatternđạt;48IDsđãreservegiữnot_run, nextR87/C188khôngreset. paidhold; bướcđềxuấtreviewrubricoffline trướcquyếtđịnhcontinuation/retry.

**Batch trả phí đã khởi chạy background** `sh_1c371f7d3001LwkOGnq3vuFvDB`: guarded `benchmark/batch48.py --paid` với approval LAUNCH48-20261110-01, artifact BENCH48-20261110-01/candidate03. Đang chờ hoàn tất hoặc stop; không poll, không khởi chạy batch/retry khác và không sửa source/protocol/fixture/config đang pin. Reserve R/C do runner thực hiện dưới lock, không cập nhật registry thủ công khi đang chạy. Sẽ audit raw/ledger/grade/cost/pacing/cleanup và báo mọi not_run sau khi kết thúc.

**Người dùng xác nhận chạy thật2026-11-10:** "ok xác nhận" sau câu hỏi rõ bắt đầu48lượt trả phí/guard16USD estimate. Approval riêng `benchmark/suite48/approvals/LAUNCH48-20261110-01.json` bind candidate03/protocolR1; template cũ giữdisabled. Prelaunch48input/hash/resource/order/registry/freshR39–86/C140–187/sourceGit gates đạt, không đọc key/gọi provider ở bước kiểm; audit `research/artifacts/BATCH48-LAUNCH-20261110-01/validation.json`. Batch mới `benchmark/suite48/artifacts/BENCH48-20261110-01/`, tách pilot/history unpriced. Chỉ48first-attempt slots, realpacing≥30s/concurrency1/cap900/reserve60/request8/output2048, guard16estimatekhônginvoicecap; providerfailure/missingusage/infra/budget dừng, không auto retry/topup/resume. Chuẩn bị launch, chưa có kết quả benchmark.

**Bộ điều phối/launch candidate2026-11-10:** người dùng đồng ý guard16USD estimate/outer-wall và tiếp tục hoàn thiện offline; **không coi là authorize dispatch**. `benchmark/batch48.py`, `PROTOCOL_48_R1.md` và candidate03 pin48input/order/resource/protocol; offline03 đạt16/16nativecase/40syntheticexchanges/0providerrequests. Có10unit+4flowtest mới, per-slot hash/resource gates, originchungbroker900/watchdog900(real)/90(offline), reservationlock/approvaltrướckey, indexbenchmarkriêng/noautorretry-resume. Lượt01–02/source/candidate cũ giữ nguyên; sửa metadata02 nhầm fieldwatchdog90 thànhbrokerdeadline, actualhandler900khôngđổi. [Chi tiết](benchmark/suite48/BATCH_RUNNER.md). Approvaltemplate03 vẫnfalse, nextR39/C140khôngreserve; chờ xác nhận bắt đầu48paid slots rồi recheckgates.

Nghiệm thu cuối bộ điều phối: **88regression tests pass**, offline03 native16/16accepted; protocol/48input/hash/resource/order/mapping/deadlineverifierđạt. Chạy gatepaidvớitemplatedisabledđãbịreject **trướckey/reserve/artifact**, 0providerrequests. Oldraw/source/syntheticcosttáchriêng, PID/socket/link/patternsecret/Git/frozenverifiersđạt. Audit `research/artifacts/BATCH48-REVIEW-20261110-01/validation.json`; planSHA7d7fe5ed…dbc699a, protocolSHAd3af611d…a70e93. Không cóCSVbenchmarkthật hoặcpaidR/Callocation; candidateprotocolfrozen/guard16đồngýkhôngbậtlaunch. **Chỉ còn explicitstart48paid-slots approval**, sau đórecheckgates trước dispatch; nếu nguồn/resource/registryđổi phải re-plan/review.

**Native preflight tiếp theo2026-11-10:** adapter riêng đã đạt **16/16 B-01–B-04×4CLI** trong `benchmark/suite48/artifacts/NATIVE48-20261110-02/`,40synthetic exchanges/0provider requests. Lượt01 giữ v1pass/Codexmockfail do thiếu usage.total_tokens,14not_run; đã sửa mock+regression, không tool/provider/task failure. Native configs/profile/broker guarded giữ nguyên, OF48namespace không reserve R/C, nguồn/response/usage đều giả cónhãn. Guards có9unit tests; virtualpacing không phải30s live, outer90s watchdog không đổi benchmark900s. [Phạm vi/ranh giới duration và gate tiếp](benchmark/suite48/NATIVE_PREFLIGHT.md). **Còn final protocol/budget/paid orchestrator**, không inference mới.

Audit native cuối: **74regression tests pass**, native16/16cohort02verify/frozenpilot/fixtureseal/orderđạt, tamperedartifact/unexpectedfile bịtừchối; toànlịchsử18nativeattempts=17pass+1mockfail/44syntheticexchanges/0providerrequests. CleanupPID/socket, raw/sourcehistory, links/patternsecret/Gitđạt; hostsnapshotghi riêng và phải rechecklaunch. `research/artifacts/NATIVE48-REVIEW-20261110-01/validation.json`. Giữpaidfalse/budgetnull/nextR39C140khôngreserve. Đề xuấtprimarydurationouterlauncher/nativeclocksecondarycầnduyệt; saufinalprotocol/budgetapproval mới thêm/kiểm paidorchestrationoffline trước dispatch.

**Cập nhật2026-11-10:** đã viết B-01–B-04 fixture/public/hidden/oracle và grader/sandbox offline; seal `benchmark/suite48/artifacts/PREP48-20261110-02/preparation.json` đạt **44variant checks** (6positive,4baseline-negative,34mutant-negative),7regression tests mới. Refactor chấp nhận module imports/from-import aliases/handler registry. Lượt đầu40checks và source được giữ, rev2 bổ sung fairness/schema. [Implementation](benchmark/suite48/IMPLEMENTATION.md). **Native CLI runner adapter còn pending**, không đồng nhất trusted offline writers với live/native acceptance; chưa budget/protocol/paid approval, không API mới. Các ghi nhận draft ngày09 bên dưới giữ theo thời điểm lịch sử.

Audit cuối bước fixture: **65regression tests pass +44variant checks đạt kỳ vọng**; seal27input/388artifact files, reject tamperedgrader/unexpectedartifact, old40-check source/raw preserved. Frozen pilot và draftorder/dự toán verify pass, links/secret-pattern/Git sạch, không đọc key/gọi nativeCLI/provider; R/Cnext39/140 không đổi. `research/artifacts/SUITE48-REVIEW-20261110-01/validation.json`. Bước tiếp theo là nativeCLIrunner adapter/preflight offline rồi final protocol/budget approval, chưa launch48slot.

Pilot đã hoàn tất coverage tám cặp qua14inference attempts/76upstream; reviewed8success/3timeout/3infra_error,1launch-error không inference. CSV legacy4 + search-r2 10 giữ nguyên, không phải8/8first-attempt hoặc một nhóm đồng nhất. Known estimate1.10640264USD,6requestunpriced/totalchargeunknown. Đã tổng kết và khóa baseline offline `search-r2 + paced-900`, fixtureP-01/P-02v2/seal, native configs/pins/hashes; xem `benchmark/BASELINE.md`. **Benchmark chính thức vẫn pending**, không gọi API mới; diagnostic/smoke không nhập pilot.

- [x] Tổng hợp offline hai CSV/raw với review override R-0009 và giữ failure/retry/launch-error.
- [x] Đóng băng baseline pilot và validator/hash/config/fixture/policy; không đồng nghĩa duyệt toàn protocol benchmark.
- [x] Người dùng chọn hướng48slot để chuẩn bị offline; soạn B-01hiểucode/B-02bug/B-03feature/B-04refactor, prompts/rubric/acceptance matrix, order48slot và dự toán. `benchmark/PROTOCOL_48_DRAFT.md`, `benchmark/suite48/README.md`. **Chưa có fixture/tests/seal cho B-01–B-04**, chưa budget/protocol approval/inference; không dùng order dự kiến thành run results.

Draft48 đã kiểm offline **58 regression tests pass** (gồm5testplanner; không phải nghiệm thu fixture mới), verify draft order/dự toán và frozen pilot đạt; links/secret-pattern scan/source Git postcheck đạt. Audit `research/artifacts/DRAFT48-REVIEW-20261109-01/validation.json`. Dự toán1×/2×/3× theo cohortP02 là5.00059584/10.00119168/15.00178752USD; **đề xuất16USD estimate chưa duyệt**, không invoice cap/không bảo đảm đủ48. R/Cnext39/140 giữ nguyên, không reserve inference IDs hoặc gọi API. Tiếp theo viết/nghiệm thu fixture+grader/runner offline rồi xin duyệt budget/protocollaunch.

Nghiệm thu offline: **53 tests pass**, freeze verifier kiểm201input hashes/audited raw/source snapshots/fixture/dependency/binary và output đạt; links và scan secret theo pattern đạt, bốn repo source vẫn sạch. Audit `research/artifacts/PILOT-FREEZE-REVIEW-20261109-01/validation.json`. Không đọc key hoặc gọi provider/CLI trong bước tổng kết. `REPORT.md` có tổng kết hiện tại, nhật ký cũ giữ trong khối lịch sử và `PILOT_RESULTS.md`.

- [x] Viết/nghiệm thu fixture và acceptance tests B-01–B-04 offline trước khi chạy agent; final task/protocol approval vẫn pending.
- [x] Pilot phủ2task×4CLI có ít nhất1success qua14inference attempts; không phải8lượt đồng nhất/first-attempt.
- [ ] Chốt model/provider, timeout, permissions, mạng và cache policy.
- Phương án72lượt không chọn ở giai đoạn này.
- [x] Chọn thiết kế4task×4CLI×3lần=48slot để soạn offline.
- [ ] Nghiệm thu fixture/tests/grader/runner và duyệt protocol/budget trước48slot trả phí.
- [ ] Reset fixture/session giữa các lượt, không dùng lại lời giải.
- [ ] Xáo trộn thứ tự tool và lưu thứ tự thực tế.
- [ ] Thu success, duration, input/output/cache/reasoning token nếu có.
- [ ] Lưu số tool call, hỏi quyền, lỗi và mọi lần thử lại.
- [ ] Tách benchmark chung khỏi demo tính năng đặc thù.
- [ ] Chốt rubric theo nhóm task: task hiểu code có tiêu chí chấm riêng; task sửa code dùng acceptance tests và ràng buộc hành vi.
- [ ] Chốt ranh giới đo: startup, chờ permission, retry provider và chạy acceptance tests có nằm trong duration hay được đo riêng.
- [ ] Chốt timeout, giới hạn chi phí/token nếu hỗ trợ và tài nguyên máy; ghi khác biệt không thể áp dụng đồng đều.
- [ ] Xác minh model ID/revision nếu có, endpoint và generation/reasoning settings; cùng tên model không mặc định là cấu hình tương đương.
- [ ] Đối chiếu semantics usage của từng tool/provider; không gộp token không tương đương thành số liệu có vẻ đồng nhất.
- [ ] Chốt tiêu chí infra error/exclusion, số retry tối đa và cách liên kết/báo cáo mọi lượt gốc và retry.
- [ ] Lưu seed/thuật toán xáo trộn hoặc danh sách thứ tự chạy đã chốt để tái tạo.

Đầu ra: protocol, task manifest, raw logs và bảng kết quả. Xem `benchmark/PROTOCOL.md`.

Điều kiện đóng băng protocol: pilot hoàn tất hoặc blocker đã có quyết định xử lý; fixture, acceptance tests/rubric, model/settings, ngân sách, số lượt, cách đo và quy tắc lỗi đã được người phụ trách duyệt và ghi ngày. Pilot không gộp vào kết quả chính thức. Thay đổi sau đóng băng phải có revision và quyết định chạy lại/tách nhóm, không trộn âm thầm.

## 6. Viết báo cáo và nghiệm thu

- [ ] Viết theo khung `REPORT.md`.
- [ ] Mọi nhận định kỹ thuật liên kết tới evidence cố định theo commit.
- [ ] Mọi số liệu có run ID và log gốc.
- [ ] Báo cáo success numerator/denominator; median và độ phân tán thời gian/token.
- [ ] Phân biệt kết quả measured, source-only và chưa kiểm chứng.
- [ ] Nêu yếu tố gây nhiễu: model, provider, default prompt, caching, mạng và phiên bản.
- [ ] Script/demo có hướng dẫn chạy lại; không lộ secret hoặc dữ liệu thật.
- [ ] Với kết luận cần bằng chứng trực quan (TUI/desktop/web hoặc tương tác permission/background), chụp màn hình từ lần chạy thật khi phù hợp; ghi version, demo/run ID, thời điểm và ngữ cảnh. Không dùng ảnh dựng thay screenshot, không coi ảnh thay thế log/source.
- [ ] Kết luận theo use case, không xếp hạng tuyệt đối từ mẫu nhỏ.
- [ ] Kiểm tra secret và dữ liệu cá nhân trước công bố, gồm log, transcript, patch, URL/endpoint và đường dẫn chứa thông tin riêng; không đưa raw log chưa duyệt vào artifact chia sẻ.
- [ ] Kiểm tra permalink, evidence/run references và tính nhất quán giữa bảng kết quả, kết luận và dữ liệu gốc.

Điều kiện nghiệm thu: mọi nhận định kỹ thuật truy được về evidence; mọi số liệu đo truy được về run/artifact; các mục chưa kiểm chứng được ghi rõ; demo có hướng dẫn tái tạo và artifact công bố đã được duyệt nhạy cảm.

## 7. Quy ước artifact và truy vết

- [ ] Evidence dùng ID ổn định `E-0001`, run dùng `R-0001`, config dùng `C-0001`; ID đã cấp không đổi hoặc tái sử dụng cho đối tượng khác.
- [ ] Mỗi run có metadata chứa tool/version/full SHA, task/fixture version, config ID, model/settings, thời điểm, thứ tự chạy, trạng thái và lý do loại/retry nếu có.
- [ ] Raw logs đặt trong `benchmark/raw/<run_id>/` hoặc `demos/raw/<demo_id>/`; chỉ mục chia sẻ trỏ tới artifact đã lọc trong `benchmark/artifacts/<run_id>/` hoặc `demos/artifacts/<demo_id>/`. Ghi rõ khi raw chỉ được giữ cục bộ.
- [ ] Lưu bản sao an toàn hoặc checksum kèm cách tìm lại bản gốc của prompt, config, fixture và script. Không lưu secret chỉ để đạt khả năng tái tạo.
- [ ] Ghi revision protocol và liên kết `retry_of`; không ghi đè artifact của lượt trước khi chạy lại.

## Thứ tự ưu tiên

Kiểm kê/chốt phiên bản → đọc source tối thiểu để xác minh cách chạy và cách ly → smoke test cả bốn → chuẩn bị task/acceptance tests và protocol pilot → pilot → nghiên cứu source và demo đầy đủ → đóng băng protocol → benchmark chính thức → hoàn thiện và nghiệm thu báo cáo.

Các điểm cần quyết định trước khi chạy: model/provider và ngân sách; fixture; có chạy desktop/web đầy đủ không; quy mô 48 hay 72 lượt. Không cần các quyết định này để bắt đầu đọc source.
