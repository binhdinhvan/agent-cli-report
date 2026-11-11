# Chính sách paced-900 — revision thời gian mới, preflight offline

Người dùng đồng ý đổi chính sách sau hai lượt v2/P-02: snapshot đúng nhưng CLI bị cắt ở cap300s, request cuối mới bắt đầu giây299.39/295.65. **Không bảo đảm mọi request/model/provider sẽ thành công**, nhưng sửa hạn chế thời gian phía harness thay vì retry nguyên điều kiện.

## Quy tắc áp dụng nhất quán cả bốn CLI

| Mục | legacy-300 | paced-900 |
| --- | ---: | ---: |
| Wall timeout mỗi lượt, gồm pacing | 300s | **900s** |
| Khoảng thời gian tối thiểu còn lại để dispatch request, sau pacing | 0s | **60s** |
| Nghỉ sau response trước | 30s trong nhóm cũ | **30s bắt buộc** |
| Concurrency/upstream active | 1 | **1** |
| Upstream request cap mỗi lượt | 8 | **8**, không tăng |
| Requested output mỗi request | ≤2048 | **≤2048**, không tăng |

Tối đa7 gap chiếm≥210s nếu đủ8 request; cap900s dành thêm chỗ cho inference/tools/final. Socket timeout45s của broker và90s bridge không đổi; 60s reserve là điều kiện tối thiểu, **không cam kết provider hoàn tất trong60s** (SSE có thể chạy lâu hơn nếu vẫn có dữ liệu). Vẫn có wall cap, request/output/budget cap và provider-failure latch, không chạy vô hạn.

- Trước khi đợi pacing, tính cả delay và reserve. Nếu không đủ thời gian thì **HTTP408 local, không đợi rồi mới gửi một request chắc chắn sát cap**. Kiểm lại sau parse/budget guard trước dispatch để tránh thời gian đọc body ăn mất reserve.
- Latch `time_window_exhausted` chặn các request tiếp theo tại local. Ghi riêng `locally_blocked_by_timing_guard`, `batch_guard_stop_reason`; **không gọi local timing stop là provider overload/failure**. Nếu isolation còn hợp lệ thì run status timeout, không task failure.
- Lưu remaining time tại dispatch, requested reserve, actual pacing waits, timing policy/limits trong batch/run, timing group trong CSV notes. `provider_stop_reason` chỉ dùng cho lỗi provider/transport thực, không cho timing guard.
- `benchmark/pilot.py` mặc định **paced-900 cho cả bốn CLI**; legacy300 vẫn tái lập bằng `--timing-policy legacy-300`. Không special-case v2 hoặc P-02.
- Retry/continuation từ lịch sử cap300 bị từ chối âm thầm. Một single timing recheck cần `--recheck-timing` + protocol riêng; không đổi đồng thời environment revision. Không gộp cap300/cap900 thành cùng điều kiện, không nâng timeout cũ thành success.

## Phần không thay đổi

Search-r2/manifest/rg bytes, binaries đã pin, model/provider/reasoning settings/native tools/permissions, task v2/prompt/public/hidden/seal/grader, network/home/XDG isolation, key host, dependencies/public tests read-only/source writable, failure latch và chi phí gate giữ nguyên. Không thêm alias Python/pytest hoặc mở Internet agent.

Guard USD không tự tăng: known estimate trước chính sách mới **0.68968632 USD**, sáu request lịch sử unpriced/totalchargeunknown. Chưa cấp quyền trả phí từ việc đổi policy; nếu chạy nghiệm thu cần protocol/ID mới và ghi rõ remaining known guard theo mức người dùng đã duyệt. Không tự retry hoặc khởi chạy ba slot còn lại.

## Acceptance offline

- Fake-clock native HTTP mock: request ở giây310 bị chặn với legacy300 nhưng được phép với paced900; request gần900 hoặc pacing sẽ ăn mất reserve bị chặn **trước opener**. Retry sau timing stop không lên upstream, không bị đếm provider failure.
- Chốt cùng wall/request/output/reserve cho bốn cấu hình, giữ pacing/cost/isolation/grader/header/secret filtering và provider-stop regressions.
- Preflight config/writable/isolation đủ bốn CLI, chỉ mock400 không key/provider. Source/protocol/manifest/fixture/binary hashes và cleanup; không sửa dữ liệu cũ.

```sh
python3 -B benchmark/pilot.py --offline-preflight --artifact-dir benchmark/artifacts/PACED-900-PREFLIGHT-20261109-01 --config-start 124 --environment-profile search-r2 --timing-policy paced-900 --protocol-file benchmark/TIMING_POLICY_R2.md --budget-usd 3 --request-gap-seconds 30
```

Đây là **lệnh offline, không model**; dùng artifact/ID mới nếu chạy lại. Protocol này chốt cho preflight, không sửa trong lúc thực thi. Kết quả ghi tài liệu riêng. Đổi timeout giảm rủi ro harness cắt final, không xác minh hết sự cố provider hoặc đảm bảo mọi task hoàn thành.
