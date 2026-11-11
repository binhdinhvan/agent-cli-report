# Chạy lại OpenAI48 — cache-cost r2

Người dùng yêu cầu “chạy lại benmark” sau nghiệm thu bản sửa. Scope mới: **chạy lại smoke thật đủ4CLI, chỉ khi cả4 đạt mới chạy48slot benchmark mới**. Không nối41slotShop, không trộn điểm smoke/benchmark hoặc provider. Giữ toàn bộ raw/failure/approval/52reservedIDs của r1; native smoke mới là retry_ofR222 cho v1, ba CLI kia là firstattempt smoke. BenchmarkOpenAI vẫnchưa cóattempttrước scope này.

Kế thừa [protocolr1](PROTOCOL_OPENAI48_R1.md) về binary/sourcepins, order/prompt/fixture/rubricr2, isolation, concurrency1/gap≥30/socket45/wall900/reserve60/request8/output2048, reasoninglow/defaulttier/ResponsesSSE/storefalse và no retry/fallback/topup trong đợt mới. Native tool event/finalmarker/isolation/usage là smoke gate; smoke grader không tính điểm. Index append-only phân biệt slot `OAI-R2-SMOKE-*`, repetitionsmoke; báo cáo benchmark chỉ lấy48slotD48.

Thay estimator bằng `openai_cache_cost_r2.estimate`, adapter `openai48_cache_r2.context`: [công thức và semantics](OPENAI_CACHE_FIX_R2.md). Positivecachewrite có breakdown thì tính đúng từng tariff, thiếu breakdown thì conservative12hupperestimate; không coi là charge, không doublecount. Missing/malformedusage vẫn dừng. Không thay cache request semantics hoặc tự suyTTL.

## Ngân sách/carry

Giữ **guard16USD**, khônginvoicecap. Historical known0.28655616USD/5unpriced giữ nguyên. Dành thêm **0.015871USD guard reserve** cho request2R222 cóusage nhưngTTLunknown theo replayr2; đây **không phải reprice vào known cost**. Guardcarry0.30242716, phần còn lại **15.69757284USD** gồm4smoke+48benchmark. Bốnrequestunknown cũ không cóusage vẫnunknown, khônggiả0. Không nhập synthetic fees vào phí thật. Mọi upperestimate mới trừ guard như tariffestimate; tổngcharge vẫn unknown.

## Launch và kết thúc

Runner mới `openai48_r2.py` bind protocol/script/tests/r2nativeoffline16×CLI/40cachewriteexchanges/source/profile/resource/registry/oldraw. Approval mới phải khớp exactplan, artifact vàbudget; lock trướcreserve52freshIDs từR274/C375, không tái dùng52IDr1. Credential private600 chỉđọc saugates, khôngin/savekey. Source snapshots giữ nguyên.

Hai giai đoạn cùngscope, cách nhau gap≥30s thật, carry smoke estimates sangbenchmark. Lỗi provider/usage/isolation/infra dừng; validtaskfailure/timeout vẫn có thểtiếp theo protocol. Không tựresume khi dừng, khôngupstreamretry. Final summary durable và đóng gateauthorization kể cả launcherexception; giữ mọiIDsnotrun. Một launch đãreserve không tựchạy lại. Unit/regression vànativeoffline không thay thế smoke thật; không cam kết hoàn thành48hoặc độổnđịnh dài hạn.
