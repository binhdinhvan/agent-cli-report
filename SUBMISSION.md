# Hướng dẫn bàn giao và kiểm chứng

## 1. Đọc theo chuỗi bằng chứng

**Phụ lục trực quan:** [APPENDIX.pdf](APPENDIX.pdf) (3 trang) và [HTML tự chứa](APPENDIX.html), gồm ảnh native có sẵn, trích log và biểu đồ từ raw/CSV. [Nguồn và giới hạn](research/APPENDIX_GUIDE.md). Không thay bộ artifact đầy đủ; chưa ghép vào PDF báo cáo chính.

1. [REPORT.md](REPORT.md): kết luận, source permalinks, code minh họa và bảng kết quả.
2. [research/REQUIREMENTS_ACCEPTANCE.md](research/REQUIREMENTS_ACCEPTANCE.md): tám yêu cầu và phạm vi nghiệm thu.
3. [research/evidence.csv](research/evidence.csv): commit/file/dòng/symbol/permalink và trạng thái từng claim.
4. [Demo vòng 1](demos/NATIVE_RUNTIME_RESULTS.md), [vòng 2](demos/NATIVE_COMPLETION_R2_RESULTS.md): case, expected/actual, raw và các attempt lỗi được giữ.
5. [Benchmark cuối](benchmark/suite48/OPENAI_BENCHMARK_FINAL.md): 48 rows, CSV, raw và audit.
6. [Phân tích fairness](research/BENCHMARK_FAIRNESS.md), [lịch sử](EXPERIMENT_HISTORY.md): chỉ số dẫn xuất và protocol/cohort cũ, không trộn với kết quả cuối.

Các audit trước vòng sửa tài liệu này là receipt của phiên bản tài liệu/harness lúc audit, không phải chữ ký xác nhận nội dung report vừa biên tập. Không cập nhật hash receipt cũ để làm chúng trông như đã audit bản mới.

## 2. Phạm vi file đi kèm

Không gửi riêng `REPORT.md` nếu muốn kiểm chứng runtime. Giữ các thư mục và tên file tương đối:

```text
REPORT.md / README.md / SUBMISSION.md / EXPERIMENT_HISTORY.md
research/   # versions, evidence, acceptance, analysis scripts, audit receipts
demos/      # launcher, TypeScript runners, fixtures, result docs, raw, screenshots/PTY
benchmark/  # protocol, fixture/grader, runner source, CSV, all attempts/raw/audit references
```

Đây là phạm vi trong [repository public](https://github.com/binhdinhvan/agent-cli-report), không phải archive toàn bộ máy hoặc chứng nhận an toàn tuyệt đối. Các file công khai được chọn theo `.gitignore` và rà soát trước commit; không tar/push nguyên workspace gồm `.local/`. Một raw lịch sử vượt giới hạn GitHub được lưu gzip lossless, [hướng dẫn khôi phục](PUBLISHING.md).

**Không đưa vào gói chia sẻ:** `.local/credentials`, API keys, passwords, credential stores hoặc dữ liệu session thật. Không cần gửi binary/dependency trees trong `.local/` để đọc bằng chứng; không coi việc có hash là quyền chia sẻ toàn bộ nội dung. Nếu cần redaction, tạo bản chia sẻ riêng kèm ghi chú/hash mapping, không sửa raw gốc hoặc receipt cũ.

**Địa chỉ bàn giao:** https://github.com/binhdinhvan/agent-cli-report — public theo yêu cầu chủ workspace, nhánh `main`. Người nhận có thể xem report/ảnh/raw trực tiếp hoặc clone; binary, SDK dependencies và credentials không được đưa vào repository.

## 3. Kiểm chứng mà không gọi model

- Đọc `runs48.csv`, theo cột `artifact` tới `result.json` từng slot; đối chiếu status, request usage, execution và grading. Hai failures được giữ ở D48-014 và D48-036 dù snapshot pass.
- Đọc audit gốc, đối chiếu raw hashes thay vì coi chữ “pass” trong report là đủ.
- Xem plugin before/after ở `demos/fixtures/plugin_v1.js` / `plugin_v2.js`, rồi đối chiếu raw loader failure và port marker/cleanup.
- Xem UI05 ID/PID, ảnh Desktop/Web và PTY. Đây là Linux headless sandbox, không nghiệm thu mọi UI/OS.
- Tái tính token/request và timing từ raw, không key/network:

```sh
python3 -B research/analyze_final_cohort.py
```

Script xuất JSON ra stdout và SHA-256 của 48 raw inputs; không ghi đè artifact hoặc thay phân loại.

## 4. Tái chạy demo khác với đọc lại bằng chứng

Lệnh demo ở report là lệnh **trong môi trường đã chuẩn bị**, không phải one-command setup trên máy sạch. Cần Linux/bwrap, Python, Bun, source repos tại đường dẫn launcher quy định, binary release/checksum và dependency đã chuẩn bị ở [PREPARATION.md](demos/PREPARATION.md) cùng manifests của từng demo. Source repos nằm ngoài workspace (`../opencode-v1`, `../opencode-v2`, `../pi`, `../codex`); archive chỉ chứa tài liệu không tự cung cấp các prerequisites này.

Client runner export source đúng SHA bằng `git show`; SDK demo còn cần published SDK/dependency tree riêng. Installed-tree hash không thay lockfile hoặc build attestation. Dùng fresh artifact ID và namespace; không dùng service/session/config thật. Demo scripted local SSE không cần API key thật; không thay bằng provider thật để “chạy cho đủ”.

**Không tự chạy lại benchmark trả phí.** Protocol/budget/approval là scope riêng. Bộ bằng chứng có thể được review và các phép tính dẫn xuất được tái lập mà không phát sinh inference mới.
