# OpenAI trực tiếp — kiểm tối thiểu trước benchmark

Người dùng đã lưu key và xác nhận chương trình **được dùng key để gọi API làm report, nhưng không được làm lộ key**. Scope kiểm ban đầu: tối đa **1GET/models +1POST/responses** cho model `gpt-6.1-sol`, không benchmark/nativeCLI/tool hoặc retry/fallback. Không dùng key Google/Shopaikey nếu key OpenAI lỗi.

Key chỉ được loader private owner600/nonsymlink đọc trong memory của process sau approval. Không dùng tool mở nội dung key, không in key/header xác thực; serializer redacts full key và patterns sk-... kể cả trong error body. Artifact chỉ có payload marker, filtered catalog match/modelcount, SSE/usage/status và hashes; không dump fullcatalog/fine-tuned model IDs/account headers.

## Protocol cố định

- Provider `https://api.openai.com/v1`, model `gpt-6.1-sol` theo [model card chính thức](https://developers.openai.com/api/docs/models/gpt-6.1-sol). Alias trên Shopaikey trước đây không được suy là cùng backend.
- GET/models chỉ kiểm exact ID. Nếu HTTPerror hoặc không có model thì dừng trước generation; không tự chọn model khác.
- Gap≥30s từ catalog xong tới generation. POST/responses dùng streamtrue/storefalse, prompt literal `Return exactly REPORT_OPENAI_DIRECT_OK without explanation.`, max_output_tokens1024, reasoning.effortlow, service_tierdefault. Không dùng none vì model card chỉ công bố low/medium/high/xhigh/max.
- Socket45s/wall90s mỗi request, capturecatalog4MiB/SSE4MiB; không retry. Pass generation cần HTTP200/SSE, response.completed, markerđúng, usageinput/output đầy đủ. Nếu cap gây incomplete thì ghi đúng incomplete, không gọi là key lỗi hoặc provider outage.
- Giá published standard short context từ [pricing](https://developers.openai.com/api/docs/pricing): input2/cache-read0.10/output10USD/M, cachewrite30m2.50/12h5USD/M. Không dùnggiásolShopaikey. Giữusage gốc; estimated/measuredcostnull nếu chưa đối chiếu cachewrite/service-tier billing. Outputcap là giới hạn request, không invoicecap.

Approval pin script/tests/profile/protocol và parser trước key/network. Mọi failure giữ lại. Không đọc full key bằng tool, không đổi session/config/service thật. Native4CLI/48benchmark hoặc retry policy mới vẫn cần acceptance/protocol/approval riêng; một request ngắn pass không chứng minh độ ổn định dài hạn.
