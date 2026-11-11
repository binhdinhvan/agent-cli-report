# Google AI Studio trực tiếp — chuẩn bị offline

Người dùng đã lưu key riêng tại `.local/credentials/google-ai.key`. Đã kiểm metadata: regular file thuộc user, không symlink; quyền ban đầu664 đã siết thành600 qua descriptor, **không đọc nội dung key trong bước chuẩn bị**. Không ghi đè key/config/source hoặc kết quả Shopaikey.

## Cấu hình đã tách riêng

- Profile: [`../research/model-profiles/google-gemini-3.8-flash.json`](../research/model-profiles/google-gemini-3.8-flash.json).
- Model được chọn: `gemini-3.8-flash`; quyền truy cập model của account chưa runtime-verified.
- Base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`.
- Generation endpoint: `/chat/completions`, **không phải `/responses`** của runner trước.
- Key chỉ được đọc từ file Google sau approval; không có fallback sang Shopaikey key/provider.
- Nguồn định hướng API: [tài liệu Google OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai) đã đọc; đây không phải kết quả API thật.

`google_gemini_smoke5.py` chuẩn bị tối đa5request provider-only có prompt marker cố định, streamtrue, max_tokens256, include_usage, gap≥30s, timeout45s/wallcap90s/request/capture4MiB; không retries/fallback, không gửi source/session thật và không chạy nativeCLI/tools. Không ép reasoning effort theo sol. Parser kiểm marker, finish_reasonstop và usageprompt/completion; giữ nguyên rawusage/cache/reasoning fields nếu provider báo.

Giá Google hiện chưa có; estimated/measuredcostnull, không dùng giá Shopaikey/sol. Muốn chạy trước khi có giá cần **approval unpriced scope5 cho Google riêng**. Approval Shopaikey cũ không dùng được. Benchmark48 và native4CLI vẫn chưa được nghiệm thu/authorize từ việc user lưu key.

## Lệnh chỉ chuẩn bị, không API/key read

```sh
python3 -B demos/google_gemini_smoke5.py --prepare-plan --artifact-dir demos/artifacts/GOOGLE-GEMINI-PREP-20261110-01
```

Lệnh tạo plan/approval template **disabled** và hashes. Chế độ `--run` chỉ hoạt động với approval đúng provider/model/scope/5request/giá pending và inputhashes, trong artifact mới; không tự dùng template để chạy.

## Ranh giới nghiệm thu

Unit/mock tests chỉ kiểm adapter chuẩn bị, credential policy với file giả và parser/stop/pacing; không xác nhận Google key hoạt động hoặc model trả lời. Không nối 5smoke Google với smoke Shopaikey; nếu chạy thật phải có artifact/approval/protocol riêng, giữ mọi failure/usageunknown. Các native CLI cần profile riêng; không mặc định Codex dùng được Google Chat Completions chỉ vì provider smoke pass.
