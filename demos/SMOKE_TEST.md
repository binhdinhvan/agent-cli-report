# Smoke test bốn cấu hình — metadata đã chạy, smoke đầy đủ chưa chạy

Mục tiêu: kiểm tra launch, cách ly, prompt/tool call và resume; **không đo hiệu quả benchmark**. Version và profile nguồn: [`../research/versions.md`](../research/versions.md), [`../research/isolation.md`](../research/isolation.md).

## Điều kiện trước khi thực thi

- [ ] Phê duyệt phương án tải binary hoặc chuẩn bị source/build riêng; có URL asset, checksum/version và absolute executable path.
- [ ] Root từng cấu hình, cwd fixture, allowlist env và config an toàn đã duyệt; không symlink tới dữ liệu thật.
- [ ] Sandbox/container hoặc hạn chế OS đã thử nghiệm phù hợp; không cấp agent quyền vào home thật chỉ để hoàn thành smoke test.
- [ ] Đã kiểm tra system config, ancestor instructions/config và effective paths; không tự sửa hoặc bypass policy hệ thống.
- [ ] Chốt model ID/provider/endpoint, auth thử, timeout và trần chi phí; không lưu secret trong source hoặc log chia sẻ.
- [ ] Có phương pháp quan sát process/file access; PID, endpoint và đường dẫn chỉ của lần thử được lưu an toàn.

Chưa đủ một điều kiện thì dừng ở preflight và ghi blocker. Có executable trên PATH không phải bằng chứng chạy được. Không dùng service status/API của môi trường thật để thử.

## Trình tự

| Bước | Thao tác dự kiến | Điều kiện đạt |
| --- | --- | --- |
| S0 | Metadata command trong env/root riêng | Version đúng release; paths quan sát khớp profile; không phát sinh kết nối tới service thật |
| S1 | Khởi tạo local/private runtime | Có PID/lifecycle xác định; v2 standalone dùng endpoint riêng; chưa coi là shared-service demo |
| S2 | Gửi prompt text ngắn | Có transcript/event và trạng thái kết thúc xác định; lỗi provider/auth được tách riêng |
| S3 | Yêu cầu đọc file fixture | Event tool call thực sự đọc file và trả đúng marker; không chấm chỉ qua lời tự nhận của model |
| S4 | Mở lại session vừa tạo | Dùng ID/path đã lưu của lần thử và có bằng chứng history được phục hồi; không truy cập session thật |
| S5 | Kết thúc lượt thử | Child/service thử kết thúc theo mode; không còn process con hoặc endpoint ngoài dự kiến |

Fixture dự kiến là Git repo tối giản mới cho từng cấu hình, có `smoke-marker.txt` chứa một marker ngẫu nhiên được harness tạo và lưu trong artifact. Prompt S3: “Đọc file smoke-marker.txt bằng tool đọc file của bạn và trả lại nguyên văn nội dung.” Không đặt marker trong prompt. S4 kiểm tra transcript/history ngoài câu trả lời của model khi API/log cho phép.

S2/S3 chỉ chạy sau duyệt model/budget. S0/S1 chưa gọi model nhưng vẫn có thể ghi file, chạy plugin hoặc tải dependency, nên cũng cần môi trường riêng và phê duyệt chuẩn bị. Không dùng `--no-session` hoặc `--ephemeral` trong S4. Timeout cụ thể còn chưa chốt; không tự chạy khi chưa có giới hạn.

## Kiểm tra cách ly

- [ ] Effective config/data/cache/state/tmp/auth/session paths nằm trong root cho phép; ghi rõ ngoại lệ runtime/system library cần thiết.
- [ ] Không dùng input/config/plugin/instructions của người dùng từ ngoài root; roots của project/ancestor/system đã được kiểm tra.
- [ ] File/process trace và sandbox policy không cho thấy đọc/ghi home thật, DB thật, plugin directory thật hoặc truy cập service endpoint thật. Trace riêng một lượt không phải chứng minh tuyệt đối mọi nhánh.
- [ ] Tạo sentinel vô hại **chỉ trong root thử** để kiểm tra config/discovery khi phù hợp; không tạo hoặc sửa sentinel trong môi trường thật.
- [ ] Plugin/extension profile được ghi rõ, bao gồm built-in bị tắt ở Pi; không dùng profile tối giản này làm benchmark chính thức mặc định.

## Artifact và kết quả

Mỗi cấu hình có demo ID riêng, lưu metadata, binary checksum, config đã lọc, env allowlist không có giá trị secret, fixture version/marker, command an toàn, PID/endpoint timeline, event/transcript, exit code, lỗi và kết quả từng S0–S5. Raw ở `demos/raw/<demo_id>/`; bản đã duyệt ở `demos/artifacts/<demo_id>/`. Không ghi đè lần trước khi retry.

Nếu cần bằng chứng trực quan, lưu screenshot từ cửa sổ/terminal thử thật trong `screenshots/` của artifact đã duyệt, kèm command, thời điểm, version và demo ID. Chỉ chụp môi trường thử, không lôi cửa sổ/session thật vào demo. Giữ bản gốc nhạy cảm ở raw nếu cần che thông tin; ghi rõ phần đã redact/crop. Ảnh kết xuất từ transcript phải ghi nhãn như vậy, không gọi là screenshot TUI. Metadata/checksum dạng text có thể chỉ cần log; không tạo ảnh cho đủ số lượng.

Đã tải/kiểm tra executable, tạo runtime directories và chạy witness cùng `--version`/`--help` cho cả bốn: xem [`PREPARATION.md`](PREPARATION.md). Đã kiểm chứng phần server/session metadata offline cho OpenCode v1/v2: [`OFFLINE_API.md`](OFFLINE_API.md). S1 và lifecycle có bằng chứng cho hai OpenCode; chưa có S2/S3 hoặc S4 theo nghĩa phục hồi lịch sử hội thoại. Chưa quan sát đầy đủ effective paths khi agent chạy, chưa khởi tạo Git fixture/marker và chưa gọi provider. Smoke đầy đủ cả bốn vẫn **unverified**. Chỉ nghiệm thu sau khi từng điều kiện có artifact; blocker không phải điểm 0 hoặc thất bại giải task.
