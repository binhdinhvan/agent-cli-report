# Pilot sol — retry kiểm tra bản sửa, protocol rev1

Người dùng yêu cầu chạy lại pilot sau sửa classifier/chống burst. Bước đầu chỉ **một lượt Pi/P-01**, retry_of R-0009; chưa mở bảy slot còn lại hoặc benchmark. R-0017/C-0069/session mới, artifact `PILOT-SOL-RETRY-20261106-01`. Giữ nguyên raw/CSV/protocol của lượt trước.

## Điều kiện cố định

- Giữ model/provider, release binary Pi 1.5.0 và fixture P-01 v2/seal/prompt/public/hidden grader như `PILOT_SOL.md`. Không đổi native settings/tools để chạy đối chứng bản sửa; `rg` thiếu trong sandbox là hạn chế môi trường còn giữ, agent có thể dùng Python stdlib/bash builtins. Không cài dependency hoặc đưa hidden tests cho agent.
- Shared known-estimate guard **3 USD**, kế thừa pilot trước **0.0280872 USD** đã tính được; remaining known-estimate guard **2.9719128 USD**. Một request trước thiếu usage, **tổng phí vẫn unknown**, không xem phần đó là 0. Đây là single retry được người dùng yêu cầu rõ, không phải tự tiếp tục sau guard. Không tính smoke/diagnostic ngoài nhóm pilot này vào ledger pilot.
- Giá user-reported input/cache/output 4.8/0.24/18 USD mỗi triệu token, chưa đối soát charge. Guard mềm, request đang chạy có thể vượt ngưỡng trước khi biết usage; không tự nạp/tăng budget.
- Concurrency **1**, khóa serialize batch; nghỉ **≥30 giây sau response**. Tối đa **8 upstream request**, requested output ≤2048/request, **300 giây/lượt** (gồm pacing). Không phát request song song hoặc retry lên provider sau lỗi. Không phối hợp với batch trả phí khác.
- Classifier kiểm HTTP **và** terminal completed, error_type, usage và ledger không rỗng; failed/incomplete/transport error/missing usage là infra_error, không giải sai task.
- Provider failure latch: HTTP lỗi, failed/incomplete/missing terminal hoặc exception thì chặn native retry tại máy, dừng batch dù response có usage/guard còn dư. Thiếu usage/cost hoặc chạm guard cũng chặn request tiếp. Không tự mở retry thứ hai sau lượt này.
- Key chỉ broker host, namespace/home/config mới, public tests read-only/hidden absent, chỉ fixture source writable; giữ witness/source/protocol/pricing/seal/config/usage/diff/grader/time/PID. Không dùng session thật, sửa binary/source tool hoặc restart service.

## Lệnh chốt trước chạy

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/PILOT-SOL-RETRY-20261106-01 --retry-run benchmark/artifacts/PILOT-SOL-20261106-01/R-0009/result.json --run-start 17 --config-start 69 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SOL_RETRY.md
```

Sau khi dừng: đối chiếu provider status/terminal và classifier, pacing/gap, local blocked retry count, usage/cumulative unknown, public/hidden/scope, key scan/PID/socket/source Git. Chỉ một lượt không chứng minh provider hết quá tải hoặc pacing live xuyên CLI; kết quả ghi riêng, không sửa protocol trong lúc chạy.
