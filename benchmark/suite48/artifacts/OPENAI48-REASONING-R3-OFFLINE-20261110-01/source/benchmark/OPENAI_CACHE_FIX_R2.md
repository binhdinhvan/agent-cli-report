# Sửa gate tính phí OpenAI — revision2, chỉ nghiệm thu offline

Người dùng yêu cầu “sửa đi”, **không mở API/retry/benchmark mới**. Giữ nguyên `openai48.py`/tests/protocolr1 và mọi raw/source/approval/CSV cũ. Bản sửa ở `openai_cache_cost_r2.py` (`estimate`) và adapter `openai48_cache_r2.py` (`context`/`offline`); không có paid CLI, không đọc credential, không reserve R/C IDs.

## Công thức và nguồn

[Tài liệu OpenAI: Monitor cache performance](https://developers.openai.com/api/docs/guides/prompt-caching#monitor-cache-performance), [cache lifetime](https://developers.openai.com/api/docs/guides/prompt-caching#cache-lifetime), [bảng giá](https://developers.openai.com/api/docs/pricing), profile giá `research/model-profiles/openai-gpt-6.1-sol.json`:

- Ordinary input = input − cached reads − cache writes. Bốn nhóm input không chồng lấn; cache-write là giá toàn phần, **không cộng thêm ordinary input** cho cùng token.
- Nếu provider báo breakdown, `ttl_30m_tokens + ttl_12h_tokens` phải bằng `cache_write_tokens`. Tính giá2.50/5USD/M tương ứng; reads0.10, ordinary2, output10USD/M. Reasoning đã nằm trong output, không cộng lần nữa.
- Nếu có write count nhưng không có TTL breakdown: **không suy default là TTL thực**. Guard dùng mức12h cao hơn cho toàn bộ writes, ghi rõ `conservative_upper_bound=true`, lifetimeunknown và khoảng tariff30m…12h. Đây là **conservative tariff estimate**, không phải giá thực hoặc invoice cap. Không tăng guard16USD.
- Thiếu counts, sai kiểu/âm/boolean, counts vượt input, breakdown không hợp lệ, total/reasoning accounting sai, giá không hợp lệ hoặc context>272K vẫn costnull và chặn. Không biến missingusage thành0 hoặc dùng tariff provider khác.
- Giá standard short context/tierdefault chỉ áp dụng trong context OpenAI đã có; response-tier/backend khác hoặc phí ngoài token vẫn cần review ở launch. TTL bất kỳ ngoài hai tariff đã công bố chưa được nghiệm thu.

## Lượt cũ và acceptance

Usage thật đã lưu của request2/R222: input3112, cached0, write3109, output32. Ordinary3. Nếu toàn30m thì estimate$0.0080985; nếu toàn12h thì$0.015871. Không có breakdown nên revision2 dùng **$0.015871 cho guard**, không ghi nó thành charge hoặc sửa rawcostnull. Request1 vẫn$0.001576. Chỉ replay offline, không thay status infra_error thànhpass hay hồi tố sửa tally/CSV.

Carry giữknown0.28655616USD/5unpriced, remaining15.71344384USD; replay không tự hợp nhất conservative bound vào known cost lịch sử. Lượt mới phải chốt carry/budget accounting và approval riêng, freshIDs sauR274/C375, giữ cảreservednotrun trước.

Unit tests bao phủ positive/mixed TTL, unknown TTL upper bound, malformed/missingusage và công thức không doublecount; broker regression gửi ba request liên tiếp trên Unixsocket với transport in-memory, chứng minh positivecachewrite không chặn request tiếp theo. Đồng thời kiểm thiếuusage vẫnchặn, không egress hoặc credential. Native synthetic16task×CLI dùng positivecachewrite3109/khôngbreakdown trên mọi turn, cùng transport/dispatcher cũ và virtualpacing; không tính phí giả vào phí thật và không chứng minh native API acceptance/runtime stability.
