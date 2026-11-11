"""Build a self-contained, three-page evidence appendix from existing artifacts.

No native agent, provider request, credential access, or screenshot fabrication.
Output HTML embeds screenshots (explicitly labeled detail crops when used) and SVG charts.
Raw inputs stay read-only.
"""
import base64
import csv
import hashlib
import html
import io
import json
import statistics
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/binhdinhvan/agent-cli-report"
EVIDENCE_COMMIT = "f2becc501cfc1b980b888402458bac81b8193370"
UI = "demos/artifacts/NATIVE-VISIBLE-UI-20261111-07/"
UI_REVIEW = "research/artifacts/NATIVE-VISIBLE-UI-REVIEW-20261111-01/validation.json"
CLIENT = "demos/artifacts/NATIVE-CLIENT-20261111-01/client-result.json"
SDK = "demos/artifacts/NATIVE-SDK-20261111-01/sdk-result.json"
PERMISSION = "demos/artifacts/NATIVE-DEMO-PERMISSION-20261111-02/summary.json"
NEGATIVE = "demos/artifacts/NATIVE-CLIENT-V1PLUGIN-20261111-02/client-result.json"
PORTED = "demos/artifacts/NATIVE-PLUGIN-PORT-20261111-03/client-result.json"
CLEANUP = "demos/artifacts/NATIVE-PLUGIN-PORT-20261111-03/client-server.log"
CSV = "benchmark/suite48/artifacts/OPENAI48-R3-SUMMARY-20261111-01/runs48.csv"
RAW = "benchmark/suite48/artifacts/OPENAI48-R3-20261110-01/benchmark/"
TOOLS = ["opencode-v1", "opencode-v2", "pi", "codex"]
LABELS = ["OpenCode v1", "OpenCode v2", "Pi", "Codex CLI"]
COLORS = ["#406482", "#147d92", "#b17b22", "#6551a2"]
HASHES = {}
DERIVED_IMAGES = []


def read(name):
    data = (ROOT / name).read_bytes()
    HASHES[name] = hashlib.sha256(data).hexdigest()
    return data


def load(name):
    return json.loads(read(name))


def esc(value):
    return html.escape(str(value))


def image(name, box=None):
    data = read(name)
    if box:
        out = io.BytesIO()
        Image.open(io.BytesIO(data)).crop(box).save(out, format="PNG")
        data = out.getvalue()
        DERIVED_IMAGES.append({"source": name, "crop_box": list(box), "png_sha256": hashlib.sha256(data).hexdigest(),
                               "operation": "exact pixel crop; no added frame, text, or generated UI"})
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def source(name):
    return '<p class="source">Nguồn: ' + public_link(name) + "</p>"


def public_link(name, label=None):
    path = ROOT / name
    assert path.exists() and path.resolve().is_relative_to(ROOT), name
    kind = "tree" if path.is_dir() else "blob"
    url = f"{REPOSITORY}/{kind}/{EVIDENCE_COMMIT}/{quote(name, safe='/')}"
    return f'<a href="{esc(url)}"><code>{esc(label or name)}</code></a>'


def chart(title, values, maximum, ticks, labels, unit):
    left, width = 142, 390
    svg = [f'<svg viewBox="0 0 680 160" role="img" aria-label="{esc(title)}">']
    for tick in ticks:
        x = left + width * tick / maximum
        svg.append(f'<line x1="{x}" y1="8" x2="{x}" y2="132" stroke="#e3e8ec"/>')
        svg.append(f'<text x="{x}" y="151" text-anchor="middle" class="axis">{tick:g}</text>')
    for i, (label, value, annotation, color) in enumerate(zip(LABELS, values, labels, COLORS)):
        y = 12 + i * 30
        svg.append(f'<text x="130" y="{y + 15}" text-anchor="end" class="label">{esc(label)}</text>')
        svg.append(f'<rect x="{left}" y="{y}" width="{width * value / maximum:.3f}" height="21" rx="3" fill="{color}"/>')
        svg.append(f'<text x="{left + width * value / maximum + 9:.3f}" y="{y + 15}" class="value">{esc(annotation)}</text>')
    svg.append(f'<text x="666" y="151" text-anchor="end" class="axis">{esc(unit)}</text></svg>')
    return '<div class="chart"><h3>' + esc(title) + "</h3>" + "".join(svg) + "</div>"


def main():
    ui, client, sdk = load(UI + "ui-visible-result.json"), load(CLIENT), load(SDK)
    review = load(UI_REVIEW)
    assert review["status"] == "pass" and review["accepted_artifact"] + "/" == UI
    assert all(ui["checks"].values())
    assert ui["service_before"]["pid"] == ui["service_after_all"]["pid"]
    assert client["status"] == "pass" and all(client["checks"].values())
    assert all(sdk["checks"].values())
    terminal = next(e for e in client["events"] if e["type"] == "session.execution.succeeded")
    assert terminal["data"]["sessionID"] == client["sessionID"]
    event = {k: terminal[k] for k in ("type", "created", "data")}
    negative, ported = load(NEGATIVE), load(PORTED)
    error = "Plugin must export a default definition with an id and an effect or setup function."
    assert any(p["state"].get("error") == error for p in negative["plugin_list_after_wait"]["data"])
    assert ported["checks"]["ported_plugin_active"] and ported["checks"]["ported_plugin_tool_invoked"]
    cleanup = read(CLEANUP).decode().strip()
    assert "REPORT_PLUGIN_V2_CLEANUP" in cleanup
    pm = load(PERMISSION)
    grouped = defaultdict(dict)
    for case in pm["cases"]:
        grouped[case["case"]["permission"]][case["case"]["tool"]] = case["shell_witness_created"]
    pmrows = []
    for case, expected in [("allow", True), ("deny", False), ("ask", False)]:
        assert all(grouped[case][t] is expected for t in TOOLS[:2])
        observed = "Có witness" if expected else "Không witness"
        pmrows.append(f'<tr><td><code>{case}</code></td><td>{observed}</td><td>{observed}</td></tr>')

    rows = list(csv.DictReader(read(CSV).decode().splitlines()))
    assert len(rows) == 48 and len({r["slot"] for r in rows}) == 48
    groups = {tool: [r for r in rows if r["tool"] == tool] for tool in TOOLS}
    counts, medians, tokens = [], [], []
    for tool in TOOLS:
        group = groups[tool]
        assert len(group) == 12 and all(r["validity"] == "valid" for r in group)
        counts.append(sum(r["status"] == "success" for r in group))
        medians.append(statistics.median(float(r["duration_seconds"]) for r in group))
        total = 0
        for row in group:
            run = load(RAW + row["slot"] + "/result.json")
            assert run["run_id"] == row["run_id"] and run["status"] == row["status"]
            total += sum(q["cost"]["usage"]["input_tokens"] for q in run["requests"])
        tokens.append(total)
    assert counts == [11, 12, 11, 12]
    assert tokens == [306163, 234202, 136527, 638403]
    charts = chart("C1 · Hoàn tất end-to-end", [c / 12 * 100 for c in counts], 100,
                   [0, 25, 50, 75, 100], [f"{c}/12 · {c / 12 * 100:.2f}%".replace('.', ',') for c in counts], "%")
    charts += chart("C2 · Median thời gian / lượt", medians, 250, [0, 50, 100, 150, 200, 250],
                    [f"{v:.2f} s".replace('.', ',') for v in medians], "giây")
    charts += chart("C3 · Tổng input token / 12 lượt", [t / 1000 for t in tokens], 700,
                    [0, 100, 200, 300, 400, 500, 600, 700], [f"{t:,}".replace(',', '.') for t in tokens], "nghìn token")

    sid = ui["session"]["data"]["id"]
    pid = ui["service_before"]["pid"]
    checks = ui["checks"]
    assert all(checks[k] for k in (
        "desktop_shared_session", "standalone_browser_shared_session",
        "tui_shared_session", "all_clients_keep_service_pid",
    ))
    assert ui["tui"]["command"][-2:] == ["--session", sid]
    assert sid in ui["web_document"]["result"]["value"]["url"]
    assert ui["desktop_document"]["result"]["value"]["url"] == "oc://renderer/index.html"
    content = f"""<!doctype html>
<html lang="vi"><meta charset="utf-8"><title>Phụ lục minh chứng — OpenCode, Pi, Codex CLI</title>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<style>
@page {{ size: A4; margin: 12mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 10pt Arial, sans-serif; color: #182b3a; background: #edf1f4; }}
.page {{ background: white; width: 186mm; height: 272mm; margin: 8mm auto; padding: 0; position: relative; break-after: page; overflow: hidden; }}
.page:last-child {{ break-after: auto; }}
.kicker {{ color: #147d92; font-size: 8pt; letter-spacing: 1px; text-transform: uppercase; padding-top: 2mm; }}
h1 {{ font-size: 19pt; line-height: 1.15; margin: 2mm 0 3mm; }}
h2 {{ font-size: 12pt; margin: 4mm 0 2mm; }}
h3 {{ font-size: 10pt; margin: 1mm 0; }}
p {{ line-height: 1.35; margin: 2mm 0; }}
.lead {{ color: #526676; font-size: 9pt; }}
.note {{ background: #eef6f8; border-left: 3px solid #147d92; padding: 2.5mm 3mm; font-size: 8.5pt; line-height: 1.35; }}
.source {{ font-size: 7pt; color: #586b78; line-height: 1.3; overflow-wrap: anywhere; margin: 1mm 0 2mm; }}
a {{ color: #14627d; text-decoration: underline; text-underline-offset: 1px; }}
code, pre {{ font-family: "DejaVu Sans Mono", monospace; }}
pre {{ font-size: 8pt; background: #f3f5f7; padding: 2.5mm; white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.4; margin: 2mm 0; }}
figure {{ margin: 2mm 0; text-align: center; }}
figure img {{ display: block; width: 146mm; height: auto; margin: 0 auto; border: 1px solid #d6dfe5; }}
figure.detail img {{ width: 178mm; }}
figcaption {{ text-align: left; font-size: 8pt; line-height: 1.3; margin: 1mm 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin: 2mm 0; }}
td, th {{ padding: 2mm; border-bottom: 1px solid #d9e2e8; text-align: left; }}
th {{ background: #f1f5f7; }}
.verification {{ background: #eef6f8; border: 1px solid #b9d6dd; padding: 2mm 3mm; margin: 2mm 0; font-size: 8pt; }}
.verification h3 {{ color: #147d92; font-size: 8pt; letter-spacing: .4px; }}
.verification p {{ margin: 1mm 0; }}
.checks {{ display: flex; justify-content: space-between; padding: 1mm 0; font-weight: bold; }}
.footer {{ position: absolute; bottom: 0; width: 100%; border-top: 1px solid #d9e2e8; padding-top: 2mm; font-size: 7pt; color: #637584; display: flex; justify-content: space-between; }}
.chart {{ padding: 2mm 0; border-bottom: 1px solid #e3e8ec; }}
svg {{ width: 100%; height: auto; display: block; }}
svg text {{ font-family: Arial, sans-serif; fill: #263f51; }}
.axis {{ font-size: 10px; fill: #71808b; }}
.label {{ font-size: 13px; }} .value {{ font-size: 12px; font-weight: bold; }}
@media print {{ body {{ background: white; }} .page {{ margin: 0; }} * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
</style>
<section class="page">
<div class="kicker">Phụ lục A · Kiến trúc và shared service</div>
<h1>Một session, nhiều giao diện</h1>
<p class="lead">Lượt chụp mới: VISIBLE-UI07 · Desktop 2.2.5, Chrome độc lập và TUI trên Xvfb riêng. Không gọi model.</p>
<figure class="detail"><img alt="Cắt vùng trên từ ảnh Desktop thật, gồm khung cửa sổ và session title" src="{image(UI + 'desktop-window.png', (40, 24, 1340, 235))}">
<figcaption><b>A1. Desktop đóng gói</b> · cắt vùng trên để thấy rõ title bar thật và session title. Renderer <code>oc://renderer/index.html</code>.</figcaption></figure>
<figure class="detail"><img alt="Cắt vùng trên từ ảnh Chrome thật, có thanh địa chỉ service/session" src="{image(UI + 'web-browser.png', (40, 24, 1558, 300))}">
<figcaption><b>A2. Web trên Chrome độc lập</b> · cắt vùng trên có toolbar/thanh địa chỉ thật, URL chứa đúng session ID. Không vẽ thêm browser chrome.</figcaption></figure>
<figure><img alt="Ảnh màn hình thật TUI native trong xterm" src="{image(UI + 'tui-terminal.png')}">
<figcaption><b>A3. TUI native trong xterm</b> · cùng title; command/raw PTY đối chiếu đúng session ID. Ảnh gốc không có chữ hoặc khung dựng thêm.</figcaption></figure>
<div class="verification">
<h3>SHARED SERVICE VERIFICATION · ĐỐI CHIẾU RAW</h3>
<p>Session ID: <code>{esc(sid)}</code></p>
<div class="checks"><span>Desktop: cùng session · PASS</span><span>Web: cùng session · PASS</span><span>TUI: cùng session · PASS</span></div>
<p>Service PID trước: <b>{pid}</b> &nbsp; | &nbsp; sau cả ba client: <b>{ui['service_after_all']['pid']}</b> &nbsp; | &nbsp; <b>Shared-service checks: PASS</b></p>
<p>Endpoint: <code>{esc(ui['service_before']['urls'][0])}</code>. Raw controller: <code>checks_passed_pending_review</code>; review ảnh/raw riêng xác nhận PASS.</p>
</div>
<p class="source"><b>Review ảnh/raw riêng — <code>status=pass</code>:</b><br>{public_link(UI_REVIEW)}<br>Receipt đối chiếu ảnh, session/PID, hashes và cleanup; raw controller giữ nguyên trạng thái pending review.</p>
<p class="source">Ảnh gốc 1600 × 1050 giữ riêng; A1/A2 chỉ cắt pixel để phóng chi tiết, không sửa nội dung. Cảnh báo Chrome <code>--no-sandbox</code> giữ nguyên; có bwrap bên ngoài, không phải security verdict. PID chỉ có ý nghĩa trong namespace này.</p>
<p class="source">Nguồn cùng lượt: {public_link(UI + 'ui-visible-result.json', 'raw ID/PID/checks')} · {public_link(UI + 'desktop-window.png', 'ảnh Desktop gốc')} · {public_link(UI + 'web-browser.png', 'ảnh Chrome gốc')} · {public_link(UI + 'tui-terminal.png', 'ảnh TUI gốc')} · {public_link(UI + 'tui-pty.ansi', 'raw PTY')}.<br>Permalink bằng chứng cố định theo commit <code>{EVIDENCE_COMMIT[:12]}</code>.</p>
<div class="footer"><span>Phạm vi: Linux headless, không service/session người dùng</span><span>A · 1/3</span></div>
</section>
<section class="page">
<div class="kicker">Phụ lục B · Minh chứng chức năng</div>
<h1>API, permission và plugin port</h1>
<p class="lead">Trích trường/log từ artifact thật, trình bày lại để đọc nhanh — không phải screenshot terminal hoặc lần chạy mới. Native runtime với scripted local SSE, không đo model quality.</p>
<h2>B1. Client / Embedded SDK</h2>
<p>Client tạo session, gửi <code>REPORT_CLIENT_USER_SEED</code>, nhận assistant marker và terminal event:</p>
<pre>{esc(json.dumps(event,ensure_ascii=False,indent=2))}</pre>
<p><code>subscribed_before_prompt=true</code>; <code>transcript_after_restart=true</code>.<br>SDK riêng: <code>embedded_prompt_assistant_marker=true</code> và <code>explicit_host_close_returned=true</code>.</p>
{source(CLIENT)}{source(SDK)}
<h2>B2. Permission v1 / v2</h2>
<table><thead><tr><th>Rule / case</th><th>v1: thực tế</th><th>v2: thực tế</th></tr></thead><tbody>{''.join(pmrows)}</tbody></table>
<p class="lead">Witness là file do shell fixture ghi. <code>ask</code> ở bảng là CLI unattended: không tự approve, không phải người dùng bấm từ chối trong UI. API once/reject/always có case riêng trong báo cáo.</p>
{source(PERMISSION)}
<h2>B3. Plugin v1 → v2</h2>
<p>Nguyên bytes v1 trên v2: loader báo lỗi. Sau port <code>id/setup/tool.transform</code>: active, gọi <code>report_marker</code> thành công.</p>
<p><b>Before port — nguyên plugin v1 nạp trên v2:</b></p>
<pre>{esc(error)}</pre>
<p><b>After port — lượt chạy bản v2 riêng:</b></p>
<pre>ported_plugin_active: true
ported_plugin_tool_invoked: true
{esc(cleanup)}</pre>
<p class="source">Nguồn: {public_link(NEGATIVE)}<br>{public_link(PORTED)}<br>{public_link(CLEANUP)}</p>
<div class="footer"><span>Trích log có chọn lọc; đầy đủ failure/retry ở bộ artifact đi kèm</span><span>B · 2/3</span></div>
</section>
<section class="page">
<div class="kicker">Phụ lục C · Benchmark OpenAI48</div>
<h1>Ba góc nhìn, cùng một cohort</h1>
<p class="lead">4 task × 4 CLI × 3 lượt · cùng model/provider trong cohort · v1.19.5 / v2.2.5 / Pi 1.5.0 / Codex 0.167.0.</p>
{charts}
<div class="note"><b>Cách đọc:</b> completion là agent hoàn tất theo protocol, không chỉ snapshot đúng (48/48 snapshot pass). Median dùng cả 12 lượt/CLI, gồm failure, startup/teardown và <b>pacing ≥ 30 giây</b>. Token là usage input tích lũy, có cache; không phải context duy nhất hoặc hóa đơn. Không suy winner tổng quát từ bốn fixture Python nhỏ.</div>
{source(CSV)}
<p class="source">Input token được cộng từ {public_link(RAW.rstrip('/'), '48 raw result.json')} → <code>requests[].cost.usage.input_tokens</code>. Vẽ biểu đồ từ dữ liệu gốc, không dùng số đã làm tròn để tính median.</p>
<div class="footer"><span>46/48 end-to-end success · 278 upstream · không benchmark mới</span><span>C · 3/3</span></div>
</section></html>"""
    out = ROOT / "APPENDIX.html"
    out.write_text(content, encoding="utf-8")
    manifest = {
        "scope": "appendix uses new authorized VISIBLE-UI07 screenshots, selected earlier feature logs and unchanged benchmark charts; generator runs no experiments",
        "input_sha256": HASHES,
        "repository": REPOSITORY,
        "evidence_commit": EVIDENCE_COMMIT,
        "derived_image_crops": DERIVED_IMAGES,
        "html_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "success": counts, "median_seconds": medians, "total_input_tokens": tokens,
        "limitations": "not a new capture, full raw audit, model-quality test, or published evidence bundle",
    }
    target = ROOT / "research/artifacts/APPENDIX-20261111-05"
    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"html": str(out.relative_to(ROOT)), "input_files": len(HASHES), "metrics": {k: manifest[k] for k in ("success", "median_seconds", "total_input_tokens")}},ensure_ascii=False))


if __name__ == "__main__":
    main()
