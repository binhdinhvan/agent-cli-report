# search-r2 — single retry v2/P-01, protocol rev1

Người dùng yêu cầu retry sau R-0025 timeout upstream ngay request đầu. **Đúng một lượt R-0026/C-0115**, session mới, retry_of R-0025; không mở năm slot khác hoặc tự retry lần nữa.

- Giữ nguyên **search-r2** manifest/dependency rg15.2.0/hash, OpenCode v2 2.2.5 standalone/binary pin, model `gpt-6.1-sol`, provider `https://api.shopaikey.com/v1`, Responses SSE, native tools/settings/permissions, P-01 fixture/prompt/seal/public/hidden/grader như `PILOT_SEARCH_R2_RECHECK.md`. Không sửa môi trường hay tăng cap để retry.
- Cap **300 giây/lượt gồm pacing**, **8 upstream request**, requested output≤2048/request. Concurrency1; nghỉ **≥30 giây sau response**. Provider failure latch dừng và chặn native retry local khi HTTP lỗi/failed/incomplete/missing terminal/exception; không tiếp tục upstream vì còn budget.
- Guard tích lũy **3 USD estimate**, prior known0.40389912 USD, remaining known-estimate2.59610088 USD. **Ba request cũ unpriced**, cumulative total/charge unknown; không coi missing là0 hoặc retry miễn phí. Đây là single retry do người dùng yêu cầu rõ sau stop, không tự vượt guard; không tự tăng/nạp tiền.
- Giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token, không phải measured charge. Guard mềm, một request đang chạy có thể vượt trước khi biết usage. Dừng trước request sau khi thiếu usage/cost hoặc known estimate chạm guard.
- Key chỉ broker host, namespace/home/XDG/session mới, dependencies/public test read-only, source fixture writable, hidden absent. Không dùng session/service thật, không thay binary hoặc cài thêm.
- Status tách infra_error/pending_review, timeout, task failure, success. Native search offline đã đạt nhưng không suy model/task đã chạy nếu request đầu lỗi. Local503 không phải bằng chứng upstream overload.
- Giữ raw R-0025/legacy/protocol/CSV; ghi r2 CSV riêng với revision/group/lineage. Không gộp r2 với legacy như cùng điều kiện.

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/SEARCH-R2-RETRY-20261109-01 --retry-run benchmark/artifacts/SEARCH-R2-RECHECK-20261109-01/R-0025/result.json --run-start 26 --config-start 115 --environment-profile search-r2 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SEARCH_R2_RETRY.md
```

Chốt trước chạy, artifact/ID chỉ dùng một lần. Giữ source/protocol/pricing/manifest/seal/binary hashes, provider ledger/config che token/stdout/stderr/diff/grader/witness/time/PID. Sau kết thúc kiểm status/terminal/pacing/usage/latch/local-blocked/cleanup, ghi kết quả riêng; không sửa protocol lúc chạy hoặc tự khởi động thêm batch.
