# Phụ lục minh chứng để ghép vào PDF báo cáo

## File để gửi

- [APPENDIX.pdf](../APPENDIX.pdf): **3 trang A4**, có thể gửi riêng hoặc ghép sau PDF báo cáo chính.
- [APPENDIX.html](../APPENDIX.html): bản tự chứa ảnh PNG và biểu đồ SVG, mở bằng browser để xem/in; không cần thư mục ảnh đi kèm để hiển thị.

Không có PDF báo cáo 16 trang trong workspace tại thời điểm tạo phụ lục, nên chưa ghép hoặc sửa link trong PDF chính. Phụ lục ghi đường dẫn artifact dưới dạng văn bản, không tạo `file://` link hoặc giả URL repository chưa publish. PDF/HTML này không thay bộ source/evidence đi kèm.

## Nội dung và tính xác thực

1. **A — Kiến trúc:** dùng ba ảnh mới từ [VISIBLE-UI07](../demos/UI_RECAPTURE_RESULTS.md): Desktop có khung thật, Chrome độc lập có thanh địa chỉ thật, TUI native hiển thị trong xterm thật. Session ID/PID lấy từ raw cùng lượt mới. A1/A2 cắt pixel vùng trên để phóng chi tiết nhận diện, có nhãn rõ; ảnh gốc 1600 × 1050 giữ nguyên trong artifact. Không vẽ thêm khung/thanh địa chỉ hoặc dùng ID/PID cũ.
2. **B — Chức năng:** trích trường/log có thật từ Client, SDK, permission và plugin port. Đây là trình bày lại raw, **không phải ảnh chụp terminal thật**. Script kiểm check/witness và loader error trước khi xuất. Inference scripted local, không đo model quality.
3. **C — Benchmark:** success và median từ CSV 48 lượt, input token cộng từ request usage trong 48 raw result. Giữ hai failures trong median, ghi rõ pacing và giới hạn cohort. Không chạy lại model để lấy số đẹp.

Nguồn và SHA-256 của 60 input files trong bản hiện tại ở [manifest revision 4](artifacts/APPENDIX-20261111-04/manifest.json), gồm metadata crop pixel và hash ảnh dẫn xuất. Revision 4 chỉ thêm đường dẫn receipt review ngay dưới khung xác minh trên trang A; ảnh và cảnh báo Chrome giữ nguyên. Source dựng phụ lục: [build_appendix.py](build_appendix.py); chạy từ workspace bằng `python3 -B research/build_appendix.py` để tái tạo HTML và manifest, không gọi API hoặc native agent.

**Trạng thái hiện tại:** trang A có khung Session ID mới, PID `12 → 12` và shared-service checks PASS; raw status `checks_passed_pending_review` giữ nguyên, [review ảnh/raw độc lập](artifacts/NATIVE-VISIBLE-UI-REVIEW-20261111-01/validation.json) xác nhận đạt. Trang B tách Before/After port; chart/data không đổi. [PDF revision 1](artifacts/APPENDIX-20261111-01/APPENDIX.pdf) và [revision 2](artifacts/APPENDIX-20261111-02/APPENDIX.pdf) được giữ riêng, không sửa ngược receipts/raw cũ.

Repository public để mở các đường dẫn artifact: [binhdinhvan/agent-cli-report](https://github.com/binhdinhvan/agent-cli-report). PDF hiện tại vẫn giữ đường dẫn dạng văn bản, chưa tự đổi thành hyperlinks; gửi kèm URL repository. Các receipt cũ ghi trạng thái chưa publish là ghi nhận lịch sử, không sửa hash/receipt để khớp trạng thái công bố mới.

PDF được in từ HTML bằng Chrome headless trong bwrap network/PID namespace riêng; HOME/profile/tmp mới, root filesystem read-only, không dùng profile Chrome hoặc service/session thật. Chrome dùng `--no-sandbox` **bên trong namespace cách ly**, không phải phép nghiệm thu security của browser. Lượt in đầu không tạo được socket do `/tmp` read-only; lượt sau bind private tmp và thành công, không đổi dữ liệu để sửa kết quả.

Đã kiểm ba trang A4 bằng `pdfinfo` và render preview để xem bố cục. Không cài dependency hệ thống; tiện ích chụp GUI được tải/kiểm SHA-256/extract riêng trong `.local`, không chạy installer scripts. Không gọi thêm inference hoặc đọc credential thật.

## Có cần tự chụp thêm không?

**Không cần làm thủ công cho phụ lục hiện tại:** đã tự chụp đủ Desktop, Chrome và TUI trong lượt cách ly mới theo yêu cầu. Session vẫn có khoảng trống vì chỉ kiểm việc mở cùng session, không giả thêm hội thoại để làm ảnh đẹp hơn. Các attempt chưa đạt được giữ trong tài liệu kết quả, không dùng ảnh đen/ảnh lỗi như proof đạt.

Nếu mentor yêu cầu ảnh mới trên môi trường của bạn, chỉ chụp sau khi chuẩn bị service/config/session cách ly như quy trình demo. Với mỗi giao diện, mở cùng session thử nghiệm, giữ title/session ID nhìn thấy được; lưu ảnh gốc và thông tin service ID/PID cùng thời điểm. Không chụp API key, config credential, conversation thật hoặc dùng ảnh đơn lẻ để khẳng định cùng PID. Không tự chạy lại benchmark hay dùng service đang làm việc chỉ để lấy screenshot.
