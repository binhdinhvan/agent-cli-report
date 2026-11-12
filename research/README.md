# Điều hướng tài liệu nghiên cứu

## Cần cho báo cáo cuối

- [versions.md](versions.md): phiên bản, commit và nguồn đối chiếu.
- [evidence.csv](evidence.csv): bằng chứng theo claim, source và runtime.
- [REQUIREMENTS_ACCEPTANCE.md](REQUIREMENTS_ACCEPTANCE.md): đối chiếu tám hạng mục đề bài.
- [BENCHMARK_FAIRNESS.md](BENCHMARK_FAIRNESS.md): fairness, token và timing.
- [isolation.md](isolation.md): cách ly môi trường và giới hạn kiểm chứng.
- [APPENDIX_GUIDE.md](APPENDIX_GUIDE.md): nguồn ảnh, phụ lục và cách xuất PDF.

## Script phân tích và kiểm chứng

- `analyze_final_cohort.py`, `derive_benchmark_dispersion.py`: tính chỉ số từ raw đã có.
- `validate_evidence.py`, `audit_source_axes.py`, `audit_offline_tasks.py`: kiểm cấu trúc bằng chứng và đối chiếu source/task.
- `build_appendix.py`, `export_final_report.py`: dựng phụ lục và PDF. Không cần chạy lại để đọc hoặc nộp bản PDF hiện tại.
- `inventory.py` và hai file `*-2026-11-06.json`: kiểm kê môi trường/source tại ngày chốt.

Không chạy script chỉ để dọn repo: một số script tạo artifact, cần đọc hướng dẫn và chọn revision mới trước khi dùng.

## Giữ để kiểm chứng lịch sử, không phải phạm vi benchmark cuối

- `artifacts/`: receipts, manifests và kết quả kiểm tra; không phải cache.
- `experiment-state.json`, `provider-pricing.json`, `environment-profiles/`, `model-profiles/`: trạng thái/giả định được các runner và audit tham chiếu.
- Các tài liệu migration, network, pacing, stop/repair policy và `REPORT_REVIEW_FIXES.md`: ghi nhận các mốc trước; xem [lịch sử thực nghiệm](../EXPERIMENT_HISTORY.md). Không nhập số liệu các cohort cũ vào OpenAI48.

## File đã loại khỏi bản nộp

- `.batch48-launch.lock`: lock runtime rỗng, runner tự tạo khi cần; đã thêm `.gitignore`.
- `transition_to_sol.py`: script migration một lần đã hoàn tất, không còn nơi tham chiếu trong repo tại thời điểm rà soát. Không xóa manifest migration, dữ liệu hoặc audit lịch sử.

[Báo cáo để nộp](../report/README.md) · [Hướng dẫn kiểm chứng](../SUBMISSION.md)
