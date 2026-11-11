# Pilot sol — protocol rev1, chốt trước chạy

Người dùng đã đồng ý pilot **2 task × 4 CLI = 8 lượt**, shared guard **3 USD ước tính** cho riêng batch này. Không cộng diagnostic Pi/smoke cũ vào kết quả pilot hoặc reset budget theo CLI. Không retry toàn lượt, không tự tăng guard/nạp tiền. Guard không phải trần hóa đơn cứng: request đang chạy có thể vượt ngưỡng trước khi usage được biết; measured charge vẫn null.

## Cấu hình cố định

- `gpt-6.1-sol`, `https://api.shopaikey.com/v1`, Responses SSE. Giá user-reported input/cache/output **4.8/0.24/18 USD mỗi triệu token**, chưa đối soát billing; cached input là subset input, không cộng reasoning hai lần.
- Bốn release/binary/checksum từ `demos/artifacts/PREP-20261106-01/preparation.json`: OpenCode v1 1.19.5, v2 2.2.5 standalone, Pi 1.5.0, Codex 0.167.0. Không sửa repo nguồn/binary/service thật.
- Task P-01/P-02 version 2, seal `artifacts/PILOT-PREP-20261106-02/preparation.json`, prompt/fixture/public/hidden không đổi. Scope/public/hidden grader như `PILOT.md`. Không dùng câu trả lời tự nhận hoặc exit 0 riêng lẻ làm success.
- Concurrency 1; tối đa **8 upstream request/2048 requested output token mỗi request/300 giây mỗi lượt**. Broker timeout 45 giây, bridge 90 giây. Mọi request title/native retry tính vào cap/budget. Pacing **≥30 giây sau response trước**, kể cả chuyển CLI/task, dùng `PacingState` batch; pacing tính vào duration/deadline. Không xếp hạng tốc độ giữa native tools/settings không tương đương.
- Model phụ v1 cố định cùng sol. Codex effort none/approval never/native workspace-write; các CLI khác capability reasoning off nhưng không ép wire tương đương. Thu `generation_settings` thực gửi, nhóm khác nhau không được gộp để kết luận ưu thế tool. Tool set/system prompt native khác nhau, backend alias/routing chưa xác minh.
- Key chỉ host broker, native config sandbox chứa nonce, bridge loopback→Unix socket/header allowlist. Namespace/home/XDG/session riêng, public test read-only, hidden grader/oracle không mount cho agent. Chỉ source fixture writable; Python stdlib, không cài dependency/Internet cho agent.
- Dừng trước request/lượt kế tiếp nếu thiếu usage/cost hoặc known estimate ≥3 USD; slot chưa chạy giữ `not_run`, không coi như tool failure. Lỗi môi trường/provider tách task failure; giữ log mọi lượt, không sửa raw để che lỗi. Dừng batch nếu witness isolation thất bại.

## Thứ tự và ID

| Run | Task | CLI | Config |
| --- | --- | --- | --- |
| R-0009 | P-01 | Pi | C-0049 |
| R-0010 | P-01 | Codex | C-0050 |
| R-0011 | P-01 | OpenCode v2 | C-0051 |
| R-0012 | P-01 | OpenCode v1 | C-0052 |
| R-0013 | P-02 | OpenCode v2 | C-0053 |
| R-0014 | P-02 | OpenCode v1 | C-0054 |
| R-0015 | P-02 | Codex | C-0055 |
| R-0016 | P-02 | Pi | C-0056 |

Thứ tự có trước chạy, không gọi là randomized. Không dùng lại ID retire. Preflight offline cập nhật dùng C-0057–C-0060, chỉ mock HTTP 400, không đọc key/provider. Cross-broker regression dùng fake clock để kiểm nghiệm pacing logic; riêng pacing live toàn batch chỉ đánh giá sau kết quả.

## Lệnh đã chốt

```sh
python3 -B benchmark/pilot.py --offline-preflight --artifact-dir benchmark/artifacts/SOL-PREFLIGHT-20261106-02 --config-start 57 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SOL.md
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/PILOT-SOL-20261106-01 --run-start 9 --config-start 49 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SOL.md
```

Artifact phải mới; không ghi đè. Runner lưu protocol/source/seal/pricing hashes, config đã che nonce, stdout/stderr, witness/PID/time, provider usage nguyên gốc và diff/grader. Sau kết thúc kiểm lại hash/key scan/pacing xuyên CLI/PID/socket/source Git. Kết quả ghi tài liệu riêng, không sửa protocol này trong lúc chạy. Chưa cho phép benchmark chính thức 48/72 lượt.
