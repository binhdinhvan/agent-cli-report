# Báo cáo so sánh OpenCode, Pi và Codex CLI

Workspace nghiên cứu source, demo native và benchmark; kết quả tổng hợp trong [REPORT.md](REPORT.md).

## Bản nộp hoàn chỉnh

**[OpenCode_Comparison_Report.pdf](OpenCode_Comparison_Report.pdf)** — **19 trang**, gồm 16 trang báo cáo chính và 3 trang phụ lục. Đây là file duy nhất cần gửi mentor để đọc báo cáo; repository đi kèm để kiểm chứng raw/code. Hyperlinks bằng chứng được pin tại commit `f2becc501cfc1b980b888402458bac81b8193370`, không trỏ về filesystem máy xuất PDF.

**Người thực hiện:** Đinh Văn Bình — **VSF – Data & AI**. **Thời gian nghiên cứu:** 06/11/2026 – 11/11/2026. Thông tin nằm ngay dưới tiêu đề, không thêm trang bìa; PDF có bookmarks cho chín chương và ba phụ lục.

**Repository public:** [binhdinhvan/agent-cli-report](https://github.com/binhdinhvan/agent-cli-report). [Hướng dẫn bàn giao và kiểm chứng](SUBMISSION.md). Credentials/binary/dependencies cục bộ không nằm trong Git; phạm vi công bố và raw gzip lossless được ghi trong [PUBLISHING.md](PUBLISHING.md).

**Phụ lục riêng nếu cần:** [APPENDIX.pdf](APPENDIX.pdf) — 3 trang A4, đã có ở cuối PDF hoàn chỉnh, gồm [ảnh thật Desktop/Chrome/TUI](demos/UI_RECAPTURE_RESULTS.md), log chức năng và biểu đồ benchmark. [HTML tự chứa](APPENDIX.html), [nguồn/cách tái tạo](research/APPENDIX_GUIDE.md).

## Kết quả cuối

Phiên bản được chốt ngày **06/11/2026**. Benchmark dùng **OpenAI trực tiếp / `gpt-6.1-sol`**: **48 lượt hợp lệ, 46 success, 2 failure, 48/48 snapshot pass**, không timeout/infra_error. Snapshot pass không thay thế end-to-end success.

Median v1/v2/Pi/Codex lần lượt **228,15 / 200,20 / 164,23 / 139,63 giây**, gồm pacing. Guard estimate riêng 48 lượt khoảng **$2,15**, không phải tổng hóa đơn dự án; smoke riêng khoảng **$0,10**.

- [Kết quả cuối và 48 lượt/raw](benchmark/suite48/OPENAI_BENCHMARK_FINAL.md), [protocol](benchmark/PROTOCOL_OPENAI48_R3.md), [audit cuối](research/artifacts/OPENAI48-R3-FINAL-20261111-01/validation.json).
- [Fairness/token/timing](research/BENCHMARK_FAIRNESS.md), [phiên bản/source pins](research/versions.md), [evidence index](research/evidence.csv).
- [8/8 hạng mục có đầu ra trong phạm vi nghiệm thu](research/REQUIREMENTS_ACCEPTANCE.md); không có nghĩa mọi tính năng đều pass hoặc hết giới hạn nghiên cứu. [Demo vòng 2](demos/NATIVE_COMPLETION_R2_RESULTS.md), [audit](research/artifacts/NATIVE-COMPLETION-R2-REVIEW-20261111-02/validation.json).

Các thử nghiệm chuẩn bị không được nhập vào kết quả cuối; xem [lịch sử thực nghiệm](EXPERIMENT_HISTORY.md). Raw/audit lịch sử được giữ nguyên, không chạy lại benchmark hoặc retry hai failure để thay kết quả.

## Đề bài

1. So sánh OpenCode với Pi và Codex CLI theo kiến trúc, vòng lặp agent, hệ thống tool, permission, quản lý context và khả năng mở rộng; nhận định kỹ thuật phải dẫn tới source code cụ thể.
2. So sánh OpenCode v1 với v2: cài song song phiên bản chốt, kiểm chứng shared background service cho TUI/Desktop/Web, API/SDK và events, permission, subagent/shell chạy nền, port plugin và benchmark cùng bộ task.

Các phát biểu trong đề là nội dung cần kiểm chứng, không mặc định là kết luận.

## Điều hướng workspace

- [PLAN.md](PLAN.md): kế hoạch, các mốc và checklist nghiệm thu.
- [REPORT.md](REPORT.md): báo cáo chính và giới hạn nghiên cứu.
- `research/`: phiên bản, source/evidence và [phương án cách ly](research/isolation.md).
- `demos/`: demo API, permission, background, plugin và UI; [HTTP offline](demos/OFFLINE_API.md), [runtime native](demos/NATIVE_RUNTIME_RESULTS.md).
- `benchmark/`: protocol, fixture, kết quả và raw.
- [AGENTS.md](AGENTS.md): hướng dẫn làm việc trong workspace.

## Source cục bộ

Đường dẫn tương đối từ workspace; không cần clone thêm repo tool:

| Tool | Source |
| --- | --- |
| OpenCode v1 | `../opencode-v1` |
| OpenCode v2 | `../opencode-v2` |
| Pi | `../pi` |
| Codex CLI | `../codex` |
