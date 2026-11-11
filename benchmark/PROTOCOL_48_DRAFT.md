# Benchmark48 — đề xuất protocol rev1, 2026-11-09

**Thiết kế được chọn để chuẩn bị: 4 task × 4 CLI × 3 lần = 48 slot.** Đây là bản soạn offline sau khi người dùng đồng ý hướng48lượt; **chưa duyệt budget, chưa frozen protocol, chưa cho phép paid runs**. Không có kết quả benchmark trong tài liệu này. [Protocol khung](PROTOCOL.md), [baseline pilot frozen](BASELINE.md).

## 1. Task và readiness

[Bộ đặc tả/prompt](suite48/README.md), [manifest](suite48/manifest.json):

| Task | Mục đích | Success đề xuất |
| --- | --- | --- |
| B-01 | Hiểu resolver nhiều file | answer.json đúng schema, rubric10/10, references có thật, scope và CLI completion |
| B-02 | Sửa bug pagination | scope + public + hidden + CLI completion |
| B-03 | Thêm TTL/LRU cache | scope + public + hidden + CLI completion |
| B-04 | Refactor dispatcher nhiều file | scope + behavior regression + structural/delegation checks + CLI completion |

Các task mới khác P-01/P-02 để không chỉ đo lại bài đã dùng debug harness. Synthetic stdlib fixtures có giới hạn đại diện cho repo thực tế; không suy rộng thành mọi dự án/ngôn ngữ. Prompt không chứa oracle/hidden tests. Fixture, public/hidden/reference/mutants và B-01 executable rubric **chưa được viết/nghiệm thu/seal**; readiness=false. Không đánh dấu benchmark ready từ việc đã có đặc tả.

## 2. Điều kiện chung đề xuất kế thừa baseline

- Giữ bốn release/commit/binary pin của baseline, model `gpt-6.1-sol`, endpoint `https://api.shopaikey.com/v1`, Responses SSE. Không cập nhật binary/source/plugin/service đang dùng.
- `search-r2`, cùng bytes rg15.2.0, read-only dependency mount; python3/stdlib, không alias python/pytest/cài package. Record host OS/CPU/RAM/runtime tại launch, cố định máy và giới hạn tài nguyên trong cùng nhóm; nếu thay đổi, tách revision.
- Native prompt/tool definitions và config riêng từngCLI được lưu/hash; **không tuyên bố generation/reasoning tương đương**. Codex effort none khác capability-reasoning-off/no-forced-wire-value. Backend revision/model gốc chưa xác minh; không ghi alias thành model gốc đã chứng thực.
- `paced-900`: wall900s/lượt gồm pacing; reserve60s sau pacing trước dispatch, tối đa8upstream và requested output≤2048/request. Concurrency1, nghỉ≥30s sau response kể cả chuyển CLI. Request/timeout/pacing values không điều chỉnh theo task hoặc tool.
- Session/workspace/home/XDG mới mỗi attempt; không dùng dữ liệu session thật hoặc lời giải cũ. bwrap net riêng, key broker host, source writable theo allowlist, public/dependency read-only, hidden/reference/oracle ngoài agent. Grader sandbox riêng không network/provider/credential.
- Cache **không kiểm soát** (kể cả warm cache giữa repetitions); ghi provider cache usage nếu có. Không gọi lượt lặp là independent cold-cache samples. Không bật/tắt cache riêng cho tool để cải thiện kết quả.
- Permission policy không tương tác: chỉ operations trong fixture/công cụ cần thiết được cấp tương đương; ngoài scope deny. Không mở approver thủ công để cứu lượt. Permission/background/plugin demos tách ngoài benchmark.

## 3. Thứ tự và ID

- [order.csv](suite48/artifacts/DRAFT48-20261109-01/order.csv) chứa48**slot dự kiến**, không run results. `D48-*` không phải ID inference R/C và không reserve các IDs đó.
- Ba round. Mỗi round sắp4task bằng SHA-256-sort; mỗi task là block bốnCLI. Sắp base tool order bằng SHA-256-sort riêng round, xoay theo offset0..3 giữa4block. Seed và encoding chính xác tại [planning.json](suite48/artifacts/DRAFT48-20261109-01/planning.json), code [plan48.py](plan48.py).
- Mỗi task/CLI có3slot; mỗiCLI xuất hiện3lần ở mỗi vị trí1..4 trên12block. Với3repetitions, không thể cân hoàn toàn vị trí mỗiCLI trong từng task. Không đổi order theo kết quả/chi phí đã thấy.
- Chỉ cấp fresh R/C IDs từ registry lúc launch đã duyệt, lưu mapping slot→attempt→config. Không tái dùng ID pilot/reserved/retired; không ghi slot chưa chạy thành failure/0tokens.
- Nếu tạm dừng do guard/provider, lưu suffix not_run và lý do; lần tiếp tục phải được duyệt, nối đúng order. Retry nếu sau này được duyệt có ID riêng, retry_of và supplemental cohort; không thay lượt đầu trong bảng chính.

## 4. Duration, usage và grading đề xuất

- Primary duration: monotonic từ **ngay trước spawn native CLI** sau setup offline đến terminal exit/cancel/deadline; gồm CLI startup, tool execution, broker pacing và native retries được quan sát. Setup fixture/hash/service-preflight trước spawn và supervisor grader sau dừng **đo riêng**, không trừ pacing ra duration chính. Nếu runner không đo đúng boundary này phải sửa/test và seal trước launch.
- Timeout900s là terminal timeout dù snapshot đã pass. Reserve cạn trả local408/time_window_exhausted, không upstream; phân loại timing stop riêng, không gọi provider overload. Grader15s/suite, output cap1MiB đề xuất như pilot; rubric/AST checks cũng có timeout riêng trước khi final seal.
- Chỉ chạy public/hidden/oracle sau agent đã dừng trên snapshot, giữ patch/source tree, exit/status/timestamps/usage/raw terminal. Scope cho phép __pycache__ tự sinh, không cho sửa public tests. B-04 file addition phải nằm allowlist; B-01 chỉ answer.json. Không chạy code agent sửa trực tiếp trên host.
- Success cần completion trong cap + scope + đầy đủ acceptance; B-01 thêm partial score0..10 nhưng success chỉ10/10. Không dùng văn bản final tự nhận thành công hoặc tùy người chấm sau khi xem tool.
- Provider usage gốc là nguồn chuẩn để tính estimated cost; CLI-reported usage lưu riêng, không cộng hai nguồn. Cache là subset input, reasoning nếu nằm trong output không cộng lại. Thiếu trường usage/cache/reasoning để null; không suy0. Lưu request index/status/terminal/timestamps/requested settings và local-blocked riêng upstream.
- Báo primary numerator/denominator theo từng task/CLI: success / attempts hợp lệ; đồng thời công bố toàn bộ assigned/executed/infra_error/pending_review/not_run. Không chỉ báo conditional rate mà giấu hạ tầng. B-01 điểm thành phần báo thêm, không trộn vào pass rate các task khác.
- Duration/token/cost: báo từng attempt, median/min–max theo cohort phù hợp; n=3 nhỏ, không xếp hạng thống kê. Timeout/censored duration báo riêng; không gộp median successful-only với all-attempt median, không giấu phí failure. Tổng cost giữ known subtotal và unpriced count, total null nếu thiếu.

## 5. Lỗi, retry và điều kiện dừng

- CLI exit0 + grading fail (scope/behavior/rubric/structure), không có provider/infra blocker: failure/valid. CLI hết wall hoặc reserve: timeout/valid nếu provenance đầy đủ; snapshot pass không nâng success.
- Upstream HTTP error/response.failed/incomplete/stream mất terminal hoặc exception: dừng batch và provider-failure latch chặn local native retry; infra_error/pending_review, giữ nguyên bằng chứng. Thiếu usage/cost cũng dừng, không bỏ qua để chạy tiếp cho đủ48. Nếu timeout và provider error chồng lấn, giữ primary/secondary reason và pending_review trước khi gộp chỉ số.
- Mất sandbox/isolation, sai binary/fixture/config hash, missing dependency hoặc grader/environment error: infra_error/pending_review; không tự quy task failure, không tiếp tục khi isolation mất. Chỉ excluded sau review có lý do/artifact; không xóa raw.
- Agent tự chạy lệnh không có trong môi trường (ví dụ pytest dù policy chỉ có stdlib) là hành vi task, không tự loại hạ tầng; khác với supervisor thiếu dependency đã cam kết.
- Không tự retry toàn attempt (max automatic full-attempt retries=0). Native retry được ghi riêng, vẫn trong wall/request caps/pacing và bị chặn sau provider-failure/usage latch. Không có retry trả phí để “đủ success”.
- Chạm estimate guard, provider lỗi/usage thiếu, drift hoặc host resource thay đổi: pause, lưu tất cả và báo người dùng. Không tự top-up; không đổi thứ tự, cap, prompt hoặc rubric để cứu kết quả. Protocol thay đổi phải tạo revision và quyết định split/rerun trước khi thực hiện.

## 6. Dự toán — không phải kết quả hay hóa đơn

Nguồn: P-02 R-0035–R-0038, bốnCLI cùng search-r2/paced-900, n=1/CLI; tổng cohort **0.41671632USD**, mean **0.10417908USD/lượt**. Mỗi CLI có12slot mới, nên dùng12×cost quan sát của từngCLI, tương đương48×mean. Không ngoại suy từ6request pilot thiếu usage.

| Kịch bản số học | Dự toán48slot USD |
| --- | ---: |
| 1× mức P-02 quan sát | 5.00059584 |
| 2× | 10.00119168 |
| 3× | 15.00178752 |

**Đề xuất xin duyệt guard mới16USD estimate** (làm tròn lên kịch bản3×), **chưa được duyệt**. Không phải trần hóa đơn cứng hoặc cam kết đủ48slot. Task mới, cache/input context và failure/retry có thể khác nhiều; đây không phải confidence interval hoặc benchmark đo được. Phí pilot đã biết1.10640264USD và6requestunpriced tách riêng, không coi đã nằm trong16USD hoặc phí thiếu=0.

Với48×8=384upstream, output requested cap cộng dồn786432tokens: **riêng output** nếu mọi request chạm cap tương ứng14.155776USD ở giá18USD/M, **chưa gồm input**. Vì vậy cap token/request không bảo đảm toàn hóa đơn≤16USD. Guard kiểm known estimate trước dispatch và sau response, không dự báo cứng hóa đơn request đang chạy; thiếu usage phải pause. Nếu cần hard invoice cap phải có cơ chế provider kiểm chứng, hiện chưa có.

48×900s = **12giờ tổng agent wall caps**, không phải ETA; chưa gồm setup/grader/pause. Không tăng concurrency để rút thời gian. Giá user-reported4.8/0.24/18USD/M input/cache/output, chưa invoice-confirmed. [Dự toán machine-readable](suite48/artifacts/DRAFT48-20261109-01/planning.json).

## 7. Điều kiện trước launch

- [x] Chọn thiết kế48lượt để chuẩn bị offline; không chọn72lượt ở giai đoạn này.
- [x] Soạn bốn task/prompt/acceptance matrix và order/dự toán offline.
- [ ] Viết fixture, oracle/rubric/public/hidden/reference/mutants, kiểm baseline/reference/mutants và seal.
- [ ] Tích hợp isolated runner/grader cho cả4task; kiểm đo duration, caps/latches, scope/permissions/file additions và ID mapping offline. Không sửa manifest baseline pilot cũ.
- [ ] Ghi host resource snapshot/limits và manifest config/model/provider đầy đủ cho launch mới.
- [ ] Hoàn thiện source/demo còn thiếu trong báo cáo hoặc ghi rõ phần nào vẫn unverified; không dùng benchmark thay thế permission/background/plugin/API demonstrations.
- [ ] Người dùng duyệt **budget estimate mới** và **protocol cuối**; ghi tên/ngày/revision, rồi mới authorize48paid slots. Dừng ở đây nếu chưa duyệt.
