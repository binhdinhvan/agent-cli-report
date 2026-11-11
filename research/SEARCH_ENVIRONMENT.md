# Kiểm chứng môi trường tìm kiếm offline — 2026-11-09

> Cập nhật sau audit: người dùng đã đồng ý chuẩn hóa, **search-r2 đã nghiệm thu offline**, không inference mới. Xem [`ENVIRONMENT_R2_RESULTS.md`](ENVIRONMENT_R2_RESULTS.md). Các phần dưới mô tả audit/nguyên nhân của revision legacy, không bị viết ngược thành r2 đã có từ đầu.

## Kết luận

**Lỗi dependency của sandbox đã được xác minh, không riêng OpenCode v2. Chưa nên tiêu thêm pilot với nguyên môi trường cũ.** Không phải bằng chứng CLI không hỗ trợ glob/grep hoặc v2 giải sai task.

| CLI/binary đã pin | Sandbox hiện tại, native tool | Đối chứng có `rg` read-only |
| --- | --- | --- |
| OpenCode v1 1.19.5 | `glob` lỗi `ripgrep execution failed`; shell không tìm thấy rg | `glob` trả đúng `audit.txt`; rg chạy được |
| OpenCode v2 2.2.5 standalone | Như v1; log ghi attempted download vào cache | `glob` trả đúng `audit.txt`; rg chạy được |
| Pi 1.5.0 | Native bash không tìm thấy rg; Python3/bash/find/ls có | Bash tìm thấy/chạy được rg |
| Codex 0.167.0 | Native exec chạy rg **15.2.0** từ `codex-path` của package | Vẫn ưu tiên rg đi kèm, chạy được |

Đây là **runtime-confirmed cho các native tool được nêu**, cùng binary/profile cách ly và fixture audit mới; không phải inference/model/benchmark. Pi audit chỉ kiểm bash như pilot, không bật native grep rồi suy kết quả. Cả bốn shell không có alias `python`, nhưng có `python3`; không cần cài Python mới để chạy fixture stdlib.

## Thiết kế và bằng chứng runtime

- Chỉ synthetic Responses SSE từ broker local, token giả; bwrap network namespace riêng, không Internet hoặc API key/provider. Ép gọi glob + shell inventory cho OpenCode, bash cho Pi, exec cho Codex. Không dùng model trả phí hoặc session thật.
- Case môi trường cũ: [`../demos/artifacts/SEARCH-ENV-OFFLINE-20261109-01/result.json`](../demos/artifacts/SEARCH-ENV-OFFLINE-20261109-01/result.json), C-0081–C-0084.
- Case đối chứng: [`../demos/artifacts/SEARCH-ENV-CONTROL-20261109-01/result.json`](../demos/artifacts/SEARCH-ENV-CONTROL-20261109-01/result.json), C-0085–C-0088. Chỉ mount read-only executable rg đã có trong package Codex vào `/opt/audit-bin/rg`, thêm thư mục đó vào PATH trong **sandbox test mới**. Hash rg lưu trong result; không tải/cài/copy vào host PATH, không sửa profile pilot hoặc bundle của tool.
- Mock **dừng chủ động bằng HTTP400 local** sau khi dispatch tool, tối đa 6 response giả trước dispatch; vì vậy exit1 của OpenCode/Codex không phải thất bại tool. Kết luận lấy từ tool execution event, output inventory và fixture read-only, không từ exit toàn CLI.
- Lượt thử đầu [`../demos/artifacts/SEARCH-ENV-OFFLINE-20261106-01/result.json`](../demos/artifacts/SEARCH-ENV-OFFLINE-20261106-01/result.json) giữ nguyên: v1 đã ghi glob error/inventory nhưng mock final chưa tương thích khiến 1642 request **local** và timeout60s. Đó là lỗi diagnostic mock, không phải lỗi provider/benchmark; không cộng request local này vào usage trả phí. Đã sửa mock có stop/cap rồi chạy bằng ID/artifact mới, không ghi đè.
- Runtime tạm C-0077–C-0080 của lần đầu không còn ở lần tiếp tục; không khôi phục hoặc giả đã kiểm cleanup chúng. Raw trong workspace còn nguyên. C-0081–C-0088 kiểm PID/socket/fixture/binary/repo postcheck tại [`artifacts/SEARCH-ENV-REVIEW-20261109-01/validation.json`](artifacts/SEARCH-ENV-REVIEW-20261109-01/validation.json); giữ log v2 download và source snapshot.

## Đối chiếu source theo commit

1. V1 `RipgrepBinary.Service` tìm rg hệ thống, cache, rồi mới tải: [`packages/core/src/ripgrep/binary.ts:91–120`](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/core/src/ripgrep/binary.ts#L91-L120). Cache bin nằm dưới XDG cache: [`Global.Path:10–23`](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/core/src/global.ts#L10-L23).
2. V2 lookup/download tương ứng: [`RipgrepBinary.Service:118–148`](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/ripgrep/binary.ts#L118-L148), [`Global.Path:12–20`](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/util/src/global.ts#L12-L20). Glob gọi binary qua spawner và map lỗi chung: [`Ripgrep.run/glob:118–180`](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/core/src/ripgrep.ts#L118-L180).
3. Pi `ensureTool` có lookup/download cho native rg/fd: [`utils/tools-manager.ts:337–395`](https://github.com/earendil-works/pi/blob/f9a26365568127461c47a07a37dcb42c140a3ac5/packages/coding-agent/src/utils/tools-manager.ts#L337-L395). Đây là **source-confirmed**, không dùng để nói native grep đã được thử trong audit bash.
4. Codex package copy rg vào `codex-path`: [`layout_package:40–63`](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/scripts/codex_package/layout.py#L40-L63). Native exec audit xác nhận PATH thực ưu tiên package đó.

Trong môi trường cũ, không có rg trên PATH/cache riêng và không có Internet để tải. Cung cấp executable qua mount trong đối chứng khiến glob hoạt động, hỗ trợ kết luận **dependency/environment gây glob failure**. Không suy điều này giải thích toàn bộ timeout R-0019: lượt đó còn latency provider và pacing30 trong cap300s, và shell find đã fallback được.

## Đề xuất trước năm slot còn lại

1. Chốt revision môi trường mới với rg đã pin/hash và cùng chính sách cung cấp dependency cho bốn CLI; không bypass sandbox/permission hoặc cho agent Internet.
2. Preflight offline lại **native glob/grep/shell cần dùng**, không chỉ model config/read marker. Chỉ chạy model sau khi người dùng đồng ý thay đổi môi trường.
3. Kết quả cũ giữ nhóm môi trường cũ. Nếu chạy năm slot với revision mới phải tách nhóm, không gộp thành so sánh tám slot cùng điều kiện; muốn so sánh đồng nhất phải chốt nhóm mới/chạy lại các slot cần thiết với budget riêng được duyệt.

**Chưa áp dụng bản sửa môi trường pilot, chưa chạy tiếp năm slot hoặc retry v2.**
