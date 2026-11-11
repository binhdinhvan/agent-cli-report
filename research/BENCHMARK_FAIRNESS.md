# Phân tích bổ sung: token, request và pacing

Đây là **phân tích dẫn xuất từ raw OpenAI48 r3**, không phải lượt benchmark mới. Giữ cả hai failure trong 48 lượt. [Raw cohort](../benchmark/suite48/artifacts/OPENAI48-R3-20261110-01/benchmark/result.json), [48 rows](../benchmark/suite48/artifacts/OPENAI48-R3-SUMMARY-20261111-01/RUNS48.md), [script chỉ đọc](analyze_final_cohort.py).

Tái tính từ workspace: `python3 -B research/analyze_final_cohort.py`. Script kiểm 48 unique slot, 46 success, 278 upstream HTTP 200/completed, 16 nhóm task/CLI × 3 lượt và xuất SHA-256 của từng raw input. Không đọc key, không gọi API hoặc sửa raw.

## 1. Token trên mỗi request theo task

Mỗi dòng gộp ba lượt của một task/CLI. `Req/lượt = tổng upstream / 3`; các cột token là `tổng token / tổng upstream`, không phải trung bình không trọng số của các trung bình lượt. Cache read/write là thành phần của input, **không cộng thêm vào input**; output gồm reasoning. Làm tròn một chữ số thập phân.

| Task | CLI | Upstream | Req/lượt | Input/req | Cache read/req | Cache write/req | Output/req |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B-01 | v1 | 18 | 6,0 | 3879,4 | 2845,0 | 867,1 | 118,0 |
| B-01 | v2 | 18 | 6,0 | 3079,7 | 2237,3 | 689,9 | 98,9 |
| B-01 | Pi | 15 | 5,0 | 1972,7 | 1483,9 | 485,8 | 77,5 |
| B-01 | Codex | 12 | 4,0 | 12075,1 | 8873,1 | 3199,0 | 136,8 |
| B-02 | v1 | 21 | 7,0 | 3436,7 | 2683,8 | 635,8 | 114,7 |
| B-02 | v2 | 18 | 6,0 | 2561,9 | 1854,8 | 585,8 | 124,7 |
| B-02 | Pi | 14 | 4,7 | 1533,6 | 1118,6 | 411,9 | 135,1 |
| B-02 | Codex | 11 | 3,7 | 11924,5 | 8390,3 | 3531,3 | 198,5 |
| B-03 | v1 | 19 | 6,3 | 3588,3 | 2694,3 | 752,7 | 137,5 |
| B-03 | v2 | 21 | 7,0 | 2882,0 | 2206,2 | 560,4 | 129,7 |
| B-03 | Pi | 15 | 5,0 | 1800,3 | 1340,3 | 456,9 | 139,6 |
| B-03 | Codex | 14 | 4,7 | 12115,9 | 9336,7 | 2776,1 | 225,5 |
| B-04 | v1 | 22 | 7,3 | 4363,0 | 3383,3 | 863,9 | 270,5 |
| B-04 | v2 | 21 | 7,0 | 3434,8 | 2541,0 | 785,4 | 304,8 |
| B-04 | Pi | 24 | 8,0 | 2435,9 | 1986,0 | 447,0 | 200,0 |
| B-04 | Codex | 15 | 5,0 | 12847,3 | 9946,1 | 2898,3 | 376,1 |

**Quan sát:** Codex có input/req lớn nhất ở cả bốn task, nhưng ít request hơn Pi ở cả bốn task. Toàn cohort: Codex khoảng 12.277 input/req so với Pi 2.008, tức khoảng 6,11 lần (tính tỷ lệ trước khi làm tròn); số request 52 so với 68 làm tỷ lệ tổng input còn khoảng 4,68 lần. Đây là phân rã số học từ usage, **không xác định nguyên nhân bên trong prompt**.

System instructions, tool schema, history projection, cache và compaction là các yếu tố cần kiểm riêng để giải thích nguyên nhân. Chưa có phân rã token theo từng thành phần để quy chênh lệch cho một yếu tố. Usage cache read không đồng nghĩa model xử lý ít context hơn hoặc hóa đơn đã đối soát. Số request cũng không đồng nhất với số tool call.

Theo task, v2 có median B-03 235,07 giây so với v1 203,50 giây, dù median toàn cohort v2 thấp hơn. Pi có median B-04 279,20 giây so với Codex 183,27 giây; cả ba lượt Pi/B-04 dùng đủ 8 upstream, nhưng chỉ một lượt là end-to-end failure. Vì vậy chạm đúng 8 request tự nó chưa đủ kết luận failure; cần terminal/error riêng.

## 2. Timing đã đo và chưa đo

Các cột dưới là **median tính riêng từ 12 lượt/CLI**, gồm failure. `Pacing/lượt` là tổng `requests[].pacing_wait_seconds` của lượt đó; có thể gồm gap chuyển từ lượt trước. `Native` là `execution.native_clock.duration_ms`, vẫn gồm chờ model/tool và pacing trong subprocess, không phải CPU time.

| CLI | End-to-end, giây | Pacing/lượt, giây | Native subprocess, giây |
| --- | ---: | ---: | ---: |
| v1 | 228,15 | 204,64 | 227,83 |
| v2 | 200,20 | 178,26 | 199,86 |
| Pi | 164,23 | 148,27 | 163,93 |
| Codex | 139,63 | 118,28 | 139,21 |

Pacing là thành phần lớn của protocol; thứ hạng thời gian không phải phép đo tốc độ runtime thuần. **Không lấy hiệu hai median để gọi là thời gian CLI thuần**: các median có thể thuộc những lượt khác nhau. Provider compute time và tổng tool execution time chưa được phân rã bằng instrumentation đồng nhất; không suy từ phần thời gian còn lại. Timestamp broker không tự tách được network, queue và compute phía provider.

## 3. Tính công bằng và ranh giới kết luận

- Giữ cùng user prompt, fixture, model/provider, budget và dependency search; fresh session/workspace mỗi lượt, thứ tự CLI cân bằng.
- Native instructions, tool schema, số bước và context projection không bị ép giống nhau: đối tượng đo là **hệ CLI + model dưới protocol**, không phải hiệu ứng nhân quả riêng của kiến trúc CLI.
- Cap 8 request là cùng một giới hạn nhưng tác động khác nhau lên workflow cần nhiều bước. Hai failure có snapshot đúng; kết luận về hoàn tất trong budget khác kết luận về sửa code đúng.
- Cache state, backend revision và background load không được kiểm soát hoàn toàn. Không dùng các bảng dẫn xuất để khẳng định significance hoặc winner tổng quát với ba lượt/task.
