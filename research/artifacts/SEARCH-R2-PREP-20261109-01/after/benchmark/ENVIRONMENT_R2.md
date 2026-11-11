# Môi trường search-r2 — chuẩn hóa dependency, chỉ preflight offline

Người dùng đồng ý chuẩn hóa sau audit thiếu rg. **Đợt này không chạy model/pilot trả phí** và không tự tiếp tục năm slot còn lại.

## Revision đã chốt

- ID **search-r2**, manifest `research/environment-profiles/search-r2.json`; môi trường cũ là **legacy**.
- `rg` **15.2.0**, SHA-256 `e62198eb19b136b88c330af83647b5a962cb99b6b1f066758568f12de1974849`. Dùng lại bytes trong package Codex đã pin/checksum; không download, installer hoặc thay binary tool. Bản private ở `.local/environments/search-r2/bin/rg`, mode0555.
- `profile` mount thư mục dependency **read-only** tại `/opt/agent-cli-report-deps/search-r2/bin`, prepend vào PATH nền. Giữ thay đổi PATH native của CLI; Codex ưu tiên `codex-path/rg` đi kèm, nhưng native preflight phải chứng minh **cùng checksum/version**, không giả cùng đường dẫn.
- Python policy không đổi: có `/usr/bin/python3` và stdlib, không tạo alias `python`, không cài package. Bash/find/ls từ cùng `/usr` read-only. Không thêm native tools/đổi system prompt/model/permission để làm task dễ hơn.
- Network namespace/home/XDG/session riêng, key host broker, public test read-only, hidden absent, source fixture writable như pilot trước; không bypass sandbox hoặc mở Internet cho agent. Giữ cap/pacing/budget logic; sửa dependency không phải quyền tiêu thêm tiền.
- Runner pilot mới mặc định search-r2, ghi environment revision/manifest hash vào batch và từng run/spec; legacy vẫn tái lập bằng cờ tường minh. Không cho `--retry-run`/`--continue-after` kế thừa chain legacy dưới search-r2 âm thầm; muốn chuyển nhóm phải có plan/protocol mới được review.

## Acceptance offline

1. Native settings như pilot: glob/grep của v1/v2 trả đúng fixture; native shell/bash/exec của cả bốn chạy `rg --files`, search nội dung, xác minh version/hash và executable không ghi được.
2. PATH native thực được thu; Python3/bash/find/ls có sẵn, thiếu alias python ghi rõ chứ không sửa âm thầm.
3. Writable pilot witness/config preflight đủ bốn CLI: project writable/public test read-only/hidden absent/home và net riêng; chỉ mock HTTP400 chủ động, không đọc API key.
4. Hash source/manifest/dependency/binary/fixture; PID/socket cleanup và repo source status. Kết quả cũ/CSV/protocol giữ nguyên.

## Lệnh offline

```sh
python3 -B demos/audit_search_environment.py --artifact-dir demos/artifacts/SEARCH-R2-NATIVE-PREFLIGHT-20261109-03 --config-start 98 --environment-profile search-r2 --pilot-settings
python3 -B benchmark/pilot.py --offline-preflight --artifact-dir benchmark/artifacts/SEARCH-R2-PREFLIGHT-20261109-01 --config-start 102 --environment-profile search-r2 --protocol-file benchmark/ENVIRONMENT_R2.md --budget-usd 3 --request-gap-seconds 30
```

Các artifact/ID một lần duy nhất; không ghi đè nếu chạy lại. Exit native audit có thể1 vì mock cố ý dừng bằng local400 sau khi tool đã hoàn tất; acceptance từ event tool và witness, không coi đó là lỗi giải task. Lượt native audit01/02 còn lỗi riêng do khóa cả project read-only không khớp Codex workspace-write; giữ log và dùng lượt03 sau sửa harness audit, không tắt sandbox.

## So sánh và bước tiếp theo

Kết quả legacy chỉ thuộc nhóm legacy. Không gộp năm slot chạy với search-r2 vào tám slot cùng điều kiện. Muốn so sánh đủ bốn CLI phải chốt nhóm r2 và kế hoạch chạy phù hợp, báo ngân sách/unknown charge cũ riêng; chưa chạy hoặc duyệt nhóm đó từ việc chuẩn hóa này. Không kết luận sửa dependency giải thích toàn bộ timeout/provider latency hoặc bảo đảm task success.
