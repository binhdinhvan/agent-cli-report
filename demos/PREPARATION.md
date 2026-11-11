# Chuẩn bị binary và môi trường thử

Phạm vi người dùng đã duyệt: tải release riêng trong workspace, tạo môi trường riêng dưới `/tmp/opencode/agent-cli-report/`, không installer/cài global, không gọi model. Không thay binary OpenCode hay restart service đang sử dụng. Source repos vẫn chỉ đọc.

## Release pins

[`releases.json`](releases.json) chốt bốn tag/commit, asset Linux x86_64, kích thước và SHA-256 lấy từ GitHub Release API. Hai OpenCode dùng bản baseline glibc; Pi dùng binary release; Codex dùng full package để giữ các executable đi kèm. Không tự đổi sang phiên bản mới hơn hoặc asset khác nếu pin không khớp.

SHA-256 được đối chiếu với metadata HTTPS từ cùng upstream, **không phải xác minh chữ ký độc lập hay chứng minh binary được build từ source SHA**. Source SHA được truy từ tag ở bước kiểm kê; runtime version sẽ được ghi riêng. Không tự cài dependency/build tool khi asset không chạy được.

## Script chuẩn bị

```sh
python3 demos/prepare.py --artifact-dir demos/artifacts/PREP-20261106-01
```

Chỉ chạy lại sau khi kiểm tra trạng thái lần trước và đổi artifact ID; script từ chối ghi đè binary/runtime root đã có. Không xóa thư mục rộng để vượt kiểm tra này. Script:

1. Xác minh metadata stable release và asset đúng pin.
2. Download vào `.local/binaries/<tool>-<version>/`, so size và SHA-256 trước extract.
3. Extract bằng `tarfile` data filter, không chạy installer trong archive; nhận diện ELF x86_64 của CLI và ghi checksum executable.
4. Tạo root/config directory riêng cho `C-0001`–`C-0004`; Codex có config auth backend `file`, không credential.
5. Lưu URL, checksum, archive inventory, đường dẫn và trạng thái; chưa khởi động CLI ở bước này.

Tổng kích thước archive pin: `457903146` bytes; cần tối thiểu 4 GiB trống cho archive và payload. Không tải desktop/web ở bước này.

## Preflight không dùng model

```sh
python3 demos/preflight.py --preparation demos/artifacts/PREP-20261106-01/preparation.json --artifact-dir demos/artifacts/PREFLIGHT-20261106-01
```

Mỗi lệnh tạo sandbox bwrap với user/PID/network/IPC/UTS namespace riêng, mount `/usr` và thư viện chỉ đọc, payload binary ở `/opt/agent-cli-report/<config_id>` chỉ đọc; root thử là mount ghi duy nhất từ dữ liệu project. `/tmp`, `/dev`, `/proc` là môi trường sandbox. Không mount home thật, source repos, desktop sockets hoặc service registration thật. Điều này không phải audit an toàn toàn bộ binary hay thay cho việc chốt sandbox benchmark.

Environment được dựng từ allowlist, không kế thừa provider key/password/config/DB overrides. Network namespace riêng không có đường ra mạng hoặc loopback service của host. Mỗi lệnh timeout 45 giây, có dừng process group riêng khi quá hạn. Không dùng `opencode service` hay gửi prompt.

Trước khi chạy CLI, witness kiểm tra: home thật bị ẩn, sentinel vô hại bên ngoài mount thử bị ẩn, network namespace khác host, cwd đúng root và không mang provider/server credentials. Sentinel chỉ tạo trong cây thử, không tạo trong home/data thật. Witness không đạt thì không chạy CLI.

Sau witness chỉ chạy `--version` và `--help`, lưu command/env không secret, stdout/stderr, PID supervisor, exit code, duration và checksum binary. Kết quả này chỉ xác minh launch/metadata trong profile sandbox, không chứng minh prompt, tool call, resume hoặc shared-service hoạt động. Không gộp duration này với benchmark.

## Artifact và trạng thái

- `demos/artifacts/PREP-20261106-01/preparation.json`: kết quả chuẩn bị; chỉ ghi nhận thành công khi tất cả checksum/extract đạt.
- `demos/artifacts/PREFLIGHT-20261106-01/preflight.json`: chỉ có sau khi chạy preflight; lỗi môi trường/tool được giữ nguyên.
- Screenshot chỉ chụp từ lần chạy thật nếu cần minh họa; text logs là bằng chứng chính cho bước metadata. Chưa có ảnh TUI/desktop/web từ bước chuẩn bị.

Không có cleanup tự động xóa dữ liệu. Không service dài hạn nào được chủ ý khởi động trong hai script này; nếu phát hiện process còn sống ngoài dự kiến, xác minh đúng PID/root trước khi dừng. Giữ artifact mọi lần thử và xin phép riêng trước thao tác dọn lớn.

## Kết quả lần đầu ngày 2026-11-06

Chuẩn bị: `03:49:40Z`–`03:52:54Z`. Bốn archive đúng size/SHA-256 đã pin, extract và nhận diện CLI ELF thành công; không dùng installer. Metadata preflight: `03:53:36Z`–`03:53:38Z`.

| Config | Tool | stdout nguyên văn của `--version` (bỏ newline cuối) | Exit version/help | Trạng thái |
| --- | --- | --- | --- | --- |
| C-0001 | OpenCode v1 | `1.19.5` | 0 / 0 | metadata_pass |
| C-0002 | OpenCode v2 | `opencode v2.2.5` | 0 / 0 | metadata_pass |
| C-0003 | Pi | `1.5.0` | 0 / 0 | metadata_pass |
| C-0004 | Codex CLI | `codex-cli 0.167.0` | 0 / 0 | metadata_pass |

Tổng 8/8 metadata command exit 0; 4/4 witness đạt năm checks đã định nghĩa. OpenCode v1 ghi help ra stderr nhưng exit 0, không phân loại đây là lỗi. Không dùng duration các lệnh này để so sánh hiệu năng tool.

Bằng chứng version: `E-0001`, `E-0002`, `E-0039`, `E-0040` trong `research/evidence.csv` có trạng thái `both` trong phạm vi metadata; các kết luận agent loop/context/permission không được nâng trạng thái từ phép thử này.

Artifact bổ sung:

- [`PREP-20261106-01/preparation.json`](artifacts/PREP-20261106-01/preparation.json): archive/binary hashes, member inventory và đường dẫn thực tế.
- [`PREP-20261106-01/script-hashes.json`](artifacts/PREP-20261106-01/script-hashes.json): checksum hai script và release manifest không thay đổi sau các lần gọi tương ứng.
- [`PREFLIGHT-20261106-01/preflight.json`](artifacts/PREFLIGHT-20261106-01/preflight.json): command/env allowlist, witness, stdout/stderr và exit code đầy đủ, không có credential.
- [`PREFLIGHT-20261106-01/postcheck.json`](artifacts/PREFLIGHT-20261106-01/postcheck.json): trạng thái bốn repo vẫn sạch, metadata file trong root thử và kiểm tra process giới hạn.
- [`../research/environment-2026-11-06.json`](../research/environment-2026-11-06.json): CPU/RAM/kernel/Python của host; chưa chốt model/provider.

Postcheck không phát hiện process mang inode của bốn CLI thử trong 111 process executable truy cập được; 284 mục `/proc` không truy cập được hoặc đã biến mất. Không khẳng định đã kiểm tra mọi process/helper; không signal process nào. Metadata command có side effect trong root riêng: Pi tạo file auth/model store, OpenCode v2 tạo log và file thư viện tạm; chi tiết size/path trong postcheck, không dùng metadata command như thao tác hoàn toàn không ghi.

**Tại mốc metadata, chưa đạt:** effective config khi agent chạy, private server lifecycle, prompt, tool call, resume, shared-service và benchmark. Các bước dùng model cần chốt model/provider/auth thử, timeout/budget và phương án mạng có kiểm soát trong sandbox. Không mở mạng hoặc tái dùng credential thật chỉ vì metadata đã pass.

Cập nhật sau mốc metadata: HTTP API/session metadata và foreground/stdio server lifecycle v1/v2 đã được kiểm chứng thêm tại [`OFFLINE_API.md`](OFFLINE_API.md). Luồng prompt/tool/resume hội thoại, managed shared-service và benchmark vẫn chưa chạy. Các artifact metadata ở trên được giữ nguyên, không ghi đè bằng kết quả mới.
