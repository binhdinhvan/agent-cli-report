# Continuation47 — rubric B-01 r2, 2026-11-10

## Quyết định người dùng

Sau yêu cầu “chạy tiếp api”, người dùng chọn **Tiếp tục47slot** và **Review và sửa có revision**. Đây là authorization cho suffix chưa chạy, không retry R-0039/D48-001. Guard16USD estimate **tính cả batch cũ**, không tăng ngân sách/timeout/retry. Không gồm các demo plugin/service/API khác.

Kế thừa nguyên caps/settings/isolation/order/duration/stop rules của [R1](PROTOCOL_48_R1.md), ngoại trừ revision rubric và continuity/carry được ghi rõ dưới đây. Không sửa R1, fixture/seal/raw/CSV cũ. Không gọi probe trước paid; lỗi request thật phải được giữ và dừng theo policy.

## Review rubric và revision

Prompt B-01 yêu cầu symbol có thật hỗ trợ câu trả lời, không công khai allowlist. `ALIASES` trong fixture định nghĩa cycle graph; dẫn thêm nó bên cạnh `canonical_name` không làm evidence sai. R2 mở rộng cycle_error evidence nhận cả hai symbol, **vẫn bắt buộc canonical_name** để chứng minh exception/message. ALIASES đơn độc, symbol bịa/không liên quan, sai value/schema vẫn không đạt. Các câu khác, prompt/public/fixture và task B02–B04 không đổi.

Revision riêng tại `suite48/revisions/b01-evidence-r2/`, tạo từ bản sealed R1; seal mới pin toàn bộ bytes và chỉ cho phép thay `B-01/hidden/acceptance.py`. Reference/mutant và16native task×CLI synthetic acceptance phải đạt trước launch. Không cho agent thấy hidden grader/oracle/log/snapshot cũ.

R39 giữ **infra_error/pending_review**, raw9/10 và request5unpriced. Test answer cũ với rubric mới chỉ là regression/counterfactual có nhãn, không regrade chính thức, không đổi status/CSV hoặc coi là success. B-01 r1/r2 không gộp score cohort âm thầm; B02–B04 không đổi grader nhưng ghi continuation lineage và khoảng ngắt thời gian.

## Continuation và IDs

Chỉ lấy đúng47 `not_run` suffix D48-002…D48-048 theo order cũ. Giữ R40–86/C141–187 reserved/not_run. Reserve **47 ID mới** dưới cùng launch lock, từ counters hiện tại; ghi `continuation_of` chứa old slot/run/config cho từng row. Không tái dùng IDs hoặc chạy lại D48-001. Lần continuation này nếu dừng thì không tự resume lần nữa.

## Chi phí và missing usage kế thừa

Batch cũ known0.06853344USD,1requestunpriced; pilot tách riêng. Guard tổng16USD nên phần known-estimate được phép dùng cho continuation là **15.93146656USD**. Broker kiểm phần còn lại ngay trước request và runner trước slot. Guard không invoice cap; request đang chạy có thể vượt, request cũ unknown vẫn có thể bị tính phí.

Việc tiếp tục là quyết định explicit sau failure/missingusage cũ; chỉ bỏ latch cũ cho batch mới, **không** biến missing usage cũ thành0. Giữ `prior_unpriced_requests=1`; tổng benchmark charge/estimate vẫn null dù continuation có usage đầy đủ. Nếu continuation mới thiếu usage/provider lỗi thì latch và stop ngay, không tự retry/top-up. Pacing state mới vì batch trước đã dừng lâu; gap xuyên batch phải kiểm từ UTC kết thúc/request ledger cũ so với start mới, vẫn≥30s.

## Launch gates và implementation

`continue48.py` dùng nguyên `batch48.run_batch`, thay context suite sang revision riêng và truyền budget còn lại vào cả slot guard và broker. Không sửa sealed runner R1. Plan pin input hashes gốc + revision seal + wrapper/tests/protocol, prior raw hashes, resource identity, suffix order và current counters. Approval bind đúng plan SHA, scope47not-run, guard16/carry known/prior unknown/rubric r2. Credential chỉ đọc sau validate/lock/reserve. State chỉ cho đúng một continuation; disabled/malformed approval không đọc key/reserve.

Artifact/CSV giữ chung định dạng benchmark48 nhưng run mới có protocol/rubric/carry trong manifest và kết quả. Offline tests có namespace riêng và synthetic label, không trả phí hoặc reserve R/C. Mọi failure giữ lại.
