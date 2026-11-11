# Hoàn thiện các yêu cầu còn lại — revision2

User yêu cầu hoàn thành đầy đủ sau báo cáo ngày2026-11-11. Không xem mục chưa kiểm là pass, không thay product/pin để ép demo đạt. Benchmark48 và mọi artifact cũ giữ nguyên; không chạy lại case đã đạt. API thật chưa mở lại ở scope này: ưu tiên native runtime + local scripted SSE, không đọc key. Nếu cần model-quality cohort riêng phải chốt protocol/cap/guard trước launch.

## Acceptance trước khi chạy

1. Managed service riêng: health qua giai đoạn boot503 tới200, event readiness có deadline/reject, shell pending qua SIGKILL → PID mới + native cancellation notice. Không dùng lỗi readiness làm feature verdict.
2. BG08: child inference đang chạy khi crash private service, parent/child lineage giữ đúng sau restart, native recovery notice/terminal và completion về parent; giữ side-effect observations, không giả exactly-once.
3. BG09: DB chỉ của fixture mới, dừng process trước fixture mutation; ghi before/after/hash/schema và exhaustion native failure/release claim. Không sửa DB thật.
4. V1 permission: native server prompt/tool call + event asked/replied, once/reject/always, side-effect witness và scope; background subagent trả childID/parent tiếp tục/completion.
5. Config v1 trên v2/unmatched: thử fresh configs, ghi effective policy và witness, không suy từ schema.
6. Client/SDK error/cancel/timeout: tách subscriber abort/request abort/session interrupt, giữ trạng thái cuối và không diễn giải HTTP abort là execution cancel.
7. Shared TUI/Desktop/Web: chỉ binaries/UI đúng pin trong HOME/XDG/service riêng; endpoint/PID/session cùng nhau, screenshot thật. Không dùng UI đang mở/session thật; thiếu desktop/display/browser automation thì chuẩn bị dependencies riêng và ghi blocker, không thế bằng HTTP client giả UI.
8. Đối chiếu từng dòng checklist PLAN với artifact hiện có; bổ sung reproducibility/lock, secret/link/source audit. Chỉ đánh dấu đạt đúng phần đã kiểm.

## An toàn

Source repos read-only. Chỉ chấm dứt process do runner tạo; không restart service người dùng. Ghi mọi attempt lỗi/retry mới. Recovery có thể tự inference nên phải namespace chặn egress, local provider giới hạn request/wall. Không nạp plugin demo vào môi trường thật.
