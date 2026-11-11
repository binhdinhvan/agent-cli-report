# Benchmark OpenAI trực tiếp — kết quả cuối

**Hoàn thành48/48slot hợp lệ:46success,2failure,0timeout,0infra_error; không retry benchmark để tăng điểm.** Cả4CLI đã pass native smoke thật trước cohort. Đây là so sánh end-to-end của **CLI + native prompt/tool schema + cùng model/provider**, không phải phép đo thuần mô hình hoặc kết luận tool tốt nhất mọi tác vụ.

## 1. Phiên bản và điều kiện

| CLI | Version | Source commit |
|---|---|---|
| OpenCode v1 | 1.19.5 | `810c0eba1a7348036f8bdf61e6632d0c36c6876c` |
| OpenCode v2 | 2.2.5 | `9bbb8ce18c80f099e0e448775f59d965ead40a21` |
| Pi | 1.5.0 | `f9a26365568127461c47a07a37dcb42c140a3ac5` |
| Codex CLI | rust-v0.167.0 | `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a` |

Provider `https://api.openai.com/v1`, model `gpt-6.1-sol`, Responses SSE, effortlow/tierdefault/storefalse; giữ native reasoning fields, gồm contextall_turns của Codex. Contextcap128K/outputcap2048, tốiđa8upstream/lượt, concurrency1/gap≥30s, wall900s/reserve60s; `search-r2/paced-900`, fresh workspace/session/config mỗi lượt. Bwrap/isolation do **harness** cung cấp, không chứng minh native sandbox tương đương.

4task ×4CLI ×3lần. B-01 hiểucode/answerJSON10điểm; B-02 sửa pagination; B-03 TTL/LRU cache; B-04 refactor router đa file. Fixture synthetic Pythonstdlib do nghiên cứu soạn; rubric `b01-evidence-r2`, scope/public/hidden/CLI completion đều được kiểm. Order SHA256 cố định, vị trí CLI cân bằng, không phải randomizedtrial lớn. [Protocol](../PROTOCOL_OPENAI48_R3.md), [raw plan/source snapshot](artifacts/OPENAI48-R3-20261110-01/plan.json).

## 2. Kết quả tổng hợp

Thời gian primary là outerbwrapspawn→bridgeexit, **gồm pacing và startup/teardown**, không gồm supervisorgrading; median dùng **cả12attempts**, không loại failure.

| CLI | Success/12 | Failure | Snapshot pass/12 | Median giây | Mean giây | Min–max giây | Upstream | Guard USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| OpenCode v1 |11/12|1|12/12|228,15|224,85|189,96–301,41|80|0,4870073|
| OpenCode v2 |12/12|0|12/12|200,20|216,07|191,51–260,77|78|0,4241899|
| Pi |11/12|1|12/12|164,23|190,51|128,06–297,19|68|0,2636218|
| Codex CLI |12/12|0|12/12|139,63|153,52|111,98–190,16|52|0,9722795|

**Success theo từng task:** B-01/B-02/B-03 đều3/3 cho mọiCLI; B-04 v1=2/3,Pi=2/3,v2=3/3,Codex=3/3. Snapshot/public/hidden pass **48/48** không thay tiêu chí end-to-end success46/48(95,83%).

- Trong cohort này Codex có median thấp nhất và ít upstream nhất; pacing làm số bước ảnh hưởng mạnh tới thời gian. Không quy chênh lệch cho hiệu năng runtime thuần hoặc khẳng định significance với n=3/task.
- Pi có guard estimate thấp nhất; Codex nhanh hơn nhưng có tổnginput lớn hơn nên estimate cao nhất. Cache và tariffunknownTTL ảnh hưởng số tiền, không gọi guardestimate là hóa đơn.
- v2 có12/12end-to-end, median thấp hơn v1 trong cohort; khác native prompts/tool schemas/steps nên chưa chứng minh v2 cải tiến nhân quả hoặc mọi task.

Benchmark thực chạy **2026-11-10 17:02:01–19:39:50 UTC**, elapsed **2giờ37phút49giây**. Có278upstream, tất cảHTTP200/response.completed/usageđịnhgiáđược. Cộng11requestsmoke là289;288gap nối tiếp đều≥30s, min30,000319s. Không có inference retry trong48slot r3.

## 3. Hai failure — không phải snapshot sai hoặc upstream400

| Run/slot | CLI/task | Quan sát | Cách báo cáo |
|---|---|---|---|
| R-0343/D48-014 |v1/B-04|8upstream200/completed, snapshotpass, nativeerror/local400, CLIexit1|Giữfailure/valid, không nâng snapshot thànhsuccess|
| R-0365/D48-036 |Pi/B-04|8upstream200/completed, snapshotpass, nativeerror/local400, CLIexit0|Giữfailure/valid; exit0 không đủ nếu có nativeerror|

Dữ liệu **phù hợp với chạm cap8request**: request tiếp bị brokerlocal từ chối, không có upstream400. Exactlocalrejectreason không được logger ghi chi tiết nên không khẳng định vượtcap là nguyên nhân duy nhất được đo trực tiếp. Đây là kết quả dưới giới hạn protocol, không phải lỗi harness mới được phép nới cap để cứu điểm. Không retryhai lượt này, không đổ thành model viết code sai hoặc provideroutage. [Rawv1](artifacts/OPENAI48-R3-20261110-01/benchmark/D48-014/result.json), [rawPi](artifacts/OPENAI48-R3-20261110-01/benchmark/D48-036/result.json).

## 4. Token và chi phí

| CLI | Input tổng | Output tổng(gồmreasoning) | Cached reads | Cache writes | Khoảngtariff phầnusageđãbáo,USD |
|---|---:|---:|---:|---:|---:|
|v1|306163|13095|233193|62266|0,3313423–0,4870073|
|v2|234202|13148|173349|51223|0,2961324–0,4241899|
|Pi|136527|9947|105688|30635|0,1870343–0,2636218|
|Codex|638403|12624|478675|159572|0,5733495–0,9722795|

Benchmark48 **guardestimate$2,1470985**, khoảngtariff **$1,3878585–$2,1470985**. 254/278request cóunknownTTL được estimatorr2 tính mức12hupperbound, không phải xác nhận actualTTL. Ordinaryinput=input−cachedreads−writes; không doublecount. [Semantics](../OPENAI_CACHE_FIX_R2.md), [OpenAI pricing](https://developers.openai.com/api/docs/pricing).

4smoke r3: guard$0,0959616 (11requests). Tổngđợtr3 **$2,2430601**; cộngcarriedguard$0,33970766→**$2,58276776**, còn$13,41723224so với guard16USD. Carrygồm oldknown/reserve/estimates, không phải invoice. **0newunpriced nhưng6historicalunpriced vẫnunknown; measuredcharge=null**, không tuyên bố tổng dự án chỉ tốn$2,58. PilotShop riêng cònknown1,10640264USD/6unpriced, không nhập cohortOpenAI.

## 5. Bằng chứng và lịch sử

- [Audit cuối](../../research/artifacts/OPENAI48-R3-FINAL-20261111-01/validation.json): source snapshots/hashes, slotcoverage, cap/pacing/ledger,52cleanupwitness, priorraw/frozenpilot/registryR378C479,0extraAPI/keyread.
- [Toàn bộ48row](artifacts/OPENAI48-R3-SUMMARY-20261111-01/RUNS48.md), [CSVderived](artifacts/OPENAI48-R3-SUMMARY-20261111-01/runs48.csv), [summaryraw](artifacts/OPENAI48-R3-20261110-01/result.json), [benchmarkraw](artifacts/OPENAI48-R3-20261110-01/benchmark/result.json).
- [Lịch sử OpenAI](OPENAI_RESULTS.md): r1smoke dừng do cachecostgate; r2smoke3pass/Codex400 do normalizer; r3fix qua185tests/16nativeoffline và4smokethậtpass. Mọi retry/failure vàIDs cũ giữ nguyên, không dùng bootstrapfailure làm taskscore hoặc xóa khỏi lịch sử vận hành.
- [Shop benchmark](BENCHMARK_RESULTS.md) chỉ7unique48slots/8attempts/41notrun, provider khác; không gộp với48OpenAI. Google/ShopGemini smoke lỗi giữ riêng, không suy model/backend giống nhau từ alias.

## 6. Giới hạn và kết luận

Đây là **một cohort hoàn chỉnh nhưng nhỏ**:4fixture syntheticPython, n=3/task, cache/backend revision vàbackgroundload uncontrolled; native systemprompts/toolset khác. Thành công trong cohort không bảo đảm ổn định dài hạn hoặc thứ hạng tổng quát. APIClient/SDKprompt, permission matrix, backgrounddisconnect/restart, pluginport và compaction/resume runtime không được benchmark này chứng minh; [báo cáo chính](../../REPORT.md) ghi rõ source/runtime/unverified.

Trong điều kiện đã khóa, v2/Codex hoàn tất12/12end-to-end; v1/Pi11/12, snapshots đềuđúng. Chọn tool theo kiến trúc/tích hợp và giới hạn vận hành, không chỉ một con số tốc độ hoặc token. **Benchmark48 đã kết thúc, không cần gọi thêmAPI để tăng điểm.**
