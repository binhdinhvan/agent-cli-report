# Cách chạy và cách ly — nghiên cứu source trước smoke test

Trạng thái: **source-confirmed; metadata offline và HTTP session-metadata v1/v2 đã kiểm chứng, luồng agent đầy đủ chưa kiểm chứng**. Chỉ áp dụng Linux và bốn commit trong `versions.md`. Các lệnh prompt dưới đây vẫn là thiết kế dự kiến, chưa chạy và chưa phải benchmark protocol. Kết quả: [`../demos/PREPARATION.md`](../demos/PREPARATION.md), [`../demos/OFFLINE_API.md`](../demos/OFFLINE_API.md).

## 1. Phương pháp và giới hạn

Đọc file bằng `git show <full-SHA>:<path>` và tìm symbol bằng `git grep <pattern> <full-SHA>`, không đổi checkout. Pi/Codex được đọc tại commit stable, không dùng implementation ở HEAD development để kết luận cho release.

Mỗi evidence ID dưới đây có commit, file, dòng/symbol và permalink trong [`evidence.csv`](evidence.csv). Tài liệu V2 tại `https://opencode.ai/v2/docs/{cli,config,troubleshooting}` chỉ dùng định hướng; các kết luận phụ thuộc source đã pin. Chưa kiểm chứng toàn bộ root của skills/instructions, mọi plugin hoặc hành vi client desktop/web.

Kiểm tra cấu trúc bằng `python3 research/validate_evidence.py` từ workspace: script chỉ đọc Git để đối chiếu ID, SHA, file, range dòng và permalink; không chứng minh semantics của claim hay kết quả runtime.

## 2. Bố trí đã tạo cho metadata preflight

```text
agent-cli-report/.local/binaries/<tool>-<version>/   # executable release riêng
/tmp/opencode/agent-cli-report/smoke/<config_id>/
  home/                                           # HOME riêng
  xdg-config/ xdg-data/ xdg-cache/ xdg-state/
  tmp/                                            # TMPDIR riêng
  managed/                                        # chỉ dùng override v1 đã xác minh
  agent/                                          # Pi agentDir
  codex-home/                                     # CODEX_HOME
  sessions/                                       # Pi session-dir
  project/                                        # cwd/fixture độc lập
```

Đây là lựa chọn vận hành, không phải feature của tool. Mỗi cấu hình/lượt thử có root riêng, dùng đường dẫn tuyệt đối và kiểm tra realpath; không symlink về home/data thật. Fixture không đặt trong repo source của tool hoặc bên dưới workspace báo cáo để tránh nạp instructions/config nghiên cứu ngoài ý muốn. Vẫn phải kiểm tra các ancestor tới filesystem root; chuyển sang `/tmp/opencode` không tự bảo đảm ancestor sạch.

Launcher phải dựng môi trường theo allowlist từ đầu, không sao chép nguyên `process.env`. Chỉ cho HOME/XDG/TMPDIR của lần thử, PATH tối thiểu đã duyệt, locale/terminal cần thiết và các biến đã được xác minh theo tool. Không kế thừa server URL/password, DB path, plugin/config overrides, `NODE_OPTIONS`, `BUN_OPTIONS`, proxy hay provider credentials ngoài quyết định thử nghiệm. Không ghi credential vào argv/config mẫu/log. Đã có `demos/preflight.py` cho witness và metadata offline; chưa có launcher gửi prompt/model.

Đổi HOME/config directory là cách ly trạng thái ứng dụng, **không phải sandbox filesystem cưỡng chế**. Trước prompt có tool call phải duyệt phương án hạn chế truy cập home thật bằng sandbox/container hoặc cơ chế OS tương đương, kiểm tra khả dụng thực tế; không coi sự hiện diện executable `bwrap`/`docker` là sandbox đã hoạt động.

## 3. OpenCode v1 — `v1.19.5`

### Điều source xác nhận

- Global paths dùng `xdg-basedir`, tách data/cache/config/state; home có `OPENCODE_TEST_HOME`. Import module có thể tạo thư mục ngay, nên ngay cả metadata command cũng cần môi trường riêng (`E-0005`). Test preload của repo đặt đủ bốn XDG env cùng home/managed overrides (`E-0010`); đây chưa phải bằng chứng chạy binary.
- `OPENCODE_CONFIG_DIR` là một nguồn bổ sung; config loader vẫn merge global/custom/project. `OPENCODE_DISABLE_PROJECT_CONFIG` không loại bỏ global config và `$home/.opencode` (`E-0006`, `E-0007`). Không chỉ đổi CONFIG_DIR rồi coi đã cách ly.
- Config discovery có thể tạo `.gitignore` và lên lịch npm install; không coi khởi động/config inspection là thao tác hoàn toàn không ghi (`E-0007`). Chỉ cho phép trong root thử sau khi duyệt tác động/network.
- Trên Linux, managed config mặc định `/etc/opencode`, có override `OPENCODE_TEST_MANAGED_CONFIG_DIR` (`E-0009`). Đây là test hook của commit v1 này, không suy sang v2 hoặc macOS MDM.
- DB nhận `OPENCODE_DB`; đường dẫn tương đối nằm dưới data root (`E-0011`).
- Nhánh `run` không `--attach` gọi server bằng custom fetch trong process (`E-0008`). Không dùng `--attach` hoặc service thật cho smoke đầu tiên. Không suy ra mọi client v1 đều có cùng lifecycle.
- Lượt HTTP offline dùng foreground `serve` riêng: `--port 0` đã chọn 4096 theo fallback source, không luôn là cổng ngẫu nhiên (`E-0049`). Test nằm trong network namespace riêng, không kết nối host port 4096.

### Profile smoke dự kiến

- HOME và `OPENCODE_TEST_HOME` cùng trỏ `home/`; bốn XDG env trỏ root riêng; TMPDIR trỏ `tmp/`.
- `OPENCODE_CONFIG_DIR=<root>/xdg-config/opencode`; `OPENCODE_DISABLE_PROJECT_CONFIG=1`; `OPENCODE_TEST_MANAGED_CONFIG_DIR=<root>/managed`.
- `OPENCODE_DB=<root>/xdg-data/opencode/smoke.db`, dùng file để kiểm tra resume; không dùng `:memory:`.
- Gọi executable tuyệt đối, dự kiến: `"$OC1_BIN" run --format json --model "$OC1_MODEL" "$PROMPT"`. Binary path và model còn phải chốt. Parser model/format có evidence `E-0038`; nhánh local có evidence `E-0008`.
- Cách chạy source có script Bun ở `E-0033`, nhưng chưa duyệt cài/build và không chạy dev command trong checkout hiện tại.

## 4. OpenCode v2 — `v2.2.5`

### Điều source xác nhận

- Bốn XDG roots được đọc từ environment; tmp dựa vào `os.tmpdir()`; `OPENCODE_TEST_HOME` chỉ đổi home, không tự đổi các root còn lại (`E-0012`, `E-0013`). CLI map CONFIG_DIR và các project/Claude flags thành server config options (`E-0018`).
- `run` có `--standalone`, `--server`, model/session và JSON format qua command definition (`E-0019`). Resolver cấm kết hợp server với standalone (`E-0014`).
- Standalone spawn child `serve --stdio --port 0` và tạo credential riêng (`E-0015`). Đã thử trực tiếp `serve --stdio` kết thúc bằng EOF (`E-0043`); chưa gọi đúng wrapper `Standalone.start` qua CLI flag. Standalone không có nghĩa config/data riêng.
- Managed service registration nằm dưới state root, config dưới config root. Một số channel dùng chung tên `service.json` và cổng mặc định; đổi XDG state không tự đổi cổng (`E-0016`). Không chạy `service set`, restart hoặc discovery mặc định bằng môi trường thật.
- Discovery có `/etc/opencode`, global `.agents`/`.claude`, project/ancestor walk tới root (`E-0017`). SDK có options `system/global`, nhưng không mặc định biến chúng thành env/CLI flag. Mapping CLI đã đọc không truyền system override (`E-0018`); chưa tuyên bố không tồn tại cơ chế khác.
- DB nhận `OPENCODE_DB`, resolve dưới data root nếu tương đối (`E-0020`).

### Profile smoke dự kiến

- HOME, `OPENCODE_TEST_HOME`, XDG và TMPDIR riêng như v1, nhưng không dùng managed override v1 cho v2.
- `OPENCODE_CONFIG_DIR=<root>/xdg-config/opencode`; `OPENCODE_CONFIG_PROJECT_DISABLE=1`; `OPENCODE_DISABLE_CLAUDE_CODE=1`, theo mapping `E-0018`. `.agents` được xử lý bằng home/cwd riêng và preflight, không giả định Claude flag tắt `.agents`.
- `OPENCODE_DB=<root>/xdg-data/opencode/smoke.db`.
- Dự kiến: `"$OC2_BIN" run --standalone --format json --model "$OC2_MODEL" "$PROMPT"`. Không kết hợp `--server`.
- Demo shared-service là lượt riêng sau này: cần state/config riêng **và cổng loopback riêng đã duyệt**, theo dõi registration/PID/endpoint. Không dùng kết quả standalone để nghiệm thu shared-service.
- Script source/Bun được định vị tại `E-0034`; chưa build hoặc chạy. Binary alias `opencode2` không phải bảo đảm cách ly service.

## 5. Pi — `v1.5.0`

### Điều source xác nhận

- APP_NAME mặc định `pi`, tạo tên env `PI_CODING_AGENT_DIR`; auth, settings, models và sessions mặc định nằm dưới agentDir (`E-0021`). Project settings vẫn ở `cwd/.pi/settings.json` (`E-0022`).
- Session directory ưu tiên `--session-dir`, rồi `PI_CODING_AGENT_SESSION_DIR`, rồi settings (`E-0025`). Không dùng `--no-session` khi kiểm tra resume.
- Parser có các flag tắt extension/MCP/skill/template/theme/context discovery (`E-0023`). Nhưng loader vẫn resolve package trước khi lọc `noExtensions`; extension đường dẫn CLI vẫn được xét (`E-0024`). Các flag không thay thế agentDir/cwd sạch và không bảo đảm không truy cập mạng.
- Manifest có bin Node ở `dist/bundle/cli.js` và build binary Bun (`E-0035`). Không suy ra source chưa build có thể chạy trực tiếp chỉ vì có Bun trên PATH.

### Profile smoke dự kiến

- HOME riêng, `PI_CODING_AGENT_DIR=<root>/agent`, session directory riêng, cwd fixture độc lập không có package/extension config ngoài dự kiến.
- Dự kiến: `"$PI_BIN" --print --mode json --session-dir "$PI_SESSIONS" --no-extensions --no-mcp --no-skills --no-prompt-templates --no-themes --no-context-files --model "$PI_MODEL" "$PROMPT"`.
- Đây là **profile chẩn đoán tối giản**, không phải cấu hình benchmark cuối: tắt built-in extension có thể thay đổi tool exposure. Phải chốt lại exposure trước pilot.
- Chưa nghiệm thu toàn bộ lifecycle/service của Pi; không kết luận không có daemon hoặc chức năng nền từ phạm vi đọc này.

## 6. Codex CLI — `rust-v0.167.0`

### Điều source xác nhận

- `CODEX_HOME` phải tồn tại và là directory, được canonicalize (`E-0026`). `--ignore-user-config` không đổi auth home; `--ephemeral` không phải cách ly config (`E-0027`). Không dùng ephemeral cho phép thử resume.
- `exec` khởi tạo `InProcessAppServerClient`; bằng chứng này chỉ cho nhánh exec, không suy sang TUI/daemon (`E-0028`).
- Config loader nạp system layer độc lập với user config (`E-0029`), gồm requirements Unix riêng (`E-0036`). `/etc/codex/config.toml`, `requirements.toml` và managed config cần preflight; không coi CODEX_HOME mới là đã loại bỏ config hệ thống.
- SQLite có thể bị chuyển bởi config/env, log mặc định dưới home (`E-0030`). Không kế thừa `CODEX_SQLITE_HOME` từ môi trường người dùng; phải kiểm tra đường dẫn thực tế.
- Auth backend phân biệt File/Keyring/Auto/Ephemeral (`E-0031`); profile thử chọn file trong CODEX_HOME mới, không dùng credential/keyring thật. Nếu auth không sẵn sàng, dừng và báo blocker thay vì tự đăng nhập.
- PluginStore có cache/data roots dưới codex_home (`E-0032`); đây chưa bao phủ mọi root plugin/skill discovery được cấu hình ngoài đó.

### Profile smoke dự kiến

- HOME riêng, tạo directory `CODEX_HOME=<root>/codex-home` trước launch; môi trường allowlist không mang SQLite/server/provider override ngoài duyệt.
- Dùng config tối giản riêng, chọn `cli_auth_credentials_store = "file"` (`E-0037`, backend ở `E-0031`) sau bước kiểm tra effective config/auth. Không dùng `--ignore-user-config` nếu nó loại bỏ chính cấu hình thử cần áp dụng.
- Dự kiến: `"$CODEX_BIN" exec --json --model "$CODEX_MODEL" "$PROMPT"`, chạy từ fixture Git mới. Giữ sandbox/approval policy có kiểm soát; không thêm bypass flag chỉ để chạy được.
- Chưa chốt mọi root skills/instructions, MCP OAuth và plugin discovery. Phải kiểm tra effective inputs và trace trước prompt; không coi PluginStore root là đủ chứng minh cách ly toàn bộ.

## 7. Quan sát host, không chạy tool

Kiểm tra metadata/PATH khoảng `2026-11-06T03:34Z`:

| Hạng mục | Quan sát |
| --- | --- |
| `/etc/opencode`, `/etc/codex` | Không tồn tại theo metadata ở thời điểm kiểm tra; kiểm tra lại trước launch |
| Bun | Có đường dẫn `/home/tts/.bun/bin/bun`; chưa gọi để xác nhận version |
| node/npm/cargo/rustc | Không tìm thấy trên PATH của shell hiện tại; không kết luận chưa cài trên toàn máy |
| strace/bwrap/docker | Tìm thấy executable trên PATH; chưa chạy hoặc xác minh khả dụng |

Chỉ kiểm tra tên/path và sự tồn tại, không đọc config/credential/session thật. Quan sát này là preflight host, **không phải runtime-confirmed cho cơ chế tool**. Cần artifact quan sát có thời gian và trace đã lọc ở smoke test để nâng trạng thái evidence.

## 8. Điều kiện để chuyển sang smoke test

1. Đã được người dùng duyệt và thực hiện tải binary release riêng, kiểm tra asset/checksum và metadata version, không installer hay cài global. Nếu sau này cần đổi asset/source build thì trình phương án riêng, không tự chuyển.
2. Đã dựng sandbox/root và chạy witness cho metadata offline. Còn cần duyệt mạng/provider cho prompt và phạm vi dọn tài nguyên; sandbox metadata không mặc định là benchmark sandbox cuối.
3. Trước launch kiểm tra system config và ancestor inputs bằng metadata; có config hệ thống thì không tự bỏ qua policy hoặc sửa/xóa file. Dừng và chọn môi trường thử được phép.
4. Mọi lệnh kể cả `--version`/`--help` chạy trong profile riêng. Quan sát file/process/network access trong root thử, không dump credential hay môi trường đầy đủ vào log chia sẻ.
5. Duyệt model/provider và ngân sách trước bất kỳ prompt thật nào. Không tái sử dụng auth/session đang hoạt động; không có auth thử thì ghi `unverified`/blocker.

Acceptance checks và trình tự dự kiến: [`../demos/SMOKE_TEST.md`](../demos/SMOKE_TEST.md). Chỉ đánh dấu cách ly runtime đạt sau khi có bằng chứng, không từ các profile dự kiến ở trên.
