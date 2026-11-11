# Quyền tự hoàn thành benchmark và báo cáo

## Yêu cầu bổ sung của người dùng

“ok tôi sẽ treo máy ở đây nếu lỗi bạn cứ fix và chạy lại k cần hỏi tôi chạy đến lúc nào hoàn thành 48 lượt và viết hoàn chỉnh báo cáo thì thôi”.

Yêu cầu này mở rộng quyền repair/relaunch trước đó cho **cùng benchmark OpenAI và báo cáo**, không phải nhiều job đồng thời. Thay giới hạn operator2vòng trong `OPENAI_REPAIR_POLICY_20261110.md` bằng quyền tự sửa/chạy lại phần lỗi đến khi hoàn tất hoặc gặp giới hạn an toàn bên dưới. Policy/approval/raw cũ vẫn giữ nguyên; **không sửa code hoặc inputs đã pin của job đang chạy**.

## Phạm vi và điều kiện

- Tiếp tục jobr3hiện tại; đợi completion notification, không poll. Khi user hỏi tiến độ được kiểm status theo yêu cầu. Không khởi chạy job trùng. Khi job dừng phải kiểm cleanup trước scope mới.
- Tự chẩn đoán lỗi harness/config, viết bản sửa mới, test offline phù hợp, bindsource/hash/resource/order/registry vào protocol/approval mới rồi launch freshIDs; dẫn quyền user này làm authorization, không cần hỏi từng lần. Giữ lineage retry_of, mọi raw/failure/usage/CSV/source snapshots và reservednotrunIDs cũ.
- Đích là **48slot benchmark có kết quả hợp lệ**, không phải48task success. Validtaskfailure/timeout vẫn giữ và tính; không retrychỉđểtăngđiểm, không sửa fixture/prompt/rubric/grader để cứu điểm. Báo firstattempt vàsupplementaryretry riêng, không thay kết quả cũ bằng retry.
- Khi phải sửa transport/adapter/settings, nghiệm thu offline và native smoke thật phù hợp trước benchmark; không bỏ gate hoặc suy providerpass từ synthetic. Có thể viết protocol continuation/smoke scope tối thiểu dựa bằng chứng tương đương, không restart toàn48vì tiện.
- Provider transient có thể xem xét retry có backoff/giới hạn rõ trong **protocol mới**, lưu mọiattempt/usageunknown/chi phí; không retrymù lỗi key/hết tiền/invalidconfiguration. Không tự bật retry ẩn trongjob đangchạy hoặc quy costnull thành0. Rootcause chưa rõ và không kiểmsoátđược ngân sách thì dừng.
- **Guard16USD hiện tại không tăng**, gồm carry/reserve/smoke/retries/benchmark; khônginvoicecap, unknownusage khônggiả0. Không auto topup, không đổi model/provider/protocol hoặc nới request/output/wallcaps chỉ để hoàn thành. User không cấp quyền tiêu tiền vô hạn.
- Không đọc/hiểnthị key bằngtool; chỉ approvedhostprocess dùng keyprivate600 trongmemory, redacts full/partialkey. Không sửa source repos, binary/service/session/config thật hoặc bật plugin trong môi trường người dùng.
- Nếu giới hạn ngân sách, credential/account/provider hoặc lỗi lặp không thể xử lý an toàn ngăn hoàn tất: dừng, đóng generation gates và ghi blocker/cácslotnotrun rõ trong báo cáo; không khẳng định đã đạt48. Không hỏi lại từng bước chỉ để chạy tiếp trong scope đãduyệt.

## Hoàn thiện tài liệu

Tổng hợp metric/timing/usage/cost với giới hạn n=3/cache/provider/unknowncharge, giữ cohort/provider riêng; bổ sung bảng kết quả48, failures/retries, phương pháp và limitations. Hoàn thiện `REPORT.md`, đồng bộ `README.md`/`PLAN.md`/experimentstate và kiểm evidence/permalinks/hashes. Source-confirmed, runtime-confirmed, both vàunverified phải phân biệt; demo/runtime còn thiếu ghi pending/unverified, không giả kết quả hoặc tự chạy thử nghiệm trảphí ngoài phạm vi benchmark để gọi báo cáo “đầy đủ”. Không commit/push/công bố dữ liệu nhạy cảm khi chưa có yêu cầu.
