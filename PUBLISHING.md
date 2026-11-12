# Repository public và phạm vi công bố

Repository public theo yêu cầu người dùng: **[binhdinhvan/agent-cli-report](https://github.com/binhdinhvan/agent-cli-report)**, nhánh `main`. Đây là repository mới dành cho báo cáo, demo và bằng chứng nghiên cứu; không phải repository source chính thức của các công cụ được so sánh.

## Phạm vi

- Đưa báo cáo, PDF/HTML phụ lục, source nghiên cứu/demo, fixtures, CSV/raw/audit và lịch sử vào Git.
- Loại `.local/` (credentials, binary, dependency payload), `.env`, key/private certificate, cache Python và runtime workspaces theo `.gitignore`.
- Không đưa bốn source repo công cụ ở thư mục cha vào repository này. Cách tái tạo binary/dependency nằm trong tài liệu; đẩy project không tự làm mọi demo chạy được trên máy sạch.
- Rà soát token/private-key patterns và literal credential fields trước khi staging; không in secret value trong kết quả rà soát. Đây là kiểm tra phòng ngừa, không phải chứng nhận tuyệt đối không có dữ liệu nhạy cảm.

## Raw log lịch sử vượt giới hạn GitHub

File `demos/artifacts/SEARCH-ENV-OFFLINE-20261106-01/C-0077/mock-requests.json` khoảng 261 MB vượt giới hạn 100 MiB/file. Bản gốc vẫn giữ trên máy, không sửa raw hoặc hash receipts. Git dùng sidecar **gzip lossless** cùng đường dẫn với đuôi `.json.gz`; không loại failure khỏi lịch sử hoặc thay nội dung để giảm kích thước.

Sau clone, nếu cần mở original JSON hoặc kiểm hash receipt gốc, khôi phục bằng lệnh dưới; từ chối ghi đè file đã tồn tại:

```sh
python3 -B - <<'PY'
import gzip
import shutil
from pathlib import Path

p = Path('demos/artifacts/SEARCH-ENV-OFFLINE-20261106-01/C-0077/mock-requests.json')
with gzip.open(str(p) + '.gz', 'rb') as source, p.open('xb') as target:
    shutil.copyfileobj(source, target)
PY
```

Đường dẫn JSON này thuộc historical offline search diagnostics, không phải 48 lượt benchmark cuối. Các file được REPORT tham chiếu trực tiếp vẫn phải hiện diện ở đúng đường dẫn trong Git.

## GitHub CLI và tài khoản

GitHub CLI được tải/kiểm SHA-256/extract riêng, không install hệ thống. Lệnh đăng nhập nếu cần trên máy nghiên cứu:

```sh
.local/github-cli/payload/usr/bin/gh auth login --hostname github.com --git-protocol https --web
```

Người dùng đăng nhập trên trang GitHub; **không gửi token/password vào chat hoặc lưu vào project**. Tài khoản công bố là `binhdinhvan`; author dùng GitHub noreply identity, không đưa email cá nhân vào commit. Cấu hình tác giả/credential helper cho thao tác agent chỉ đặt local trong repo, không đổi Git config global. Không force push hoặc ghi đè repository có sẵn.

Trước commit đầu đã kiểm file staged, loại `.local/`/credentials/binary, giới hạn 100 MiB, không có symlink staged và không phát hiện các mẫu key/token đã quét. Tổng dữ liệu staged ban đầu khoảng 91 MB; đây không phải chứng nhận bảo mật tuyệt đối. Các URL technical source đã pin commit trong report không thay đổi. [Bản PDF nộp hoàn chỉnh](report/Bao_cao_so_sanh_OpenCode_Pi_Codex_CLI.pdf) và PDF phụ lục đã có hyperlink artifact theo commit bằng chứng `f2becc501cfc1b980b888402458bac81b8193370`; link tải bản PDF mới nhất dùng nhánh `main` và không được coi là permalink của raw evidence.
