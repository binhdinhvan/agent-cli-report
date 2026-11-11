# Pi context — nguồn implementation

Giữ source evidence E-0071–E-0076 về lưu/replay `thinkingSignature`, xử lý same-model, store=false và backfill encrypted_content. Các runtime traces/model cũ đã xóa theo yêu cầu; source không tự chứng minh backend cryptographic validity hoặc runtime của model sol.

`trace_pi_context.py` là helper lịch sử phụ thuộc dataset đã rút, hiện từ chối thực thi. Muốn trace sol phải thiết kế dataset/profile/artifact mới, không tải session thật hoặc khôi phục kết quả đã xóa. Không strip encrypted context hoặc đổi payload âm thầm.
