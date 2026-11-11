# Kết quả demo native — 2026-11-11

**Cập nhật sau vòng1:** các blocker managed-service/BG08/BG09/v1permission/subagent/sharedUI bên dưới đã được xử lý ở [vòng2](NATIVE_COMPLETION_R2_RESULTS.md). Văn bản vòng1 và audit cũ giữ như historical receipt; raw không đổi.

**Đã nghiệm thu các đường runtime bên dưới; recovery còn bị chặn.** [Audit pass](../research/artifacts/NATIVE-DEMOS-REVIEW-20261111-01/validation.json) kiểm raw hashes, source snapshot của controller, cleanup và benchmark48 không đổi. Sáu unit tests mới pass; không chạy lại case đã đạt. Regression tổng: **73 demo +118 benchmark tests đạt**; hai legacy reservation tests cần CSV view cách ly vì IDs lịch sử đã nằm trong registry thật. Lượt chạy không cách ly có2 lỗi được giữ trong [receipt](../research/artifacts/NATIVE-DEMOS-REVIEW-20261111-01/regression.json), không sửa source đã seal hoặc registry để làm test pass.

## Phạm vi và bằng chứng

Binary native chạy trong namespace riêng, HOME/XDG/config/DB/plugin/service riêng; model được thay bằng **scripted local Responses SSE provider**. Có 0 request tới provider thật và 0 lần đọc nội dung key. Đây là bằng chứng runtime của plumbing, không phải chất lượng model, semantic memory hoặc sandbox bảo mật của sản phẩm. Dependencies SDK chỉ cài tại `.local/demo-sdk-2.2.5`, lifecycle scripts tắt; không sửa repo nguồn hay service đang dùng.

Pins v1 `810c0eba1a7348036f8bdf61e6632d0c36c6876c`, v2 `9bbb8ce18c80f099e0e448775f59d965ead40a21`. Implementation/permalink cố định và giới hạn từng claim: [E-0125–E-0134](../research/evidence.csv), bổ sung E-0087–E-0124 ở [REPORT mục4](../REPORT.md#4-opencode-v1-so-với-v2).

| Demo | Kết quả và artifact |
| --- | --- |
| Permission CLI v1/v2 | [10 case](artifacts/NATIVE-DEMO-PERMISSION-20261111-02/summary.json): allow/deny, overlap allow/deny và ask noninteractive; witness đúng dự kiến. Deny toàn phần có thể ẩn tool; overlap-deny giữ tool visible rồi chặn execution. Ask CLI là unattended rejection, không phải UI approval. |
| Permission API v2 | [17 checks](artifacts/NATIVE-PERMISSION-API-20261111-01/client-result.json), gồm readiness: once/reject/always, pending lifecycle, saved approval đúng resource, resource khác vẫn ask, configured deny thắng saved allow. Không thay side-effect witness của CLI. |
| TypeScript Client v2 | [Prompt/events/transcript](artifacts/NATIVE-CLIENT-20261111-01/client-result.json); restart private server đổi PID, request resume chứa history cũ. Client source xuất đúng pin bằng `git show`. |
| Location shell API | [Running/exit7/cancel/disconnect](artifacts/NATIVE-CLIENT-LIFECYCLE-20261111-02/client-result.json): parent tiếp tục, sibling sống sau cancel, observer mới nhận terminal sau client disconnect. Không phải durable agent-job recovery, chưa kiểm toàn bộ descendant PID. |
| Embedded SDK | [Published SDK 2.2.5](artifacts/NATIVE-SDK-20261111-01/sdk-result.json): prompt/events/explicit close; host PID bằng `server.info.pid`, `urls=[]`. `server.info.version=unknown`; mapping package build→source commit chưa attested. Có hash package manifests nhưng không có full dependency lock/snapshot. |
| Plugin v1 | [Native marker](artifacts/NATIVE-DEMO-ROUND1-20261111-01/PL01-v1/result.json) load và gọi thành công. |
| V1 plugin trên v2 | [Expected loader failure](artifacts/NATIVE-CLIENT-V1PLUGIN-20261111-02/client-result.json): nguyên bytes v1 bị lỗi `Plugin must export a default definition with an id and an effect or setup function.` Chờ `plugin.updated`, không suy từ inventory rỗng lúc startup. |
| Plugin đã port v2 | [Marker và cleanup](artifacts/NATIVE-PLUGIN-PORT-20261111-03/client-result.json): `id/setup/tool.transform`, gọi qua Code Mode `tools.report_marker()`. [Cleanup log](artifacts/NATIVE-PLUGIN-PORT-20261111-03/client-server.log). Không phải full hooks/options/storage migration. |
| Native shell background v2 | [Success](artifacts/NATIVE-BG-TOOL-20261111-01/client-result.json) và [exit7](artifacts/NATIVE-BG-ERROR-20261111-01/client-result.json): parent marker trước worker terminal, completion về parent. Shell notice có thể `state=completed` cả khi exit7; phải đọc exit/output, không suy thành success từ notice state. |
| Background subagent v2 | [Lineage và completion](artifacts/NATIVE-SUBAGENT-20261111-02/client-result.json): child ID/parent đúng, parent tiếp tục trước child hoàn tất, child marker về parent. Fake inference có delay xác định; không đánh giá model quality. |
| Compaction v2 | [Checkpoint plumbing](artifacts/NATIVE-COMPACTION-20261111-03/client-result.json): native summary template, scripted summary hợp lệ, request tiếp dùng `REPORT_COMPACT_SUMMARY`. Không chứng minh semantic retention của model. |

## Recovery và các phần chưa nghiệm thu

- BG-07: private server thực đổi PID nhưng **không quan sát cancellation notice** trong [stdio graceful](artifacts/NATIVE-BG-RESTART-20261111-01/client-result.json) và [stdio crash](artifacts/NATIVE-BG-CRASH-RECOVERY-20261111-02/client-result.json). Kiểm DB thử nghiệm read-only thấy shell job vẫn `running`; activation phụ thuộc hosting lifecycle (E-0121–E-0124), không kết luận unsupported.
- Managed service: [attempt01](artifacts/NATIVE-BG-SERVICE-RECOVERY-20261111-01/manifest.json) và [attempt02](artifacts/NATIVE-BG-SERVICE-RECOVERY-20261111-02/manifest.json) timeout harness, không có `client-result.json`; [stage cuối](artifacts/NATIVE-BG-SERVICE-RECOVERY-20261111-02/demo-progress.json) là `client_created`, chưa event readiness. Readiness promise chưa reject khi stream lỗi có thể che lỗi thật. Không retry mù hoặc sửa product để ép pass.
- BG-08 subagent restart, BG-09 resume-budget exhaustion, v1 interactive approve/saved approval và v1 background-subagent runtime chưa chạy. GUI/TUI/Desktop dùng chung service chưa nghiệm thu; private HTTP không thay được bằng chứng UI/shared-service.
- Không claim exactly-once execution/notification từ các case completion này.

## Giữ lịch sử lỗi và sửa harness

Mọi attempt giữ nguyên trong [audit inventory](../research/artifacts/NATIVE-DEMOS-REVIEW-20261111-01/validation.json), không chọn retry đẹp để thay raw cũ:

- Permission attempt01 lỗi `AF_UNIX path too long` trước native process; shortened hashed config ID sửa harness, attempt02 mới chạy đủ10case. [Receipt](artifacts/NATIVE-DEMO-PERMISSION-20261111-01/failure-receipt.json).
- Lifecycle/V1PLUGIN attempt01 đọc nhầm envelope `{location,data}`; attempt sau unwrap `.data`.
- Plugin round1 chỉ thấy tool không được gọi, chưa phải loader verdict. Port01/02 định tuyến sai catalog/input; port03 đọc catalog trong `instructions` và gọi qua Code Mode. Không sửa plugin loader sản phẩm.
- Compaction01 thiếu template/detect sai; các request vẫn có tool definitions. Compaction02/03 sửa scripted summary/detection, giữ raw lỗi cũ.
- Subagent01 định tuyến nhầm vì child kế thừa parent `prompt_cache_key`; subagent02 dùng custom system + child seed.
- SDK dependency prep01 xử lý `--config` thành dependency, prep02 bỏ flag và install thành công; không có lockfile, không giấu giới hạn tái lập.

## Ảnh hưởng benchmark

Benchmark giữ **48 valid, 46 success/2 failure**, raw hashes không đổi. Registry vẫn R-0378/C-0479; paid generation gates đóng; không tăng guard/cost hoặc retry benchmark. Kết quả demo này là cohort synthetic riêng.
