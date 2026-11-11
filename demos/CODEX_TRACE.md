# Codex protocol — source và harness hiện tại

Giữ truy vết source E-0060–E-0065: nhánh Responses Lite dùng `additional_tools` trong input; HTTP request type không có `previous_response_id`; client thêm header Lite; final message là completed agent message cuối. Runtime traces model cũ đã xóa theo yêu cầu, nên các evidence liên quan chỉ còn source-confirmed.

Harness hiện giữ header protocol qua cả bridge/broker theo `proxy_headers.py`, thay Authorization ở host, không chuyển cookie/hop-by-hop/credential response. Unit tests offline kiểm tra header/auth/error/status, không thay bằng kết luận Codex đã chạy sol. `codex_trace_offline.py` yêu cầu artifact/config ID mới, không tự dùng lại ID đã retire; mock SSE/HTTP 418 không phải số đo model.

Chưa chạy Codex/sol sau chuyển đổi. Muốn xác minh phải tạo profile mới và artifact mới; không restart service thật hoặc dùng session người dùng.
