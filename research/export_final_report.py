"""Export REPORT.md plus linked APPENDIX.html into one portable, public-evidence PDF.

Only document rendering: no native agent, model request, key read or benchmark rerun.
Uses installed markdown-it-py, Chrome, bwrap and Poppler; installs nothing.
"""
import base64
import hashlib
import html
import json
import mimetypes
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from markdown_it import MarkdownIt

from build_appendix import EVIDENCE_COMMIT, REPOSITORY, ROOT

ARTIFACT = ROOT / "research/artifacts/FINAL-SUBMISSION-20261111-01"
PUBLIC_LINKS = set()


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs)


def permalink(href):
    if href.startswith(("https://", "http://", "mailto:", "#")):
        return href
    parsed = urlsplit(href)
    path = (ROOT / unquote(parsed.path)).resolve()
    assert path.is_relative_to(ROOT) and path.exists(), href
    relative = path.relative_to(ROOT).as_posix()
    # No invented remote path: the evidence target must exist in the published pin.
    run(["git", "cat-file", "-e", EVIDENCE_COMMIT + ":" + relative])
    kind = "tree" if path.is_dir() else "blob"
    link = f"{REPOSITORY}/{kind}/{EVIDENCE_COMMIT}/{quote(relative, safe='/')}"
    if parsed.fragment:
        link += "#" + quote(unquote(parsed.fragment), safe="-_.~")
    PUBLIC_LINKS.add(link)
    return link


def report_html():
    markdown = (ROOT / "REPORT.md").read_text()
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    tokens = md.parse(markdown)
    slugs = {}
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            title = re.sub(r"[`*_]", "", tokens[i + 1].content.lower())
            slug = "".join(c for c in title if c.isalnum() or c in " -_").replace(" ", "-")
            n = slugs.get(slug, 0)
            slugs[slug] = n + 1
            token.attrSet("id", slug + (f"-{n}" if n else ""))
        for child in token.children or []:
            if child.type == "link_open":
                child.attrSet("href", permalink(child.attrGet("href")))
            elif child.type == "image":
                path = (ROOT / unquote(child.attrGet("src"))).resolve()
                assert path.is_relative_to(ROOT) and path.is_file()
                mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                child.attrSet("src", f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode())
    body = md.renderer.render(tokens, md.options, {})
    return """<!doctype html><html lang="vi"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<title>So sánh OpenCode, Pi và Codex CLI — Báo cáo chính</title>
<style>
@page { size: A4; margin: 14mm 12mm 16mm;
  @bottom-right { content: "Báo cáo · " counter(page); font: 8pt Arial; color: #657582; }
}
* { box-sizing: border-box; }
body { margin: 0; color: #1d2f3d; font: 10pt Arial, sans-serif; line-height: 1.42; }
h1 { font-size: 21pt; line-height: 1.18; color: #183b50; margin: 0 0 5mm; }
h2 { font-size: 15pt; color: #14627d; margin: 7mm 0 3mm; }
h3 { font-size: 12pt; color: #214b62; margin: 5mm 0 2mm; }
h4 { font-size: 10.5pt; margin: 4mm 0 2mm; }
h1,h2,h3,h4 { break-after: avoid; }
p { margin: 2.5mm 0; orphans: 3; widows: 3; }
ul,ol { padding-left: 6mm; margin: 2mm 0; }
li { margin: 1.2mm 0; }
a { color: #116682; text-decoration: underline; text-underline-offset: 1px; overflow-wrap: anywhere; }
code { font: .9em "DejaVu Sans Mono", monospace; background: #f1f4f6; border-radius: 2px; }
pre { padding: 3mm; background: #f1f4f6; border-left: 2px solid #b7cdd6; font-size: 8.3pt; line-height: 1.36;
      white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; }
pre code { font-size: inherit; background: none; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; margin: 3mm 0; font-size: 8.6pt; line-height: 1.36; }
th,td { border: 1px solid #d9e2e8; padding: 2mm; vertical-align: top; overflow-wrap: anywhere; }
th { background: #eaf1f5; color: #193f55; font-weight: bold; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
td code { overflow-wrap: anywhere; }
img { max-width: 100%; }
.export-note { background: #edf6f8; border-left: 3px solid #147d92; padding: 2.5mm 3mm; margin-bottom: 5mm; font-size: 8pt; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
</style><body><div class="export-note">Bản nộp gồm báo cáo chính và 3 trang phụ lục minh chứng ở cuối.
Nguồn/artifact nội bộ được chuyển thành hyperlink GitHub theo commit cố định <code>""" + EVIDENCE_COMMIT[:12] + """</code>.
Không cần đường dẫn trên máy xuất PDF để mở bằng chứng.</div>""" + body + "</body></html>"


def render(source, output, temporary):
    profile = temporary / (output.stem + "-profile")
    command = ["bwrap", "--die-with-parent", "--unshare-net", "--unshare-pid", "--new-session",
        "--ro-bind", "/", "/", "--proc", "/proc", "--dev", "/dev", "--bind", str(temporary), "/tmp",
        "--setenv", "HOME", "/tmp/home", "--setenv", "TMPDIR", "/tmp", "/usr/bin/google-chrome",
        "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-background-networking",
        "--disable-sync", "--disable-extensions", "--no-first-run", "--no-default-browser-check",
        "--user-data-dir=/tmp/" + profile.name, "--no-pdf-header-footer",
        "--print-to-pdf=/tmp/" + output.name, source.as_uri()]
    result = run(command, timeout=100)
    (temporary / (output.stem + "-render.log")).write_text(result.stdout + result.stderr)


def pages(path):
    return int(re.search(r"^Pages:\s+(\d+)$", run(["pdfinfo", str(path)]).stdout, re.M)[1])


def main():
    temp = Path(tempfile.mkdtemp(prefix="final-report-", dir="/tmp/opencode"))
    (temp / "home").mkdir()
    work = ROOT / ".local/final-report-export"
    work.mkdir(parents=True, exist_ok=True)
    source = work / "REPORT_PRINT.html"
    source.write_text(report_html())
    report, appendix, combined = [temp / name for name in ("REPORT.pdf", "APPENDIX.pdf", "OpenCode_Comparison_Report.pdf")]
    render(source, report, temp)
    render(ROOT / "APPENDIX.html", appendix, temp)
    assert pages(appendix) == 3
    run(["pdfunite", str(report), str(appendix), str(combined)])
    assert pages(combined) == pages(report) + 3
    uris = run(["pdfinfo", "-url", str(combined)]).stdout
    assert "file:" not in uris and "/mnt/data/" not in uris, "Nonportable PDF hyperlink"
    assert EVIDENCE_COMMIT in uris and UI_REVIEW_SUFFIX in uris
    pdf_text = run(["pdftotext", "-layout", str(combined), "-"]).stdout
    for text in ["1. Tóm tắt kết quả", "8. Kết luận và khuyến nghị", "9. Phụ lục và bằng chứng",
                 "Một session, nhiều giao diện", "Ba góc nhìn, cùng một cohort", "638.403"]:
        assert text in pdf_text, text
    (ROOT / "APPENDIX.pdf").write_bytes(appendix.read_bytes())
    final = ROOT / combined.name
    final.write_bytes(combined.read_bytes())
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    receipt = {
        "status": "pass_pending_visual_review", "scope": "document rendering and merge, no new experiments",
        "repository": REPOSITORY, "evidence_commit": EVIDENCE_COMMIT,
        "report_pages": pages(report), "appendix_pages": 3, "total_pages": pages(combined),
        "report_markdown_sha256": hashlib.sha256((ROOT / "REPORT.md").read_bytes()).hexdigest(),
        "appendix_html_sha256": hashlib.sha256((ROOT / "APPENDIX.html").read_bytes()).hexdigest(),
        "combined_pdf_sha256": hashlib.sha256(final.read_bytes()).hexdigest(),
        "appendix_pdf_sha256": hashlib.sha256(appendix.read_bytes()).hexdigest(),
        "converted_report_links": sorted(PUBLIC_LINKS),
        "pdf_url_annotation_rows": len(uris.splitlines()) - 1,
        "file_url_links": 0, "temporary_render_directory": str(temp),
        "limitations": "existing REPORT.md re-rendered, not editing an unavailable earlier 16-page PDF; total pages depend on layout",
    }
    (ARTIFACT / "validation.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("report_pages", "appendix_pages", "total_pages", "file_url_links")}, ensure_ascii=False))
    print("PDF:", final)
    print("Render directory:", temp)


UI_REVIEW_SUFFIX = "NATIVE-VISIBLE-UI-REVIEW-20261111-01/validation.json"

if __name__ == "__main__":
    main()
