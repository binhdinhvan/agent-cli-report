# Benchmark48 — protocol candidate r1, 2026-11-10

Đã nhận đồng ý của người dùng với hướng48slot, guard mới **16USD estimate** và primary duration outer-wall. Tài liệu này cụ thể hóa các quyết định đã nêu; **khóa bytes để kiểm thử runner không đồng nghĩa authorize dispatch**. Chỉ mở paid launch bằng approval manifest riêng sau offline acceptance. Không nhập kết quả pilot/preflight/reference vào benchmark.

## Thiết kế và bằng chứng cố định

- 4task×4CLI×3repetitions=48slot, theo đúng `suite48/artifacts/DRAFT48-20261109-01/order.csv`. Seed/thuật toán SHA-256-sort và rotation giữ nguyên draft, không đổi thứ tự theo kết quả. n=3/task/CLI, mẫu nhỏ; không kết luận ưu thế thống kê.
- B-01hiểucode, B-02pagination bug, B-03TTL/LRU feature, B-04multi-file refactor; prompt/fixture/public/hidden/oracle sealed tại `suite48/artifacts/PREP48-20261110-02/preparation.json`. Chỉ fixture/prompt visible; không reference/oracle/log hoặc history preflight trong workspace/session thật.
- B-01 cần đúng schema/rubric10/10 và evidence hợp lệ; báo partial score riêng, không success nếu dưới10. B-02/B-03 cần scope/public/hidden pass; B-04 thêm behavioral/structural/delegation checks. Mọi task còn cần native CLI completion trong wall cap. Snapshot pass nhưng CLI timeout không phải success.
- OpenCode v1.19.5/v2.2.5, Pi1.5.0, Codex0.167.0 giữ full SHA/binary/native config pins từ baseline; model alias `gpt-6.1-sol`, endpoint `https://api.shopaikey.com/v1`, Responses SSE. Native prompts/tools/reasoning không tương đương; Codex explicit none và các nhóm capability-reasoning-off ghi riêng. Backend/model gốc chưa xác minh; cache uncontrolled, không gọi repetitions là independent cold-cache.

## Isolation, caps và thời gian

- Search-r2/rg15.2.0 read-only cùng bytes, python3/stdlib, không install/alias; network/home/XDG/session riêng mỗi attempt, host key chỉ ở broker. Public/immutable files read-only, source/allowlisted additions writable, hidden grader chỉ ở sandbox chấm riêng sau agent dừng.
- Primary wall: **monotonic ngay trước outer bwrap spawn → launcher/bridge exit**, gồm startup, pacing, tool/native retry và teardown. Offline setup và broker startup trước spawn đo riêng; supervisor grading sau exit đo riêng. Exact native subprocess clock là secondary, không âm thầm thay primary khi tổng hợp.
- **Wall cap900s**, cùng monotonic origin với broker deadline; reserve60s sau pacing và kiểm lại trước dispatch. Concurrency1, nghỉ≥30s sau response kể cả qua CLI, tối đa8upstream/attempt, requested output≤2048/request. Broker socket45s và bridge90s như baseline. Không tăng cap theo task/tool hoặc khi thấy thất bại.
- Grading15s/suite, output1MiB, CPU12s/address-space512MiB trong grader; native output capture16MiB bounded. Không áp dụng resource limits của grader cho native CLI. Ghi CPU/RAM/kernel/runtime/cgroup snapshot tại plan và recheck launch; CPU exclusivity/background load uncontrolled, không giả vờ máy riêng hoàn toàn.

## Usage, budget và dừng

- Ledger provider là nguồn usage/cost estimate; CLI usage lưu trong raw, không cộng hai lần. Cache subset input, reasoning đã nằm trong output không cộng lại. Thiếu usage/cache/reasoning giữ null, không gán0. Dùng giá user-reported4.8/0.24/18 USD/M input/cache/output; measured charge null cho đến khi đối soát.
- Guard mới **16USD estimated known usage cho batch benchmark**, tách pilot known1.10640264USD và6requestunpriced. Không invoice cap hoặc bảo đảm đủ48; một request có thể vượt phần còn lại trước khi usage trả về. Không top-up tự động. Thiếu usage hoặc known subtotal chạm guard dừng batch, suffix not_run; tổngcost null nếu có unpriced.
- Provider HTTP error/failed/incomplete/missing terminal/exception: latch chặn local native retry và dừng batch. Thiếu reserve: local408/time_window_exhausted/no upstream, không provider overload. Mất isolation/hash drift hoặc lỗi supervisor/grader: dừng, infra_error/pending_review. Không gọi local-blocked requests là upstream.
- Timeout và provider failure cùng xuất hiện: giữ cả reason, infra_error/pending_review trước review; timing-only hoặc wall-only với provenance đầy đủ là timeout/valid. CLI/acceptance/scope fail không infra blocker là failure/valid. Success chỉ khi CLI exit0, không timeout/output overflow/native error, scope và mọi test pass, ledger terminal/usage hợp lệ.
- Full-attempt automatic retries=0. Failure giải task có thể tiếp slot tiếp theo đúng order; provider/usage/budget/isolation/infra stop phải dừng. Retry/continue trả phí cần quyết định riêng, giữ ID/lineage mới, không thay first-attempt result hoặc chọn success để giấu failure. Runner r1 chưa hỗ trợ auto resume; không bắt đầu lại48slot để né suffix chưa chạy.

## ID, artifact và báo cáo

- Draft D48slot không phải run. Chỉ reserve fresh R/C cho toàn batch dưới lock **sau launch authorization và hash/resource gates**, trước dispatch; mọi ID chưa chạy vẫn reserved/not_run, không tái sử dụng. Credential chỉ đọc sau gates, không log/key trong agent/config mẫu/artifact. Không ghi pilot CSV; index benchmark riêng `runs-benchmark48.csv` và raw per-run.
- Lưu plan/config/source/prompt/seal/model/provider/pricing/resource hashes, slot→R/C mapping, stdout/events, snapshots/patch/grading, original usage, terminal/error/local-blocked/pacing/time bounds và mọi not_run. Raw artifact chỉ chia sẻ sau secret/PII review.
- Công bố assigned/executed/success/failure/timeout/infra/pending/not_run theo task/CLI. Completion success/valid attempts phải kèm toàn bộ denominators và infra/exclusion reasons; không che thiếu48. Duration/token/cost báo per-attempt và median/min–max theo cohort phù hợp, timeout/censored riêng. Báo known subtotal/unpriced count và totalnull; không chỉ báo phí success.
- Source/API/permission/background/plugin demos còn thiếu trong REPORT giữ unverified; benchmark không thay thế các demo đó. Synthetic fixture nhỏ không đại diện mọi ngôn ngữ/repo/context lớn.

## Launch gate

Paid command phải có manifest đã khóa input hashes/order/resource/registry, **approval riêng ghi `launch_authorized=true`**, cùng manifest SHA-256/budget16USD và người duyệt/ngày. Manifest draft luôn `launch_authorized=false`. Chỉ đồng ý tiếp tục chuẩn bị hoặc đồng ý mức budget không tự bật launch. Hash/resource/registry thay đổi phải re-plan/review trước inference, không cập nhật âm thầm approval cũ. Offline verification và real dispatch là hai chế độ tách biệt; default không đọc key hoặc gửi request.
