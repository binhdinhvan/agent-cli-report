# P-02 còn lại — search-r2/paced-900, protocol rev1

Người dùng yêu cầu chạy nốt sau R-0035 v2/P-02 acceptance đã đạt. **Chỉ ba slot**, giữ nguyên điều kiện môi trường/thời gian cho P-02, không chạy lại v2 hoặc mở benchmark chính thức.

| Run | Task | CLI | Config |
| --- | --- | --- | --- |
| R-0036 | P-02 | OpenCode v1 | C-0137 |
| R-0037 | P-02 | Codex | C-0138 |
| R-0038 | P-02 | Pi | C-0139 |

## Điều kiện cố định

- `search-r2` manifest/rg15.2.0/hash read-only, release/binary pin và native settings/tools/reasoning/permission như pilot đã kiểm. Model gpt-6.1-sol/provider shopaikey/Responses SSE, fixture P-02 v2/prompt/seal/public/hidden/grader giữ nguyên. Python3/stdlib policy không đổi, không cài pytest/alias/dependencies hoặc sửa binary/service/config/session thật.
- `paced-900` **chung bốn CLI**, cap **900 giây/lượt gồm pacing**, reserve **60 giây sau pacing trước dispatch**, một upstream active tối đa/nghỉ≥30s kể cả chuyển CLI. **8 upstream requests/lượt**, requested output≤2048/request như cũ. Broker socket45s/bridge90s không đổi.
- Không đủ reserve: local408/time_window_exhausted/no upstream, latch chặn request tiếp và ghi timeout riêng, không provider overload. HTTP lỗi/failed/incomplete/missing terminal/exception: provider-failure latch chặn native retry local, dừng batch dù còn budget.
- Guard chung **3 USD estimate**, kế thừa known **0.76549224 USD**, remaining known-estimate **2.23450776 USD**. **Sáu request lịch sử unpriced**, totalchargeunknown không xem0; user đồng ý rõ tiếp tục ba slot. Missing usage/cost hoặc known estimate chạm guard thì dừng request/lượt kế tiếp, slot chưa chạy not_run. Không tăng ngân sách/nạp tiền/retry toàn lượt tự động. Guard mềm, không trần hóa đơn cứng.
- Giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token, usage gốc/estimate tách measured charge. Giữ mọi failure/retry và hash/lineage, không chọn success rồi xóa lượt lỗi.
- Key broker host, bwrap private net/home/XDG/session, dependencies/public test read-only/source writable/hidden absent; không bypass native sandbox hoặc mở Internet agent. Root parent tạo lại nếu thiếu, sandbox có sẵn không overwrite.

## Nhóm so sánh và lệnh

`--complete-after` kiểm single retry v2/P-02 sourceR-0035 đã completed/success, đúng search-r2/paced-900/modelprovider, chọn đúng ba slot và tính lại priorcost/unknown. Batch/run/CSVr2 ghi timing/group rõ. P-02/v2 acceptance và ba slot này cùng environment/timing nhưng native system prompt/tools/reasoning khác nhau; không suy native settings tương đương. **Không gộp P-01 legacy/cap300 thành tám slot cùng điều kiện**; mẫu nhỏ/retries không phải benchmark xếp hạng.

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/PACED-900-COMPLETE-20261109-01 --complete-after benchmark/artifacts/PACED-900-RECHECK-20261109-01/result.json --run-start 36 --config-start 137 --environment-profile search-r2 --timing-policy paced-900 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_PACED_900_COMPLETE.md
```

Protocol chốt trước request; freshID/source/protocol/pricing/manifest/seal/binary/chain hash và regression trước chạy. Sau dừng kiểm CLIcompletion/snapshot scope/public/hidden, terminal/usage/pacing/reserve/latch/cost/keyscan/PID/socket/Git; kết quả ghi riêng. Không sửa protocol lúc chạy, không tự mở batch/retry khác khi kết thúc hoặc lỗi.
