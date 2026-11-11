# Baseline pilot đã đóng băng — rev1, 2026-11-09

**Phạm vi đã duyệt:** tổng kết pilot và khóa cấu hình chung offline. **Không phải duyệt protocol benchmark hoặc cho phép inference mới.**

- [Tổng kết từ hai CSV và raw](artifacts/PILOT-FREEZE-20261109-01/SUMMARY.md), [ledger JSON](artifacts/PILOT-FREEZE-20261109-01/summary.json).
- [Manifest baseline](artifacts/PILOT-FREEZE-20261109-01/baseline.json): full source commits, binary/config hashes, fixture/seal, source snapshots lúc chạy, environment/dependency/pricing/policy hashes và môi trường máy ghi trong raw.
- [Lịch sử đầy đủ](PILOT_RESULTS.md): giữ mọi failure/retry, không thay raw/CSV. R-0009 dùng reviewed `infra_error/pending_review`, vẫn giữ raw `failure/valid`. R-0027 launch-error không inference là mục riêng, không thêm giả vào CSV.

## Những gì được khóa

| Thành phần | Baseline |
| --- | --- |
| CLI | OpenCode v1.19.5, v2.2.5, Pi v1.5.0, Codex rust-v0.167.0; full SHA/checksum trong manifest |
| Model / provider | `gpt-6.1-sol` / `https://api.shopaikey.com/v1`; alias, không xác minh model gốc/backend revision |
| Transport | Responses SSE qua broker/bridge cách ly; config reference riêng từng CLI |
| Environment | `search-r2`, rg15.2.0 cùng bytes/SHA-256, read-only mount; python3/stdlib, không thêm alias hoặc pytest |
| Timing | `paced-900`: wall900s gồm pacing; reserve60s sau pacing trước dispatch; concurrency1, gap≥30s kể cả chuyển CLI |
| Request caps | Tối đa8 upstream/lượt; requested output≤2048/request |
| Dừng | Provider failure/missing usage dừng batch/chặn local native retry; thiếu reserve trả local408, không gửi upstream hoặc quy provider overload |
| Budget pilot | Guard3USD estimate kế thừa lineage; không phải invoice cap hoặc ngân sách benchmark mới |
| Fixture/grading | P-01/P-02 v2/seal; CLI completion + scope + public + hidden; snapshot pass nhưng timeout không phải success |
| Isolation | bwrap net/home/XDG/session riêng, key tại broker host; dependency/public read-only, source writable, hidden ngoài agent |

**Native settings không tương đương:** giữ native prompts/tools/permissions và generation group riêng. Codex explicit effort `none` khác nhóm capability-reasoning-off/no-forced-wire-value. Manifest giữ wire reasoning từng request và hash config đã lọc credential. Cache không kiểm soát; không bảo đảm alias trỏ cùng backend revision giữa các lần.

## Kết quả đã khóa, không xếp hạng

- **14 inference attempts / 76 upstream requests**: reviewed **8 success, 3 timeout, 3 infra_error**; một launch-error riêng không inference. Không tính coverage thành success rate8/8.
- Tám cặp task/CLI đều có success qua retry và revision khác nhau. P-01 không đồng nhất environment; không pool với P-02 để so tool.
- Cohort P-02 R-0035→R-0038: v2→v1→Codex→Pi, cùng search-r2/paced-900, **n=1/CLI**, không randomized. Cả bốn pass; duration đều dưới300s dù cap900 nên không kết luận riêng tăngcap gây success.
- Known estimate pilot **1.10640264 USD**, **6 request unpriced**; total/measured charge null. Giá user-reported4.8/0.24/18 USD mỗi triệu input/cache/output token; không gồm smoke/diagnostic ngoài pilot.

## Tái tạo/kiểm tra offline

```sh
python3 -B benchmark/test_freeze_pilot.py
python3 -B benchmark/freeze_pilot.py --verify
# Tạo lại ở thư mục MỚI, không ghi đè bản đã khóa:
python3 -B benchmark/freeze_pilot.py --output-dir benchmark/artifacts/PILOT-FREEZE-REPRO
```

Validator kiểm hash đầu vào, audited raw, launch source snapshots, review override, fixture/seal, dependency/binary, ledger và so sánh toàn output. Không đọc key, không gọi CLI/provider. Hash thay đổi là drift cần review/revision mới, không cập nhật manifest cũ để che drift. Source thực thi được giữ trong launch artifacts; manifest còn pin source hiện tại lúc đóng băng để phát hiện thay đổi sau đó.

## Benchmark vẫn pending

Xem [PROTOCOL.md](PROTOCOL.md): chưa chốt bộ4/6task đầy đủ, rubric/acceptance,48/72lượt, budget, order/seed, cách đo/exclusion/retry và người duyệt protocol. Hai fixture đã seal chỉ là baseline pilot, không mặc nhiên đủ bộ task chính thức. Chưa được gọi API trả phí mới.
