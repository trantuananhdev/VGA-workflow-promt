# skill_verify_web_deployment

**Dùng bởi:** `devops`, phase `devops-release`, **chỉ khi** `shared/contracts/tech-stack.json` → `delivery_targets` chứa `web_app` và/hoặc `backend_service`. Đối ứng `check_app_store_policy` của nhánh `mobile_native`.

**Mục tiêu:** Chứng minh bằng **lệnh thật** rằng bản build đã live và có đường lùi — không phải bằng câu "đã deploy".

**Vì sao cần:** với app store, việc submit có bên thứ ba (Apple/Google) xác nhận hộ. Web/API **không có ai xác nhận**: pipeline xanh chỉ nghĩa là artifact đã build, hoàn toàn không nói gì về việc người dùng có tải được trang hay API có trả 200 hay không. Đó là lớp lỗi "im lặng" mà Gate 6 sinh ra để chặn.

**Output:** `{ "checks": [...], "release_id": "...", "rollback_verified": true|false }` — Gate 6 đọc trực tiếp.

---

## Kiểm bắt buộc — mỗi dòng là 1 lệnh, giữ output làm `artifact_refs`

### Nếu có `web_app`

| # | Kiểm | Lệnh/cách | Đạt khi |
|---|---|---|---|
| 1 | URL production trả nội dung | `curl -sS -o /dev/null -w '%{http_code}' <url>` | `200` |
| 2 | TLS hợp lệ, còn hạn | `curl -vI <url>` (đọc phần certificate) | không cảnh báo, hạn > 14 ngày |
| 3 | Security header còn nguyên **ở bản production** | `curl -I <url>` | có CSP + HSTS + `X-Content-Type-Options` (khớp `shared/capabilities/client.json` → `web.csp`) |
| 4 | Bản đang live **đúng** bản vừa build | so `release_id`/commit hash nhúng trong bundle với `git tag` | khớp semver vừa tag |
| 5 | Không phục vụ HTML cũ sau deploy | tải lại 2 lần, so hash asset | asset có hash mới, HTML không cache dài |
| 6 | Route chính đi được | `curl` 3 route quan trọng nhất | tất cả `200`, không redirect vòng |
| 7 | **Rollback đã thử thật** | chạy lệnh rollback về bản trước rồi tiến lại | cả 2 chiều thành công, ghi thời gian thực hiện |

### Nếu có `backend_service`

| # | Kiểm | Lệnh/cách | Đạt khi |
|---|---|---|---|
| 8 | Health endpoint | `curl <api>/health` | `200` + phiên bản đúng bản vừa release |
| 9 | Migration đã chạy | log migration của bản này | không có migration `pending` |
| 10 | Migration có đường lùi | tài liệu/lệnh `down` tồn tại và đã thử ở staging | có, kèm log |
| 11 | Biến môi trường/secret không lộ | quét log khởi động | 0 hit tên secret |
| 12 | **Rollback đã thử thật** | như điều 7 (image/phiên bản trước) | thành công |

## Không được làm

- **Không coi "pipeline xanh" là đã release.** Pipeline xanh = artifact tồn tại; nó không chứng minh gì về môi trường production.
- **Không bỏ điều 7/12 (rollback).** Release không có đường lùi đã thử nghĩa là sự cố đầu tiên sẽ được xử lý bằng cách ứng biến — đúng lúc tệ nhất để ứng biến. Đây là điều kiện gần nhất với "chặn ở nơi rẻ" mà nhánh web/API có, tương đương vai trò của bản review store ở nhánh mobile.
- **Không tự nới lỏng header/CSP để pass** — sai lệch so với `client.json` là drift, báo `doc_drift_detected`.
- Không dùng tag `latest` (xem `skills/git_workflow/SKILL.md`).

## Khi FAIL

Điều 1-3, 8 là lỗi hạ tầng của chính `devops` → sửa rồi chạy lại. Điều 4-6 thường là lỗi cấu hình build của `client` → Sync Session với `cto`, **không** tự sửa code client. Theo `kernel/gates/gate6-release-verified.md`: điều liên quan cấu hình bên ngoài **không retry mù** — fail 2 lần liên tiếp thì escalate ngay.
