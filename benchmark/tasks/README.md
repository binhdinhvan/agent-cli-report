# Fixture pilot tự viết — version 2

Chỉ `P-01/fixture/` hoặc `P-02/fixture/` được copy vào workspace agent; prompt tương ứng từ `prompt.txt`. `acceptance.py`, script supervisor, báo cáo/log và oracle **không** mount cho agent. Hai fixture chỉ dùng Python standard library, không cài dependency hoặc truy cập repo source tool. Đây là code nhân tạo tự viết trong workspace báo cáo, không lấy từ repo bên thứ ba; không gán license upstream. License phân phối của workspace chưa được người dùng chốt.

| Task | Nhóm | Baseline public | Hidden acceptance |
| --- | --- | --- | --- |
| P-01 | Sửa bug interval boundaries/validation/mutation | 1 test phải pass | 7 test methods; baseline phải fail, reference phải pass |
| P-02 | Thêm tính năng dependency ordering | 1 test phải pass | 9 test methods; baseline phải fail, reference phải pass |

Version fixture/prompt/test khóa bằng SHA-256 từng file trong artifact chuẩn bị pilot. Mọi thay đổi sau khi seal phải tạo artifact mới, không ghi đè. Chưa phải bộ task benchmark chính thức 48/72 lượt.

Version 2 bổ sung phạm vi sửa file vào prompt để agent thực sự được biết tiêu chí chấm; chỉ cho ngoại lệ cache `__pycache__` sinh tự động. Thuật toán nguồn/public/hidden tests không đổi. Toàn bộ bytes version 1 đã lưu trước thay đổi tại `benchmark/task-history/fixture-v1/`, seal cũ giữ nguyên; version 2 phải có self-test/seal mới.

## Acceptance và phạm vi sửa

- P-01: chỉ `intervals.py` được sửa; P-02: chỉ `scheduler.py` được sửa. Không thêm/xóa file hoặc sửa public tests. Supervisor so file tree/bytes, không chỉ dựa trên agent tự nhận.
- Mỗi lượt chấm cả public và hidden tests; exit 0 tất cả, đúng phạm vi file, không timeout mới đạt. Tool không bắt buộc trả văn bản theo một marker; câu trả lời cuối không thay acceptance tests.
- Public command tại fixture: `python3 -B -m unittest -v test_public`.
- Hidden command được supervisor chạy trong sandbox chấm riêng sau khi dừng agent: `python3 -B /grader/acceptance.py`. `/grader` chỉ được mount ở pha chấm; Python import target bằng cwd/PYTHONPATH đã cách ly. Không chạy code do agent sửa trực tiếp trên host.
- Timeout test đề xuất 15 giây mỗi suite; output giới hạn 1 MiB. Không network/credential/provider socket trong pha chấm. Agent không ghi được thư mục public test khi chính thức dựng sandbox; nếu native tool cần atomic replacement file nguồn phải cho ghi thư mục fixture nhưng re-mount test read-only.
- Input bool cho P-01 không đưa vào rubric vì Python bool là subclass int; outer iterable không hợp lệ không thuộc contract. P-02 chỉ xét dictionary string→list[string] như prompt, không đo validation kiểu dữ liệu ngoài contract.

Task không có full Git commit vì fixture tự viết và workspace báo cáo chưa khởi tạo Git. Không thay hash artifact bằng commit giả.
