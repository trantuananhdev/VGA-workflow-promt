# domain: on-demand-booking

> Gọi xe, giao đồ ăn, đặt phòng/sân/lịch hẹn, thuê dịch vụ tại nhà, đặt vé theo suất.
> Dấu hiệu nhận biết trong PRD: có **bên thứ hai phải xác nhận** (tài xế/chủ nhà/nhân viên), có **thời điểm** (giờ hẹn, giờ nhận), và trạng thái đơn **thay đổi khi user không mở app**.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Chọn dịch vụ/địa điểm | Điểm vào | Thường có bản đồ hoặc ô tìm kiếm chiếm nửa trên |
| **Chọn thời gian** | Bắt buộc | Tách "ngay bây giờ" và "hẹn giờ" thành 2 nhánh rõ — không nhét vào 1 date picker |
| Xem lại & xác nhận | Chốt giá | Giá + **phí phát sinh tách dòng** trước nút xác nhận, không gộp thành 1 số |
| **Chờ đối tác xác nhận** | Màn riêng | Có bộ đếm thời gian + nút Huỷ luôn hiển thị |
| Theo dõi tiến trình | Sau xác nhận | Timeline trạng thái, không phải 1 dòng text đổi nội dung |
| Huỷ / đổi lịch | Màn riêng | Nêu **hậu quả** (phí huỷ, hết chỗ) trước khi cho bấm |
| Lịch sử đơn | Quay lại | Cần lọc theo trạng thái, không chỉ theo thời gian |

Nhịp chung: **1 quyết định 1 màn**. Nhồi chọn giờ + chọn dịch vụ + thanh toán vào 1 màn là pitfall phổ biến nhất của domain này trên mobile.

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `pending_partner_confirm` — đã gửi, **chưa** ai nhận. Có đếm ngược + huỷ được.
- `partner_timeout` — hết thời gian chờ mà không ai nhận (khác hẳn `rejected`).
- `partner_rejected` — bị từ chối, kèm đường đi tiếp (tìm đối tác khác / đổi giờ).
- `confirmed` — đã có đối tác, kèm thông tin liên hệ.
- `in_progress` — đang thực hiện, có tiến trình.
- `slot_unavailable` — khung giờ vừa chọn bị người khác lấy **trong lúc** đang thao tác.
- `cancelled_by_user` / `cancelled_by_partner` — 2 state khác nhau, hậu quả khác nhau.
- `completed` + đường vào đánh giá.
- `location_permission_denied` — với app cần vị trí, đây là state **thường xuyên** xảy ra thật, không phải edge case.

PRD viết từ brief thô hầu như luôn thiếu `partner_timeout`, `slot_unavailable` và `cancelled_by_partner`. Thấy thiếu → **hỏi `ba`**, đừng tự thêm.

## 3. Pitfall UX riêng domain này

- **Nút Huỷ biến mất ở màn chờ.** User đang chờ 5 phút không thấy cách thoát là nguồn 1-star review lớn nhất của domain. Huỷ phải hiển thị ở **mọi** state trước `in_progress`.
- **Giá đổi sau khi xác nhận** mà không có màn thông báo riêng → cảm giác bị lừa. Mọi thay đổi giá phải có state riêng, user phải bấm đồng ý lại.
- **Timeline trạng thái làm bằng 1 dòng text đổi nội dung** → user không biết đã qua bước nào, còn bao nhiêu bước. Dùng danh sách bước có đánh dấu.
- **Chọn thời gian mặc định là "ngay bây giờ" nhưng không nói rõ** → user đặt nhầm giờ. Trạng thái mặc định phải hiển thị tường minh.
- **Trạng thái đơn đổi khi app đang đóng** → cần thiết kế cả thông báo đẩy, không chỉ màn hình. Nêu rõ trong layout để `client-shell` biết là cần push (nếu `client.json` chưa khai → Sync Session `cto`).
- **Đơn cũ trong lịch sử mở ra lại thành màn "đang theo dõi"** → phải có state read-only cho đơn đã đóng.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Xin quyền vị trí:** iOS có "Cho phép một lần" (`When In Use` vs `Always`) và hỏi lại lần 2 rất khó; Android có "Chỉ vị trí gần đúng". → layout cần state riêng cho **vị trí gần đúng** (Android) chứ không chỉ có/không có quyền.
- **Bản đồ:** Apple Maps vs Google Maps khác nhau về vùng an toàn của nút điều khiển — không đặt CTA sát góc dưới bên phải.
- **Huỷ bằng cử chỉ:** iOS user kỳ vọng swipe-back thoát được màn chờ; Android dùng nút back hệ thống. Cả 2 **không** được huỷ đơn ngầm — swipe-back chỉ rời màn, đơn vẫn sống.
- **Date/time picker:** iOS bánh xe cuộn, Material lịch + đồng hồ. Đừng vẽ 1 picker tự tạo giống nhau cho cả 2.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- Trạng thái đơn **không được** chỉ phân biệt bằng màu (xanh=xong / vàng=chờ / đỏ=huỷ) — phải kèm icon + nhãn chữ.
- Bộ đếm ngược phải có nhãn đọc được cho screen reader dạng "còn 2 phút", không phải chuỗi `02:00` trần.
- Bản đồ phải có **đường đi bằng danh sách text** song song, vì bản đồ trực quan gần như vô dụng với screen reader.
- Nút Huỷ phải đạt tap target ≥ 44pt/48dp **kể cả** khi đặt trong thanh trên cùng.
