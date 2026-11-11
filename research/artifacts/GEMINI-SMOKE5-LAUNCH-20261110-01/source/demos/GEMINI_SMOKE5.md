# Gemini smoke5 — exception giá pending, không benchmark

Người dùng xác nhận vẫn Shopaikey, yêu cầu **chạy thử5lượt trước**, giá bổ sung sau, và **benchmark phải chạy lại**, không nối tiếp hai model. Đây là quyền cho tối đa5request generation có tính phí nhưng **chưa định giá**, không phải quyền chạy48benchmark hoặc mọi demo/provider endpoint.

## Chốt trước khi chạy

- Model alias `gemini-3.8-flash`, provider `https://api.shopaikey.com/v1`, endpoint thử `/responses`, SSE. Compatibility vẫn unverified trước phép thử. Không tự đổi protocol/model khi lỗi.
-5request giống nhau, tuần tự, cùng prompt literal `Return exactly REPORT_GEMINI_SMOKE_OK without explanation.`, streamtrue/storefalse/max_output_tokens256. Không truyền reasoning effort hoặc capabilities đoán theo tên Gemini. Không tools/files/session thật/native CLI; phép thử này **không** nghiệm thu cả4CLI/toolcalling/benchmark.
- Gap≥30giây từ request trước kết thúc đến request sau bắt đầu, sockettimeout45s, wall tối đa90s/request, capture4MiB. Tối đa5upstream, không retry/fallback/networkprobe/catalog riêng. Bất kỳ HTTP/error/terminalfailure/thiếuusage/marker mismatch thì dừng, giữ suffixnot_run.
- Pass mỗi request: HTTP200/SSE, terminalresponse.completed, markerđúng và có usageinput/output. Giữ usageprovider gốc và modelreturn. Missing cache/reasoning lànull/chưa báo, không tự điền0.
- Giá input/cache/output hiệnnull. **Estimated cost và measured charge giữnull**, không dùng giá sol, không gọi là miễn phí hoặc áp trần16USD cũ thành invoicecap. Giới hạn an toàn ở scope5request/output256; user đã chấp nhận chờ giá sau. Gate thiếugiá của các runner cũ và benchmark48 vẫn giữ nguyên.
- Approval riêng bound script/tests/protocol/profile hashes trước đọc key. Key private chỉ đọc trong process, không log/argv/config/agent. NoRedirect/directTLS và không kế thừa proxy như transport trước; không tắt TLSverify. Snapshot source/result/rawSSE; fail/retry giữ nguyên.

## Diễn giải

5/5pass chỉ cho thấy short provider-only SSE smoke thành công tại thời điểm thử; không đủ kết luận Gemini ổn định hơn sol từ tải khác, latencyngangnhau, backendgốc đúngalias hoặc benchmark/tools đã sẵn sàng. Nếu fail thì không tựretry hoặc mở48. Gemini benchmark sẽ là cohort48mới sau adapter/smoke/protocol/budget riêng; toànsolraw/history/usageunknown giữ nguyên.
