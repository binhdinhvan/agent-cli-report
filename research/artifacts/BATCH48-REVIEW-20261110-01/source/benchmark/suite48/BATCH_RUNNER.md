# Bộ điều phối benchmark48 — nghiệm thu offline, 2026-11-10

Đã hoàn thiện `benchmark/batch48.py`, [protocol candidate r1](../PROTOCOL_48_R1.md) và [launch manifest](artifacts/LAUNCH48-CANDIDATE-20261110-03/launch-plan.json). Người dùng đã đồng ý guard16USD estimate/outer-wall và tiếp tục hoàn thiện offline. **Chưa authorize dispatch**, [approval template](artifacts/LAUNCH48-CANDIDATE-20261110-03/approval-template.json) vẫn `launch_authorized=false`.

## Kết quả kiểm thực tế

- [Batch offline03](artifacts/BATCH48-OFFLINE-20261110-03/result.json): **16/16 cặp task×CLI**,40response exchanges giả trong memory,0provider requests. Cùng prepare/execute/grading/stop logic mà paid branch dùng, nhưng transport/key/pacing được tách rõ; không phải model giải task, không nhập synthetic costs vào phí thật.
- Primary timestamp trước outer bwrap spawn là origin chung cho watchdog900s và broker deadline trong paid mode. Offline watchdog90s là safety cap riêng; metadata03 phân biệt watchdog90s với broker900s. Exact native subprocess clock là secondary; setup/broker startup và supervisor grading ngoài primary.
- 10unit tests cho approval/hash/budget/scope/registry atomic/deadline/classification/per-slot drift;4flow tests local Unix broker cho missing usage/provider failure/soft budget stop và task failure vẫn đi đúng suffix. Các guard HTTP/request/output/pacing/latch còn có9test native-adapter ở pha trước.
- Per-slot kiểm input/resource identity trước prepare và sau grading; profile kiểm binary/dependency bytes trước chạy, postcheck binary và search-r2 sau chạy. Hash/resource drift là infra stop, không tự cập nhật approval hoặc cứu kết quả.
- Paid path yêu cầu manifest bound hashes/resources/order/registry và approval riêng, dùng lock trước reserve48fresh R/C. Chỉ đọc credential **sau** gates; giữ reserved/not_run IDs, không rewind/tái dùng. Index riêng `benchmark/runs-benchmark48.csv`, không sửa haiCSV pilot. Full-attempt retries và auto-resume=0; một batch đã reserve không tự chạy lại48slot.
- Task failure/timeout hợp lệ vẫn giữ và tiếp slot theo order; provider/usage/budget/isolation/infra stop dừng, suffix not_run. Timeout/provider overlap pending_review, không nâng snapshot pass thành success. Không đòi marker synthetic khi chạy paid: success dựa CLI/ledger/scope/grading, không dựa lời tự nhận.

## Revision và giới hạn

- Offline01 kiểm luồng cơ bản; offline02 bổ sung per-slot drift gates. Đều16case functional pass, giữ raw/source/candidate01–02; source trước mỗi thay đổi nằm ở `research/artifacts/BATCH48-PRE-HARDENING-20261110-01/` và `BATCH48-PRE-METADATA-FIX-20261110-01/`.
- Verifier phát hiện metadata02 gán watchdog90s vào field tên broker deadline, dù actual handler đã dùng900s. Đã sửa field và regression kiểm timeout khác900; **offline03/candidate03 là cohort nghiệm thu cuối**. Không xóa lịch sử, không gọi đó là lỗi model/provider hoặc sửa raw cũ.
- Virtual pacing ở offline không chứng minh actual30s wall gaps hoặc latency/provider stability. Paid branch dùng `PacingState()` real clock/sleep; chưa dispatch nên chưa có live acceptance cho bộ48task này.
- Resource snapshot giữ CPU/RAM/platform và cgroup fields; null là không đọc được/thông tin chưa có, không suy “không giới hạn”. CPU exclusivity/background load uncontrolled. Recheck khi launch, thay đổi identity phải re-plan/review.
- Guard16USD là estimated known usage, không hard invoice cap; request đang chạy có thể vượt guard. Pilot1.10640264USD known và6requestunpriced tách riêng. Model/backend revision/cache uncontrolled, fixture synthetic nhỏ và n=3 giới hạn suy rộng.

## Tái kiểm không gọi model

```sh
python3 -B benchmark/test_batch48.py
python3 -B benchmark/test_batch48_flow.py
python3 -B benchmark/verify_batch48.py --artifact-dir benchmark/suite48/artifacts/BATCH48-OFFLINE-20261110-03 --candidate benchmark/suite48/artifacts/LAUNCH48-CANDIDATE-20261110-03
```

Manifest candidate03 pin48input hashes, protocol hash, order48slot và host resource identity. Chưa reserve R-0039/C-0140 hoặc ID nào khác trong registry thật; proposed counters không phải allocation. Approval template disabled không phải quyền chạy. **Chỉ sau xác nhận bắt đầu48lượt trả phí riêng mới được tạo approval thực, recheck gates và dispatch.** Không đưa key vào approval/config/log, không dùng command paid như một phép thử offline.
