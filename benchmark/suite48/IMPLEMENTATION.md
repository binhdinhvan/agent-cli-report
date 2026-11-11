# Nghiệm thu fixture và grader offline — 2026-11-10

**Đã có code fixture/public/hidden/oracle và seal cho B-01–B-04**, không còn chỉ là đặc tả. [Đặc tả ngày09](README.md) và [protocol48draft ngày09](../PROTOCOL_48_DRAFT.md) được giữ nguyên để tái lập order/dự toán cũ; các câu readiness=pending ở đó là trạng thái lịch sử. [Manifest triển khai hiện tại](implementation-r1.json) cập nhật readiness, **không tự duyệt protocol hoặc paid runs**.

## Kết quả thực tế (chỉ offline)

| Task | Fixture | Variant checks đạt | Positive / baseline fail / mutant fail |
| --- | --- | ---: | --- |
| B-01 | Resolver ba file và JSON schema public; hidden rubric10điểm | 17 | 1 / 1 / 15 |
| B-02 | Pagination và public/hidden contract tests | 8 | 1 / 1 / 6 |
| B-03 | TTL/LRU với injected clock và state-machine tests | 9 | 1 / 1 / 7 |
| B-04 | Dispatcher ba command, oracle hành vi cũ và delegation checks | 10 | 3 / 1 / 6 |
| Tổng | | **44** | **6 / 4 / 34** |

“Đạt” nghĩa là **reference/valid alternative pass và baseline/mutant bị fail đúng kỳ vọng**, không phải model giải44task. B-01 baseline thiếu answer phải fail schema; B-02/B-03 baseline public pass nhưng hidden fail; B-04 baseline behavior public pass nhưng chưa tách module nên hidden fail. B-01 từng đáp án hoặc evidence sai chỉ được9/10, không success. Fixture B-01 đã được đối chứng giá trị/precedence/alias/cycle/mutation bằng gọi implementation thật trong sandbox.

B-04 kiểm actual calls thay vì chỉ monkeypatch tên module: cả module import, from-import alias và cached handler registry đều pass. Có regression riêng để tránh chấm theo một phong cách code. Corpus hành vi và structural checks là bằng chứng theo test, không chứng minh tương đương mọi input hoặc chống mọi code cố tình phá grader.

## Cách ly và giới hạn

- `suite48_runtime.py` dựng bwrap user/PID/net/IPC/UTS namespaces, clear environment, không mount home/key/config/session/broker/provider thật. Witness xác nhận net namespace khác host, public/immutable files read-only, hidden grader và real home vắng ở pha writer.
- Grader chạy sau writer đã dừng, trên snapshot read-only riêng; chỉ pha hidden mới có `/grader`. Không import/execute code submission trên host interpreter.
- Scope hỗ trợ answer-only B-01, source-only B-02/B-03 và allowlisted file additions B-04. Reject deleted baseline files, public test edits, unexpected files, symlink/FIFO/oversize/file-count/directory-count violations; bỏ qua cache Python tự sinh. Các test scope dùng project sạch riêng từng trường hợp.
- Giới hạn15s/suite và output1MiB; CPU12s, address-space512MiB và file-size/file-descriptor limits trong Python entrypoint. Process-group timeout hủy worker; output ghi bounded regular files, không giữ buffer vô hạn.
- **Offline runner chỉ áp dụng writer stdlib do supervisor viết**, không gọi native CLI/model. Native CLI/config/broker integration, paid-run duration/classification/usage/ID mapping vẫn cần nghiệm thu riêng; không nâng offline witness thành live acceptance của bốnCLI.

## Seal và tái lập

- [Seal rev2](artifacts/PREP48-20261110-02/preparation.json): hash27source/fixture/prompt/manifest files,388artifact files, bwrap/python checksums; giữ source snapshots và mọi execution/grading/patch/snapshot.
- [Lượt đầu40checks](artifacts/PREP48-20261110-01/preparation.json) giữ nguyên; thay thế bởi rev2 do bổ sung schema checks và fairness cho aliases/handler registries. Source lượt đầu được giữ tại `research/artifacts/SUITE48-PRE-R2-SOURCE-20261110-01/`, không xóa/ghi đè kết quả cũ. Verifier dùng source hiện tại phải dùng seal rev2; seal rev1 khác source là drift có chủ đích, không phải lỗi model.

```sh
python3 -B benchmark/test_suite48.py
python3 -B benchmark/verify_suite48.py --artifact-dir benchmark/suite48/artifacts/PREP48-20261110-02 --verify
# Nếu muốn chạy lại self-test, phải dùng một thư mục MỚI:
python3 -B benchmark/verify_suite48.py --artifact-dir benchmark/suite48/artifacts/PREP48-REPRO
```

Seal/hash sẽ từ chối drift, không sửa manifest cũ để che thay đổi. Đây là nghiệm thu logic fixture/grader, không kết quả benchmark, không xin hoặc tiêu ngân sách inference; R/Cnext vẫn R-0039/C-0140, không reserve paid IDs.

## Việc còn lại trước benchmark trả phí

1. Nối bộ task/grader mới vào **native CLI runner adapter** riêng, không sửa runner/baseline pilot đã khóa. Preflight offline cả4CLI cho scope/isolation/config/usage/guard/duration/slot mapping; giữ những mục chưa chứng minh là pending.
2. Chốt resource/launch manifest và protocol cuối. Reference/mutant không thay được native/live acceptance.
3. Xin duyệt budget mới (đề xuất16USD estimate, không invoice cap) và quyền chạy48slot riêng. **Hiện chưa được duyệt và chưa gọi API mới.**
