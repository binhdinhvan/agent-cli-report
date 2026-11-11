# Bảng giá sol và estimate từ lượt đã lưu

Người dùng cung cấp ngày 2026-11-06 cho `gpt-6.1-sol` tại `https://api.shopaikey.com/v1`:

| Loại | USD / 1M token |
| --- | ---: |
| Input không cache | 4.8 |
| Cache read | 0.24 |
| Output | 18 |

Nguồn **user-reported**, không phải invoice-confirmed. Manifest [`../research/provider-pricing.json`](../research/provider-pricing.json). Không dùng giá model khác, không tự nạp tiền hoặc suy số dư.

## Estimate offline của diagnostic sol đã giữ

Nguồn usage: sáu response trong [`MODEL-COMPARE-GPT61-20261106-01/result.json`](artifacts/MODEL-COMPARE-GPT61-20261106-01/result.json), giữ raw artifact nguyên trạng. Bản tính riêng [`SOL-COST-20261106-01/estimate.json`](artifacts/SOL-COST-20261106-01/estimate.json) có hash source/pricing/estimator, không gọi provider hoặc đọc key.

- Input provider-reported: **106944**.
- Cached input: **72509**, giả định là subset của input, không cộng hai lần.
- Uncached input: **34435**.
- Output: **1793**, không cộng reasoning lại nếu đã nằm trong output.

`(34435 × 4.8 + 72509 × 0.24 + 1793 × 18) / 1e6 = 0.21496416 USD`.

**Khoảng 0.215 USD ước tính**, measured charge vẫn null. Không xác minh phụ phí, định nghĩa token/billing nội bộ hoặc số dư. Các input usage do gateway báo được giữ nguyên, không tự hiệu chỉnh theo prompt nhìn thấy. Không ngoại suy một lượt thành chi phí chắc chắn của 8 lượt pilot.

```sh
python3 -B benchmark/estimate_saved_usage.py --result benchmark/artifacts/MODEL-COMPARE-GPT61-20261106-01/result.json --artifact-dir benchmark/artifacts/SOL-COST-20261106-01
```

Artifact trên đã tồn tại; nếu tính lại phải đổi artifact mới, không ghi đè. Cập nhật giá và tính từ dữ liệu cũ **không tự khởi chạy model**. Cần review ngưỡng budget/settings/smoke trước pilot nhóm mới.
