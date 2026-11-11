# Thiết kế bộ 48 lượt — draft rev1

Người dùng đồng ý hướng **4 task × 4 CLI × 3 lần** và cho phép soạn task/protocol/dự toán offline. **Chưa duyệt budget, protocol cuối hoặc inference.**

Đây là **đặc tả task và prompt**, không phải fixture đã nghiệm thu. Chưa có code fixture, public/hidden tests, oracle/rubric executable, reference/mutants hoặc seal cho B-01–B-04; các trường này giữ pending. Không dùng runner pilot để giả chạy bộ task này.

| ID | Nhóm | Fixture đề xuất | Đầu ra / tiêu chí chính |
| --- | --- | --- | --- |
| B-01 | Hiểu code | Resolver cấu hình ba file | `answer.json`: 5 câu trả lời có source references; rubric10điểm |
| B-02 | Sửa bug | Gộp các trang bản ghi | `pagination.py`: ổn định thứ tự, update duplicate, không mutation |
| B-03 | Thêm tính năng | TTL/LRU cache với injected clock | `cache.py`: expiry/capacity/default/eviction không sleep |
| B-04 | Refactor nhiều file | Dispatcher ba command | Tách validation/handlers, giữ API và hành vi cũ |

- [Manifest draft](manifest.json): scope, câu hỏi/contract, acceptance matrix và điểm còn thiếu.
- Prompt nguyên văn đề xuất: [B-01](B-01/prompt.txt), [B-02](B-02/prompt.txt), [B-03](B-03/prompt.txt), [B-04](B-04/prompt.txt). Cùng bytes cho mọi CLI trong một task, không điều chỉnh theo kết quả.
- [Protocol48](../PROTOCOL_48_DRAFT.md): kiểm soát, order, retry, cách đo, dự toán và gates.
- [Thứ tự48slot](artifacts/DRAFT48-20261109-01/order.csv), [dự toán offline](artifacts/DRAFT48-20261109-01/planning.json).

## Tái tạo offline

```sh
python3 -B benchmark/test_plan48.py
python3 -B benchmark/plan48.py --verify
```

`plan48.py` chỉ đọc JSON/prompt và số đo pilot đã lưu, tạo order/dự toán/hash. Không import runner, gọi binary/model/provider hoặc đọc credential. Slot `D48-*` không phải run IDs, không reserve R/C hoặc tạo kết quả benchmark.

## Gate trước khi coi task ready

1. Viết fixture tự tạo version1, public/hidden tests và oracle đúng contract; không đưa log/answer pilot vào fixture. License phân phối vẫn chờ người dùng, không gán license upstream.
2. Chạy reference + baseline + mutants offline: B-01 thiếu answer phải fail; B-02/B-03 baseline public pass, hidden fail; B-04 baseline behavior pass nhưng cấu trúc mới fail. Reference phải pass mọi mục; mutants sai từng tiêu chí phải bị phát hiện.
3. Chốt oracle/rubric B-01 bằng dữ liệu cấu trúc, không chấm theo văn phong hoặc lời tự nhận; kiểm lại câu hỏi thật sự được trả lời từ code.
4. Tích hợp grader/runner cách ly cho task đọc code và refactor (khác pilot), kiểm scope/readonly/hidden-absent, usage/duration/event/ID allocation, rồi tạo seal mới. Không sửa baseline pilot đã khóa.
5. Duyệt budget và protocol chính thức, ghi người duyệt/ngày/revision; chỉ khi đó mới cấp quyền paid-entrypoint.
