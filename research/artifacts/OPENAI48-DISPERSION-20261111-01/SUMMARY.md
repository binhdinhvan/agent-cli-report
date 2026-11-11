# Độ phân tán benchmark48 — derived, không inference mới

12attempts/CLI, gồm2failure; token là tổng reported usage của mọi upstream request trong attempt. Input lifetime gồm cache; output gồm reasoning, không cộng lại. Duration gồm pacing/startup. Quartile inclusive (n nhỏ, không significanceclaim).

| CLI | Duration median [Q1–Q3],s | Input median [Q1–Q3] | Output median [Q1–Q3] |
| --- | ---: | ---: | ---: |
| opencode-v1 | 228.15 [201.94–235.74] | 24035.50 [23271.00–26963.00] | 804.00 [744.75–1281.25] |
| opencode-v2 | 200.20 [196.47–236.68] | 18557.00 [16444.50–23475.50] | 752.00 [698.50–1258.25] |
| pi | 164.23 [162.97–192.07] | 9011.00 [8605.75–12601.75] | 679.50 [544.50–901.00] |
| codex | 139.63 [135.37–178.73] | 48750.50 [48067.50–61631.00] | 824.50 [628.00–1224.75] |

[JSON, all run IDs và raw hashes](summary.json); [báo cáo](../../../REPORT.md). Không đổi sealed benchmark hoặc loại failure.
