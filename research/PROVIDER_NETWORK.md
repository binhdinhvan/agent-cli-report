# Chẩn đoán mạng host → provider, 2026-11-09

**Không thấy chặn DNS/TCP/TLS/HTTP tại thời điểm kiểm tra.** Chưa kiểm luồng Responses có xác thực hoặc backend model; không suy những lượt timeout trước không thể có lỗi mạng thoáng qua.

Được người dùng yêu cầu kiểm sau R-0025/R-0026 timeout trước HTTP status. Kiểm từ host nơi broker gửi request, không từ sandbox cố ý chặn Internet; dùng kết nối trực tiếp/no environment proxy giống `demos/model_smoke.py:handler` (`ProxyHandler({})`). Không đọc key, không Authorization/cookie, không redirect và **không gọi `/responses`/generation**.

| Bước | Quan sát runtime | Thời gian |
| --- | --- | ---: |
| DNS `api.shopaikey.com` | IPv4 `103.109.43.8` | 149 ms |
| TCP443 | Kết nối thành công | 286 ms đến TCP |
| TLS/SNI hostname | TLS1.3, CA/hostname verified, issuer Let's Encrypt YE1 | 762 ms cả TCP+TLS |
| GET `/v1/models`, không key | **401**, JSON/nginx | 303 ms đến HTTP headers |
| GET `/`, không key | **200**, JSON/nginx | 164 ms đến HTTP headers |

401 ở endpoint cần auth là bằng chứng đã tới HTTP/auth gate, không phải bằng chứng mạng chặn. Không đọc body hoặc lưu cookie/header credential. Các bước chạy tuần tự, không retry tự động. Timeout giới hạn cho chẩn đoán: DNS/process tối đa20s, TCP/TLS socket8s, HTTP12s; không đổi timeout45s của broker hoặc cap300s của pilot.

## Lần kiểm tra lại theo yêu cầu người dùng

Giữ nguyên script/protocol, artifact mới [`PROVIDER-NETWORK-20261109-02/result.json`](../demos/artifacts/PROVIDER-NETWORK-20261109-02/result.json): DNS cùng IPv4 **7ms**, TCP **50ms**, cả TCP+TLS verified **103ms**, GET/models **401/55ms**, GET/ **200/57ms**. Vẫn không Authorization/key/generation/redirect/proxy môi trường. Kết quả cơ bản nhất quán với lần01, không thấy chặn mạng lúc probe; authenticated Responses/model backend vẫn **unverified**, không tự retry pilot từ kết quả này.

Script [`../demos/check_provider_network.py`](../demos/check_provider_network.py), raw [`PROVIDER-NETWORK-20261109-01/result.json`](../demos/artifacts/PROVIDER-NETWORK-20261109-01/result.json) có timestamp/source SHA-256 và tên biến proxy hiện diện (không lưu giá trị). Đây là **runtime-confirmed cho các probe không auth lúc kiểm tra**, không benchmark hoặc model support test.

## Diễn giải cho pilot

- Không có bằng chứng host bị chặn toàn bộ domain/port443 hoặc TLS lỗi trong phép thử này. Sandbox không có Internet là thiết kế; broker host vẫn có đường ra.
- Hai request pilot trước timeout mà chưa HTTP headers: luồng có auth/model routing/Responses hoặc biến động mạng khác có thể khác endpoint public. **Chưa xác định gateway/provider/model/backend/network là root cause**; không kết luận overload, key bị chặn hay OpenCode sai chỉ từ public401/200.
- Một GET không auth thành công không kiểm chứng xử lý token, quota, quyền model, Responses streaming hoặc time-to-first-byte của request thực. Muốn kiểm các mục đó phải chốt probe riêng/ngân sách nếu có inference; không tự gọi generation trong bước kiểm mạng.
- Raw pilot, protocol, key, service, binary, environment r2 giữ nguyên. **Chưa retry hoặc mở năm slot còn lại.**
