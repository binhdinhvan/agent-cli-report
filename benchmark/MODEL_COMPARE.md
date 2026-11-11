# Kết quả sol được giữ — Pi/P-01 diagnostic

Artifact gốc giữ nguyên: [`MODEL-COMPARE-GPT61-20261106-01/result.json`](artifacts/MODEL-COMPARE-GPT61-20261106-01/result.json), protocol/hash và script tại cùng thư mục. Catalog exact ID giữ ở [`MODEL-COMPARE-CATALOG-20261106-01/result.json`](artifacts/MODEL-COMPARE-CATALOG-20261106-01/result.json). Tên artifact là ID lịch sử, không đổi/reuse.

## Quan sát runtime của sol

- Model field `gpt-6.1-sol`, provider `https://api.shopaikey.com/v1`, Pi release/binary đã pin, P-01 fixture v2, C-0039/session thử riêng.
- Lượt `08:14:31Z`–`08:18:16Z` ngày 2026-11-06: **6/6 HTTP 200/completed**, không timeout, Pi exit 0 và assistant cuối `stopReason="stop"`.
- Chỉ sửa `intervals.py` trong fixture tạm; **scope/public/hidden tests đều đạt**. Snapshot/diff/output ở [`grader/`](artifacts/MODEL-COMPARE-GPT61-20261106-01/grader/).
- Khoảng nghỉ sau response trước ≥30 giây đủ năm gap. Replay reasoning counts 0,0,0,1,1,1; không gặp lỗi encrypted context trong lượt này, nhưng chưa kiểm tra nhiều encrypted items đồng thời hoặc nhiều lần lặp.
- Witness namespace/home/hidden tests/public-test read-only đạt. Không thay client/proxy/source tool; key scan/cleanup đã kiểm tra. Không suy model gốc phía sau alias hoặc provider ổn định tổng quát.
- Tại thời điểm chạy chưa có giá: raw estimate/charge **null** được giữ nguyên. Sau khi người dùng cung cấp giá, ledger riêng tính **0.21496416 USD ước tính**, không phải measured charge: [`SOL_COST.md`](SOL_COST.md).

## Sau yêu cầu xóa dữ liệu cũ

Phần control và các lượt model cũ đã xóa, nên **rút mọi kết luận so sánh hai model**. Raw sol artifact không sửa để giữ tính toàn vẹn; trường previous_model/comparison_against và `run.py` có thể nhắc ID control đã rút. Các trường này không phải artifact control còn tồn tại và không được dùng làm bằng chứng so sánh hiện tại. Script diagnostic đã seal không chạy lại; source helpers tương ứng được snapshot trước chuyển đổi để đối chiếu hash.

Sol là model mặc định và giá user-reported đã có; không có nghĩa ba CLI khác đã được model smoke hoặc pilot đủ 8 lượt đã chạy. Review settings/budget/smoke trước nhóm mới có ID mới. Không ghi diagnostic này vào CSV pilot chính thức.
