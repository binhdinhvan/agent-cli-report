# Sửa pacing xuyên CLI — kiểm chứng offline

Sau review smoke sol, đã sửa `demos/model_smoke.py:PacingState/handler/main` và `benchmark/pilot.py:main` để mỗi batch có **một** trạng thái monotonic và khóa serialize dùng chung. Mỗi broker/CLI nhận cùng object; không reset thời điểm hoàn tất request khi chuyển CLI/task. Deadline riêng từng CLI vẫn giữ, thời gian chờ vẫn tính trong timeout; không tăng budget hoặc cap.

`handler` cập nhật trạng thái trong `finally`, nên HTTP error/exception cũng không cho request tiếp theo gửi ngay. Không đủ thời gian nghỉ trước deadline thì trả HTTP 408 local, không mở upstream. Mặc định caller không truyền state vẫn có state riêng để giữ tương thích; runner smoke và pilot đều truyền state batch một cách tường minh.

## Kiểm tra đã chạy

| Suite | Kết quả |
| --- | ---: |
| `python3 -B demos/test_pacing.py` | 5/5 |
| `python3 -B demos/test_model_smoke.py` | 7/7 |
| `python3 -B benchmark/test_pilot.py` | 6/6 |
| `python3 -B demos/test_provider_pricing.py` | 5/5 |

Test mới dùng **hai Unix broker liên tiếp**, chung state/ledger, fake monotonic clock và fake sleep: sau 2 giây chuyển CLI phải nghỉ thêm 28 giây. Bao gồm completed, HTTP 503 giả, OSError giả và deadline không đủ; spy xác nhận không tạo upstream trong nhánh deadline. Không đọc key thật, không Internet/model request, không giả làm số đo pacing live.

Source trước sửa đã lưu ở `artifacts/PACING-FIX-20261106-01/before/`; hash file smoke khớp đợt raw cũ. Source sau sửa và hash raw artifact được kiểm tra tại `artifacts/PACING-FIX-20261106-01/validation.json`. Protocol smoke sol rev1/raw log **không sửa**, không nâng lượt cũ thành protocol-pass sau khi sửa harness.

Trạng thái: **offline-confirmed**, chưa runtime-confirmed với provider cho pacing xuyên CLI sau sửa. Không tự rerun smoke hoặc mở pilot. Trước nhóm pilot mới cần chốt budget/settings/protocol revision; không dùng kết quả này để khẳng định pilot đủ tám lượt sẽ thành công.
