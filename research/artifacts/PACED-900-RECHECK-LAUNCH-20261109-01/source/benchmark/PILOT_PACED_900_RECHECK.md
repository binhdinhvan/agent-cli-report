# v2/P-02 — nghiệm thu paced-900, protocol rev1

Người dùng đồng ý chạy sau khi sửa timing policy và nghiệm thu offline48 tests/preflight4CLI. **Một lượt R-0035/C-0136**, OpenCode v2/P-02/session mới, timing_recheck_of R-0034; **nhóm riêng search-r2:paced-900:recheck**, không nâng timeout cũ thành success hoặc gộp cap300/cap900 như cùng điều kiện.

## Điều kiện cố định

- Search-r2/manifest/rg15.2.0/hash read-only, v2 2.2.5 standalone/binary pin, model gpt-6.1-sol/provider shopaikey/Responses SSE/native settings/tools/permissions; P-02 v2/prompt/seal/public/hidden/grader không đổi. Không cài package/alias, sửa source tool/binary/service hoặc dùng session thật.
- **paced-900 chung cả bốn CLI** theo `TIMING_POLICY_R2.md`: wall cap900s gồm pacing, reserve60s tại quyết định dispatch sau tính pacing và kiểm lại sauparse; concurrency1, nghỉ≥30s, request cap8/requested output≤2048 như cũ. Broker socket45s/bridge90s không đổi. Reserve60 không bảo đảm mọi stream sẽ hoàn tất trong60s; vẫn có deadline/provider latch.
- Thiếu thời gian thì local408/time_window_exhausted, không tạo upstream; ghi timing stop riêng, không gọi provider overload. HTTP lỗi/failed/incomplete/missing terminal/exception thì provider-failure latch chặn native retry local. Thiếu usage/cost hoặc known estimate chạm guard dừng request sau. Không tự retry thêm hoặc mở ba slot khác.
- Guard chung **3 USD estimate**, prior known **0.68968632 USD**, remaining known-estimate **2.31031368 USD**. **Sáu request lịch sử unpriced**, totalchargeunknown, không xem0; đây là recheck được người dùng yêu cầu rõ, không tự nạp/tăng budget. Guard mềm không phải trần hóa đơn cứng.
- Giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token; cached input subset input/reasoning không cộng hai lần. Giữ full provider usage và rawcost, không coi subtotal biết là invoicecharge.
- Key broker host, bwrap network/home/XDG/session riêng, dependencies/public tests read-only/source writable/hidden absent; native sandbox không bypass.
- R2 CSV riêng có timing policy/group trong notes và batch/runlimits. Raw/protocol/CSV cap300 và mọiattempt cũ giữ nguyên, same-env retry lineage chỉ để truy vết.

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/PACED-900-RECHECK-20261109-01 --retry-run benchmark/artifacts/SEARCH-R2-P02-RETRY-20261109-01/R-0034/result.json --recheck-timing --run-start 35 --config-start 136 --environment-profile search-r2 --timing-policy paced-900 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_PACED_900_RECHECK.md
```

Chốt trước request; freshIDs/source/protocol/pricing/manifest/fixture/binary/lineage hashes và bộ source đã test trước chạy. Sau dừng kiểm CLI completion/scope/public/hidden/providerterminal/usage/pacing/reserve/localstop/cost/keyscan/PID/socket/Git; báo kết quả riêng, không sửa protocol khi chạy. Một lượt đạt không chứng minh provider ổn định lâu dài hoặc timeout cũ chỉ do một nguyên nhân. Không benchmark chính thức hoặc retry tự động.
