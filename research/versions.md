# Phiên bản và môi trường

**Mốc chốt phiên bản: 06/11/2026**, theo [kiểm kê upstream bên dưới](#kiểm-kê-và-lựa-chọn-source-ngày-2026-11-06). Giữ nguyên OpenCode 1.19.5/2.2.5, Pi 1.5.0 và Codex rust-v0.167.0 trong nghiên cứu; không cam kết vẫn là mới nhất ngày nộp. Các mục “snapshot ban đầu”, “chưa chạy” và “provider hiện tại” bên dưới là ghi nhận theo từng mốc chuẩn bị, không phải trạng thái cuối. Trạng thái cuối: [REPORT](../REPORT.md), [OpenAI48](../benchmark/suite48/OPENAI_BENCHMARK_FINAL.md), [demo hai vòng](../demos/NATIVE_COMPLETION_R2_RESULTS.md). Cohort benchmark hoàn chỉnh dùng OpenAI trực tiếp, không phải Shopaikey.

## Snapshot ban đầu

Các giá trị dưới đây được kiểm tra từ source local trong cuộc trao đổi chuẩn bị ngày 2026-11-06. Chưa xác minh release mới nhất trên upstream, chưa xác minh binary/runtime cài đặt.

| Tool | Folder | Tag/package | Commit | Branch | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| OpenCode v1 | `../opencode-v1` | `v1.19.5` | `810c0eba1a` | detached HEAD | Chưa xác minh là 1.x cuối |
| OpenCode v2 | `../opencode-v2` | `v2.2.5` | `9bbb8ce18c` | detached HEAD | Chưa xác minh là 2.x mới nhất |
| Pi | `../pi` | coding-agent `1.5.0`; describe `v1.5.0-219-g2a32a605a` | `2a32a605a` | `main` | Snapshot development, không phải tag 1.5.0 |
| Codex | `../codex` | Manifest `0.0.0` / `0.0.0-dev` | `da279f6fd4` | `main` | Snapshot development; không suy ra release từ placeholder |

Remote:

- OpenCode: `https://github.com/anomalyco/opencode.git`
- Pi: `https://github.com/earendil-works/pi.git`
- Codex: `https://github.com/openai/codex.git`

## Cần ghi trước khi benchmark

- Ngày chốt và nguồn xác minh release/tag:
- Full commit SHA và Git status từng repo:
- Lệnh chạy/binary path và version thực tế:
- OS/kernel/architecture:
- CPU/RAM:
- Runtime/build tools:
- Model ID chính xác/provider/API endpoint (không ghi secret):
- Reasoning effort, generation settings:
- Permission/sandbox policy:
- Config/data/service isolation:
- Network/cache policy:
- Budget, timeout và số lượt:

Không ghi đè snapshot ban đầu; thêm bảng phiên bản cuối cùng bên dưới sau khi xác minh.

## Kiểm kê và lựa chọn source ngày 2026-11-06

Thời gian quan sát: `2026-11-06T03:27:35Z`–`2026-11-06T03:28:41Z`. Chính sách lựa chọn: release stable, không draft/prerelease; tách tag của package phụ khỏi release CLI. Đây là mốc chốt source cho nghiên cứu; chưa xác nhận binary/runtime hoặc sẵn sàng benchmark.

### Source local đã kiểm tra

| Repo | Full HEAD | Nhánh/tag tại HEAD | Git status |
| --- | --- | --- | --- |
| OpenCode v1 | `810c0eba1a7348036f8bdf61e6632d0c36c6876c` | detached HEAD, `v1.19.5` | Sạch |
| OpenCode v2 | `9bbb8ce18c80f099e0e448775f59d965ead40a21` | detached HEAD, `v2.2.5` | Sạch |
| Pi | `2a32a605a9f18a5f0191f65358a2e764b2f69fc7` | `main`, không có tag tại HEAD | Sạch |
| Codex | `da279f6fd4a942261b3232feb515af4259922417` | `main`, không có tag tại HEAD | Sạch |

“Sạch” nghĩa là `git --no-optional-locks status --porcelain=v1 --untracked-files=normal` thành công và không có output; không bao gồm nội dung ignored hoặc trạng thái service. Remote `origin` của cả bốn repo khớp các URL trong snapshot ban đầu; không suy ra lịch sử clone chỉ từ remote hiện tại.

Đã đọc hướng dẫn root của hai repo OpenCode và Pi; Codex không có `AGENTS.md` tại root ở checkout hiện tại. Đã đọc `README.md` của Codex và hướng dẫn release của Pi để định hướng; vẫn phải đọc hướng dẫn theo thư mục/commit trước khi thử nghiệm. Không chạy lệnh build/release/installer trong các hướng dẫn đó.

### Phiên bản source được chọn

| Cấu hình | Stable release | Full commit đích | Published UTC | Tình trạng local |
| --- | --- | --- | --- | --- |
| OpenCode v1 | [v1.19.5](https://github.com/anomalyco/opencode/releases/tag/v1.19.5) | `810c0eba1a7348036f8bdf61e6632d0c36c6876c` | 2026-10-28 06:17:49 | HEAD khớp |
| OpenCode v2 | [v2.2.5](https://github.com/anomalyco/opencode/releases/tag/v2.2.5) | `9bbb8ce18c80f099e0e448775f59d965ead40a21` | 2026-10-30 23:17:23 | HEAD khớp |
| Pi | [v1.5.0](https://github.com/earendil-works/pi/releases/tag/v1.5.0) | `f9a26365568127461c47a07a37dcb42c140a3ac5` | 2026-11-02 11:05:31 | Commit đã có, HEAD không khớp; chưa tạo checkout riêng |
| Codex CLI | [rust-v0.167.0](https://github.com/openai/codex/releases/tag/rust-v0.167.0) | `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a` | 2026-11-06 01:40:00 | Commit đã có, HEAD không khớp; chưa tạo checkout riêng |

Cách xác minh upstream:

- Đọc 100 release trên trang đầu GitHub API của mỗi upstream; chỉ xét tag đúng dạng `v1.x.y`/`v2.x.y` (OpenCode), `vx.y.z` (Pi), `rust-vx.y.z` (Codex), không draft/prerelease.
- Đối chiếu với danh sách tag công khai qua `git ls-remote --tags https://github.com/<owner>/<repo>.git`; lấy commit đã peel nếu là annotated tag. Không dùng `target_commitish` làm commit release.
- Cả bốn release được chọn đều trùng tag có số phiên bản lớn nhất theo mẫu tương ứng trong danh sách remote tại thời điểm quan sát. Không chỉ dựa vào thứ tự API hoặc endpoint `releases/latest`.
- OpenCode có release package phụ `process-daemon-v0.5.0` mới hơn về thời gian nhưng không phải release CLI; Codex có `0.168.0-alpha.*` nhưng không đáp ứng chính sách stable.
- Xác minh commit đích Pi/Codex tồn tại local bằng `git show -s --format=fuller <full-SHA>`; chưa checkout và chưa xác minh môi trường thực thi ở các commit này.

Phạm vi: đây là xác minh metadata source/upstream, không phải `runtime-confirmed`. Không cam kết phiên bản vẫn là mới nhất sau mốc quan sát; không tự cập nhật trong thực nghiệm. API mới đọc một trang, được đối chiếu danh sách tag remote đầy đủ theo mẫu; không tuyên bố đã đọc toàn bộ lịch sử release hay kiểm tra các dòng version ngoài mẫu.

### Bằng chứng source cố định

- `E-0001`: OpenCode v1 manifest khai báo `1.19.5`: [`packages/opencode/package.json:3`](https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/package.json#L3).
- `E-0002`: OpenCode v2 CLI manifest khai báo `2.2.5`: [`packages/cli/package.json:4`](https://github.com/anomalyco/opencode/blob/9bbb8ce18c80f099e0e448775f59d965ead40a21/packages/cli/package.json#L4).
- `E-0003`: Pi local manifest vẫn khai báo `1.5.0` dù HEAD không phải release: [`packages/coding-agent/package.json:3`](https://github.com/earendil-works/pi/blob/2a32a605a9f18a5f0191f65358a2e764b2f69fc7/packages/coding-agent/package.json#L3). Metadata Git phân biệt development snapshot với release, không dùng manifest một mình để nhận diện release.
- `E-0004`: Codex local workspace manifest khai báo `0.0.0`: [`codex-rs/Cargo.toml:175`](https://github.com/openai/codex/blob/da279f6fd4a942261b3232feb515af4259922417/codex-rs/Cargo.toml#L175). Không dùng giá trị này để suy ra release CLI.

### Artifact và cách kiểm tra lại

- Snapshot đã lọc, không chứa raw release body hay biến môi trường: [`inventory-2026-11-06.json`](inventory-2026-11-06.json).
- Script chỉ đọc: [`inventory.py`](inventory.py), dùng Python standard library và Git; gọi GitHub API công khai và `ls-remote`, không `fetch`, checkout hay chạy binary tool.
- Chạy từ workspace, dùng tên output mới để không ghi đè snapshot:

```sh
python3 research/inventory.py > research/inventory-review-2026-11-06T040000Z.json
```

Tên output trên là ví dụ; thay bằng mốc thời gian mới trước mỗi lần chạy. Lệnh kiểm tra trạng thái tại thời điểm chạy lại, không tái tạo metadata upstream lịch sử. Cần mạng; trường `error_type`/`unverified` hoặc exit code khác 0 là thiếu bằng chứng, không phải kết luận về tool. Script chỉ thu metadata manifest, không xác minh cách chạy hoặc isolation.

### Môi trường và việc tiếp theo

Quan sát sơ bộ: Linux kernel `6.17.0-1033-oem`, `x86_64`, glibc `2.39`, 16 logical CPU. Chưa chốt CPU model/RAM, runtime thực tế, binary path, model/provider hay budget; chưa chạy smoke test, demo hoặc benchmark.

1. Giữ nguyên checkout hiện tại. Đề xuất chuẩn bị source riêng cho Pi/Codex tại commit stable đã chọn; chỉ tạo worktree/checkout hoặc cài/build sau khi phương án được người dùng duyệt.
2. Đọc source ở đúng bốn commit đích bằng `git show` khi chưa có checkout riêng để xác minh entry point, prerequisites và cơ chế cách ly config/data/plugin/service.
3. Ghi lệnh chạy dự kiến và acceptance checks cho isolation, rồi mới xin phép chuẩn bị môi trường và smoke test.

Giai đoạn 1 chưa nghiệm thu đầy đủ: đã chốt source và kiểm kê Git, nhưng cách chạy, vị trí fixture và phương án cách ly còn cần xác minh. Không dùng checkout development của Pi/Codex thay cho release đã chọn mà không ghi quyết định thay đổi.

## Cập nhật sau đọc source cách chạy/cách ly

Đã lập [`isolation.md`](isolation.md) tại đúng bốn commit stable, kèm evidence `E-0005`–`E-0038` và [`../demos/SMOKE_TEST.md`](../demos/SMOKE_TEST.md). Cách gọi dự kiến: v1 `run` local, v2 `run --standalone`, Pi `--print --mode json`, Codex `exec --json`; tất cả dùng executable tuyệt đối trong thư mục thử riêng, không binary đang dùng. Đây là source-confirmed, chưa xác nhận runtime.

Đề xuất binary ở `.local/binaries/<tool>-<version>/`; fixture và state ở `/tmp/opencode/agent-cli-report/smoke/<config_id>/`. Chưa tạo các thư mục, chưa tải asset hoặc chốt checksum/binary path thực tế. Chưa cần worktree Pi/Codex nếu dùng binary release; nếu chuyển sang source build phải xin phép riêng.

Preflight PATH chỉ tìm thấy Bun, chưa thấy node/npm/cargo/rustc; chưa chạy runtime để lấy version. `/etc/opencode` và `/etc/codex` không tồn tại theo metadata ở thời điểm kiểm tra, cần kiểm tra lại trước launch. Chi tiết, giới hạn và điều kiện duyệt trong `isolation.md`; không đánh dấu smoke test đạt từ các quan sát này.

## Binary đã chuẩn bị và metadata runtime ngày 2026-11-06

Sau khi được người dùng cho phép, đã tải bốn archive release riêng và đối chiếu SHA-256/size với pins tại [`../demos/releases.json`](../demos/releases.json); không sửa checkout source hoặc binary đang dùng. Đường dẫn executable sau extract, tính từ workspace:

| Config | Binary trên host | stdout `--version` |
| --- | --- | --- |
| C-0001 | `.local/binaries/opencode-v1-1.19.5/payload/opencode` | `1.19.5` |
| C-0002 | `.local/binaries/opencode-v2-2.2.5/payload/opencode` | `opencode v2.2.5` |
| C-0003 | `.local/binaries/pi-1.5.0/payload/pi/pi` | `1.5.0` |
| C-0004 | `.local/binaries/codex-0.167.0/payload/bin/codex` | `codex-cli 0.167.0` |

Không gọi trực tiếp binary trên host: `demos/preflight.py` mount payload chỉ đọc ở `/opt/agent-cli-report/<config_id>` trong bwrap, dùng HOME/XDG/TMPDIR riêng ở `/tmp/opencode/agent-cli-report/smoke/<config_id>/`. Hai lệnh `--version` và `--help` mỗi tool đều exit 0; witness kiểm tra home/sentinel ẩn và network namespace riêng đều đạt. Chưa chạy local server/prompt/tool/resume; chưa tạo Git fixture hay dùng model/provider.

Hardware snapshot: Intel Core 7 240H, 16 logical CPU, RAM `15845056 KiB`, Linux `6.17.0-1033-oem`, glibc `2.39`, Python `3.12.3`; xem [`environment-2026-11-06.json`](environment-2026-11-06.json). Không cần cài host Node/npm/Cargo/Rust cho bước binary metadata này; chưa xác định chính xác phiên bản runtime nhúng trong từng binary.

Kết quả, commands, script/archive/executable hashes và giới hạn process postcheck: [`../demos/PREPARATION.md`](../demos/PREPARATION.md). Evidence version `E-0001`, `E-0002`, `E-0039`, `E-0040` là `both` trong phạm vi metadata, không phải bằng chứng benchmark hoặc attestation build từ source commit.

## HTTP API offline v1/v2

Lượt `OFFLINE-API-20261106-01` ngày 2026-11-06 dùng lại binary đã pin, không đổi checkout/source hay credential thật. Cả hai đạt acceptance tests auth, OpenAPI, SSE trước create và session metadata qua restart (`demos/OFFLINE_API.md`, evidence `E-0041`–`E-0051`). Hai server cùng nằm trong sandbox/network namespace thử tương ứng, không phải shared host service.

V1 foreground serve được dừng bằng SIGTERM (exit `-15`), v2 stdio server kết thúc sau stdin EOF (exit `0`, không fallback). Chưa có prompt, tool call, transcript resume, Client/embedded SDK runtime hoặc benchmark. Các kết luận mới không thay thế điều kiện nghiệm thu đầy đủ của giai đoạn 1/3/4.

## Provider/model hiện tại sau reset kết quả

Model hiện tại là `gpt-6.1-sol` qua `https://api.shopaikey.com/v1`. Key vẫn ở file private, không thay binary/source checkout. Giá user-reported đã cung cấp: input/cache/output 4.8/0.24/18 USD mỗi triệu token; không kế thừa giá model đã xóa. Paid-entrypoints vẫn kiểm tra đúng model/provider/giá đủ trước key/network, nhưng cập nhật giá không tự khởi chạy.

Giữ catalog exact ID và diagnostic Pi/P-01 sol hoàn tất task/public/hidden, 6 HTTP 200/completed. Đây chưa là model smoke đủ bốn CLI hoặc benchmark; model gốc/backend revision chưa xác minh. [`../benchmark/MODEL_COMPARE.md`](../benchmark/MODEL_COMPARE.md).

Artifact/log/result model cũ đã xóa theo yêu cầu; ID retire, source/permalinks giữ và runtime evidence phụ thuộc đã hạ source-only. Phạm vi cleanup: [`SOL_MIGRATION.md`](SOL_MIGRATION.md).
