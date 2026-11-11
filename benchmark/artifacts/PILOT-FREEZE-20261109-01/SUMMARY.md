# Tổng kết pilot đã khóa

Không phải benchmark chính thức hoặc xếp hạng tool.

- 14 inference attempts / 76 upstream requests; 1 launch-error riêng, không inference.
- Reviewed: {'infra_error': 3, 'success': 8, 'timeout': 3}; coverage 8 cặp có success, không phải 8/8 first-attempt.
- Known estimate **1.10640264 USD**; 6 request unpriced; total/charge **unknown**.

## Mọi inference attempt (thứ tự CSV legacy rồi search-r2)

| Run | Task / CLI | Environment / timing | Raw → reviewed | Requests | ms gồm pacing | Known USD / unpriced |
| --- | --- | --- | --- | ---: | ---: | --- |
| R-0009 | P-01 / pi | legacy / legacy-300 | failure/valid → infra_error/pending_review | 2 | 78497 | 0.0280872 / 1 |
| R-0017 | P-01 / pi | legacy / legacy-300 | success/valid → success/valid | 7 | 233296 | 0.07692480 / 0 |
| R-0018 | P-01 / codex | legacy / legacy-300 | success/valid → success/valid | 5 | 215013 | 0.27390552 / 0 |
| R-0019 | P-01 / opencode-v2 | legacy / legacy-300 | timeout/valid → timeout/valid | 5 | 300008 | 0.0249816 / 1 |
| R-0025 | P-01 / opencode-v2 | search-r2 / legacy-300 | infra_error/pending_review → infra_error/pending_review | 1 | 137378 | 0 / 1 |
| R-0026 | P-01 / opencode-v2 | search-r2 / legacy-300 | infra_error/pending_review → infra_error/pending_review | 1 | 129965 | 0 / 1 |
| R-0028 | P-01 / opencode-v2 | search-r2 / legacy-300 | success/valid → success/valid | 7 | 217097 | 0.06716400 / 0 |
| R-0029 | P-01 / opencode-v1 | search-r2 / legacy-300 | success/valid → success/valid | 7 | 224527 | 0.08659104 / 0 |
| R-0030 | P-02 / opencode-v2 | search-r2 / legacy-300 | timeout/valid → timeout/valid | 7 | 300039 | 0.06105024 / 1 |
| R-0034 | P-02 / opencode-v2 | search-r2 / legacy-300 | timeout/valid → timeout/valid | 7 | 300041 | 0.07098192 / 1 |
| R-0035 | P-02 / opencode-v2 | search-r2 / paced-900 | success/valid → success/valid | 7 | 234718 | 0.07580592 / 0 |
| R-0036 | P-02 / opencode-v1 | search-r2 / paced-900 | success/valid → success/valid | 7 | 223735 | 0.10021872 / 0 |
| R-0037 | P-02 / codex | search-r2 / paced-900 | success/valid → success/valid | 6 | 286901 | 0.10290408 / 0 |
| R-0038 | P-02 / pi | search-r2 / paced-900 | success/valid → success/valid | 7 | 278457 | 0.13778760 / 0 |

## P-02: search-r2 / paced-900

Thứ tự thực tế v2 → v1 → Codex → Pi; n=1/CLI, không randomized. Mọi lượt success/valid, scope/public/hidden pass; native settings không tương đương.

| Run / CLI | Requests | ms gồm pacing | Estimate USD |
| --- | ---: | ---: | ---: |
| R-0035 / opencode-v2 | 7 | 234718 | 0.07580592 |
| R-0036 / opencode-v1 | 7 | 223735 | 0.10021872 |
| R-0037 / codex | 6 | 286901 | 0.10290408 |
| R-0038 / pi | 7 | 278457 | 0.13778760 |

Tổng cohort 0.41671632 USD, không phải tổng pilot.

Nguồn, lineage/review override, token/cache/reasoning (null khi thiếu): `summary.json`; pins/config/fixture/source hashes: `baseline.json`.

- Coverage không phải 8/8 first-attempt success; không gộp revision để xếp hạng
- Giữ toàn bộ retry/failure; snapshot pass không nâng CLI timeout thành success
- Usage thiếu là null, không phải 0; giá user-reported, charge chưa đối soát
- n=1/CLI ở P-02; thứ tự không randomized; native prompts/tools/reasoning khác nhau
- Backend revision và cache không kiểm soát; không suy causal từ cap900 hoặc duration
