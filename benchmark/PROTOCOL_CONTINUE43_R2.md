# Continuation43 — không retry lượt đã chạy

Người dùng yêu cầu **“chạy tiếp”** sau khi được báo retryR134 đạt và R135/Codex-B02timeout. Scope lần này là **43slot chưa chạy D48-006…D48-048**, giữ order gốc; **không retryR135** hoặc bất kỳ slot đã có attempt. Nếu provider/usage/infra lỗi thì dừng; không tự mở continuation mới, không top-up. Task failure/timeout hợp lệ giữ nguyên và có thể tiếp slot sau theo policy cũ.

Kế thừa nguyên [protocol r2](PROTOCOL_47_CONTINUE_R2.md) về fixture/prompt/rubric, settings/model/provider, isolation, caps900s/reserve60/request8/output2048 và pacing≥30s xuyên CLI, cách đo và phân loại. Không sửa rubric r2 hoặc raw/status/CSV cũ. R134 supplementary retry vẫn tách R89 first-attempt infra_error; không thay firstattempt bằng retry success.

Ba batch trước known **0.25185936USD**, **3requestunpriced**; guard tổng vẫn **16USD estimated known usage**, phần dùng cho batch mới **15.74814064USD** tại cả broker và slot gate. Tổng charge vẫn null; missing usage cũ không đổi thành0. Explicit continuation mở latch mới, nhưng failure/usage thiếu mới vẫn stop. Không probe hoặc generation kiểm tra riêng trước batch.

43IDs mới reserve dưới lock từ registry hiện tại, dự kiến R179–221/C280–322. Giữ toàn bộ IDs reserved/not_run cũ, ghi lineage tới row chưa chạy trong batch retry45. Không nạp session/lời giải cũ. Tối đa43firstattempts mới; báo unique slots/attempts/retry riêng.

`continue43.py` dùng nguyên context/broker/dispatcher đã kiểm; chỉ thêm scope43/schedule từ raw đã audit, approval và reservation mới. Plan bind3predecessor raw/hash/resource/seal/order/counters cùng protocol/script/tests. Offline tests và16native synthetic task×CLI acceptance trước approval; credential đọc sau validate/lock/reserve. Runner từ chối khi đã có batch thứ4; không dùng lệnh paid như test offline.
