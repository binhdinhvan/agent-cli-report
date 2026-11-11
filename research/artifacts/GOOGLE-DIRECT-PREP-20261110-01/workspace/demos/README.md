# Demo và kiểm chứng

- [`GOOGLE_GEMINI.md`](GOOGLE_GEMINI.md): Google-direct ChatCompletions smoke adapter/profile/disabledplan, offline tests only; chưa API/key-content read hoặc native4CLI acceptance.

- [`GEMINI_SMOKE5_RESULTS.md`](GEMINI_SMOKE5_RESULTS.md): provider-onlyGemini smoke dừng1/5 vớiHTTP500/internal_error,4not_run,usage/costnull; khôngnative4CLI/benchmark acceptance.

- [`OFFLINE_DEMO_PLAN.md`](OFFLINE_DEMO_PLAN.md): acceptance matrix background/restart/plugin/permission/context/SDK; fixture worker và tests cục bộ không API. Đây là chuẩn bị, không phải native demo pass.

- [`../research/ENVIRONMENT_R2_RESULTS.md`](../research/ENVIRONMENT_R2_RESULTS.md): search-r2 chuẩn hóa rg, native search/config/isolation offline đủ bốn CLI; không inference mới, tách nhóm legacy.

- [`PREPARATION.md`](PREPARATION.md): release pins, binary SHA-256, metadata preflight; giữ nguyên.
- [`OFFLINE_API.md`](OFFLINE_API.md): HTTP auth/events/session metadata v1/v2 offline; giữ nguyên, không dùng model.
- [`PROVIDER_PROBE.md`](PROVIDER_PROBE.md): model `gpt-6.1-sol`, giá user-reported đã cập nhật; chưa chạy thêm generation.
- [`MODEL_SMOKE.md`](MODEL_SMOKE.md): protocol đã đóng băng; [`MODEL_SMOKE_SOL_RESULTS.md`](MODEL_SMOKE_SOL_RESULTS.md): ba CLI đạt chức năng nhưng lệch pacing xuyên CLI, chưa pilot.
- [`CODEX_TRACE.md`](CODEX_TRACE.md): implementation source và header/final parser guards; runtime traces cũ đã rút.
- [`../benchmark/MODEL_COMPARE.md`](../benchmark/MODEL_COMPARE.md): diagnostic sol/Pi duy nhất đang giữ.

Các demo shared-service/Client/SDK runtime, permission matrix, background/subagent và plugin port chưa được nghiệm thu. Xem `SMOKE_TEST.md`, `../research/isolation.md` và `PLAN.md` trước khi chạy. Không bật plugin, thay binary/service hoặc dùng session/config thật.

Kết quả model cũ đã xóa theo yêu cầu. Key/binary/fixture/source evidence giữ nguyên; paid-entrypoints vẫn từ chối nếu giá thiếu/sai model. Bảng giá đã đủ, nhưng cập nhật giá không tự cấp quyền chạy nhóm mới. Estimate offline lượt sol cũ: `../benchmark/SOL_COST.md`.
