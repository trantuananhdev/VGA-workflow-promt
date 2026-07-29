# domain: education-learning

> Khoá học video, flashcard, luyện thi, học ngôn ngữ, quản lý lớp học, bài tập/kiểm tra.
> Dấu hiệu nhận biết trong PRD: có **tiến độ học theo bài/chương**, có **bài kiểm tra/chấm điểm**, có **nội dung tuần tự phải mở khoá dần**, hoặc có **giáo viên/học viên là 2 vai trò khác nhau**.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Danh sách khoá học/lộ trình | Điểm vào | Phân biệt rõ: đã mua/chưa mua, đang học/đã hoàn thành |
| Chi tiết khoá học | Trước khi học | Mục lục chương/bài hiển thị **trước** khi vào học, kèm thời lượng ước tính |
| Màn học (video/đọc/tương tác) | Nội dung chính | Thanh tiến độ trong bài, nút tiếp tục đúng vị trí đã dừng (resume) |
| Bài tập/câu hỏi | Kiểm tra | Từng câu 1 màn trên mobile, không nhồi cả bài dài vào 1 màn cuộn |
| Kết quả & giải thích | Sau kiểm tra | Hiện đáp án đúng + giải thích, không chỉ điểm số |
| Tiến độ tổng quan | Động lực | Biểu đồ streak/chương đã hoàn thành, theo tuần |
| Hồ sơ giáo viên/lớp học (nếu có vai trò giáo viên) | Quản lý | Layout khác hẳn học viên: danh sách học viên, giao bài, xem điểm |
| Chứng chỉ/hoàn thành | Kết thúc lộ trình | Màn ăn mừng rõ ràng — đây là điểm chạm cảm xúc quan trọng của domain |

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `content_locked` — bài/chương chưa mở khoá (do chưa hoàn thành bài trước, hoặc cần trả phí) — 2 lý do khác nhau phải hiện khác nhau.
- `download_required` / `download_in_progress` — nếu cho học offline, cần state tải nội dung trước khi vào bài.
- `video_buffering` / `video_playback_error` — 2 state khác nhau: đang tải và lỗi phát, xử lý khác nhau (chờ vs thử lại/tải lại).
- `quiz_in_progress_interrupted` — thoát giữa bài kiểm tra (cuộc gọi tới, thoát app) — có được cho tiếp tục hay phải làm lại, phải nói rõ.
- `time_limit_expiring` — bài kiểm tra có giới hạn thời gian, cảnh báo trước khi hết giờ.
- `answer_submitted_pending_grade` — với bài tự luận cần giáo viên chấm — khác hẳn kết quả tự động ngay.
- `streak_broken` — mất chuỗi ngày học liên tục — trung lập, không dùng ngôn ngữ tạo cảm giác thất bại (giống nguyên tắc ở `health-fitness`).
- `course_expired` / `access_revoked` — hết hạn truy cập khoá học (mua theo thời hạn) hoặc bị thu hồi quyền truy cập.
- `low_bandwidth_mode` — nếu app hỗ trợ giảm chất lượng video cho mạng yếu, cần state chuyển đổi rõ ràng.
- `certificate_generation_pending` — chứng chỉ đang xử lý sau khi hoàn thành, chưa có ngay lập tức.

PRD từ brief thô hầu như luôn thiếu `content_locked` (2 lý do khác nhau), `quiz_in_progress_interrupted`, và `answer_submitted_pending_grade`. Thấy thiếu → **hỏi `ba`**.

## 3. Pitfall UX riêng domain này

- **Không cho resume đúng vị trí video/bài đọc đã dừng** → user mất động lực học tiếp vì phải tìm lại chỗ cũ. Đây là kỳ vọng nền tảng của mọi app học hiện đại.
- **Nhồi cả bài kiểm tra dài vào 1 màn cuộn** trên mobile → tỉ lệ bỏ dở cao. Từng câu 1 màn, có thanh tiến độ câu hỏi.
- **Không giải thích đáp án sau khi làm sai** (chỉ hiện đúng/sai) → mất giá trị học tập, đây là lý do chính user học app thay vì chỉ làm đề giấy.
- **Khoá nội dung không nói rõ lý do** (chỉ hiện icon ổ khoá) → user không biết cần hoàn thành gì hay cần trả phí mới mở.
- **Không có chế độ học offline** cho nội dung đã tải, dù đã cho tải → mất niềm tin nếu mạng yếu giữa lúc học (nhiều user học lúc di chuyển).
- **Thông báo nhắc học dùng giọng điệu ép buộc/tội lỗi** ("Bạn đã bỏ lỡ 3 ngày!") → hiệu ứng ngược, giảm giữ chân người dùng lâu dài.
- **Giáo viên và học viên dùng chung 1 layout** chỉ đổi vài nút → 2 vai trò có mục tiêu hoàn toàn khác nhau (dạy vs học), cần thiết kế riêng, không phải biến thể của cùng 1 màn.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Phát video nền/picture-in-picture:** iOS PiP qua AVKit có giới hạn khác Android PiP (Activity phải khai báo riêng) — nếu PRD yêu cầu "vừa học vừa làm việc khác" thì 2 nền tảng cần cấu hình khác nhau, nêu rõ cho `mobile-shell`.
- **Tải nội dung offline:** quản lý dung lượng lưu trữ hiển thị khác nhau — iOS có mục quản lý dung lượng app riêng trong Settings hệ thống, Android qua App Info — layout màn "quản lý nội dung đã tải" trong app nên tự đủ, không phụ thuộc user vào Settings hệ thống.
- **Thanh toán mua khoá học trong app:** nếu bán khoá học số thì áp dụng ràng buộc In-App Purchase của iOS giống domain `e-commerce-marketplace` — nêu rõ trong layout checkout.
- **Bàn phím nhập câu trả lời tự luận:** kiểu bàn phím và gợi ý tự động sửa khác nhau — với câu trả lời cần chính xác (chính tả, công thức) cân nhắc tắt auto-correct, khai rõ cho `mobile-screen`.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- Video học **bắt buộc** có phụ đề/transcript — không chỉ vì accessibility mà còn vì học trong môi trường ồn/yên lặng bắt buộc.
- Câu hỏi trắc nghiệm: đáp án đúng/sai không được chỉ biểu diễn bằng màu — cần icon + nhãn chữ ("Đúng"/"Sai").
- Thanh tiến độ chương/khoá học cần công bố phần trăm bằng số khi focus, không chỉ thanh trực quan.
- Nội dung toán/công thức cần có mô tả bằng lời tương đương cho screen reader, không chỉ ảnh công thức.
- Giới hạn thời gian bài kiểm tra cần có tuỳ chọn gia hạn hợp lý — người dùng screen reader hoặc khó khăn vận động cần nhiều thời gian hơn để thao tác.
