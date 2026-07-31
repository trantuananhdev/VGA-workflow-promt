# domain: social-community

> Feed, nhắn tin, hồ sơ cá nhân, theo dõi/kết bạn, bình luận, nhóm/cộng đồng, chat trong app khác (vd chat với tài xế).
> Dấu hiệu nhận biết trong PRD: có **feed nội dung do user tạo**, có **like/comment/share**, có **quan hệ giữa 2 user** (follow, bạn bè, chặn), hoặc có **tin nhắn realtime**.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Feed chính | Điểm vào | Pull-to-refresh + infinite scroll là mặc định; skeleton loading khi tải lần đầu |
| Chi tiết bài đăng | Tương tác sâu | Comment thread thu gọn/mở rộng, không load hết 1 lần |
| Soạn bài/tin nhắn | Tạo nội dung | Lưu nháp tự động — mất mạng giữa chừng không được mất nội dung đang gõ |
| Danh sách hội thoại | Nhắn tin | Badge chưa đọc, trạng thái online/last seen (nếu PRD cho phép) |
| **Chat 1-1 hoặc nhóm** | Realtime | Trạng thái gửi/đã nhận/đã xem tách biệt rõ; typing indicator nếu có |
| Hồ sơ cá nhân (của mình / người khác) | Danh tính | 2 layout khác nhau: xem hồ sơ mình có nút Sửa, xem người khác có nút Theo dõi/Nhắn tin |
| Thông báo | Tổng hợp tương tác | Nhóm theo loại (like/comment/follow), không phải 1 danh sách phẳng dài vô tận |
| Chặn/báo cáo | An toàn | Luôn có, kể cả khi PRD ban đầu không nhắc — đây là kỳ vọng nền tảng (App Store/Play Store yêu cầu) |

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `sending` / `sent` / `delivered` / `seen` — 4 trạng thái tin nhắn khác nhau, không gộp thành "đã gửi".
- `message_failed` — gửi lỗi (mất mạng giữa chừng), có nút gửi lại **tại đúng vị trí tin nhắn đó**.
- `content_removed` / `content_reported_pending` — bài/bình luận đã bị gỡ hoặc đang chờ duyệt báo cáo — không hiện như bình thường, không biến mất im lặng.
- `blocked_by_other_user` — mình bị người khác chặn: KHÔNG được báo rõ "bạn đã bị chặn" (rò rỉ thông tin cho hành vi rình rập) — hiện như user không tồn tại/không phản hồi.
- `account_deactivated` / `account_deleted` — hồ sơ người khác đã xoá tài khoản.
- `empty_feed_new_user` — user mới chưa follow ai, feed trống — cần gợi ý follow, không phải màn trắng.
- `typing_indicator_stale` — người kia đang gõ nhưng ngừng gõ quá lâu, indicator phải tự ẩn.
- `group_member_left` / `group_you_removed` — khác nhau: rời nhóm tự nguyện vs bị xoá khỏi nhóm.
- `content_age_restricted` — nếu có kiểm duyệt độ tuổi.
- `rate_limited` — spam quá nhanh bị chặn tạm (post/comment liên tục).

PRD từ brief thô hầu như luôn thiếu `blocked_by_other_user`, `message_failed`, và việc tách 4 trạng thái tin nhắn. Thấy thiếu → **hỏi `ba`**.

## 3. Pitfall UX riêng domain này

- **Trạng thái "đã xem" (seen) luôn bật** mà không cho tắt → vấn đề riêng tư nghiêm trọng, nhiều app phải thêm cài đặt ẩn read receipt sau khi ra mắt. Nêu rõ trong PRD có cho tắt hay không **trước khi** vẽ, đừng để mặc định luôn bật.
- **Đếm like/comment nhảy số khi cuộn feed** (do refetch không cache) → cảm giác dữ liệu không đáng tin. Cần giữ số ổn định trong 1 phiên xem.
- **Không có preview trước khi đăng** (đăng xong mới thấy sai) → cần màn xem lại, đặc biệt với ảnh/video.
- **Comment dài không thu gọn** làm feed dài vô tận ở 1 bài. Luôn có "Xem thêm".
- **Chặn xong vẫn thấy nội dung cũ của người đó** trong feed lịch sử → phải ẩn hồi tố, không chỉ chặn tương tác mới.
- **Không phân biệt "đang tải thêm" với "đã hết nội dung"** ở cuối feed → user cuộn mãi tưởng còn.
- **Nhắn tin nhóm không rõ ai đã đọc** khi cần (thông báo quan trọng) → cân nhắc read-receipt theo từng thành viên nếu PRD yêu cầu.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Thông báo đẩy cho tin nhắn:** iOS gộp nhóm theo thread trong Notification Center khác cách Android gộp theo app — layout thông báo rich (ảnh preview, quick reply) khai báo khác nhau ở tầng native, nêu rõ cho `client-shell`.
- **Chia sẻ bài đăng ra ngoài app:** share sheet (iOS) vs intent chooser (Android) — nội dung chia sẻ (ảnh + link) phải test cả 2 vì preview card render khác nhau.
- **Chọn ảnh/video để đăng:** iOS PHPicker giới hạn quyền truy cập thư viện ảnh (chọn ảnh cụ thể thay vì cấp toàn bộ) khác với Android Photo Picker — layout nút "chọn thêm ảnh" cần tính tới việc user không cấp full-access.
- **Vuốt để xoá/trả lời tin nhắn:** chuẩn iOS là vuốt trái/phải trên bong bóng chat; Android thường dùng long-press mở menu. Không chỉ có 1 cách.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- Ảnh trong feed **bắt buộc** có alt text do người đăng cung cấp (khuyến khích) hoặc caption thay thế — không được để trống hoàn toàn cho screen reader.
- Trạng thái tin nhắn (gửi/nhận/xem) không được chỉ biểu diễn bằng icon nhỏ đổi màu — cần nhãn đọc được.
- Nút like/react phải công bố **số lượng hiện tại** khi được focus ("Thích, 24 lượt thích"), không chỉ đọc "nút thích".
- Typing indicator cần thông báo qua live region cho screen reader, không chỉ hiệu ứng chấm nhấp nháy.
- Voice message (nếu có) cần có bản chuyển văn bản hoặc ít nhất hiển thị độ dài — không được là trải nghiệm chỉ-nghe.
