# Trạng thái kết quả hiện tại

> **Tổng kết offline đã khóa:** [BASELINE.md](BASELINE.md), [bảng mọi attempt và cohort P-02](artifacts/PILOT-FREEZE-20261109-01/SUMMARY.md), [ledger](artifacts/PILOT-FREEZE-20261109-01/summary.json). Phần dưới giữ lịch sử theo từng thời điểm, không coi các câu “chưa chạy” lịch sử là trạng thái hiện tại. Benchmark chính thức vẫn pending, không inference mới.

## Ba lượt cuối đã hoàn tất — tất cả đạt

Đợt [`PACED-900-COMPLETE-20261109-01/result.json`](artifacts/PACED-900-COMPLETE-20261109-01/result.json), protocol [`PILOT_PACED_900_COMPLETE.md`](PILOT_PACED_900_COMPLETE.md), `2026-11-09T15:01:01Z`–`15:14:13Z`, **3/3 success/valid**, không timeout:

| Run | CLI / task | Requests | Duration gồm pacing | Estimate USD |
| --- | --- | ---: | ---: | ---: |
| R-0036 | v1 / P-02 | 7 | 223735ms | 0.10021872 |
| R-0037 | Codex / P-02 | 6 | 286901ms | 0.10290408 |
| R-0038 | Pi / P-02 | 7 | 278457ms | 0.13778760 |
| Tổng đợt | | **20** | | **0.34091040** |

Cả ba chỉ sửa `scheduler.py`, **scope/public/hidden đều pass**, CLI exit0; 20/20 HTTP200/response.completed đúng model field/usage đủ. **19/19 gap≥30s**, xuyên CLI30.008372s/30.000807s, reserve tại dispatch≥633.661532s. Không providerfailure/timingstop/localblocked. Mọi lượt hoàn tất dưới300s dù policy900, không quy thành công chỉ cho tăngcap hoặc hứa provider ổn định lâu dài.

Cumulative known estimate của toàn **pilot/lineage** là **1.10640264 USD**, gồm14 inference attempts/76 upstream requests được lưu; **sáu request unpriced**, cumulative total/measured charge unknown. Đây không gồm smoke/diagnostic ngoài pilot và không phải số tiền đã đối soát. Known guard3USD không chạm. Hash/source/protocol/manifest/pricing/seal/chain/binary, keyscan/PID/socket/Git postcheck đạt; review [`../research/artifacts/PACED-900-COMPLETE-REVIEW-20261109-01/validation.json`](../research/artifacts/PACED-900-COMPLETE-REVIEW-20261109-01/validation.json).

### Phủ đủ tám cặp task/CLI, không phải success rate8/8

Mỗi cặp hiện có ít nhất một lượt đạt; **bảng dưới chọn successful coverage để điều hướng**, không xóa/mặc nhiên loại các retry/failure nằm trong các phần sau hoặc tính completion rate của một nhóm đồng nhất:

| Task | CLI | Lượt đạt | Environment | Timing |
| --- | --- | --- | --- | --- |
| P-01 | Pi | [R-0017](artifacts/PILOT-SOL-RETRY-20261106-01/R-0017/result.json) | legacy | cap300 |
| P-01 | Codex | [R-0018](artifacts/PILOT-SOL-CONTINUE-20261106-01/R-0018/result.json) | legacy | cap300 |
| P-01 | v2 | [R-0028](artifacts/SEARCH-R2-RETRY-20261109-03/R-0028/result.json) | search-r2 | cap300 |
| P-01 | v1 | [R-0029](artifacts/SEARCH-R2-FINISH-20261109-01/R-0029/result.json) | search-r2 | cap300 |
| P-02 | v2 | [R-0035](artifacts/PACED-900-RECHECK-20261109-01/R-0035/result.json) | search-r2 | paced-900 |
| P-02 | v1 | [R-0036](artifacts/PACED-900-COMPLETE-20261109-01/R-0036/result.json) | search-r2 | paced-900 |
| P-02 | Codex | [R-0037](artifacts/PACED-900-COMPLETE-20261109-01/R-0037/result.json) | search-r2 | paced-900 |
| P-02 | Pi | [R-0038](artifacts/PACED-900-COMPLETE-20261109-01/R-0038/result.json) | search-r2 | paced-900 |

**Không còn slot task/CLI chờ chạy trong phạm vi pilot đã yêu cầu**, nhưng không gọi đây là8/8 first-attempt success, benchmark chính thức hoặc so sánh tám lượt cùng environment/timing. P-02 bốn CLI cùngsearch-r2/paced900, native prompts/tools/reasoning vẫn khác; mẫu một lần/tool không đủ xếp hạng. Bước tiếp theo là review/chốt protocol benchmark nếu được yêu cầu, không tự chạy thêm.

## paced-900 nghiệm thu — R-0035 v2/P-02 đạt

**Success/valid**, chỉ `scheduler.py` đổi, **scope/public/hidden đều pass** (1 public/9 hidden tests). CLI exit0, không timeout, duration **234718ms ≈3phút55giây** gồm pacing. Protocol [`PILOT_PACED_900_RECHECK.md`](PILOT_PACED_900_RECHECK.md), search-r2/paced-900/sessionC-0136/nhóm riêng `search-r2:paced-900:recheck`; không đổi timeout cap300 cũ thành success.

- **7/7 HTTP200/response.completed**, đúng model fieldsol/usage đủ. Sáu gap≥30.001173s; minremaining tại dispatch671.370163s, reserve60s được giữ. Không providerfailure/timingstop/localblocked ở lượt này.
- Lượt này hoàn tất **dưới300s** dù cap mới900s: **không chứng minh riêng tăng timeout gây thành công**, không loại yếu tố latency/provider/agent workflow. Guard reserve sátdeadline vẫn chỉ được kích hoạt trong kiểm thử offline, chưa stress live.
- Estimate lượt **0.07580592 USD**, cumulative known **0.76549224 USD**. **Sáu request lịch sử unpriced**, cumulative total/charge unknown. Không tăng guard3USD, không coi phí thiếu0.
- Hash source/protocol/manifest/pricing/seal/binary/lineage, keyscan/PID/socket/Git postcheck đạt. Raw [`PACED-900-RECHECK-20261109-01/result.json`](artifacts/PACED-900-RECHECK-20261109-01/result.json), review [`../research/artifacts/PACED-900-RECHECK-REVIEW-20261109-01/validation.json`](../research/artifacts/PACED-900-RECHECK-REVIEW-20261109-01/validation.json).

**Ba slot P02/v1,Codex,Pi chưa chạy.** Một v2 acceptance success không phải pilot đồng nhất8slot hoặc bằng chứng provider ổn định tổng quát; tiếp tục phải giữ revision chung/lineage/budget và không gộp các nhóm legacy/search-r2/cap300/cap900 như cùng điều kiện.

> Sau R-0034, người dùng đồng ý sửa timing: **paced-900** chung bốn CLI đã đạt48 tests/preflight offline4/4; cap900s gồm pacing, reserve60s trước dispatch, không tăng request/output/USD guard. Chưa inference mới; các kết quả dưới vẫn thuộc cap300 và không đổi trạng thái. [`../research/PACED_900_RESULTS.md`](../research/PACED_900_RESULTS.md).

## search-r2 P-02 retry — R-0034 lặp timeout, snapshot vẫn pass

Single retry_of R-0030 theo yêu cầu người dùng, C-0123/session mới, protocol [`PILOT_SEARCH_R2_P02_RETRY.md`](PILOT_SEARCH_R2_P02_RETRY.md); **timeout/valid**, duration300041ms gồm pacing. Chỉ `scheduler.py` đổi và **scope/public/hidden snapshot đều pass** (1 public/9 hidden tests), nhưng CLI chưa hoàn tất nên không nâng thành success.

- **7 upstream request**, sáu HTTP200/completed, request7 HTTP200 nhưng không terminal/usage và TimeoutError tại giới hạn lượt. Request cuối bắt đầu **295.647861 giây** vào cap300s. Không có bằng chứng explicit provider overload.
- **6/6 gap≥30 giây**, tối thiểu180s trong cap300s dành cho pacing. Native **glob completed thành công trong lượt model thật**; lỗi rg đã không tái hiện ở call này. Agent thiếu `python` và `pytest`, sau đó tự chuyển `python3`/`unittest` với test command exit0; không cài alias/package.
- Known estimate lượt **0.07098192 USD**, cumulative known **0.68968632 USD**. Nay **sáu request lịch sử unpriced**, total/charge unknown; guard thiếu usage dừng, không coi request cuối miễn phí.
- Raw timeoutR30 giữ nguyên, không retry để che failure; **ba slot P02/v1,Codex,Pi vẫn not_run**. Không tự retry tiếp/tăng cap/mở slot.
- Hash source/protocol/manifest/pricing/seal/binary/lineage, keyscan/PID/socket/source Git postcheck đạt. Artifact [`SEARCH-R2-P02-RETRY-20261109-01/result.json`](artifacts/SEARCH-R2-P02-RETRY-20261109-01/result.json), review [`../research/artifacts/SEARCH-R2-P02-RETRY-REVIEW-20261109-01/validation.json`](../research/artifacts/SEARCH-R2-P02-RETRY-REVIEW-20261109-01/validation.json).

Hai lượt P02/v2 đều snapshot đúng nhưng thiếu completion trong cùng cap; không nên lặp lại cùng điều kiện chỉ để chọn một success. Nếu đổi chính sách timeout/pacing/accounting ở đợt sau phải đóng băng revision mới, áp nhất quán cho nhóm so sánh và giữ kết quả cap300s cũ. Chưa có bằng chứng để quy tất cả timeout cho mạng/provider hoặc chất lượng giải task.

## search-r2 finish — dừng 2/5, snapshot P-02 đạt nhưng timeout

Đợt [`SEARCH-R2-FINISH-20261109-01/result.json`](artifacts/SEARCH-R2-FINISH-20261109-01/result.json), protocol [`PILOT_SEARCH_R2_FINISH.md`](PILOT_SEARCH_R2_FINISH.md), `2026-11-09T14:11:16Z`–`14:20:03Z`:

| Run | Task/CLI | Kết quả CLI | Scope/public/hidden snapshot | Known estimate USD |
| --- | --- | --- | --- | ---: |
| R-0029 | P-01/v1 | **success/valid**, exit0, 224527ms | Pass, chỉ intervals.py đổi | 0.08659104 |
| R-0030 | P-02/v2 | **timeout/valid**, 300039ms | **Pass**, chỉ scheduler.py đổi | 0.06105024 |

- V1 có7/7 HTTP200/completed, usage đủ. V2 có6 completed và request7 HTTP200 nhưng thiếu terminal/usage, broker BrokenPipeError gần supervisor deadline. Request đó bắt đầu **299.393594 giây** vào lượt300s gồm pacing, còn dưới1s; không kết luận provider overload từ lỗi này.
- V2 đã tạo snapshot vượt toàn bộ grader, nhưng CLI chưa kết thúc trong cap nên **giữ timeout, không nâng thành success** hoặc gọi là sửa sai. Không error tool được ghi nhận ở hai lượt này; không có lỗi ripgrep trong log tool đã đọc.
- **13/13 gap≥30s**, xuyên v1→v2 **30.000826s**. Pacing được tính trong timeout theo protocol, không loại bỏ sau chạy để so tốc độ.
- Batch dừng `usage_missing`/latch, **ba slot P-02/v1, Codex, Pi còn not_run**. Không tự retry v2, mở slot hoặc tăng cap.
- Known estimate đợt **0.14764128 USD**, cumulative known **0.61870440 USD**; **năm request lịch sử unpriced**, tổng/charge unknown. Guard không chạm known3USD; vẫn dừng vì usage thiếu, không coi request cuối miễn phí.
- Hash source/protocol/manifest/pricing/seal/chain/binary, keyscan/PID/socket/Git postcheck đạt. Review [`../research/artifacts/SEARCH-R2-FINISH-REVIEW-20261109-01/validation.json`](../research/artifacts/SEARCH-R2-FINISH-REVIEW-20261109-01/validation.json). Raw/CSV riêng r2 và mọi failure cũ giữ nguyên, không gộp legacy+r2 như đồng nhất.

Trước bước tiếp theo cần quyết định xử lý ba slot còn lại và timeout riêng. Có thể review chính sách không mở request khi còn quá ít deadline cho revision tương lai; **không sửa ngược cap/protocol hoặc xóa timeout hiện tại**.

## search-r2 — R-0028 đạt sau khôi phục launch

**OpenCode v2/P-01 trên search-r2: success/valid**, `2026-11-09T14:03:02Z`–`14:06:40Z`, agent duration **217097ms** gồm pacing; không timeout. Lượt R-0027 trước đó lỗi tạo parent runtime **trước broker/CLI, 0 upstream**, giữ artifact chỉ protocol và IDreserved. R-0028/C-0117 khôi phục lời gọi đã yêu cầu, lineage inference retry_of R-0026; protocol [`PILOT_SEARCH_R2_RETRY_03.md`](PILOT_SEARCH_R2_RETRY_03.md).

- **7/7 HTTP200/response.completed** đúng model field sol; usage đủ. Sáu gap≥30 giây, min **30.000791s**. Không provider failure/localblocked trong lượt này; chưa suy provider ổn định lâu dài.
- Chỉ sửa `intervals.py`, **scope/public/hidden đều pass**, CLI exit0/không error event. Agent gọi read/patch/shell; `python` thiếu làm hai lệnh exit127, sau đó tự chuyển `python3` và test thành công. Không tạo alias hoặc đổi Python policy.
- Không gọi glob/grep trong lượt này: **task inference trên r2 đã đạt**, còn xác minh trực tiếp native glob/grep với dependency r2 vẫn dựa trên preflight offline, không tuyên bố cả hai đã được dùng live.
- Estimate lượt **0.06716400 USD**, cumulative known pilot/lineage **0.47106312 USD**. **Bốn request cũ vẫn unpriced**, cumulative total/charge unknown, không biến lượt launch chưa gửi thành generation miễn phí hoặc giả missingusage=0.
- Hash source/protocol/manifest/pricing/seal/binary/lineage, key scan/PID/socket/source Git postcheck đạt. Artifact [`SEARCH-R2-RETRY-20261109-03/result.json`](artifacts/SEARCH-R2-RETRY-20261109-03/result.json), review [`../research/artifacts/SEARCH-R2-RETRY-REVIEW-20261109-03/validation.json`](../research/artifacts/SEARCH-R2-RETRY-REVIEW-20261109-03/validation.json).

R2 CSV riêng hiện có R-0025/R-0026 infra_error và R-0028 success; không xóa lỗi hoặc gộp legacy+r2 như cùng môi trường. **Chưa mở năm slot khác/chưa có pilot tám slot cùng revision**; kết quả không chứng minh thiếu rg là toàn bộ nguyên nhân timeout trước.

> Network check sau R-0026: host DNS/TCP/TLS/public HTTP tới provider hoạt động, GET/models không auth401 và root200, dưới1s. Không có bằng chứng chặn mạng cơ bản tại thời điểm probe; authenticated Responses/model backend vẫn unverified. Không inference mới: [`../research/PROVIDER_NETWORK.md`](../research/PROVIDER_NETWORK.md).

## search-r2 retry — R-0026 vẫn infra_error trước task

Single retry do người dùng yêu cầu, retry_of R-0025, C-0115/session mới, **cùng search-r2/settings/cap/pacing**, protocol [`PILOT_SEARCH_R2_RETRY.md`](PILOT_SEARCH_R2_RETRY.md). Đợt `2026-11-09T03:02:22Z`–`03:04:32Z` kết thúc **infra_error/pending_review**, không supervisor timeout300s; chỉ **1 upstream request** timeout trước HTTP status/terminal/usage, request không có tool schema, chưa đổi source/chạy task.

Provider-failure latch chặn **11 lần gọi tiếp local**, không gửi thêm upstream. HTTP503 trong CLI vẫn là local stop response, không chứng minh provider overload/503. Hai lần search-r2 liên tiếp cùng dạng lỗi trước tool execution; chưa xác định gateway/provider/network là root cause, không kết luận môi trường rg lỗi hoặc tool giải sai. Không nên retry mù tiếp; cần chẩn đoán đường kết nối/timeout có kiểm soát trước lượt trả phí khác.

Lượt mới chưa biết phí; cumulative known estimate vẫn **0.40389912 USD**, **bốn request unpriced**, total/charge unknown. Raw subtotal0 là tổng rỗng, không miễn phí. R2 CSV riêng hiện có R-0025/R-0026, legacy giữ nguyên. Không tự mở năm slot còn lại.

Artifact [`SEARCH-R2-RETRY-20261109-01/result.json`](artifacts/SEARCH-R2-RETRY-20261109-01/result.json), review [`../research/artifacts/SEARCH-R2-RETRY-REVIEW-20261109-01/validation.json`](../research/artifacts/SEARCH-R2-RETRY-REVIEW-20261109-01/validation.json). Source/protocol/manifest/pricing/seal/binary/lineage hashes, key scan/PID/socket/source Git postcheck đạt; dependency/preflight offline vẫn được giữ, không suy model đã nghiệm thu.

## search-r2 recheck — R-0025 infra_error, chưa tới task

Lượt riêng v2/P-01/C-0114, protocol [`PILOT_SEARCH_R2_RECHECK.md`](PILOT_SEARCH_R2_RECHECK.md), `2026-11-09T02:53:40Z`–`02:55:58Z`: **infra_error/pending_review**, exit1, không supervisor timeout300s. Artifact [`SEARCH-R2-RECHECK-20261109-01/result.json`](artifacts/SEARCH-R2-RECHECK-20261109-01/result.json), CSV riêng `runs-search-r2.csv`, không gộp legacy.

- **Chỉ một upstream request**: broker ghi TimeoutError trước khi nhận HTTP status/terminal/usage. Request không có tool schema; không có event tool execution, chưa đổi file, **chưa tới bước kiểm chứng task/glob**. Không kết luận môi trường search-r2 lỗi hoặc v2 giải sai.
- Latch provider_failure dừng đợt; **11 request tiếp theo bị chặn local**, không gửi provider. HTTP503 trong CLI là local stop response, **không phải chứng cứ provider overload/503**. Lượt này không đủ request để đánh giá pacing live.
- Không có request nào tính được chi phí: raw known subtotal0 là tổng rỗng, **không phải miễn phí**. Cumulative known estimate giữ **0.40389912 USD**; nay **ba request lịch sử unpriced**, cumulative total/charge unknown.
- Dependency/manifest/source/protocol/pricing/seal/chain/binary hash khớp; witness isolation đạt, fixture chưa đổi; key scan/PID/socket/Git postcheck đạt. [`../research/artifacts/SEARCH-R2-RECHECK-REVIEW-20261109-01/validation.json`](../research/artifacts/SEARCH-R2-RECHECK-REVIEW-20261109-01/validation.json).

Native search-r2 đã đạt offline, nhưng inference task chưa được kiểm chứng trong lượt này. Không tự retry, tăng cap hoặc chạy năm slot còn lại. Một request timeout không xác định root cause ở provider/gateway/network hoặc model; không suy provider hết/ngược lại đang quá tải từ local503.

> Phần lịch sử bên dưới thuộc **legacy**, không gộp cùng r2. search-r2 đã chuẩn hóa/preflight offline và có một inference attempt riêng được nêu ở trên; [`../research/ENVIRONMENT_R2_RESULTS.md`](../research/ENVIRONMENT_R2_RESULTS.md) lưu nghiệm thu offline trước inference.

## Continuation bảy slot — dừng sau 2/7

Đợt [`PILOT-SOL-CONTINUE-20261106-01/result.json`](artifacts/PILOT-SOL-CONTINUE-20261106-01/result.json), protocol [`PILOT_SOL_CONTINUE.md`](PILOT_SOL_CONTINUE.md) rev1, ngày 2026-11-06 `09:53:36Z`–`10:02:15Z`:

| Run | Task/CLI | Kết quả | Request | Known estimate USD |
| --- | --- | --- | ---: | ---: |
| R-0018 | P-01/Codex | success/valid; scope/public/hidden pass | 5 | 0.27390552 |
| R-0019 | P-01/OpenCode v2 | timeout 300 giây gồm pacing; chưa sửa source | 5 | 0.02498160 |
| Tổng đợt | | 5 slot còn not_run | 10 | **0.29888712** |

- 9 response HTTP200/completed; request cuối R-0019 đã HTTP200 nhưng thiếu terminal/usage, broker ghi TimeoutError tại giới hạn lượt. Supervisor kill sau 300008 ms. Không thấy thông báo overload trực tiếp trong log đã đọc; **không suy timeout là provider quá tải hoặc tool giải sai**.
- `provider_failure` latch được đặt và `usage_missing` dừng batch; không có request tiếp theo để thử latch live, không mở năm slot còn lại hoặc tự retry. Một request đợt này unpriced, cộng request cũ R-0009 thành **hai request unpriced**.
- **9/9 gap ≥30 giây**, gap Codex → v2 **30.003446 giây**: pacing xuyên CLI nay runtime-confirmed trong đợt này; không gửi đồng thời. Duration gồm pacing, không dùng để xếp hạng tốc độ tool.
- V2 gặp `glob` error `ripgrep execution failed`, sau đó dùng `read`/`shell find` được; chưa sửa file. Public baseline pass/hidden baseline fail không phải bằng chứng bản sửa sai. Raw `timeout/valid` giữ nguyên; cần review môi trường và latency khi diễn giải timeout. Codex đã khắc phục `python` thiếu bằng `python3`; fixture không phải Git repo, lệnh git diff bị lỗi nhưng agent vẫn hoàn thành.
- Cumulative known usage estimate của pilot + retry + continuation **0.40389912 USD**. Total/charge vẫn **unknown**, chưa chạm guard known3 USD; không báo số này là tổng phí.
- Hash source/protocol/pricing/seal/chain/binary khớp; key scan/supervisor PID/socket/runtime-process/source Git postcheck đạt. [`../research/artifacts/SOL-PILOT-CONTINUE-REVIEW-20261106-01/validation.json`](../research/artifacts/SOL-PILOT-CONTINUE-REVIEW-20261106-01/validation.json).

Toàn pilot hiện có **Pi/P-01 và Codex/P-01 đạt**, OpenCode v2/P-01 timeout, năm slot chưa chạy; R-0009 infra_error vẫn giữ riêng cùng retry lineage. Chưa đủ pilot 8 slot/benchmark chính thức. Không tự nâng timeout/tăng cap hoặc tiếp tục khi thiếu usage; cần quyết định bước tiếp theo.

Audit môi trường offline sau đó đã tái hiện glob failure **cả v1/v2**, Pi shell thiếu rg; Codex có rg bundled. Đối chứng mount rg read-only trong sandbox test mới khiến glob v1/v2 hoạt động. [`../research/SEARCH_ENVIRONMENT.md`](../research/SEARCH_ENVIRONMENT.md). Đây là lỗi dependency của environment cần xử lý trước năm slot còn lại, chưa phải bằng chứng toàn bộ timeout v2 do rg. **Chưa thay môi trường pilot hoặc chạy thêm generation**; nếu đổi dependency phải đóng băng revision/tách nhóm, không gộp âm thầm với kết quả cũ.

## Retry sau bản sửa — R-0017 đạt

Theo yêu cầu người dùng, chạy riêng Pi/P-01/C-0069/session mới, retry_of R-0009, protocol [`PILOT_SOL_RETRY.md`](PILOT_SOL_RETRY.md). **Success/valid**; không mở bảy slot còn lại. Artifact [`PILOT-SOL-RETRY-20261106-01/result.json`](artifacts/PILOT-SOL-RETRY-20261106-01/result.json), review [`../research/artifacts/SOL-PILOT-RETRY-REVIEW-20261106-01/validation.json`](../research/artifacts/SOL-PILOT-RETRY-REVIEW-20261106-01/validation.json).

- `09:41:18Z`–`09:45:12Z` ngày 2026-11-06; duration agent gồm pacing 233296 ms. Exit 0, không timeout, assistant cuối stopReason stop.
- **7/7 HTTP 200/response.completed**, đúng model field sol, usage đủ; không provider failure hoặc local blocked retry trong lượt này.
- **6/6 gap ≥30 giây** (min30.000974); không dồn request. Một CLI nên pacing live xuyên CLI chưa được kiểm chứng; failure latch không được kích hoạt live vì không có lỗi provider, vẫn chỉ được kiểm chứng offline.
- Chỉ đổi `intervals.py`; **scope/public/hidden đều pass**, chấm lại classifier success. Không trộn lượt diagnostic ngoài pilot hoặc xóa lượt R-0009 bị lỗi.
- Lượt retry estimate **0.07692480 USD**; cumulative known estimate pilot + retry **0.10501200 USD**. Cumulative total/charge vẫn unknown do một request R-0009 thiếu usage. Không coi phần unknown là 0.
- Hash source/protocol/pricing/seal/binary khớp, raw không sửa; key scan/PID supervisor/socket broker/source Git postcheck đạt.

Kết luận hẹp: **lượt retry Pi/P-01 hoạt động**, chưa phải toàn bộ pilot hoặc chứng minh provider hết quá tải lâu dài. Cần quyết định mở các slot còn lại theo protocol/ID và shared budget cập nhật; không tự khởi chạy từ kết quả này.

Theo yêu cầu người dùng, các log/artifact/results model cũ đã xóa; ID cũ retire, không tái sử dụng. CSV hiện có R-0009/R-0017/R-0018/R-0019 của sol, không có kết quả model cũ. Xem [`../research/SOL_MIGRATION.md`](../research/SOL_MIGRATION.md).

## Pilot sol đợt 01 — dừng sau 1/8 lượt

Protocol [`PILOT_SOL.md`](PILOT_SOL.md) rev1, guard 3 USD estimate, pacing30; artifact [`PILOT-SOL-20261106-01/result.json`](artifacts/PILOT-SOL-20261106-01/result.json). Chạy ngày 2026-11-06 `09:28:41Z`–`09:30:00Z`, R-0009/Pi/P-01/C-0049; **7 slot còn not_run**, không tự retry hoặc mở batch mới.

- Request 1 HTTP 200/`response.completed`, usage đủ, estimate **0.0280872 USD**.
- Request 2 HTTP 200 nhưng **`response.failed`**, không có usage hợp lệ. Pi ghi provider error `Our servers are currently overloaded. Please try again later.` (`R-0009/stdout.jsonl:58-59`). Đây là thông báo gateway, không xác minh độc lập backend/accounts.
- Guard `usage_missing` chặn request/lượt tiếp theo. Pi tự thử native retry một lần nhưng bị broker chặn local; chỉ **hai** request thực gửi upstream. Không diễn giải thông báo gateway thử ba account thành ba request harness.
- Khoảng nghỉ quan sát **30.000943 giây**. Chỉ một CLI chạy nên pacing live xuyên CLI sau sửa vẫn unverified.
- Agent chỉ đọc source, chưa sửa file; public baseline pass, hidden baseline fail. Có thêm lỗi môi trường **`rg: command not found`** (`stdout.jsonl:49`), không quy nó là nguyên nhân của overload.
- **Tổng phí chưa biết**, measured charge null, không coi subtotal known usage là tổng hoặc request lỗi miễn phí.

## Sửa diễn giải phân loại, không sửa raw

Runner gán `failure/valid` do chỉ kiểm HTTP status/error_type, bỏ qua terminal `response.failed`. Đánh giá review là **`infra_error/pending_review`**, không dùng lượt này để kết luận Pi giải sai task hoặc tính task success rate. Giữ raw JSON/CSV/protocol nguyên trạng để truy vết lỗi classifier; consumer phải đọc review này trước khi tổng hợp. Cần bổ sung classifier/tests HTTP 200 + failed/incomplete/empty ledger trước đợt mới.

Review/hash/key scan/cleanup/source Git: [`../research/artifacts/SOL-PILOT-REVIEW-20261106-01/validation.json`](../research/artifacts/SOL-PILOT-REVIEW-20261106-01/validation.json). Source/protocol/pricing/seal khớp, key không có trong artifact, PID supervisor và broker socket không còn, bốn repo source sạch. Source dùng chạy giữ trong snapshot launch; không sửa protocol đã đóng băng.

Chưa hoàn tất pilot/benchmark chính thức. Diagnostic Pi/P-01 sol trước vẫn giữ riêng ở [`MODEL_COMPARE.md`](MODEL_COMPARE.md), không gộp vào pilot. Trước lượt trả phí mới cần sửa/test classifier và review tools/PATH; không tự tăng budget hoặc retry chỉ vì subtotal thấp.

Cập nhật bản sửa sau đợt: classifier và provider-failure latch đã sửa/test offline, **30 tests đạt**, gồm hai client đồng thời nhưng chỉ một upstream active; lỗi provider chặn native retry và CLI kế tiếp tại local dù vẫn còn budget. Chấm lại log cũ cho infra_error, raw/CSV vẫn giữ nguyên. [`../research/PROVIDER_STOP_FIX.md`](../research/PROVIDER_STOP_FIX.md). Chưa gọi provider lại; còn review tools/PATH và protocol/decision trước lượt trả phí tiếp theo.
