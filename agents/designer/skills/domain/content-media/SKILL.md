# domain: content-media

> Đọc báo/tin tức, nghe nhạc/podcast, xem video/phim, đọc truyện, streaming trực tiếp.
> Dấu hiệu nhận biết trong PRD: có **thư viện nội dung để duyệt/phát**, có **hàng đợi phát/tiếp tục xem**, có **gói thuê bao mở khoá nội dung**, hoặc có **phát nội dung nền/ngoại tuyến**.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Trang chủ/khám phá | Điểm vào | Khối theo mục đích (tiếp tục xem, gợi ý, mới ra mắt) — giống nguyên tắc ở `e-commerce-marketplace` |
| Tìm kiếm | Truy cập trực tiếp | Kết quả phân loại theo nghệ sĩ/thể loại/nội dung, không phải 1 danh sách phẳng |
| Trang chi tiết nội dung | Trước khi phát | Mô tả + thời lượng + nút phát chính, phần liên quan bên dưới |
| **Trình phát** (audio/video) | Trải nghiệm chính | Điều khiển phát phải luôn truy cập được kể cả khi cuộn nội dung khác — thu nhỏ (mini-player), không đóng hẳn |
| Hàng đợi/playlist | Quản lý phát | Kéo-thả sắp xếp lại, xoá tại chỗ |
| Thư viện cá nhân (đã lưu/đã tải) | Truy cập lại | Phân biệt đã tải offline vs chỉ lưu online |
| Gói thuê bao/nâng cấp | Kiếm tiền | Màn riêng, so sánh rõ ràng lợi ích từng gói |
| Bình luận/đánh giá (nếu có) | Tương tác | Dùng chung pattern `social-community` cho phần này |

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `buffering` / `playback_error` / `playback_stalled_low_bandwidth` — 3 tình huống khác nhau, xử lý khác nhau (chờ / thử lại / hạ chất lượng tự động).
- `content_unavailable_in_region` — nội dung bị chặn theo khu vực địa lý (bản quyền) — nói rõ lý do, không hiện như lỗi kỹ thuật.
- `content_removed` — nội dung đã bị gỡ (hết hạn bản quyền) sau khi user đã lưu/thêm playlist.
- `download_expired` — nội dung tải offline hết hạn sử dụng (thuê bao) — khác với bị xoá thủ công.
- `subscription_required` / `subscription_expired` — 2 lý do khác nhau chặn quyền truy cập.
- `queue_empty` — hàng đợi phát trống, cần gợi ý thêm nội dung.
- `background_playback_restricted` — nếu tài khoản miễn phí không được phát nền, phải nói trước khi user tắt màn hình rồi mất nhạc.
- `casting_connection_lost` — nếu hỗ trợ phát qua loa/TV ngoài (Chromecast/AirPlay) và mất kết nối giữa chừng.
- `autoplay_next_countdown` — đếm ngược tự động phát tiếp, phải cho huỷ được trong lúc đếm.
- `resume_position_available` — có vị trí xem dở, hỏi tiếp tục hay xem lại từ đầu.

PRD từ brief thô hầu như luôn thiếu `content_unavailable_in_region`, `subscription_required` (tách khỏi lỗi mạng), và `background_playback_restricted`. Thấy thiếu → **hỏi `ba`**.

## 3. Pitfall UX riêng domain này

- **Đóng mini-player khi chuyển màn** → mất ngữ cảnh đang nghe/xem, phải tìm lại từ đầu. Mini-player phải sống xuyên suốt app trừ khi user chủ động dừng phát.
- **Không lưu vị trí đã xem/nghe** khi thoát giữa chừng → mất trải nghiệm "tiếp tục xem" là giá trị cốt lõi của domain.
- **Autoplay tự động chuyển nội dung tiếp theo không cho huỷ kịp** → phát nhầm nội dung không muốn xem, đặc biệt nhạy cảm với nội dung phân loại độ tuổi.
- **Không nói rõ nội dung nào cần thuê bao trước khi user bấm phát** → cảm giác bị lừa khi vừa bấm play đã hiện paywall.
- **Chất lượng phát không tự thích ứng mạng yếu** mà chỉ báo lỗi → nên có state hạ chất lượng tự động trước khi coi là lỗi hẳn.
- **Tải offline không báo dung lượng sẽ dùng** trước khi tải → tràn bộ nhớ thiết bị bất ngờ.
- **Danh sách gợi ý không giải thích vì sao gợi ý** → với nội dung nhạy cảm (tin tức) cần minh bạch hơn thuật toán gợi ý ngầm.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Phát nhạc/video nền + điều khiển từ màn khoá:** iOS qua MPNowPlayingInfoCenter/Remote Command Center, Android qua MediaSession — cả 2 đều cần cấu hình native riêng, layout điều khiển (nút tua/dừng) trên màn khoá do hệ điều hành vẽ, không phải do app vẽ — nêu rõ cho `mobile-shell`.
- **Phát qua thiết bị ngoài:** AirPlay (iOS) vs Chromecast (Android/cả 2) là 2 SDK khác nhau hoàn toàn — nút "phát tới thiết bị khác" cần xử lý riêng từng nền tảng, không dùng chung 1 icon giả định hành vi giống nhau.
- **Tải offline giới hạn dung lượng:** cách hệ thống báo dung lượng còn trống khác nhau — app nên tự kiểm tra và báo trước khi gọi API hệ thống.
- **Picture-in-Picture cho video:** giống lưu ý ở `education-learning` — cấu hình khai báo khác nhau giữa 2 nền tảng.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- Video **bắt buộc** hỗ trợ phụ đề nếu nội dung có lời nói — không chỉ vì luật ở nhiều thị trường mà vì đây là tính năng lõi của domain.
- Điều khiển trình phát (play/pause/tua) phải đạt tap target tối thiểu **ngay cả** ở dạng mini-player thu nhỏ — không được thu nhỏ tới mức dưới ngưỡng vì lý do thẩm mỹ.
- Thanh tiến độ phát (scrubber) cần hỗ trợ điều chỉnh bằng nút bấm rời rạc cho screen reader, không chỉ kéo-thả bằng ngón tay.
- Trạng thái phát/tạm dừng không được chỉ đổi icon — cần thông báo trạng thái cho screen reader khi thay đổi.
- Danh sách nội dung dài (thư viện nhạc/phim) cần hỗ trợ nhảy nhanh theo chữ cái/section cho công nghệ hỗ trợ, không chỉ cuộn tuyến tính.
