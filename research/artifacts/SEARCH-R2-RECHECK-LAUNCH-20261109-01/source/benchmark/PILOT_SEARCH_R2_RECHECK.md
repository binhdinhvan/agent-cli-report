# OpenCode v2/P-01 — search-r2 environment recheck, protocol rev1

Người dùng yêu cầu chạy lại sau chuẩn hóa. **Chỉ một lượt OpenCode v2/P-01**, R-0025/C-0114/session mới. Đối chiếu R-0019 legacy đã timeout; **nhóm riêng search-r2-environment-recheck**, không xem như retry cùng môi trường hoặc mở năm slot còn lại.

## Điều kiện chốt trước chạy

- `search-r2`, manifest `research/environment-profiles/search-r2.json`; rg15.2.0 cùng checksum đã nghiệm thu offline/native tool và writable/isolation. Không thay task/prompt/fixture P-01 v2/seal/public/hidden/grader.
- Giữ OpenCode v2 2.2.5 standalone/binary pin, model `gpt-6.1-sol`, provider `https://api.shopaikey.com/v1`, Responses SSE, native tools/permission/reasoning settings như pilot trước. Không dùng session/service thật, không mở Internet cho agent hoặc cài thêm dependency.
- Cap vẫn **300 giây/lượt gồm pacing**, **8 upstream request**, **2048 requested output token/request**. Không tăng cap riêng để đạt; một request đang xử lý tối đa, nghỉ **≥30 giây sau response**.
- Latch dừng khi HTTP lỗi/failed/incomplete/missing terminal/transport exception; không gửi native retry lên provider sau lỗi. Thiếu usage/cost hoặc chạm known budget thì chặn request tiếp; không tự retry thêm hoặc mở slot khác.
- Giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token; shared guard **3 USD estimate** kế thừa known pilot/lineage **0.40389912 USD**, còn **2.59610088 USD** theo phần biết. **Hai request cũ unpriced**, cumulative charge/total unknown, không coi là0; user-authorized recheck không giải quyết phần phí thiếu. Guard mềm, không phải trần hóa đơn cứng; không nạp/tăng budget.
- Status phân biệt success/task failure/timeout/infra_error; scope/public/hidden, witness và provider terminal/usage phải phù hợp. Không dùng lời tự nhận hoặc exit0 riêng làm đạt.
- Raw legacy/r2 preflight/protocol/CSV giữ nguyên. Kết quả inference r2 vào **`benchmark/runs-search-r2.csv` riêng**, có revision/group trong notes và batch/run metadata. Retry lineage chỉ để truy vết, không gộp kết quả cùng điều kiện.

## Lệnh

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/SEARCH-R2-RECHECK-20261109-01 --retry-run benchmark/artifacts/PILOT-SOL-CONTINUE-20261106-01/R-0019/result.json --recheck-environment --run-start 25 --config-start 114 --environment-profile search-r2 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SEARCH_R2_RECHECK.md
```

Chỉ dùng artifact/ID một lần. Hash source/protocol/manifest/pricing/fixture/binary và lineage trước chạy. Giữ logs/config che token/provider usage/diff/grader/witness/time/PID. Sau kết thúc kiểm native search errors, status/terminal/pacing/cost/cleanup; ghi kết quả riêng, không sửa protocol trong lúc chạy. Một lượt đạt không chứng minh timeout cũ chỉ do rg hoặc hết lỗi provider, không thay benchmark đồng nhất tám slot.
