# search-r2 — năm slot còn lại, protocol rev1

Người dùng yêu cầu chạy nốt sau R-0028 v2/P-01 đã đạt. **Chỉ năm slot theo bảng**, không chạy lại P-01/Pi, Codex hoặc v2 đã có kết quả; không mở benchmark chính thức.

| Run | Task | CLI | Config |
| --- | --- | --- | --- |
| R-0029 | P-01 | OpenCode v1 | C-0118 |
| R-0030 | P-02 | OpenCode v2 standalone | C-0119 |
| R-0031 | P-02 | OpenCode v1 | C-0120 |
| R-0032 | P-02 | Codex | C-0121 |
| R-0033 | P-02 | Pi | C-0122 |

## Điều kiện cố định

- **search-r2** manifest/dependency rg15.2.0/hash read-only như `ENVIRONMENT_R2.md`; dùng cùng release/binary pinned/native settings/tools/permission và P-01/P-02 fixture v2/prompt/seal/public/hidden/grader như runner đã test. Python3 policy không đổi, không tạo alias python, không cài dependency hoặc mở Internet cho agent.
- `gpt-6.1-sol`, `https://api.shopaikey.com/v1`, Responses SSE; giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token. Native prompt/tools/reasoning không giả tương đương giữa CLI; ghi metadata và không xếp hạng quality/tốc độ từ pilot nhỏ.
- Concurrency1/khóa serialize chung batch, nghỉ **≥30 giây sau response**, cả khi chuyển CLI/task. Cap **300 giây/lượt gồm pacing**, **8 upstream request/lượt**, **2048 requested output token/request**. Title/background/native retry cũng tính cap/ledger; không nới timeout hoặc skip lỗi để đạt.
- Guard chung toàn lineage **3 USD estimate**, prior known **0.47106312 USD**, remaining known-estimate **2.52893688 USD**. **Bốn request lịch sử unpriced**, cumulative total/charge unknown, không xem missing là0. Người dùng cho phép rõ chạy tiếp năm slot; không tự suy quyền tiêu thêm từ ledger. Guard mềm không phải trần hóa đơn cứng; không tăng/nạp tiền.
- Provider error HTTP/failed/incomplete/missing terminal/transport exception kích hoạt latch **dừng batch**, native retry bị chặn local, không gửi upstream thêm. Missing usage/cost hoặc known estimate chạm guard cũng dừng trước request/lượt sau. Slot chưa chạy giữ not_run. Không tự retry toàn lượt hoặc restart đợt sau lỗi.
- Bwrap namespace/home/XDG/session mới, key host broker, dependency/public tests read-only/source writable/hidden absent. Không dùng session/service thật, thay binary/source/config người dùng hoặc bypass native sandbox.
- Chấm scope/public/hidden và witness/provider terminal/usage; không chỉ exit0 hay lời tự nhận. Giữ timeout/infra/task failure riêng. Root runtime parent được tạo lại nếu thiếu, nhưng sandbox đã có vẫn bị từ chối overwrite.

## Nhóm và lineage

`--finish-after` chỉ nhận single retry v2/P-01 trênsearch-r2 đã success/completed/modelproviderkhớp, chọn đúng năm slot còn lại và tính lại prior costs/unknown. Kết quả **CSV search-r2 riêng**, không gộp legacy với r2 như tám slot cùng môi trường. Pi/Codex P-01 trước thuộc legacy, v2/P-01 và năm slot này thuộc r2; muốn so sánh toàn bộ đồng nhất vẫn cần nhóm thực nghiệm được chốt riêng.

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/SEARCH-R2-FINISH-20261109-01 --finish-after benchmark/artifacts/SEARCH-R2-RETRY-20261109-03/result.json --run-start 29 --config-start 118 --environment-profile search-r2 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SEARCH_R2_FINISH.md
```

Protocol chốt trước request, artifact/ID dùng một lần; source/protocol/manifest/pricing/seal/binary/chain hashes và regression tests trước chạy. Giữ raw mọiattempt, usage/config che token/stdout/stderr/witness/PID/time/diff/grader. Sau dừng kiểm pacing xuyên CLI/budget/classifier/usage/keyscan/cleanup/Git, ghi báo cáo riêng; không sửa protocol trong lúc chạy, không retry để che failure.
