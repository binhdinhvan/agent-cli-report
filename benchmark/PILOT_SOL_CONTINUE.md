# Pilot sol — bảy slot còn lại, protocol rev1

Người dùng xác nhận chạy **7 lượt còn lại**, không chạy lại Pi/P-01 đã đạt ở R-0017. Đây là continuation mới, không retry toàn pilot hoặc benchmark chính thức. Raw/protocol/CSV của R-0009/R-0017 giữ nguyên.

## Plan cố định

| Run | Task | CLI | Config |
| --- | --- | --- | --- |
| R-0018 | P-01 | Codex | C-0070 |
| R-0019 | P-01 | OpenCode v2 standalone | C-0071 |
| R-0020 | P-01 | OpenCode v1 | C-0072 |
| R-0021 | P-02 | OpenCode v2 standalone | C-0073 |
| R-0022 | P-02 | OpenCode v1 | C-0074 |
| R-0023 | P-02 | Codex | C-0075 |
| R-0024 | P-02 | Pi | C-0076 |

Thứ tự như `PILOT_SOL.md` sau bỏ slot đầu đã đạt; không gọi randomized. ID mới, không tái sử dụng R-0010–R-0016/C-0050–C-0056 còn reserved từ đợt đã dừng.

## Model/settings/fixture và giới hạn

- Model `gpt-6.1-sol`, `https://api.shopaikey.com/v1`, Responses SSE; native configs/release/binary từ preparation đã pin như `PILOT_SOL.md`. Không đổi model/tool set/system prompt để làm đẹp kết quả; Codex explicit effort none khác nhóm capability reasoning off, ghi metadata/tách nhóm, không giả tương đương.
- Fixture P-01/P-02 v2 cùng seal `PILOT-PREP-20261106-02`, prompt/public/hidden/grader không đổi; chỉ file source task được phép đổi. Python stdlib, public test read-only, hidden absent trong agent; chấm snapshot sau dừng. Không cài dependency hoặc sửa source tool/binary/service/config thật. `rg` chưa có trong sandbox vẫn ghi hạn chế môi trường, không coi là lỗi overload; Python/bash/find/ls đã kiểm kê.
- **Một upstream request đang xử lý tối đa**, một CLI/lượt mỗi lần. **Nghỉ ≥30 giây sau response trước**, kể cả chuyển CLI/task; khóa/mốc monotonic chung toàn batch. Không chạy song song batch khác.
- Cap **8 upstream request/2048 requested output token mỗi request/300 giây mỗi lượt**, pacing tính trong duration/deadline. Title/background/native retry đều tính cap/usage/budget.
- Shared guard toàn nhóm pilot **3 USD ước tính**, kế thừa R-0009+R-0017 **0.10501200 USD known usage**, remaining **2.89498800 USD**. Không reset budget theo CLI. Một request lịch sử thiếu usage nên **cumulative total/charge unknown**, không coi bằng 0. Người dùng cho phép tiếp tục rõ ràng sau khi được báo phần thiếu; không tự suy quyền chạy từ ledger.
- Giá user-reported input/cache/output 4.8/0.24/18 USD mỗi triệu token; cached input subset input, không tính reasoning hai lần. Guard mềm, request đang chạy có thể vượt trước khi biết usage; không tăng budget/tự nạp tiền.
- Provider lỗi (HTTP không 200, failed/incomplete/missing terminal/exception) kích hoạt latch **dừng batch và chặn retry native tại local**, kể cả usage đủ/guard còn dư. Không gửi retry upstream hoặc mở slot tiếp. Missing usage/cost hoặc known estimate chạm guard cũng dừng trước request/lượt sau. Slot chưa chạy giữ not_run, không task failure.
- Classifier kiểm HTTP+terminal+usage+isolation+grader; không dùng exit0/HTTP200 riêng để success. Giữ phân biệt infra_error/pending_review, timeout, task failure, success. Lỗi isolation dừng batch; không tự retry toàn lượt.
- Key host broker, nonce sandbox, bwrap namespace/home/XDG/session riêng, header allowlist/bridge Unix socket. Không dùng session thật. Giữ source/protocol/pricing/seal/config/usage/diff/grader/time/PID/witness và mọi failure.

## Lệnh chốt trước chạy

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/PILOT-SOL-CONTINUE-20261106-01 --continue-after benchmark/artifacts/PILOT-SOL-RETRY-20261106-01/result.json --run-start 18 --config-start 70 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SOL_CONTINUE.md
```

Runner kiểm continuation là single Pi/P-01 retry đã hoàn tất/success, model/provider khớp, tự tính lại prior known và carry unknown; không chỉ tin subtotal hiển thị. Snapshot chain nguồn/hash trước chạy. Sau đợt kiểm pacing xuyên CLI, classifier/usage/guard, public/hidden/scope, hash/key scan/PID/socket/Git. Kết quả ghi tài liệu riêng; **không sửa protocol trong lúc chạy**, không tự chạy lại slot thất bại hoặc mở benchmark 48/72 lượt.
