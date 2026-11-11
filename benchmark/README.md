# Benchmark và pilot sol

- [`suite48/BENCHMARK_RESULTS.md`](suite48/BENCHMARK_RESULTS.md): batch thật dừng sauR-0039/v1/B-01 infra_error/pending_review, request5TimeoutError/usageunknown;47not_run và rubric evidence cần review riêng, không retry/resume tự động.

- [`suite48/BATCH_RUNNER.md`](suite48/BATCH_RUNNER.md): runner và protocol/launch candidate03 đã nghiệm thu offline; guard16USD estimate được đồng ý, nhưng launch approval vẫn disabled, chưa dispatch48paid slots.

- [`BASELINE.md`](BASELINE.md): tổng kết pilot đã khóa và baseline `search-r2 + paced-900`, manifest/ledger/validator offline; benchmark protocol vẫn pending, không inference mới.
- [`PROTOCOL_48_DRAFT.md`](PROTOCOL_48_DRAFT.md): hướng48slot đã chọn để chuẩn bị; bốn task/prompt, order và dự toán; fixture/acceptance/budget/protocol cuối chưa duyệt.
- [`suite48/IMPLEMENTATION.md`](suite48/IMPLEMENTATION.md): cập nhật2026-11-10, fixture/public/hidden/reference/mutants và seal đã có;44offlinevariant checks đạt, native CLI adapter/budget/protocol launch vẫn pending. Draft ngày09 giữ trạng thái lịch sử để tái lập.
- [`suite48/NATIVE_PREFLIGHT.md`](suite48/NATIVE_PREFLIGHT.md): cập nhật tiếp, adapter đã đạt16/16task×CLI với40synthetic exchanges/0provider requests; giữ1mock-schema failure trước đó, virtual pacing không phải live pacing; final protocol/budget/paid orchestration vẫn pending.

- [`PILOT.md`](PILOT.md): tài liệu chuẩn bị lịch sử; protocol từng batch/revision được dẫn từ kết quả, không dùng lệnh cũ để tự chạy lại.
- [`SOL_COST.md`](SOL_COST.md): giá 4.8/0.24/18 USD mỗi triệu token và estimate offline khoảng 0.215 USD cho diagnostic đã giữ.
- [`MODEL_COMPARE.md`](MODEL_COMPARE.md): diagnostic sol/Pi/P-01 đang giữ, không phải pilot đủ bốn CLI.
- [`PILOT_RESULTS.md`](PILOT_RESULTS.md): đã đủ8cặp task/CLI cóít nhất1success, giữ mọi retry/failure; P-02 cả4 cùngsearch-r2/paced900, không gộp toànpilot thành8/8first-attempt.
- [`tasks/README.md`](tasks/README.md): fixture v2/public/hidden acceptance.
- [`artifacts/PILOT-PREP-20261106-02/preparation.json`](artifacts/PILOT-PREP-20261106-02/preparation.json): hash seal và 16/16 self-check offline, không kết quả model.
- [`PROTOCOL.md`](PROTOCOL.md): khung benchmark; chọn48slot để soạn offline, chưa đóng băng/duyệt chạy chính thức.
- [`runs.csv`](runs.csv):4 attempts legacy; [`runs-search-r2.csv`](runs-search-r2.csv):10 attempts search-r2, tách timing/group. Không tái sử dụng ID đã retire hoặc làm mất retry lineage.
- [`../research/PACED_900_RESULTS.md`](../research/PACED_900_RESULTS.md): timing900/reserve60/pacing30; nghiệm thu offline và các lượt live ghi ở PILOT_RESULTS.
- [`../research/SOL_MIGRATION.md`](../research/SOL_MIGRATION.md): phạm vi cleanup/migration, giữ key/binary/fixture/sol data.

Giá đúng model/provider phải đủ trước mọi paid-entrypoint. Không coi null là 0, không tự nạp tiền, không dùng session/config/service thật. Không mount hidden acceptance/oracle cho agent.
