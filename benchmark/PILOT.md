# Pilot gpt-6.1-sol — bản chuẩn bị rev3, đã có giá

## Phạm vi hiện tại

Người dùng yêu cầu xóa kết quả model cũ và chuẩn bị chuyển sang **gpt-6.1-sol**. Provider `https://api.shopaikey.com/v1`, bốn release/commit/binary giữ nguyên. Diagnostic Pi/P-01 sol đã giữ riêng ở `MODEL_COMPARE.md`, **không coi là pilot đủ bốn CLI**. Pilot/benchmark sol chưa chạy.

Giá input/cache/output user-reported đã cập nhật: **4.8 / 0.24 / 18 USD mỗi triệu token**, tại `research/provider-pricing.json`. Không tái sử dụng giá model cũ. Runner phải qua `require_pricing` đúng model/provider trước key/network/artifact; đủ giá không tự khởi chạy. Review ngân sách/settings/smoke trước pilot. Một diagnostic sol đã giữ có estimate khoảng 0.215 USD (`SOL_COST.md`), không bảo đảm 8 lượt nằm trong 1 USD hoặc đủ để ngoại suy tổng chính xác.

Đây là revision tài liệu sau khi nhận giá, không có lượt inference mới. Protocol rev2 của preflight offline đã snapshot nguyên hash tại `research/artifacts/SOL-PRICING-20261106-01/pilot-protocol-rev2.md`; không gán ngược giá mới cho metadata lịch sử hoặc thay raw artifact.

## Task và kiểm thử còn giữ

Hai fixture tự viết **version 2**: P-01 bugfix interval boundaries, P-02 dependency ordering. Prompt/public/hidden/task manifests được seal tại [`PILOT-PREP-20261106-02/preparation.json`](artifacts/PILOT-PREP-20261106-02/preparation.json); 16/16 kiểm tra baseline/reference/negative controls đạt kỳ vọng, không dùng model. V1 bytes/seal giữ để tái lập fixture, không phải kết quả luna. Không sửa fixture đã seal mà thiếu revision mới.

Agent chỉ thấy fixture task hiện tại, không hidden tests/oracle hoặc dữ liệu thật. Public test bind read-only, source writable; sau CLI dừng chấm snapshot trong sandbox riêng không socket/key. Scope/public/hidden/timeout phải đạt; không dùng lời tự nhận hoặc exit 0 riêng nó làm success. Cache `__pycache__` tự sinh được bỏ qua, symlink/nonregular/ngoài scope bị từ chối.

## Thông số đề xuất, cần chốt lại với giá sol

- 2 task × 4 CLI × 1 lượt = 8, concurrency 1; không gộp diagnostic trước hoặc kết quả đã xóa.
- Model sol, Responses SSE; system prompt/tools và backend revision/routing không giả định giống nhau. Native settings phải thu wire metadata; không suy capability off và explicit effort none tương đương.
- Cap dự kiến 8 request/2048 output token yêu cầu/request/300 giây/lượt; spacing 30 giây sau mỗi response để tránh burst. Pacing tính trong duration; không so timing với điều kiện không pacing.
- Shared budget toàn đợt từ giá mới; native retries vẫn tính request/usage. Thiếu usage/cost hoặc chạm guard thì chặn request sau và không mở slot tiếp. Không retry toàn lượt tự động, không tự nạp tiền.
- Source/public tests và grader cùng Python stdlib, không cài dependency/Internet. Key chỉ host broker; namespace mạng riêng, bridge socket, allowlist header, native sandbox không bypass. Chốt baseline tools/PATH trước nhóm mới.
- Usage/cache/reasoning thiếu để null. Không dùng giá catalog CLI hoặc mock test làm charge. Ghi source/fixture/prompt/protocol/config hashes, original usage, diff, public/hidden output, witness/PID/timing/status/validity.

Thứ tự dự kiến: P-01 Pi → Codex → OpenCode v2 → OpenCode v1; P-02 OpenCode v2 → OpenCode v1 → Codex → Pi. Đây là danh sách cố định có trước chạy, không tự gọi randomization thống kê.

## ID và lệnh

R-0001–R-0008 và C-0005–C-0038/C-0040 đã retire, không tái sử dụng dù đã xóa results. Giữ C-0039 sol. Nhóm preflight mới C-0041–C-0044; smoke model dự kiến C-0045–C-0048; pilot dự kiến R-0009–R-0016/C-0049–C-0056. Registry: `research/experiment-state.json`.

Offline không trả phí:

```sh
python3 -B benchmark/pilot.py --offline-preflight --config-start 41 --artifact-dir benchmark/artifacts/SOL-PREFLIGHT-20261106-01
```

Lệnh pilot thật **chỉ sau khi đủ giá, smoke và chốt protocol**:

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/PILOT-SOL-20261106-01 --run-start 9 --config-start 49
```

Không sửa file protocol khi lượt thật đang chạy. CSV hiện chỉ là header, không giữ run model cũ hoặc thêm placeholder. Kết quả sol diagnostic không tự được gán R-0009.
