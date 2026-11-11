# Demo không gọi provider — kế hoạch revision1 và cập nhật nghiệm thu

**Cập nhật 2026-11-11:** user đã yêu cầu chạy demo trong sandbox riêng. [Kết quả native](NATIVE_RUNTIME_RESULTS.md), [audit pass](../research/artifacts/NATIVE-DEMOS-REVIEW-20261111-01/validation.json). Lệnh cấm startup/plugin ở phạm vi cũ bên dưới không còn áp cho sandbox demo đã duyệt; vẫn tuyệt đối không tác động môi trường thật. Scripted local SSE, không provider thật.

**Cập nhật vòng2:** [Recovery/budget/v1permission/config/sharedUI/failurematrix đã kiểm](NATIVE_COMPLETION_R2_RESULTS.md); [audit revision02](../research/artifacts/NATIVE-COMPLETION-R2-REVIEW-20261111-02/validation.json). Source/sdkbuildquality chưa kiểm không được nâng thành pass từ các case chức năng này.

## Phạm vi hiện tại

Theo yêu cầu ngày2026-11-10: làm việc chưa cần API trước. **Không gọi provider, probe mạng, nạp plugin, khởi động/restart service hoặc resume session.** Các trường hợp bên dưới là acceptance plan, chưa phải runtime pass.

Pins: v1 `810c0eba1a7348036f8bdf61e6632d0c36c6876c`, v2 `9bbb8ce18c80f099e0e448775f59d965ead40a21`. Định hướng loader/recovery: E-0109–E-0124 trong [`../research/evidence.csv`](../research/evidence.csv); diễn giải và permalink tại [`../REPORT.md`](../REPORT.md) mục4.4–4.5. Không fetch docs web khi đang giữ pause mạng; trước khi viết/nạp plugin cần đọc guide tại pin và kiểm API implementation tương ứng.

## 1. Fixture cục bộ đã có thể kiểm

`fixtures/background_worker.py` là **tác vụ giả lập do nghiên cứu viết**, không phải agent/provider mock và không import OpenCode. Dùng Python standard library, không mạng, không child process, không ghi file. Chỉ stdout JSONL có event, sequence, elapsed monotonic. Tối đa30steps×0.1s, exit0 khi success, exit7 khi lỗi chủ động, exit143 khi nhận SIGTERM ở POSIX.

```sh
python3 -B -m unittest discover -s demos -p 'test_background_fixture.py' -v
```

Tests chỉ nghiệm thu fixture: output xác định, thứ tự event, duration bound, lỗi, validation input và hủy đúng child do test tạo. Không chứng minh progress/cancel/notification của tool. Không cấp R/C inference IDs cho unit tests này.

## 2. Acceptance matrix sẽ áp dụng khi chạy demo thật

| ID | Tình huống | Điều kiện pass cần quan sát | Trạng thái hiện tại |
| --- | --- | --- | --- |
| BG-01 | Start background | Tool trả job/session/shell ID trước worker terminal; giữ clocks riêng tool-return và worker-end | v2shell/subagent và v1subagentexperimentalflag đạt |
| BG-02 | Parent tiếp tục | Parent marker xuất hiện sau tool-return nhưng trước worker-end; không sleep/poll agent để lấy kết quả | v2shell/subagent và v1subagent đạt |
| BG-03 | Completion | Đúng owner nhận terminal/result; lưu raw event và output file nếu có; kiểm duplicate thay vì giả định exactly-once | v2 completion đạt; chưa nghiệm thu exactly-once/duplicate guarantee |
| BG-04 | Worker lỗi | Exit7 và terminal error được báo; không biến lỗi fixture thành lỗi provider | v2 exit7/output đạt; notice state có thể completed |
| BG-05 | Hủy | Hủy đúng job; worker của job kết thúc; parent và sibling không bị hủy nhầm; kiểm PID đã ghi | Location-shell cancel/sibling đạt một phần; chưa full descendant PID matrix |
| BG-06 | Client disconnect | Client ngắt trong lúc worker chạy; observer mới đọc đúng state/result; không suy server chết chỉ vì client mất | Location-shell API v2 đạt; không suy durable recovery |
| BG-07 | Restart shell v2 | Service thử nghiệm thật sự đổi PID; pending running shell có cancellation notice theo E-0118; kiểm riêng OS process còn/không còn | Managed-service native cancellation đạt; stdio cũ khôngnotice giữ riêng; không OSsurvivalclaim |
| BG-08 | Restart subagent v2 | Parent/child lineage giữ đúng; resume/terminal/notice được ghi; side-effect counter phát hiện lặp thay vì giả định exactly-once | Managedchildresume/lineage/completion đạt; counter1trước-saucrash ở case toolđãcommit, khôngexactly-onceclaim |
| BG-09 | Restart budget | Chuẩn bị fixture DB thử riêng theo schema đã kiểm; exhaustion tạo terminal; tuyệt đối không sửa DB/session thật |11nativecrashes/exhaustion/no12threquest/read-onlyDBrelease/reset đạt; không mutate DB |
| PL-01 | Plugin v1 tối giản | Custom tool chỉ trả marker cố định; loader và invocation có log; không đọc env/key/home | native marker đạt |
| PL-02 | V1 module nguyên dạng trên v2 | Giữ nguyên bytes; ghi chính xác loader error/acceptance, tách config/dependency/API failure | expected loader failure đã quan sát |
| PL-03 | Plugin v2 đã port | Cùng marker/behavior; id/setup hoặc effect đúng loader; ghi before/after/diff và cleanup | marker qua Code Mode và cleanup đạt |
| PM-01 | Permission matrix | allow/approve/reject/deny, overlap, unmatched và saved approval scope có event và side-effect witness riêng |10CLIcase+v2API+v1API6turn+legacyconfig5case+unmatchedv2 đạt; khôngkeyboardUI/fullrestartTTLclaim |
| CT-01 | Resume/compaction | Marker/constraint trước-sau resume và compact được kiểm; không dùng session title làm proof hội thoại | v2 transcript resume + checkpoint plumbing đạt; semantic retention chưa kiểm |
| SDK-01 | Client/SDK lifecycle | Subscribe trước prompt, terminal/error/cancel/timeout và transcript; tách HTTP client khỏi embedded host | Client/embedded prompt/events/close+nativeHTTP400failed/waittimeout/interrupt đạt; requesttimeout≠executioncancel |

**Không có background flag trong legacy shell schema đã đọc không đồng nghĩa v1 không có background subagent.** BG subagent so sánh v1/v2; shell native background ghi đúng phạm vi E-0113/E-0112, không thêm `&` để giả vờ cùng native feature.

## 3. Gate trước runtime — chưa đạt thì không chạy

1. Đọc hướng dẫn root/thư mục source liên quan; không sửa/cài dependencies trong repo tool. Kiểm runtime/dependency sẵn có; thiếu thì ghi blocker, không tự cài.
2. Mỗi demo root mới nằm dưới `/tmp/opencode/agent-cli-report/`, tách HOME/XDG/DB/config/plugin/service registration/cổng; dùng OS namespace và mounts đã được các profile cũ nghiệm thu. Không tự đoán env override. Tham khảo [`../research/isolation.md`](../research/isolation.md), [`OFFLINE_API.md`](OFFLINE_API.md).
3. Model/provider network mặc định bị chặn ở OS. Nếu dùng local scripted transport sau này, gắn nhãn synthetic, ghi request/response và **không dùng làm model quality evidence**. Chưa có runner/transport demo cho matrix này; không tái dùng paid launcher để thử nhanh.
4. Ghi version/config hash, entrypoint/hosting mode, effective roots, PID/endpoint, fixture hash, expected/actual, terminal và cleanup. Chỉ dừng PID đã tạo và xác minh danh tính; không kill theo tên, không xóa rộng.
5. Restart/resume có thể tự phát sinh inference (E-0121/E-0123): chỉ chạy khi sandbox chặn egress và transport local đã kiểm, hoặc có chấp thuận provider rõ sau pause. Không coi “chỉ khởi động server” là chắc chắn không inference.
6. Không bật plugin trong môi trường đang dùng. Plugin demo chỉ được load khi root/config/dependencies/egress đã kiểm và tác động được duyệt. Static/source check không thay load/invocation acceptance.

## 4. Artifact tối thiểu khi có lần chạy thật

Mỗi attempt giữ manifest (demo/config ID, timestamp, full pins, source/binary/fixture hashes, mode), raw JSONL, stdout/stderr đã duyệt nhạy cảm, observations và cleanup. Failure/retry giữ riêng, không ghi đè. Không lưu env dump, key, Authorization hay nội dung session thật. Screenshot chỉ từ runtime thật khi cần UI evidence; log/source vẫn là bằng chứng chính. Token/usage thiếu để null/unverified, không ghi0 vì “offline”.

## 5. Phần làm tiếp mà không provider

- Rà claim/permalink và tài liệu tái tạo; đồng bộ checklist mà không nâng demo chưa chạy thành pass.
- Hoàn thiện manifest/observer cho matrix và kiểm bằng traces synthetic có nhãn; chỉ sau đó xem xét native offline sandbox.
- Truy lifecycle callers và v1 recovery tương ứng trước khi mở rộng so sánh restart. Chưa kết luận v1 không hỗ trợ từ việc mới trace v2.
