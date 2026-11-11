# Lượt chụp UI mới — phạm vi đã duyệt

Người dùng yêu cầu tự chạy/chụp lại sau khi được giải thích cách ly; scope chỉ là kiểm chứng UI, không mở inference/benchmark. Giữ OpenCode v2.2.5 và Desktop 2.2.5 đã pin; dùng Google Chrome độc lập hiện có, Xvfb/twm/xterm extract riêng từ package Ubuntu đã kiểm SHA-256. Không install global, không chạy installer scripts hoặc đổi source repo.

## Cách ly

Reuse bwrap profile đã kiểm: network/PID/IPC/user/UTS namespaces riêng, HOME/XDG/config/DB/service/project mới; host home/display/session/config không mount. Xvfb `:91` chỉ tồn tại trong namespace, không dùng DISPLAY/Wayland của người dùng. Desktop và browser không có GPU/device host. Chrome profile riêng, không credential người dùng; Basic auth thử tạo ngẫu nhiên chỉ trong private config/memory và không đưa vào ảnh/log chia sẻ.

Không gửi prompt. Create session có title cố định để ba UI mở cùng ID; không đọc API key hoặc paid registry, không reserve R/C IDs. Network namespace chặn egress của native processes kể cả telemetry. Tải tiện ích qua HTTPS trước lượt chạy chỉ là tải package công khai, không phải provider request.

## Acceptance trước khi thay ảnh phụ lục

1. Create session mới, lưu ID, service URL và PID trước/sau trong raw cùng lượt.
2. Desktop là packaged app thật; ảnh capture X root screen thấy khung cửa sổ thực, không chỉ CDP viewport.
3. Web là Chrome độc lập thật; ảnh thấy toolbar/address bar và route service/session; không chèn thanh địa chỉ bằng vẽ ảnh.
4. TUI native chạy qua PTY thực, hiển thị trong xterm trên display riêng; lưu raw ANSI và command chứa session ID; screenshot thật, không render log thành terminal giả.
5. Các check theo session/title/service PID đều đúng, PID/endpoint service không đổi; không trộn ảnh/raw của UI05 cũ.
6. Các process do launcher tạo được dừng theo handles; namespace supervisor đã thoát. Giữ attempt lỗi nếu readiness/capture không đạt; chỉ công bố ảnh thật sự nhìn thấy điều được claim.

Controller `ui_visible_inside.ts`/`tui_visible_inside.py`; host launcher `ui_recapture.py` dùng fresh artifact ID. Ảnh do Pillow/XCB chụp màn hình Xvfb thực; không dùng image-generation. Chrome/Desktop `--no-sandbox` bên trong OS namespace không phải security verdict của sản phẩm. Không suy universal desktop/browser/OS compatibility từ lượt này.
