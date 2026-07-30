# design_patterns: on-demand-booking

> Craft đặt-theo-yêu-cầu trên mobile: bản đồ/lịch chiếm không gian, nhưng thứ user cần đọc luôn là **trạng thái + thời gian**.
> Đọc cùng `skills/domain/on-demand-booking/SKILL.md` — file đó lo *state/pitfall*, file này lo *bố cục/tỉ lệ/motion*. Không lặp lại nhau.

## 1. Bố cục màn hình chủ đạo

| Màn | Cấu trúc | Tỉ lệ / ghi chú |
|---|---|---|
| Chọn dịch vụ / điểm đến | Bản đồ full-bleed phía trên + **bottom sheet thường trú** phía dưới | Bản đồ 55-65% chiều cao viewport; sheet ở mức peek 35-45%. Sheet expand thì bản đồ vẫn phải thấy **≥25%** — không che hết |
| Chọn thời gian | Segmented "Ngay bây giờ / Hẹn giờ" ở đầu → nội dung nhánh → CTA đáy | Nhánh đang chọn phải có **nhãn chữ tường minh**, không chỉ tô nền |
| Chọn khung giờ (lịch hẹn) | Dải ngày cuộn ngang (ô 48-56dp: thứ trên, số dưới) → grid slot **3 cột** | Slot hết chỗ **hiện nhưng disabled**, không ẩn — user cần thấy mật độ để đổi ngày |
| Xem lại & xác nhận | Khối thông tin đơn → khối giá tách dòng → CTA dính đáy | Khối giá là phần cao nhất của màn; CTA không cuộn mất |
| **Chờ đối tác** | Khối trạng thái ~40% trên (đếm ngược là element lớn nhất màn) → đơn thu gọn → Huỷ dưới cùng | Nút Huỷ **không** cùng vị trí và hình dạng với CTA vừa bấm ở màn trước — tránh bấm quán tính |
| Theo dõi | Bản đồ trên + sheet dưới | Peek chứa: trạng thái + **ETA (lớn nhất)** + partner row + hàng icon liên hệ. Kéo lên mới ra timeline đầy đủ |
| Huỷ / đổi lịch | Hậu quả (phí, mất chỗ) → lý do → 2 nút | Hậu quả đứng **trên** mọi thứ, không nhét vào caption dưới nút |

Nút "vị trí của tôi" nổi trên bản đồ, đặt **sát cạnh trên của sheet, lệch phải** — không góc dưới phải (đụng vùng attribution/điều khiển của Maps).
Timeline trạng thái: dọc, 1 bước = 1 hàng; **đúng 1 hàng** (bước hiện tại) có emphasis cao, bước đã qua nhạt và thu gọn, bước tương lai chỉ còn nhãn.

## 2. Hierarchy & emphasis

**Nhiều nhất 1** `primary`/màn/state (trần, không phải đẳng thức — `limits.json → design._primary_why_not_exactly_one`). Đặc thù domain này: **primary đổi theo state của đơn**, nên `emphasis` phải khai theo từng state, không khai 1 lần cho cả màn.

| State / màn | Primary | Bị hạ cấp |
|---|---|---|
| Chọn dịch vụ | **Ô nhập điểm đến** (một input, không phải nút) — hành động kế tiếp là *nhập*, không phải *bấm* | Nút vị trí, khuyến mãi, lịch sử địa điểm |
| Chọn thời gian | Nút "Tiếp tục" | Segmented, picker |
| Xem lại | Nút "Xác nhận" | **Tổng giá** — dòng đậm nhất trong bảng nhưng là thông tin, không phải primary |
| `pending_partner_confirm` | **Bộ đếm ngược + dòng trạng thái** | Nút **Huỷ** ở đây phải là text/outlined. Đây là chỗ dễ sai nhất: nâng Huỷ lên filled thì user huỷ do quán tính, ẩn Huỷ thì vi phạm domain skill — đúng là "luôn thấy, emphasis thấp" |
| `confirmed` / `in_progress` | **ETA + trạng thái** | Gọi/chat = icon button secondary; Huỷ tụt xuống tertiary |
| Màn huỷ | Nút **"Giữ đơn"** | Nút huỷ thật là text màu error — hành động phá hoại **không bao giờ** giành primary |
| `completed` | Nút đánh giá | Chi tiết giá, hoá đơn |

Suy ra một nguyên tắc dùng được: **primary trên các màn chờ/theo dõi là một element thông tin (đếm ngược, ETA), không phải nút** — vì lúc đó user không có hành động nào đáng làm, và mọi nút được nhấn mạnh đều là nút gây hối hận.

## 3. Cấu trúc bên trong từng component chủ đạo

**Bottom sheet điều hướng**: drag handle 32×4dp căn giữa cạnh trên (M3) → vùng peek chứa **đúng 1 hành động chính + ≤2 dòng phụ** (peek phải dùng được mà không cần kéo) → nội dung mở rộng cuộn được bên dưới.

**Ô nhập hành trình** (2 điểm): 2 field xếp dọc, nối bằng đường dot ở lề trái; icon điểm đi (hình tròn nhỏ) và điểm đến (hình vuông/pin) **khác hình dạng**, không chỉ khác màu; nút đảo chiều bên phải, căn giữa theo chiều dọc của cả 2 field.

**Thẻ phương án dịch vụ** (loại xe/gói/kỹ thuật viên): 1 hàng gồm ảnh/icon 40-48dp trái → khối text (tên; mô tả 1 dòng scale nhỏ; ETA) → **giá bên phải, là phần nặng nhất của hàng**. Trạng thái đang chọn = viền + nền tonal, không chỉ dấu tick.

**Khối giá**: mỗi dòng label trái / value phải; dòng tổng cách nhóm trên bằng divider **và** spacing lớn 1.5-2× dòng thường; phí phát sinh có icon info bấm được (vùng bấm ≥44/48) mở giải thích — không ghi giải thích thành caption dài.

**Bộ đếm ngược**: số `phút:giây` là text lớn nhất màn, **kèm nhãn chữ ngay dưới** nói đang chờ gì; nếu có vòng progress bao quanh thì con số vẫn phải đọc được khi bỏ vòng đi.

**Partner row**: avatar tròn 40-48dp trái → khối text 2 dòng (tên; rating · biển số/mã nhận diện) → 2 icon action phải, mỗi cái ≥44pt/48dp. Mã nhận diện (biển số, số phòng) phải ở scale **≥ tên** — đó là thứ user thực sự đối chiếu ngoài đời.

**Timeline step**: cột chỉ báo trái rộng cố định 24-32dp (icon bước + đường nối chạy suốt) → nội dung phải (nhãn bước; timestamp ở scale nhỏ hơn). Bước hiện tại là hàng duy nhất đổi weight/nền.

**Slot chip**: 1 dòng nhãn giờ, chiều cao ≥48dp, 3 cột; state hết chỗ có gạch/nhãn "Hết", không chỉ mờ.

## 4. Interaction & motion

- **Bottom sheet peek ↔ expand**: kéo đi theo ngón **1:1, không duration**; thả ra thì settle ~300-400ms emphasized-decelerate `cubic-bezier(0.05, 0.7, 0.1, 1)`. Sheet **không** tự expand khi mở màn.
- **Camera bản đồ**: recenter/zoom ~400-600ms ease-out, và **chỉ** khi user bấm nút vị trí hoặc đối tác ra khỏi viewport. **KHÔNG** animate camera mỗi lần toạ độ cập nhật — đó là nguồn cảm giác rung lắc tệ nhất của domain này.
- **Marker đối tác**: nội suy vị trí mượt giữa 2 tick dữ liệu (~1-2s, linear), có xoay theo hướng; marker di chuyển, bản đồ đứng yên.
- **Đếm ngược**: đổi số **mỗi 1s, không tween chữ số**; vòng progress animate linear đúng 1s/tick. Tween số làm người ta không đọc được.
- **Đổi state đơn** (`pending` → `confirmed`): đây là khoảnh khắc đáng đầu tư — transition rõ ~300ms (medium2, easing emphasized `cubic-bezier(0.2, 0, 0, 1)`) + haptic nhẹ + cập nhật live region cho screen reader. **Không** animation ăn mừng dài che nội dung: user cần đọc thông tin đối tác ngay.
- **Timeline**: bước mới chỉ đổi trạng thái icon 150-200ms; không animate lại cả danh sách.
- **Nút Huỷ phải có mặt từ frame đầu** của màn chờ — không fade-in trễ, không xuất hiện sau vài giây (user kết luận là không huỷ được).
- **Chỉ báo đang chờ**: indeterminate hoặc pulse chậm ≥1.5s/chu kỳ. Spinner nhanh ở màn chờ dài tạo cảm giác app lỗi.
- **Chọn slot/phương án**: đổi trạng thái ~100ms (short2) standard; giá tổng cập nhật cùng frame, **không** count-up.
- `prefers-reduced-motion`: bỏ pulse, bỏ nội suy marker (nhảy vị trí), thay sheet slide bằng fade 100ms. Mọi cập nhật dữ liệu vẫn tức thì.

## 5. Nguồn tham chiếu + ranh giới IP

**Tier 1 (design system chính thống, đã đối chiếu):** duration/easing của Material 3 (`short2` 100ms, `medium2` 300ms, emphasized `cubic-bezier(0.2,0,0,1)`, emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)`, emphasized-accelerate `cubic-bezier(0.3,0,0.8,0.15)`) — nguồn `m3.material.io/styles/motion/easing-and-duration`; bottom sheet M3 (drag handle 32×4dp, standard vs modal, kéo theo ngón) và Apple HIG *Sheets* (detent medium/large, grabber, dùng cho tác vụ tự chứa) → căn cứ cho pattern "map trên + sheet dưới"; progress indicator indeterminate cho tác vụ không biết thời lượng; tap target 48dp (M3) / 44pt (HIG). Lưu ý: trang M3 và HIG render bằng JS nên `WebFetch` trả rỗng — phải đối chiếu qua token spec.

**Suy đoán của tôi (chưa có tier 1 chống lưng — hãy chỉnh nếu thấy sai):** toàn bộ con số tỉ lệ ở mục 1 và 3 (bản đồ 55-65%, peek 35-45%, bản đồ còn ≥25% khi expand, khối trạng thái ~40%, rail timeline 24-32dp, ô ngày 48-56dp, grid slot 3 cột); khoảng nội suy marker 1-2s và camera 400-600ms; quy tắc "không tween chữ số đếm ngược"; và đặc biệt **"primary trên màn chờ/theo dõi là element thông tin chứ không phải nút"** cùng **"nút Huỷ không được trùng vị trí/hình dạng với CTA vừa bấm"** — hai cái này là suy luận của tôi từ pitfall "Huỷ biến mất / huỷ do quán tính" trong `domain` skill, không phải convention đã được phát biểu ở đâu.

**Ranh giới IP:** chỉ cấu trúc, thứ tự, tỉ lệ và quan hệ — không hex thương hiệu, logo, bộ icon độc quyền, copy nguyên văn; cố ý không nêu tên app cụ thể như hình mẫu.

## 6. Thich ung kich thuoc man hinh

> Dien `components[].responsive` theo muc nay; co che va thu tu degrade chung o `agents/designer/skills/responsive_layout/SKILL.md`. Cac con so duoi thuoc dien **SUY DOAN** cua muc 5 tru khi ghi ro tier 1.

**Cot:** grid slot khung gio `compact_small` **2** cot / `compact` **3** / `medium` 4-5. Duoi 360dp giu 3 cot thi moi slot ~100dp — chua duoc "07:30 - 08:00" nen phai ha ve 2 cot, KHONG duoc rut ngan nhan gio.

**Ban do + bottom sheet:** ban do `sizing: aspect_ratio` hoac `fill`, **khong** khoa `min_height_dp`. O landscape ti le "ban do 55-65% / sheet peek 35-45%" khong con dung: chuyen sang ban do **trai 55-60%**, sheet thanh panel phai. Rang buoc "ban do van thay >=25% khi sheet expand" giu nguyen o moi huong.

**Degrade trong peek cua sheet theo doi:** hang icon lien he -> partner row -> nhan trang thai dai. **Khong bao gio**: ETA (element lon nhat peek) va nut Huy.

**Dai ngay cuon ngang:** `axis: horizontal` + `scroll_horizontal`, o 48-56dp giu **kich thuoc co dinh** — khong `shrink`, vi o nho hon 48dp la pha tap target 48dp/44pt (tier 1).

**CTA dinh day + man cho doi tac:** moi CTA/nut Huy dinh day khai `pinned: true` + `safe_area: "bottom"`. Toi da 2 vung pinned — man theo doi da co top bar + sheet, nen khong them bar thu ba.

**Co chu 200%:** khoi dem nguoc o man "Cho doi tac" la element lon nhat man; khoi chua no PHAI `min_height_dp: null`, neu khong so dem nguoc bi cat.
