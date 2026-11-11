# search-r2 — retry02 v2/P-01, protocol rev1

Người dùng yêu cầu gọi lại sau hai network probe không auth thành công. **Chỉ một lượt R-0027/C-0116**, session mới, retry_of R-0026. Probe public HTTP không bảo đảm Responses/model backend; không tự mở năm slot còn lại hoặc retry thêm.

Giữ toàn bộ điều kiện `PILOT_SEARCH_R2_RETRY.md`: search-r2/manifest/rg hash, binary OpenCode v2 2.2.5 standalone, model gpt-6.1-sol/provider shopaikey/Responses SSE, native settings/tools/permission, fixture P-01 v2/prompt/seal/public/hidden/grader; không sửa môi trường hoặc task.

- Cap **300 giây gồm pacing**, **8 upstream request**, **2048 requested output token/request**, một request đang xử lý tối đa, nghỉ **≥30 giây sau response**.
- Provider failure latch dừng ngay sau lỗi và chặn native retry local; missing usage/cost hoặc known estimate chạm guard cũng dừng trước request tiếp. Local503 không phải upstream overload evidence.
- Guard chung **3 USD estimate**, kế thừa known **0.40389912 USD**, remaining known-estimate **2.59610088 USD**. **Bốn request lịch sử unpriced**, cumulative total/charge unknown, không coi là0. Đây là retry được người dùng yêu cầu rõ, không tự tiếp tục sau guard. Không tăng budget/nạp tiền hoặc coi guard mềm là trần hóa đơn cứng.
- Giá user-reported input/cache/output4.8/0.24/18 USD mỗi triệu token; không coi subtotal biết được là measured charge. Giữ ledger gốc và mọi attempt.
- Key broker host, agent net namespace riêng, dependencies/public test read-only/source fixture writable/hidden absent. Không sửa binary/service/config/session thật.
- R2 CSV riêng, raw R-0025/R-0026/legacy/protocol giữ nguyên. Status/validity/scope/test/witness/terminal/usage kiểm như runner; không suy task success từ exit0 hoặc HTTP200 riêng.

```sh
python3 -B benchmark/pilot.py --artifact-dir benchmark/artifacts/SEARCH-R2-RETRY-20261109-02 --retry-run benchmark/artifacts/SEARCH-R2-RETRY-20261109-01/R-0026/result.json --run-start 27 --config-start 116 --environment-profile search-r2 --budget-usd 3 --request-gap-seconds 30 --protocol-file benchmark/PILOT_SEARCH_R2_RETRY_02.md
```

Chốt trước request, artifact/ID chỉ dùng một lần. Hash source/protocol/pricing/manifest/seal/binary/lineage trước chạy; sau dừng kiểm usage/status/tool execution/pacing/local-blocked/cleanup, ghi kết quả riêng. Không đổi protocol khi đang chạy, không tự kéo dài timeout để đạt.
