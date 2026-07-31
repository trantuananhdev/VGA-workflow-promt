# domain: e-commerce-marketplace

> Bán hàng, sàn nhiều người bán, mua theo giỏ, đấu giá, đăng tin rao bán.
> Dấu hiệu nhận biết trong PRD: có **danh mục sản phẩm**, có **giỏ hàng hoặc mua ngay**, có **tồn kho/số lượng**, giá có thể đổi theo biến thể.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Trang chủ / khám phá | Điểm vào | Khối theo mục đích (đang giảm giá, đã xem, gợi ý) — không phải 1 grid vô tận duy nhất |
| Tìm kiếm + **bộ lọc** | Đường chính tới mua | Bộ lọc là **màn/sheet riêng** trên mobile, không phải sidebar thu nhỏ |
| Danh sách kết quả | So sánh nhanh | Mỗi item cần: ảnh, tên, giá, giá gốc nếu giảm, tín hiệu tin cậy (đánh giá/đã bán) |
| **Chi tiết sản phẩm** | Màn quyết định | Thứ tự: ảnh → tên → giá → **chọn biến thể** → tồn kho → CTA. CTA phải neo cố định (sticky) vì màn này luôn dài |
| Giỏ hàng | Gom đơn | Sửa số lượng + xoá tại chỗ, hiển thị tổng tiền **cập nhật ngay** |
| Checkout | Chốt | Chia bước rõ: địa chỉ → vận chuyển → thanh toán → xem lại. Hiển thị bước hiện tại |
| Đơn của tôi + chi tiết đơn | Sau mua | Trạng thái + tra cứu vận chuyển + đường vào đổi/trả |

Với **marketplace** (nhiều người bán): thêm màn hồ sơ người bán, và giỏ hàng phải **nhóm theo người bán** — mỗi nhóm có phí vận chuyển riêng. Gộp thành 1 tổng duy nhất là sai mô hình.

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `out_of_stock` — hết hàng ở **cấp biến thể**, không chỉ cấp sản phẩm (đỏ size M hết, size L còn).
- `stock_changed_in_cart` — món trong giỏ hết hàng/đổi giá **sau khi** đã thêm vào giỏ. Xảy ra thật rất thường xuyên.
- `price_changed_at_checkout` — giá đổi giữa lúc bấm thanh toán.
- `cart_empty` — empty state có đường đi tiếp, không phải chỉ chữ "Giỏ hàng trống".
- `search_no_result` — kèm gợi ý (bỏ bớt filter / từ khoá gần đúng), không phải màn trắng.
- `filter_no_result` — khác `search_no_result`: đường đi tiếp là **xoá filter**, không phải sửa từ khoá.
- `payment_failed` / `payment_pending` — 2 state khác nhau: fail thì thử lại, pending thì **không được** cho bấm thanh toán lần nữa (nguy cơ trừ tiền 2 lần).
- `promo_invalid` / `promo_expired` / `promo_not_eligible` — 3 lý do khác nhau, phải nói rõ lý do nào.
- `address_required` — chưa có địa chỉ giao khi vào checkout.
- `guest_vs_logged_in` — nếu cho mua không cần đăng nhập thì đây là 2 luồng khác nhau.

PRD từ brief thô hầu như luôn thiếu `stock_changed_in_cart`, `payment_pending` và việc tách 3 lý do promo. Thấy thiếu → **hỏi `ba`**.

## 3. Pitfall UX riêng domain này

- **CTA "Thêm vào giỏ" không neo cố định** ở màn chi tiết → user cuộn 3 màn xuống đọc mô tả rồi phải cuộn lên. Sticky CTA là mặc định của domain này.
- **Chọn biến thể sau khi bấm mua** (mở sheet chọn size lúc bấm CTA) làm user không biết giá thật trước đó. Chọn biến thể phải nằm **trên** CTA và giá phải đổi theo biến thể ngay.
- **Phí vận chuyển chỉ hiện ở bước cuối** → tỉ lệ bỏ giỏ tăng vọt. Hiện sớm nhất có thể, hoặc ghi rõ "phí tính ở bước sau".
- **Nút xoá khỏi giỏ không có hoàn tác** → xoá nhầm phải tìm lại sản phẩm từ đầu. Cần undo, không cần dialog xác nhận (dialog cho mọi thao tác nhỏ mới là phiền).
- **Tổng tiền không cập nhật ngay** khi sửa số lượng (chờ round-trip API) → user bấm nhiều lần. Cần state optimistic + state rollback nếu server từ chối.
- **Đánh giá sản phẩm nhồi vào tab** làm user không thấy → đưa điểm trung bình + 2-3 đánh giá thật lên màn chính.
- **Marketplace: không thể hiện đang mua của ai** → user không biết nhiều người bán nghĩa là nhiều đơn, nhiều phí, nhiều thời gian giao.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Thanh toán trong app:** nếu bán **hàng số/nội dung số** thì iOS bắt buộc In-App Purchase (Apple thu 15-30%); hàng vật lý thì được dùng cổng ngoài. Ảnh hưởng trực tiếp tới luồng checkout → nêu rõ trong layout, đừng để `client-screen` phát hiện lúc submit store.
- **Apple Pay / Google Pay:** vị trí và hình dạng nút do guideline của từng bên quy định, **không** được vẽ nút tự tạo. Layout phải để chỗ cho nút gốc.
- **Chia sẻ sản phẩm:** iOS share sheet vs Android intent chooser — nội dung chia sẻ giống nhau nhưng điểm gọi khác nhau.
- **Swipe để xoá item trong giỏ:** là chuẩn iOS; Android thường dùng nút xoá tường minh. Đừng chỉ có swipe.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- **Giá giảm** không được chỉ dùng gạch ngang + màu đỏ — screen reader phải đọc được "giá gốc 500.000, giá hiện tại 350.000".
- Biến thể hết hàng phải có **trạng thái disabled đọc được**, không chỉ làm mờ màu.
- Ảnh sản phẩm cần alt text mang thông tin thật (không phải "ảnh sản phẩm 1").
- Bộ lọc dạng chip: số filter đang bật phải đọc được ở nhãn nút mở bộ lọc.
- Số lượng trong giỏ: nút +/− phải cách nhau đủ để không bấm nhầm, ≥ 44pt/48dp mỗi nút.
