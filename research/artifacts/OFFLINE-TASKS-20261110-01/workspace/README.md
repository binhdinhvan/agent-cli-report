# Báo cáo so sánh OpenCode, Pi và Codex CLI

Workspace để nghiên cứu source, chạy demo và benchmark, sau đó viết báo cáo.

**Đang làm offline:** hoàn thiện so sánh source trong `REPORT.md`. Benchmark tạm hoãn theo yêu cầu; người dùng cho biết mạng công ty bị chặn và sẽ yêu cầu chạy lại khi về nhà. Không tự retry hoặc probe mạng/provider.

[So sánh source sáu trục](REPORT.md) đã có bản first-pass theo commit, gồm permission/sandbox, context/session, extension, background/loader v1-v2 và recovery consumer v2;124 evidence IDs đã kiểm cấu trúc. [Chuẩn bị demo offline](demos/OFFLINE_DEMO_PLAN.md) có acceptance matrix và fixture/tests cục bộ. Demo native security/resume/plugin port và subagent/background vẫn chưa nghiệm thu, không nâng source-only hoặc fixture tests thành runtime support.

**Benchmark48 đã dừng sau1/48slot**: R-0039/v1/B-01 infra_error/pending_review, request5TimeoutError trước HTTP/usage;47slot chưa chạy. Known estimate0.06853344USD,1unpriced/totalunknown. [Kết quả và review rubric](benchmark/suite48/BENCHMARK_RESULTS.md). Không tự retry/resume; các dòng “chưa launch” bên dưới giữ lịch sử chuẩn bị.

**Đã tổng kết pilot và khóa baseline offline** `search-r2 + paced-900`: [baseline/manifest/validator](benchmark/BASELINE.md), [mọi attempt và cohort P-02](benchmark/artifacts/PILOT-FREEZE-20261109-01/SUMMARY.md). Benchmark chính thức vẫn pending, không inference mới.

**Hướng48slot:** đã có [protocol/task/order/dự toán draft](benchmark/PROTOCOL_48_DRAFT.md), [fixture/grader44checks](benchmark/suite48/IMPLEMENTATION.md) và [native preflight16/16cặp task×CLI](benchmark/suite48/NATIVE_PREFLIGHT.md) với response giả cục bộ. Còn final protocol/budget/paid orchestration và duyệt launch; chưa gọi provider hoặc chạy benchmark trả phí.

**Cập nhật bộ điều phối:** [batch runner/launch candidate03](benchmark/suite48/BATCH_RUNNER.md) đã qua offline16/16case. Đã ghi nhận đồng ý guard16USD estimate/outer-wall để hoàn thiện runner; approval launch vẫn tắt, chưa gọi provider hoặc reserve paid IDs.

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
4. Chuẩn bị [pilot 8 lượt](benchmark/PILOT.md), rồi chốt [protocol benchmark chính thức](benchmark/PROTOCOL.md). Fixture pilot đã qua 16 kiểm tra offline; chưa chạy model pilot.
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
- [demos/SMOKE_TEST.md](demos/SMOKE_TEST.md): checklist smoke test bốn cấu hình; mới có metadata và HTTP API offline, chưa đầy đủ.
- [demos/OFFLINE_API.md](demos/OFFLINE_API.md): kết quả HTTP auth/events/session metadata v1/v2 và giới hạn so với Client/SDK.
- [demos/PROVIDER_PROBE.md](demos/PROVIDER_PROBE.md): kiểm tra gateway/model bằng request tối thiểu, usage và giới hạn ngân sách chưa xác minh.
- `benchmark/`: protocol, task manifest, mẫu kết quả và nơi lưu log.
- `REPORT.md`: khung báo cáo cuối.
- `AGENTS.md`: hướng dẫn cho coding agent làm việc tại workspace này.

Model hiện tại **`gpt-6.1-sol`**, dữ liệu model cũ đã xóa theo yêu cầu. [Pilot đã phủ đủ tám cặp task/CLI có ít nhất một lượt đạt](benchmark/PILOT_RESULTS.md), giữ nguyên mọi failure/retry. **P-02 cả bốn CLI đạt trên search-r2/paced-900**; không gọi toànpilot là8/8first-attempt hoặc đồng nhất mọi revision. Pacing≥30s đã kiểm chứng; cumulative known estimate **1.10640264 USD**, total/charge unknown (sáu requestunpriced). Chưa benchmark chính thức/xếp hạng tool. [Phạm vi chuyển đổi](research/SOL_MIGRATION.md). Workspace chưa khởi tạo Git.

Để chuyển sang làm việc:

```sh
cd /home/tts/Project/agent-cli-report
```
