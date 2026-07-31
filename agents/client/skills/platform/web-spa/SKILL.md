# platform pack: web-spa

**`delivery_target`:** `web_app` · **Dùng bởi:** `client` (cả 2 phase), nạp ở bước 0.
**draft: false** — nhưng xem mục 5: phần chưa có đường chạy thật trong repo được ghi rõ.

**Phạm vi:** app người dùng mở bằng **URL trong browser** (SPA hoặc SSR/SSG). Framework cụ thể (React/Next, Vue/Nuxt, SvelteKit…) lấy từ `shared/contracts/tech-stack.json`; pack này giữ phần đúng cho **mọi** web app.

**Khác mobile-native ở đâu — 3 điểm quyết định thiết kế vỏ:**
1. **Không có bước cài đặt.** Người dùng tới bằng link, tải code mỗi lần vào → kích thước bundle và thời gian hiện nội dung đầu tiên là *yêu cầu chức năng*, không phải "tối ưu sau".
2. **URL là trạng thái.** Mỗi `state_id` mà hợp đồng layout khai *có thể chia sẻ được* phải map tới 1 route/query thật; back/forward của browser phải đúng. Mobile không có lớp này.
3. **Không có store gác cổng, nhưng có browser gác cổng.** Không cần submit review, nhưng phải tự chịu CSP/HTTPS/quyền browser + hỗ trợ nhiều engine. Release vì thế là *deploy*, không phải *submit* (xem `kernel/gates/gate6-release-verified.md`).

**Skill trong pack:** `setup_web_shell/` (dựng vỏ, đối ứng `setup_native_shell`) · `check_web_platform_compliance/` (điều kiện Gate 3 của `client-shell`, đối ứng `check_platform_compliance`).

---

## 1. Vỏ gồm những gì (`client-shell`) — mỗi dòng phải có bằng chứng kiểm được

| Thành phần | Bằng chứng "đã dựng" |
|---|---|
| App shell + routing (map route ↔ story, 404, redirect) | log `build` thành công + bảng route thật trong repo |
| Render mode đã chốt (SPA / SSR / SSG / ISR) **có lý do**, khớp `architecture.md` | ghi trong `shared/capabilities/client.json` → `web.render_mode` |
| Biến môi trường + tách secret (client bundle KHÔNG chứa secret) | grep bundle build ra: 0 hit với tên biến secret |
| Security header: CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy` | header thật của bản deploy/preview (`curl -I`) |
| Browser support matrix + fallback khi JS lỗi | `client.json` → `web.browser_support`, và 1 trang test tải được khi JS fail |
| SEO cơ bản nếu đề bài cần khám phá qua tìm kiếm: title/meta/OG/sitemap/robots | file thật trong repo + kiểm 1 URL render ra HTML có nội dung |
| PWA/offline **chỉ khi** `product_signals.offline_need` = true | `manifest.webmanifest` + service worker + test tắt mạng |
| Ngân sách hiệu năng (bundle KB, LCP/CLS/INP) | số đo thật từ 1 lần build/lighthouse, đính kèm log |
| `check_web_platform_compliance/` trả `violations: []` | điều kiện Gate 3 của `client-shell` |

**Không** dựng PWA/service worker khi đề bài không đòi offline: nó thêm một tầng cache có vòng đời riêng, và lớp lỗi "người dùng thấy bản cũ sau khi deploy" là lỗi tốn nhất của web app.

## 2. STACK BINDING — điền theo `tech-stack.json`

| Việc | Vite/React | Next.js | Nuxt/SvelteKit |
|---|---|---|---|
| dev serve | `npm run dev` | `next dev` | `nuxt dev` / `vite dev` |
| build | `npm run build` | `next build` | `nuxt build` / `vite build` |
| lint | `eslint . --max-warnings=0` | như trên | như trên |
| unit test | `vitest run` | `vitest run` / `jest` | `vitest run` |
| e2e/route | `playwright test` | `playwright test` | `playwright test` |
| bậc hẹp nhất | DevTools 320px, hoặc `playwright --viewport-size=320,640` | như trên | như trên |
| cỡ chữ 200% | zoom 200% + `font-size: 32px` ở `html` (mô phỏng cỡ chữ browser) | như trên | như trên |

`run_lint`/`run_unit_test` của agent lấy lệnh từ bảng này, không hard-code trong skill đó.

## 3. Map `type` (hợp đồng layout) → element/pattern thật

| `type` | Web |
|---|---|
| `section`/`column`/`row` | `<section>`/`<div>` + flex/grid (`row` + `wrap_behavior` → `flex-wrap: wrap`) |
| `list`/`grid` | `<ul>`/`<ol>` hoặc grid container; danh sách dài → virtualize |
| `card` | `<article>` (là **1 khối nội dung**, không phải `<div>` suông) |
| `text`/`badge` | `<p>`/`<span>` + `-webkit-line-clamp`/`text-overflow` theo `behavior` |
| `input`/`select`/`search_field` | control native trong `<form>` — **KHÔNG** `<div onclick>`; `<label>` bắt buộc |
| `button`/`icon_button` | `<button>` (`icon_button` phải có `aria-label` = `a11y.label`) |
| `sheet`/`dialog` | `<dialog>` hoặc pattern modal có focus trap + đóng bằng `Esc` |
| `snackbar`/`tooltip` | vùng `aria-live="polite"` / `[role=tooltip]` — tooltip **không** là nơi đặt thông tin bắt buộc |
| `app_bar`/`tab_bar`/`nav_drawer`/`bottom_nav` | `<header>`/`<nav>` + `aria-current`; điều hướng chính phải là `<a href>` thật để mở tab mới được |
| `progress_indicator`/`skeleton` | `[role=progressbar]` / skeleton + `aria-busy` |
| `ad_slot` | slot do `ads-placement` chèn; giữ chỗ **cố định** để không gây layout shift (CLS) |

Quy tắc xuyên suốt: **element ngữ nghĩa trước, style sau.** `<div>` bấm được là lỗi a11y mà `min_tap_target_ok` trong hợp đồng không đủ để chặn.

## 4. Thực hiện `responsive` / `safe_area` / `text_overflow`

| Hợp đồng khai | Làm đúng | Làm SAI (không lint/test nào bắt) |
|---|---|---|
| bậc breakpoint | `@media (min-width: …)` **mobile-first**, hoặc container query cho component dùng lại ở nhiều chỗ | chỉ test ở bề rộng desktop → vỡ ở 320px |
| `min_height_dp: null` | `min-height` + để nội dung tự cao, đơn vị `rem` | `height` px cứng → cắt chữ khi người dùng đặt cỡ chữ lớn |
| `wrap_behavior` | `flex-wrap: wrap` / `grid-template-columns: repeat(auto-fit, minmax(…))` | `nowrap` + `overflow: hidden` → mất nội dung im lặng |
| `safe_area` cho khối `pinned` | `env(safe-area-inset-*)` + `dvh` thay `vh` | `100vh` + `position: fixed` → bị thanh URL động của mobile browser che |
| `text_overflow` | `-webkit-line-clamp` đúng `max_lines`, `hyphens`/`overflow-wrap` cho từ dài | để tràn → đẩy vỡ grid |
| cỡ chữ | `rem` (gốc theo browser), tối đa ~75 ký tự/dòng ở bậc rộng | `font-size` px → phớt lờ cỡ chữ người dùng đặt |

## 5. Compliance + capability

- `check_web_platform_compliance/` trả `violations: []` **trước khi** `client-screen` bắt đầu: CSP không dùng `unsafe-inline`/`unsafe-eval` cho script, mọi ảnh có `alt` (hoặc `alt=""` khi trang trí), mọi form control có nhãn, tương phản đạt `tokens.json → a11y_contract`, keyboard đi hết được luồng chính, có `<title>`/`lang`, ngân sách bundle/LCP không vượt ngưỡng đã chốt.
- `shared/capabilities/client.json`: `target: "web_app"`, khối `web` gồm `render_mode`, `browser_support`, `csp`, `permissions_used` (mỗi quyền browser — geolocation/camera/notification — trỏ đúng 1 `story_id` + `reason`, least-privilege y như permission native), `pwa`, `perf_budget`. Là **bản khai của vỏ thật**: lệch với header/manifest thật = chưa xong.
- **SUY ĐOÁN chưa có đường chạy thật trong repo này** (đọc lại khi review): mọi lệnh cụ thể ở mục 2 và ngưỡng hiệu năng — chúng theo quy ước phổ biến của hệ sinh thái, chưa được chạy trên 1 project web thật trong repo. Project web đầu tiên phải cập nhật lại mục 2 bằng lệnh đã chạy được và ghi vào `shared/lessons_learned.md`.
