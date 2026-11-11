# Hướng dẫn làm việc

## Phạm vi

Workspace này dùng để hoàn thiện báo cáo trong REPORT.md; README.md là trang giới thiệu và điều hướng. Đọc PLAN.md trước khi thực hiện.
Các repo source nằm ở thư mục cha: ../opencode-v1, ../opencode-v2, ../pi, ../codex.

## An toàn và tính tái lập

- Mặc định chỉ đọc các repo tool. Không sửa, checkout, cài dependencies hoặc chạy installer trong đó khi chưa xác định tác động và được người dùng cho phép.
- Không thay thế binary OpenCode đang dùng, restart service đang dùng hoặc dùng dữ liệu session thật để thử nghiệm.
- Cách ly config, dữ liệu, plugin và service của các bản thử nghiệm bằng cơ chế thực sự được từng phiên bản hỗ trợ; không tự đoán biến môi trường.
- Không lưu API key/password vào source, config mẫu, báo cáo hay log chia sẻ.
- Không tạo kết quả benchmark giả. Ô trống hoặc `unverified` khác với 0 hoặc thất bại.
- Không cài hoặc bật plugin của một phiên bản trong môi trường người dùng đang sử dụng.

## Bằng chứng

- Mọi nhận định kỹ thuật cần commit, file, dòng/symbol và permalink cố định theo commit.
- Phân biệt source-confirmed, runtime-confirmed, both và unverified.
- Tài liệu/README chỉ là định hướng; nhận định implementation phải truy tới code.
- Không kết luận không hỗ trợ chỉ vì tìm kiếm lần đầu chưa thấy.
- Đọc hướng dẫn repo liên quan trước khi thay đổi code hoặc chạy kiểm thử tại repo đó.

## Thực nghiệm

- OpenCode v2 đại diện cho OpenCode trong so sánh ba tool; benchmark gồm cả v1 và v2, tổng cộng bốn cấu hình.
- Chốt version, protocol và acceptance tests trước khi chạy chính thức.
- Giữ nguyên prompt, fixture, giới hạn và cấu hình trong cùng một nhóm so sánh.
- Nếu không dùng cùng model/provider được, tách kết quả và nêu yếu tố gây nhiễu.
- Ghi lỗi môi trường/provider riêng với lỗi tool và lỗi giải task; giữ mọi lần thử và đánh dấu lượt chạy lại.
- Viết tài liệu bằng tiếng Việt, giữ nguyên tên API/symbol trong code.
