# Quyền sửa lỗi và chạy lại có giới hạn

Người dùng bổ sung khi job OpenAI reasoning-r3 đang chạy: **“nếu có lỗi hãy fix và chạy lại”**. Đây là steering cho cùng mục tiêu benchmark, không phải yêu cầu tạo job trùng. Không sửa script/protocol/approval hoặc source snapshots đã pin của job đang chạy.

## Giới hạn áp dụng cho các bước tiếp theo

- Assistant được tự chẩn đoán/sửa **lỗi harness hoặc cấu hình tái hiện được**, test offline rồi chạy lại bước bị ảnh hưởng. Giới hạn tự áp dụng: **tối đa2vòng repair/relaunch mới** sau yêu cầu này, không phải2retry ẩn cho mỗi upstream và khôngresetcounter khiđổilỗi.
- Chỉ sau job hiện tại dừng, cleanup được kiểm, không còn worker/scope chạy, mới reserve freshIDs và launch lượt mới. Mỗi vòng có protocol/approval riêng bindsource/hash/resource/order/registry, dẫn lại quyền user bổ sung này. Approval cũ vẫn giữ nguyên.
- Giữ guard16USD và trừ mọi estimate/reserve/usage mới theo policy hiện hành; không tăng ngân sách, khôngzero missingusage hoặc suy invoicecap. Không đổi model/provider/protocol, cap, prompt/fixture/rubric hoặc tiêu chí chấm để cứu điểm.
- Lỗi key/hết tiền/billing, usage không thể ước lượng có kiểm soát hoặc provider/transport chưa rõ nguyên nhân: dừng báo user, không retry mù. Cache TTLunknown đã có conservativeguardestimate vẫn xử lý như revision đã nghiệm thu, không phải missingusage.
- Taskfailure hợp lệ giữ nguyên; không sửa lời giải fixture, không chọn chạy lại chỉ để tăng điểm. Chỉ sửa lỗi tích hợp đã xác định; mỗi retry có lineage và không thay firstattempt bằng retry.
- Giữ mọi raw/failure/usage/config/source snapshots/CSV, bao gồm reservednotrunIDs; không phục hồi dữ liệu đã xóa. Key chỉ dùng trong approvedhostmemory, không hiển thị hoặc lưu vào artifact.
- Không bypass gate native smoke. Sau đổi adapter phải nghiệm thu offline phù hợp và smoke thật trước benchmark; chỉ kế thừa smoke nào được protocol mới chứng minh vẫn tương đương. Báo lần sửa/lần chạy lại riêng.

Hai vòng là giới hạn bảo vệ do assistant chọn trong phạm vi yêu cầu, không phải ngân sách hay quyền vô hạn do user cấp. Khi hết hai vòng hoặc vượt guard/gặp blockers trên thì dừng và báo. Không có repair/relaunch nào đã thực hiện tại lúc ghi policy này.
