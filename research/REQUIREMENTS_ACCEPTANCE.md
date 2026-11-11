# Đối chiếu nghiệm thu đề bài

Mốc hoàn thiện2026-11-11, pins ở [versions.md](versions.md). **8/8 hạng mục đề bài có đầu ra và bằng chứng tương ứng trong phạm vi dưới đây.** Đây không phải “100% tính năng sản phẩm”, không phải mọi benchmark slot đều success, không xóa hạn chế nghiên cứu. [REPORT](../REPORT.md), [vòng1](../demos/NATIVE_RUNTIME_RESULTS.md), [vòng2](../demos/NATIVE_COMPLETION_R2_RESULTS.md), [audit native vòng2](artifacts/NATIVE-COMPLETION-R2-REVIEW-20261111-02/validation.json), [audit tài liệu cuối](artifacts/NATIVE-COMPLETION-DOCUMENTS-20261111-02/validation.json).

| # | Yêu cầu | Nghiệm thu | Bằng chứng/phạm vi |
| --- | --- | --- | --- |
| 1 | So sánh3tool theo6trục, dẫn source cụ thể | Đạt | REPORT3.1–3.6; [147 evidence IDs](evidence.csv) gồm commit/file/line/symbol/permalink/status. Không gọi source-only là runtime. |
| 2 | OpenCode1.x cuối/2.x mới nhất tại ngày chốt, cài song song | Đạt | [Versions/sourcepins](versions.md), [binary preparation](../demos/PREPARATION.md), payload/version/checksum riêng; không thay OpenCode người dùng. Không cập nhật pin theo release mới sau ngày chốt. |
| 3 | TUI/Desktop/Web dùng chung backgroundservice | Đạt trong isolated headless test | [Native UI05](../demos/artifacts/NATIVE-SHARED-UI-20261111-05/ui-result.json), Desktop/web screenshots1280×800 và TUIrawPTY; cùng session/title, defaultdiscovery, servicePID không đổi. Web thực render trong Chromiumengine của package, không standalonebrowser. |
| 4 | Script tạo session/prompt/events qua API/SDK mới | Đạt | TypeScriptClientsourcepin + publishedembeddedSDK2.2.5; vòng1 prompt/events/transcript/close và vòng2 HTTP400/waittimeout/interrupt. Inference scripted local, không modelquality; SDKexactbuild→source chưa attest. |
| 5 | Permissionobjectv1 vs orderedrulesv2 | Đạt |10CLIcase, v1interactiveAPI6turn, v2APIonce/reject/always/savedscope;5legacypermission-on-v2cases và unmatchedfallback. Sideeffects riêng; không claim UIkeyboardapproval hoặc savedapprovaldurablemọihost. |
| 6 | Subagent và shell chạy nền | Đạt theo contract mỗi phiên bản | V1subagent với documentedexperimentalflag; v2shell/subagent nativeparentcontinue/completion; cancel/disconnect Location API; BG07managedshellcancel/BG08childresume/BG09budgetexhaustion. V1legacy shell khôngbackgroundflag ởschemađãtruy; không thêm `&` giả nativeequivalence. Không exactly-once. |
| 7 | Port pluginv1→v2 | Đạt markerplugin | V1markerpositive, nguyênbytestrênv2expectedloaderfailure, v2`id/setup/tool.transform` markerquaCodeMode+cleanup. Before/after[sourcefixtures](../demos/fixtures/plugin_v1.js)/[portedfixture](../demos/fixtures/plugin_v2.js); không fullplugin ecosystemcompatibility. |
| 8 | Cùng bộtask đo success/token/time | Đạt | [Benchmark48thật](../benchmark/suite48/OPENAI_BENCHMARK_FINAL.md):4task×4CLI×3,48valid,46success/2failuregiữnguyên,raw/usage/time/guard/audit. Khôngretryđểđẹpđiểm; thiếuusagehistoryđểunknown. |

## Checklist mở rộng đã đóng

BG01–04/06/07/08/09 có acceptance trong kết quả hai vòng. BG05 kiểm Location-shellcancel/sibling, không đánh dấu full descendant OSprocess security. CT01 kiểm transcriptresume/compactionplumbing, khôngsemanticretention. SDK01 kiểm đúng Clientvsembedded và error/timeout/interrupt; không cam kết mọi failure mode. Các giới hạn này là ranh giới kết luận, không thay đổi tiêu chí đề bài.

## Những điều không được suy từ “hoàn tất”

- Không suy model nhớ semantic qua compaction vì summary là script.
- Không suy exactly-once sideeffects hoặc native OS confinement từ namespace của nghiên cứu.
- Không suy mọi desktop/display/browser/OS hoạt động; đo Linuxheadless đúng pin.
- Không có hóa đơn/providercharge đối soát; guardestimate không phải measuredcharge.
- Không có cryptographic attestation xác nhận SDKpackagebuild đúng sourcecommit; packageversion/runtimeđượckiểm, fullinstalledtreehashđượcgiữ, không giảlockfile.
- Các traces/retry/lỗi cũ và rawcontrollerbudgeterror không bị ghi đè. Không gọi API thật mới trong đợt hoàn thiện demo.
