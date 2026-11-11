# search-r2 — single retry v2/P-02, protocol rev1

Người dùng yêu cầu thử lại sau R-0030: snapshot scope/public/hidden đã pass nhưng CLI timeout300s. **Chỉ một lượt R-0034/C-0123**, v2/P-02/session mới, retry_of R-0030; không mở ba slot P02/v1,Codex,Pi và không nâng kết quả cũ thành success.

Giữ điều kiện `PILOT_SEARCH_R2_FINISH.md`: search-r2/manifest/rg15.2.0/hash read-only, OpenCode v2 2.2.5 standalone/binary pin, gpt-6.1-sol/provider shopaikey/Responses SSE/native settings/permission/tools, P-02 fixture v2/prompt/seal/public/hidden/grader, Python3 policy. Không đổi task/source tool/binary/service/config người dùng hoặc cài dependency.

- Cap vẫn **300 giây/lượt gồm pacing**, **8 upstream requests**, requested output≤2048/request. Concurrency1, nghỉ≥30s sau response, không gửi đồng thời hoặc tăng timeout riêng để đạt.
- Provider failure latch dừng sau HTTP error/failed/incomplete/missing terminal/exception, native retry bị chặn local. Thiếu usage/cost hoặc known estimate chạm guard chặn request sau; không retry toàn lượt thêm.
- Guard chung **3 USD estimate**, kế thừa known **0.61870440 USD**, remaining **2.38129560 USD**. **Năm request cũ unpriced**, cumulative total/charge unknown, không coi0; user-requested single retry không giải quyết phí thiếu. Guard mềm không phải trần hóa đơn cứng, không tự nạp/tăng ngân sách.
- Giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token, không phải charge đã đối soát. Giữ nguyên raw/CSV/protocol và lineage các lượt trước, r2 CSV riêng không gộp legacy.
- Key chỉ broker host, private namespace/home/XDG/session, dependencies/public tests read-only/source writable/hidden absent; không bypass sandbox hoặc mở Internet agent. Tạo parent runtime khi thiếu nhưng từ chối overwrite sandbox có sẵn.

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/SEARCH-R2-P02-RETRY-20261109-01 --retry-run benchmark/artifacts/SEARCH-R2-FINISH-20261109-01/R-0030/result.json --run-start 34 --config-start 123 --environment-profile search-r2 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SEARCH_R2_P02_RETRY.md
```

Chốt protocol trước request; source/protocol/manifest/pricing/seal/binary/chain hash và freshIDs trước chạy. Sau dừng phân biệt snapshot correctness/CLI completion, kiểm terminal/usage/pacing/localblocked/cleanup/keyscan/Git. Không sửa protocol khi đang chạy hoặc tự mở batch tiếp theo.
