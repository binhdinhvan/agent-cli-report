# HTTP API offline v1/v2 — session metadata và lifecycle

## Phạm vi và acceptance protocol

Chốt trước lần chạy đầu: OpenCode v1 `1.19.5` và v2 `2.2.5`, binary/hash từ `PREP-20261106-01`. Chỉ HTTP API qua Python standard library, **không phải demo TypeScript Client hoặc embedded SDK**. Không cài package, không dùng credential/session thật, không gửi prompt hay gọi model/tool.

Tiếp tục dùng bwrap với HOME/XDG/DB riêng đã xác minh ở metadata preflight. Harness và server cùng ở network namespace mới; HTTP chỉ tới loopback trong namespace, không mở cổng host hay mạng provider. Payload binary và file harness mount chỉ đọc, chỉ runtime root thử được ghi. Không dùng `service start/restart/discover` mặc định.

| Test | Điều kiện đạt |
| --- | --- |
| A0 — guards | Home thật không được mount, network namespace khác host, không provider key, cwd đúng root thử |
| A1 — boot | v1 `serve --hostname 127.0.0.1 --port 0`; v2 thêm `--stdio`; nhận endpoint loopback trong 30 giây |
| A2 — auth | GET session collection thiếu auth hoặc auth sai trả 401; auth đúng đọc được health/version |
| A3 — contract | Đọc OpenAPI từ `/doc` (v1) hoặc `/openapi.json` (v2), có POST create session đúng route |
| A4 — subscribe trước mutation | Mở SSE và đọc `server.connected` trước POST tạo session, không dựa vào việc mới tạo iterator |
| A5 — metadata | Tạo session rỗng với title thử; nhận `session.created` khớp ID; GET và list thấy cùng session |
| A6 — stop/restart | v1 dừng đúng child bằng SIGTERM; v2 đóng stdin và đợi EOF shutdown không fallback; khởi động process mới cùng DB |
| A7 — persistence | Process mới đọc lại được cùng ID/title; DB file có thật; cuối lượt dừng đúng child |

Server password ngẫu nhiên chỉ tồn tại trong bộ nhớ harness và environment child, không argv/config/artifact. Không lưu Authorization headers; scrub password/base64 token khỏi stdout/stderr/result trước xuất. Đây là server credential tạm cho auth test, không phải provider credential. Mỗi HTTP request timeout 8 giây; host supervisor timeout 120 giây mỗi cấu hình, chỉ dừng process group do lượt đó tạo nếu quá hạn.

Harness chỉ cho POST đúng create-session route; không có nhánh POST prompt/generate/shell/tool. Giữ session metadata trong DB thử để làm bằng chứng, không xóa hay đụng DB thật. A7 **không** chứng minh resume hội thoại, replay event, khôi phục LLM execution hoặc exactly-once sau crash.

## Khác biệt contract được đối chiếu source

| Nội dung | v1 | v2 |
| --- | --- | --- |
| Health | `GET /global/health` | `GET /api/info` |
| Create/list/get | `/session`, `/session/:sessionID` | `/api/session`, `/api/session/:sessionID` |
| Create/get response | Session object trực tiếp | `{ data: Session.Info }` |
| List response | Array | `{ data: [...], cursor: ... }` |
| Location cho test | `x-opencode-directory` header | `location.directory` trong body create |
| Event | `GET /event`, envelope `properties` | `GET /api/event`, envelope `data` |
| Server auth env | `OPENCODE_SERVER_PASSWORD` | `OPENCODE_PASSWORD` qua CLI |
| Ownership trong test | Foreground child, stop bằng SIGTERM | Child `serve --stdio`, ownership lease qua stdin EOF |

Nguồn chính: `E-0041`–`E-0048` trong [`../research/evidence.csv`](../research/evidence.csv), cùng `E-0015`, `E-0018` và các file source dẫn ở đó. Không suy ra service discovery/shared-service chỉ từ foreground/stdio test này.

## Cách chạy

```sh
python3 demos/offline_api.py --preparation demos/artifacts/PREP-20261106-01/preparation.json --artifact-dir demos/artifacts/OFFLINE-API-20261106-01
```

Target artifact và `api-offline/<demo_id>` phải mới, không ghi đè lần cũ. Nếu thất bại, giữ nguyên log; đổi revision/script và demo ID trước retry. Không tự mở mạng/cài dependency để biến failure thành pass.

Artifacts: `summary.json` chứa hash script, binary, lệnh sandbox và trạng thái từng cấu hình; mỗi tool có `result.json`, `harness.stdout.json`, `harness.stderr.txt`, OpenAPI thực tế nếu đọc được. Chỉ công bố log sau kiểm tra nhạy cảm. Phiên bản credential tạm không được xuất ra log. Screenshot chưa cần cho HTTP JSON; không tạo ảnh giả giao diện để thay log.

## Kết quả

Protocol trên được chốt trước lần chạy đầu. Lượt `OFFLINE-API-20261106-01` đã chạy từ `2026-11-06T04:07:18Z` đến `04:07:21Z`:

| Hạng mục | v1 | v2 |
| --- | --- | --- |
| Trạng thái harness | `offline_api_pass` | `offline_api_pass` |
| Checks boolean | 19/19 đạt | 21/21 đạt |
| GET session thiếu/sai auth | 401 / 401 | 401 / 401 |
| Tạo session rỗng, GET/list | Đạt | Đạt |
| SSE trước mutation | connected → session.created khớp ID | connected → session.created khớp ID |
| Đọc ID/title từ process mới | Đạt | Đạt |
| Dừng mỗi server | SIGTERM, exit `-15` | stdin EOF, exit `0`, không fallback |
| Endpoint hai cycle, trong namespace riêng | `127.0.0.1:4096` / `127.0.0.1:4096` | `127.0.0.1:42721` / `127.0.0.1:37135` |

Hai check thêm của v2 là PID health trùng child và EOF shutdown. Các số đếm check khác nhau không phải thang điểm so sánh tool. Mỗi cấu hình có 8 request JSON được ghi và một SSE subscription, không có request prompt/generate/shell. Các counter cost/token mặc định trong metadata session v1 không được dùng như số liệu usage benchmark.

**Phát hiện về port:** v1 `--port 0` thực tế ưu tiên 4096 rồi mới fallback port tự do (`E-0049`); không diễn giải nó là luôn lấy cổng ngẫu nhiên. Trong test không va chạm host vì network namespace riêng. V2 `serve --stdio --port 0` dùng cổng động trong hai cycle đã quan sát. Chưa thử tình huống cổng v1 bị chiếm.

**Giới hạn persistence:** v1 được terminate bằng SIGTERM, không gọi đó là graceful shutdown; v2 EOF kết thúc được không fallback. Chỉ quan sát metadata của session chưa có message, không thử transcript resume, execution recovery sau crash hay exactly-once (`E-0050`, `E-0051`). Không phải demo shared-service/TUI/desktop/web.

Artifacts thực tế:

- [`summary.json`](artifacts/OFFLINE-API-20261106-01/summary.json): version/profile/hash script, PID supervisor, sandbox commands và exit codes.
- [`opencode-v1/result.json`](artifacts/OFFLINE-API-20261106-01/opencode-v1/result.json), [`opencode-v2/result.json`](artifacts/OFFLINE-API-20261106-01/opencode-v2/result.json): checks, request/response, event và server cycle log đã lọc credential.
- [`opencode-v1/openapi.json`](artifacts/OFFLINE-API-20261106-01/opencode-v1/openapi.json), [`opencode-v2/openapi.json`](artifacts/OFFLINE-API-20261106-01/opencode-v2/openapi.json): contract lấy từ server thử thực tế.
- [`postcheck.json`](artifacts/OFFLINE-API-20261106-01/postcheck.json): bốn repo source vẫn sạch, không có service registration trong hai root thử. Không thấy process mang inode CLI thử trong 111 executable truy cập được; 277 mục `/proc` không truy cập được/đã biến mất, không suy ra đã audit mọi helper. Không signal process ngoài lượt thử.

Đây không phải benchmark và không gộp duration với kết quả giải task.

## Phân biệt HTTP API, Client và SDK

Lượt trên chỉ dùng HTTP qua Python, không được gọi là runtime-confirmed cho hai package sau:

- `@opencode/client` có Promise/Effect và service entrypoints riêng (`E-0052`). Promise service API `discover` đọc/probe registration, trong khi `ensure` có nhánh spawn `serve --service` (`E-0054`); không dùng chúng trên môi trường thật chỉ để minh họa.
- `@opencode/sdk` ở `PromiseSdk.create` ghép `EmbeddedHost` với `OpenCode.make({ fetch: host.fetch })`, thêm aliases `sessions`/`events` và ownership `close`/asyncDispose (`E-0053`). Đây là truy vết source, chưa chạy embedded host.

Demo gửi prompt/nhận completion event, TypeScript Client và embedded SDK vẫn chưa kiểm chứng; không đánh dấu hoàn thành mục API/SDK tổng thể từ lượt metadata này.
