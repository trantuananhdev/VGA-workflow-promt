# skill_setup_web_shell

**Dùng bởi:** `client`, phase `client-shell`, khi `platform_pack: "web-spa"`. Tương ứng `setup_native_shell` của pack `mobile-native`.

**Mục tiêu:** Dựng vỏ web app đúng theo `architecture.md`/`system-spec.md` — **trước khi** `client-screen` code màn hình đầu tiên.

**Input:** anchor-tag slice `shared/architecture.md` + `shared/system-spec.md` + entry `PROJ` của `shared/contracts/tech-stack.json`

**Output:** app shell trong repo + `shared/capabilities/client.json` (khối `web`) + log build

---

## Quy trình

```
1. Khởi tạo project theo framework đã chốt trong tech-stack.json (KHÔNG tự chọn framework khác).
   Verify: lệnh build ở STACK BINDING của pack chạy exit 0 -> giữ log.

2. CHỐT RENDER MODE bằng căn cứ, không theo thói quen:
     cần index bởi máy tìm kiếm / chia sẻ link có preview  -> SSR hoặc SSG
     nội dung tĩnh, đổi thưa                               -> SSG
     sau đăng nhập, dữ liệu riêng từng người               -> SPA (hoặc SSR có auth)
   Ghi mode + LÝ DO vào client.json.web.render_mode. Mode sai chỉ lộ ra khi SEO/preview
   không hoạt động — lúc đó sửa là viết lại tầng render.

3. ROUTING: mỗi story có màn chia sẻ được -> 1 route thật (<a href>, không phải onClick).
   Khai bảng route ↔ story_id trong repo. Có 404 + redirect chuẩn.
   Back/forward của browser phải trả đúng trạng thái — test tay 1 lần, ghi lại.

4. ENV + SECRET: biến client-side có tiền tố công khai của framework; secret CHỈ ở server.
   Verify BẰNG LỆNH: grep tên biến secret trong thư mục build ra 0 hit (đính kèm output).

5. SECURITY HEADER: CSP (script không dùng unsafe-inline/unsafe-eval), HSTS,
   X-Content-Type-Options, Referrer-Policy. Verify bằng `curl -I` trên bản preview thật.

6. SEO nếu bước 2 cần: title/meta/OG per route, sitemap.xml, robots.txt, canonical.
   Verify: curl 1 URL -> HTML trả về CÓ nội dung chính (không phải chỉ <div id=root>).

7. PWA/offline CHỈ khi project-profile.product_signals.offline_need == true:
   manifest.webmanifest + service worker + chiến lược cache có phiên bản.
   Verify: tắt mạng, tải lại, app còn dùng được ở phạm vi đã khai.
   KHÔNG cần offline thì BỎ HẲN — service worker không cần thiết là nguồn lỗi
   "user thấy bản cũ sau deploy".

8. NGÂN SÁCH HIỆU NĂNG: chốt trần bundle (KB) + LCP/CLS/INP, đo thật 1 lần, ghi số vào
   client.json.web.perf_budget. Không có số thì Gate 3 không có gì để đối chiếu.

9. Ghi shared/capabilities/client.json khối `web` — bản khai của vỏ THẬT, không phải mong muốn.
```

## Không được làm

- Không tự đổi framework/render mode khác `tech-stack.json` — Sync Session với `cto`.
- Không thêm quyền browser (geolocation/camera/notification) mà không có story cần + `reason` (least-privilege, y hệt permission native).
- Không báo xong khi chưa có **log thật** cho bước 1, 4, 5, 8.

## Verify trước khi emit handoff

Build exit 0 · secret grep 0 hit · header thật đúng · route table khớp story · số đo perf có thật · `check_web_platform_compliance` trả `violations: []`. Thiếu bất kỳ mục nào = chưa xong (Gate 3, điều kiện phase `client-shell`).
