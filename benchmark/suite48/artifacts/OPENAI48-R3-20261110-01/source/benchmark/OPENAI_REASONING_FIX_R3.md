# Sửa normalizer reasoning — r3, chỉ offline

Người dùng “sửa đi” sau CodexHTTP400/R277. Không gọi API, không retry smoke/benchmark hoặc mở approval; không đọc key/reserveID. Giữ nguyên tất cả script/tests/protocolr1/r2 và raw/source/CSV cũ. Bản sửa ở `openai48_reasoning_r3.py:reasoning_fields/context`, có entrypoint chỉoffline.

## Root cause và thay đổi

- [RawR277](suite48/artifacts/OPENAI48-R2-20261110-01/result.json) và [audit](../research/artifacts/OPENAI48-R2-REVIEW-20261110-01/validation.json): native đã gửi `reasoning={effort:low,context:all_turns}`, headerResponsesLite=true; effectivepayload mấtcontext, provider trả400yêucầuall_turns. **Runtime-confirmed lỗi adapter**, không phải lỗi provider chập chờn.
- Normalizercũ tại [snapshot `openai48.py:request`](suite48/artifacts/OPENAI48-R2-20261110-01/source/benchmark/openai48.py#L111-L120), pinnedhash trongaudit, thay cảobjectreasoning.
- R3 merge `{**native_reasoning, effort:low}`: giữcontext/summary/cácfieldkhác, không đổi input/tool schema, header, protocol, cacheoptions, service_tierdefault/storefalse, cap/pacing/budget hoặc estimatorcache-r2. Không sửa payload đầu vào.
- Ghi native/effective settings trongledger đúngpayloadthực; đánh dấu `reasoning_normalizer_revision=preserve-native-fields-r3`. Reuse transport/guards r2 bằng context-scopedwrapper, khôi phục globals khi thoát.
- Nếu ResponsesLiteheader=true mà native context khôngphảiall_turns, rejectlocal trướcupstream thayvì phátrequest biếtchắc sai; **không tự thêmcontext, xóaheader hoặc fallbackprotocol**. Lỗi reasoning saikiểu cũngreject. Không coi localrejection là provider400.

## Acceptance

Unit kiểm preservecontext/summary/fieldkhác, onlyeffortoverride, nonmutation, headers/endpoint/store/tier/capunchanged, ledger khớppayload, replayR277nativeheader/settings vàcache-r2 vẫn địnhgiápositivewrite. LocalUnixbroker với openerinmemory từchốinếu mấtall_turns kiểmroundtrip2request thật của broker, khôngTCP/keythật. Native16task×CLI dùngfakeprovider kiểm context theoheader vàpositivecachewrite3109/TTLunknown trênmọiturn; khônginputlờigiảithật hoặc gửiAPI.

Giữ rawR277HTTP400/usageunknown, không sửa thànhpass; khônggọi bảnsửaoffline là nativeproviderpass. Guardcarry0.33970766USD gồmestimate/reserveđãchốt, remaining15.66029234USD/6historicalunpriced, guard16USD khôngtăng; không nhập synthetictoken/cost vào phí thật. NextR326/C427 giữ nguyên. Cần liveprotocol/plan/approval mới vàfreshIDs trước chạy lại; không bypass gateCodex từ3CLIđãpass.
