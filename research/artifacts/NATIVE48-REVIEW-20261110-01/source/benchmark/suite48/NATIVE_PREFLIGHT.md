# Adapter và native preflight — 2026-11-10

**Đạt offline16/16 cặp B-01–B-04 × bốnCLI** tại [NATIVE48-20261110-02](artifacts/NATIVE48-20261110-02/result.json): native tool thực thi reference được tiêm qua synthetic SSE, scope/public/hidden/rubric/structure pass, CLI kết thúc và trả final marker. **40response exchanges đều giả lập trong memory; provider requests=0.** Không phải16kết quả model hoặc benchmark trả phí.

## Phạm vi được kiểm

- Adapter riêng `benchmark/suite48_native.py` dùng lại config builder/profile/broker đã pin, không sửa runner/baseline pilot. Dùng private roots `OF48-*`, không reserve R/C IDs; mapping slot→task→CLI→offline config lấy từ16slot round1 đúng thứ tự draft.
- Actual binaries vẫn v1.19.5/v2.2.5/Pi1.5.0/Codex0.167.0, `search-r2` và config native như pilot. Prompt argument đúng bytes task, không thay prompt riêng cho CLI. Witness xác nhận net namespace riêng, public/immutable files read-only, home/hidden/key env thật vắng; B-01 answer-only và B-04 allowed additions hoạt động.
- Dùng **production handler thật** qua bridge và Unix broker, nhưng thay urllib opener bằng object in-memory; TCP creation ở host broker bị deny trong context này. Không đọc credential, không có HTTP client outbound thật, không cài dependencies hoặc chạm service/session thật.
- Fake usage có input/output/total/cache/reasoning để test parsing và ledger. Các cost bên trong `synthetic_ledger` là phép tính trên token giả, **không nhập ledger pilot/benchmark hoặc coi là phí đã chi**. Synthetic response ID/request ID được gắn nhãn offline.
- **9unit tests adapter/broker**: cap8request, output clamp2048, serialization/virtual pacing, missing usage không thành0, provider-failure latch, reserve local408 không upstream, soft estimate guard, slot mapping/no paid IDs, refusal of non-offline CLI, bounded capture/timeout/duration và SSE total_tokens.
- `suite48_native_inside.py` giữ riêng timestamp trước/sau actual native subprocess. Outer monotonic duration còn gồm bwrap/bridge startup/teardown. Cả hai được lưu, không trừ pacing khỏi chỉ số một cách ngầm định.
- Cleanup tại thời điểm capture: supervisor PID và broker socket đã mất cả16case. Native stdout/stderr/config, mock payloads, grading/patch/snapshot và source snapshots được giữ/hash. Không sửa CSV/raw/seal pilot hoặc fixture seal rev2.

## Giới hạn quan trọng

1. **Pacing dùng virtual clock**, không ngủ30s thật ở preflight. Guard arithmetic giữ interval30/reserve60/cap8/output2048, nhưng đây không phải bằng chứng native real-wall pacing. Live pilot cũ có evidence pacing riêng; không nâng bằng chứng này thành live acceptance của bộ task mới.
2. Offline outer watchdog90s là safety limit preflight, **không phải đổi policy900s benchmark**. Broker vẫn exercise paced-900/reserve60 bằng virtual time. Real provider latency, quota, backend revision/cache và việc model tự giải task chưa kiểm.
3. Reference được đưa vào tool-call giả để kiểm transport/permissions/filesystem/grader; benchmark thật phải dùng workspace/session mới, không reference/hidden/oracle hoặc lịch sử preflight trong context.
4. Chưa có paid-entrypoint ở adapter này. Thiếu `--offline-preflight` bị từ chối trước tạo runtime; không có cờ mở provider. Paid orchestration và fresh R/C allocation chỉ được thêm/sử dụng sau protocol/budget approval riêng, rồi phải kiểm offline trước dispatch.

## Lỗi preflight đã giữ nguyên

[NATIVE48-20261110-01](artifacts/NATIVE48-20261110-01/result.json) chạy2/16case: v1/B-01 pass, Codex/B-01 thực thi tool nhưng CLI lỗi vì **mock SSE thiếu `usage.total_tokens`**;14slot còn lại not_run. Đây là lỗi mock/schema, không lỗi tool giải task hoặc provider.

Đã thêm field đúng và regression, dùng namespace/artifact mới chạy đủ16case ở02. Source/raw lượt01 giữ nguyên trong chính artifact; verifier hiện tại dùng02 vì source mock rev2 khác01. Không gọi toàn lịch sử là18/18 pass: thực tế18native attempts gồm17pass và1mock failure,44synthetic exchanges,0provider requests. Cohort nghiệm thu02 là16/16pass.

## Tái kiểm offline

```sh
python3 -B benchmark/test_suite48_native.py
python3 -B benchmark/verify_native48.py --artifact-dir benchmark/suite48/artifacts/NATIVE48-20261110-02
```

Verifier kiểm source snapshots/raw hash/inventory, fixture seal, order, mapping, prompt bytes, scope/grading, ledger caps/usage, duration boundaries và captured cleanup. Không chạy lại CLI/provider. Chạy preflight lại cần thư mục/namespace mới; không overwrite artifact cũ.

## Đề xuất chốt trước paid launch

- Giữ48slot và order draft, native config/settings/search-r2/paced-900 như đã đề xuất. Grade cap15s/suite, hidden riêng; primary task success phải có native completion + graderpass, không dùng injected marker của preflight cho benchmark thật.
- **Đề xuất primary duration là outer launcher wall** (bwrap spawn→launcher/bridge exit, gồm startup/pacing/teardown), giữ exact native subprocess duration làm secondary. Đây là cách diễn đạt chặt hơn của draft ngày09 và gần ranh giới pilot; **cần duyệt vào protocol cuối trước launch**, không tự thay draft đã hash hoặc trộn hai ranh giới. Real900s wall/deadline phải dùng cùng monotonic origin trong paid orchestrator khi triển khai, không lấy virtual preflight làm bằng chứng đã chạy điều đó.
- Xin duyệt guard mới **16USD estimate**, không hard invoice cap hoặc cam kết đủ48slot; giá và sáu request pilot unpriced giữ nguyên giới hạn. Chưa được duyệt.
- Chốt final protocol/resource/launch manifest, ghi người duyệt/ngày/revision, kiểm guards/ID allocation của paid orchestrator offline rồi mới cấp fresh R/C và dispatch. **Hiện chưa authorize inference.**
