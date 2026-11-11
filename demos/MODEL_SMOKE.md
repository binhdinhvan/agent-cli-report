# Smoke gpt-6.1-sol — ba CLI còn lại, protocol sol rev1

Model mặc định đã chuyển sang `gpt-6.1-sol`; provider/release binaries giữ nguyên. Hiện chỉ có diagnostic Pi/P-01 [đã giữ](../benchmark/MODEL_COMPARE.md). **Chưa có model smoke sol cho OpenCode v1/v2 hoặc Codex**, không suy bốn cấu hình đạt từ kết quả model đã xóa.

Đã có giá user-reported đúng model/provider; chưa chạy nhóm mới chỉ từ cập nhật giá. Runner `model_smoke.py` kiểm tra giá trước key/artifact. Đề xuất profile mới C-0045–C-0048 (không tái sử dụng ID đã retire), artifact mới; prompt cùng fixture chỉ đọc, local tool đọc marker thật, final đúng marker/exit 0/provider completed/namespace riêng/fixture không đổi mới đạt.

Giữ broker ngoài sandbox, key host, bridge loopback→Unix socket, allowlist header protocol, stream Responses, fixed model/endpoint, cap 4 request/CLI và output yêu cầu 512, timeout 180 giây. Cần review lại config/generation settings cho sol đủ bốn CLI trước kết luận so sánh. Không chạy chỉ từ ví dụ lệnh khi chưa có giá/đồng ý.

Ví dụ **sau** khi có giá và được phép:

```sh
python3 -B demos/model_smoke.py --artifact-dir demos/artifacts/MODEL-SMOKE-SOL-20261106-01 --config-start 45
```

Giữ regression parser lấy completed agent message cuối của Codex (E-0065), không ghép progress vào final. Code/header guard có unit tests offline; kết quả runtime model cũ và artifact minh chứng cũ đã rút khỏi evidence. Nguồn implementation vẫn ở `research/evidence.csv`; không nâng source-only thành sol runtime-confirmed.

## Đợt được người dùng đồng ý sau cập nhật giá — chốt trước chạy

Chỉ OpenCode v1 → OpenCode v2 standalone → Codex, profile/session mới C-0045/C-0046/C-0047. Pi không chạy lại vì đã có diagnostic sol/P-01 đạt; không gộp nó thành một lượt marker smoke giống ba CLI này. Không mở pilot.

- Cùng prompt/marker read-only như runner; không sửa fixture, cần event tool đọc marker thật và final đúng marker/exit 0/provider completed. OpenCode final lấy text parts của message cuối, Codex final lấy agent message cuối, không ghép progress. Error events hoặc request upstream không hoàn tất đều không pass.
- **Shared budget guard 0.50 USD ước tính cho cả đợt**, không reset mỗi CLI. Giá user-reported đã chốt 4.8/0.24/18; không phải trần hóa đơn cứng, một request có thể vượt guard trước khi biết usage. Dừng trước request/lượt kế tiếp khi chạm ngưỡng hoặc thiếu usage/cost; slot chưa chạy giữ not_run, không gọi là tool failure.
- Tối đa 4 upstream requests/CLI, requested output ≤512, 180 giây/CLI. Serialize và nghỉ ≥30 giây sau response trước, tính pacing trong timeout/duration. Title/background generation cũng tính cap/budget; v1 small_model cố định đúng sol (E-0070), không dùng model phụ khác. Codex effort none/native read-only, approval never, retry native 0; không bypass sandbox.
- Key host, bwrap network namespace riêng, bridge/header allowlist như đã kiểm tra; không service/config/session thật. Giữ mọi failure và native retries, không retry toàn lượt tự động. Không xếp hạng quality/tốc độ từ smoke.
- Runner/hash/pricing/protocol snapshot trước request, log/usage/witness/PID và summary từng slot. Sau đợt mới quyết định pilot, không tự tăng budget nếu hết.

```sh
python3 -B demos/model_smoke.py --artifact-dir demos/artifacts/MODEL-SMOKE-SOL-20261106-01 --config-start 45 --tools opencode-v1 opencode-v2 codex --budget-usd 0.50 --request-gap-seconds 30
```

Chưa có kết quả tại thời điểm chốt; kết quả ghi ở tài liệu riêng sau khi dừng, không sửa protocol này trong lúc chạy.
