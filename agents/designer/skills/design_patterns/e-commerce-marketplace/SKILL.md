# design_patterns: e-commerce-marketplace

> Craft mua sắm trên mobile: mật độ cao nhưng vẫn so sánh được, và giá phải đọc được trong 1 nhịp mắt.
> Đọc cùng `skills/domain/e-commerce-marketplace/SKILL.md` — file đó lo *state/pitfall*, file này lo *bố cục/tỉ lệ/motion*. Không lặp lại nhau.

## 1. Bố cục màn hình chủ đạo

| Màn | Cấu trúc theo chiều dọc | Tỉ lệ / ghi chú |
|---|---|---|
| Trang chủ | Ô tìm kiếm dính đỉnh → các **khối theo mục đích** xếp dọc, mỗi khối = header 1 dòng (+ "Xem tất cả" phải) + 1 hàng cuộn ngang | Card kế tiếp phải **hở 15-20%** ở cạnh phải để báo cuộn được. Không grid vô tận ngay dưới fold đầu |
| Kết quả tìm kiếm | Ô tìm kiếm → thanh filter/sort dính (chip cuộn ngang) → grid | **2 cột** trên điện thoại (M3 compact <600dp), margin ngoài ≈ gutter giữa cột; khoảng cách giữa 2 hàng card > padding trong card |
| Chi tiết sản phẩm | Gallery → giá → tên → tín hiệu tin cậy → biến thể → tồn kho → người bán → mô tả → đánh giá → gợi ý | Gallery 1:1 full-bleed, chiếm **45-55% chiều cao viewport**. Giá đứng **trên** tên: tên dài 2-3 dòng sẽ đẩy giá xuống dưới fold |
| Giỏ hàng | Danh sách dòng (nhóm theo người bán, header nhóm dính khi cuộn) → khối tổng tiền dính đáy | Khối tổng đáy 2 tầng: dòng tổng + CTA; chiếm ≤ 20% chiều cao |
| Checkout | Chỉ báo bước → đúng 1 nhóm form đang mở → khối giá → CTA dính đáy | 1 bước 1 màn; không cuộn qua 3 bước trong 1 màn |

Sticky bottom action bar ở chi tiết sản phẩm: 1 hàng cao 56-64dp **cộng** safe-area inset, có divider/elevation tách khỏi nội dung cuộn, và **không tự ẩn khi cuộn**.

## 2. Hierarchy & emphasis

**Nhiều nhất 1** `primary`/màn/state (trần, không phải đẳng thức — xem gạch đầu dòng "màn danh sách" dưới, và `limits.json → design._primary_why_not_exactly_one`). Quy tắc phân xử của domain này:

- **Primary luôn là hành động, không phải con số.** Ở chi tiết sản phẩm, `emphasis: primary` thuộc CTA "Thêm vào giỏ". Giá là element có **type scale lớn nhất trang** nhưng vẫn là `secondary` — bấm vào nó không làm gì.
- **2 CTA (Thêm giỏ / Mua ngay) thì 1 filled + 1 outlined**, không bao giờ 2 filled. Filled thuộc hành động ít hối hận hơn (thêm giỏ).
- **Màn danh sách không có primary.** Emphasis phân bổ **đều** giữa các card — nâng 1 card lên là phá chính chức năng so sánh của màn. Primary ở đây là *tập item*, không phải phần tử nào.
- **Trong phạm vi 1 card**, phần nặng nhất là **giá**, không phải ảnh (ảnh to nhất nhưng không phải "đậm" nhất) và không phải tên.
- Giỏ hàng: primary = "Thanh toán". Checkout: primary = nút bước tiếp; **tổng tiền** là dòng đậm nhất trong bảng giá nhưng không phải primary.
- **Phải bị hạ cấp** (tertiary/quiet, dễ bị nhồi lên sai): badge giảm giá, banner khuyến mãi, wishlist/share, nút chat người bán, "tiếp tục mua sắm", ô nhập mã giảm giá. Badge giảm giá đặc biệt hay bị vẽ to hơn giá — sai, nó chỉ là nhãn phụ của giá.
- Màu: đúng **1 accent** dùng cho primary; badge/giá-giảm dùng màu ngữ nghĩa riêng, tiết chế. Giá trị hex do `tokens.json` sinh, không lấy từ app nào.

## 3. Cấu trúc bên trong từng component chủ đạo

**Card sản phẩm** (grid) — 6 phần, trên xuống:
1. Media 1:1 full-bleed cạnh trên, **55-65% chiều cao card**, bo góc theo card ở 2 góc trên.
2. Overlay trên media: badge góc trên trái (rộng ≤ 1/4 chiều rộng ảnh), wishlist góc trên phải (vùng bấm ≥44pt/48dp dù icon nhỏ).
3. Vùng nội dung: padding 8-12dp; khoảng cách **2-4dp** giữa 2 dòng cùng nhóm, **8dp** giữa 2 nhóm khác nhau — đây là thứ tạo cảm giác "sạch", không phải font.
4. Tên: tối đa **2 dòng** rồi ellipsis, scale nhỏ, weight thường.
5. **Price block** (xem dưới).
6. Trust row 1 dòng: sao + điểm + "đã bán N" ở scale **nhỏ nhất card**, màu nhạt hơn (on-surface-variant).
   → Không đặt nút "thêm vào giỏ" trong card nếu sản phẩm có biến thể.

**Price block** — 3 phần **cùng baseline**, thứ tự cố định: giá hiện tại (lớn nhất, weight cao nhất) → giá gốc gạch ngang (~70-80% scale, màu nhạt) → chip `-N%` (nhỏ nhất). Đảo thứ tự này làm mắt đọc giá gốc trước.

**Bộ chọn biến thể** — mỗi thuộc tính là 1 khối: nhãn + **giá trị đang chọn cùng dòng** ("Màu: Đen") → hàng chip wrap tối đa 2 hàng rồi "Xem tất cả" → chip hết hàng có gạch chéo/nhãn, không chỉ giảm opacity. Đổi chip cập nhật giá + ảnh + tồn kho **ngay**.

**Sticky action bar**: cụm icon phụ bên trái (≤2 icon, ≤30% chiều rộng) + CTA bên phải chiếm **≥60% chiều rộng**.

**Dòng trong giỏ**: [checkbox] → thumbnail vuông 56-64dp → khối text (tên ≤2 dòng, biến thể 1 dòng nhỏ hơn, giá) → **stepper** bên phải. Stepper = 3 phần −/số/+, mỗi nút ≥44pt/48dp và cách nhau đủ để không bấm nhầm.

**Filter sheet**: header dính (tiêu đề + đóng) → body cuộn, nhóm dạng accordion, mỗi nhóm cho thấy số đang chọn → footer dính 2 nút: "Đặt lại" (text/outlined, trái, hẹp) + "Xem N kết quả" (filled, phải, rộng hơn) với **N cập nhật liên tục** khi đổi filter.

## 4. Interaction & motion

- **Vào chi tiết sản phẩm**: container transform từ card, ảnh là shared element, ~300-400ms với easing emphasized `cubic-bezier(0.2, 0, 0, 1)`. Đây là chuyển đổi duy nhất trên luồng đáng đầu tư motion.
- **Filter sheet / chọn biến thể**: bottom sheet vào ~400-500ms emphasized-decelerate `cubic-bezier(0.05, 0.7, 0.1, 1)`, ra nhanh hơn ~200-250ms emphasized-accelerate. Kéo sheet đi theo ngón 1:1, chỉ khi thả mới có duration.
- **Chip/checkbox/chọn biến thể**: đổi trạng thái ~100ms (short2) easing standard — cảm giác tức thì, không "mượt".
- **Thêm vào giỏ**: badge số lượng ở tab bar pop scale nhẹ ≤150ms + snackbar có "Xem giỏ". **KHÔNG** vẽ ảnh sản phẩm bay vào icon giỏ — vui 1 lần, phiền từ lần thứ 3.
- **KHÔNG animate con số tiền** (count-up tổng tiền/giá): người ta đang đọc số, không xem hiệu ứng. Giá đổi theo biến thể phải **nhảy tức thì**, không cross-fade — fade tạo cảm giác app đang chờ server.
- **Stepper trong giỏ**: cập nhật optimistic ngay, tổng tiền đổi cùng frame; server từ chối thì rollback + snackbar giải thích.
- **Tải grid**: skeleton **đúng khung card thật** (đúng tỉ lệ ảnh, đúng số dòng text), cross-fade sang nội dung 100-150ms. Không spinner giữa màn. Trang kế tiếp nối vào cuối danh sách, không nhảy scroll.
- **Xoá khỏi giỏ**: item collapse ~200ms + snackbar Hoàn tác; không dialog xác nhận.
- `prefers-reduced-motion`: thay container transform và sheet slide bằng fade 100ms; bỏ pop badge. Giữ nguyên toàn bộ cập nhật tức thì.

## 5. Nguồn tham chiếu + ranh giới IP

**Tier 1 (design system chính thống, đã đối chiếu):** giá trị duration/easing của Material 3 (`short2` 100ms, `medium2` 300ms, emphasized `cubic-bezier(0.2,0,0,1)`, emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)`, emphasized-accelerate `cubic-bezier(0.3,0,0.8,0.15)`) — nguồn `m3.material.io/styles/motion/easing-and-duration`; pattern container transform và bottom sheet (M3 components); breakpoint compact <600dp → 2 cột; tap target 48dp (M3) / 44pt (Apple HIG). Lưu ý cho lần cập nhật sau: trang M3 và HIG render bằng JS nên `WebFetch` trả về rỗng — phải đối chiếu qua token spec.

**Suy đoán của tôi (chưa có tier 1 chống lưng — hãy chỉnh nếu thấy sai):** mọi con số tỉ lệ cụ thể trong mục 1 và 3 — 45-55% viewport cho gallery, 55-65% chiều cao card cho media, CTA ≥60% chiều rộng bar, thumbnail 56-64dp, hở 15-20% card kế tiếp, giá gốc ở 70-80% scale, spacing 2-4dp/8dp. Đây là chưng từ quan sát app phổ biến (tier 3-4: ảnh store), **không** có spec chính thống nào chốt các số này. Quy tắc "màn danh sách không có primary" và "primary là hành động, không phải con số" cũng là suy luận của tôi từ ràng buộc 1-primary-mỗi-màn của layout JSON, không phải convention đã được ai phát biểu.

**Ranh giới IP:** file này chỉ chứa cấu trúc, thứ tự, tỉ lệ và quan hệ — không có hex thương hiệu, logo, bộ icon độc quyền hay copy nguyên văn của app nào, và cố ý không nêu tên app cụ thể như hình mẫu.

## 6. Thich ung kich thuoc man hinh

> Dien `components[].responsive` theo muc nay; co che va thu tu degrade chung o `agents/designer/skills/responsive_layout/SKILL.md`. Cac con so duoi thuoc dien **SUY DOAN** cua muc 5 tru khi ghi ro tier 1.

**Cot:** grid ket qua tim kiem `compact_small` **1** cot / `compact` **2** / `medium` 3 / `expanded` 4. Tier 1: M3 compact <600dp -> 2 cot. Duoi 360dp thi 2 cot chi con ~150dp/cot — khong du cho anh 1:1 + ten 2 dong + price block, nen ha ve 1 cot va doi card sang bo cuc ngang (thumbnail trai, text phai).

**Hang cuon ngang tren trang chu:** `axis: horizontal` + `wrap_behavior: scroll_horizontal`, chieu rong item **co dinh theo ti le** (khong theo % man) de moc "ho 15-20% card ke tiep" con dung o moi be rong.

**Degrade trong card san pham** (`degrade_order`, bo truoc -> sau): trust row ("da ban N") -> badge giam gia -> gia goc gach ngang -> ten rut ve 1 dong. **Khong bao gio**: anh, gia hien tai. Cat gia la lam sai chuc nang man so sanh.

**Sticky action bar chi tiet san pham:** `pinned: true` + `safe_area: "bottom"` (bat buoc — 56-64dp *cong* inset la con so o muc 1). O co chu 200% thi cum icon phu ben trai bi bo TRUOC khi CTA hep lai; CTA giu >=60% be rong.

**Gallery san pham:** `sizing: aspect_ratio` 1:1, **khong** dung % chieu cao viewport — o landscape thi "45-55% viewport" lam gallery an het man va gia tut xuong duoi fold.

**Landscape / medium:** chi tiet san pham chuyen sang 2 khoi ngang (gallery trai ~45%, thong tin + CTA phai) thay vi keo dai truc doc. Grid gio hang giu 1 cot dong, khong bao gio 2 cot.
