# search-r2 — khôi phục launch lỗi, protocol rev1

Tiếp tục **một inference retry người dùng đã yêu cầu**, không thêm lượt trả phí tự động: lần launch R-0027/C-0116 lỗi FileNotFoundError tại `prepare.root.mkdir` vì runtime parent trong `/tmp` đã mất, **chưa tạo broker/chạy CLI/gửi request provider**. Giữ nguyên artifact/protocol của lần lỗi và không tái sử dụng ID.

Lượt khôi phục **R-0028/C-0117**, session mới, lineage retry_of **R-0026** (lượt inference hoàn tất gần nhất), launch_recovery_of R-0027 ghi ở protocol/audit. Không mở năm slot khác, không retry inference sau nếu provider lỗi.

Giữ mọi điều kiện `PILOT_SEARCH_R2_RETRY_02.md`: v2/P-01/search-r2, binary/model/provider/native tools/settings/prompt/fixture/seal/grader, cap300s gồm pacing/8 upstream/2048 requested output, concurrency1/nghỉ≥30 giây/failure latch, namespace/private HOME/key chỉ host/dependencies public test read-only. **Chỉ sửa harness tạo runtime parent khi thiếu (`parents=True`)**, vẫn `exist_ok=False` để không ghi đè sandbox cũ.

Guard **3 USD estimate**, prior known **0.40389912 USD**, remaining **2.59610088 USD**, bốn request cũunpriced/cumulative totalchargeunknown. Lần launch lỗi không có upstream request nên không thêm usage/cost; không sửa phí thiếu thành0, không tự tăng budget/nạp tiền. Giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token; guard mềm không phải trần hóa đơn cứng.

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/SEARCH-R2-RETRY-20261109-03 --retry-run benchmark/artifacts/SEARCH-R2-RETRY-20261109-01/R-0026/result.json --run-start 28 --config-start 117 --environment-profile search-r2 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SEARCH_R2_RETRY_03.md
```

R2 CSV riêng, không gộp legacy, giữ mọi logs/failure/protocol. Snapshot/hash nguồn và regression test trước request; sau dừng kiểm status/usage/tool execution/pacing/keyscan/PID/socket/Git. Không sửa protocol khi chạy hoặc tự khôi phục thêm một inference đã gửi rồi bị lỗi.
