# skill_check_web_platform_compliance

**Dùng bởi:** `client`, phase `client-shell`, khi `platform_pack: "web-spa"`. Đối ứng `check_platform_compliance` của pack `mobile-native`.

**Khác gì `check_app_store_policy` của `devops`?** Web không có store gác cổng, nên **không có ai** chặn app sai chuẩn ngoài chính gate này. Đó là lý do skill này phải chạy **trước** khi code story đầu tiên: web thiếu cửa review nghĩa là mọi lỗi vỏ đi thẳng ra người dùng.

**Output:** `{ "violations": [...] }` — Gate 3 của `client-shell` yêu cầu `violations: []`.

---

## Kiểm bằng LỆNH/SỐ, không bằng nhận xét

| # | Mục | Cách kiểm | Vi phạm khi |
|---|---|---|---|
| 1 | CSP | `curl -I <preview-url>` | thiếu `Content-Security-Policy`, hoặc script có `unsafe-inline`/`unsafe-eval` |
| 2 | HTTPS + HSTS | `curl -I` | thiếu HSTS, hoặc còn asset tải qua `http://` |
| 3 | Header khác | `curl -I` | thiếu `X-Content-Type-Options: nosniff` hoặc `Referrer-Policy` |
| 4 | Secret trong bundle | grep thư mục build | có bất kỳ hit với tên biến secret |
| 5 | Ảnh có `alt` | quét HTML/JSX build | có `<img>` không `alt` (trang trí phải `alt=""`) |
| 6 | Form control có nhãn | quét build | có `input`/`select` không `<label>`/`aria-label` |
| 7 | Tương phản | đo cặp màu thực tế vs `tokens.json → a11y_contract` | dưới ngưỡng — báo **bằng số**, không phải "đã kiểm tra" |
| 8 | Keyboard | đi hết luồng chính bằng Tab/Enter/Esc | có bước không tới được, hoặc focus trap của modal sai |
| 9 | `lang` + `<title>` | quét HTML | thiếu ở bất kỳ route |
| 10 | Browser support | build target vs `client.json.web.browser_support` | build target rộng hơn hoặc hẹp hơn bản khai |
| 11 | Ngân sách hiệu năng | 1 lần build + đo LCP/CLS/INP | vượt trần đã chốt ở `client.json.web.perf_budget` |
| 12 | Cache/versioning | asset có hash, HTML không cache dài | deploy mới mà user vẫn nhận HTML cũ |
| 13 | Không JS | tải 1 route với JS tắt | trang trắng hoàn toàn **và** đề bài cần SEO/chia sẻ link |

## Vì sao đặt ở `client-shell`, không ở `qa`

11/13 mục trên là **thuộc tính của vỏ**, không của story: sửa CSP hay đổi render mode sau khi đã có N story build lên trên là việc đắt nhất trong pipeline. `qa` vẫn kiểm lại theo story, nhưng phát hiện lần đầu phải ở đây.

## Khi vi phạm không sửa được ở tầng client

Vd HSTS/CSP do tầng hosting quyết định → **không** tự nới lỏng yêu cầu để pass. Mở Sync Session với `cto` (`max_turns: 3`); nếu là việc của hạ tầng thì `devops-infra` là bên sửa, ghi rõ trong `violations[].owner`.
