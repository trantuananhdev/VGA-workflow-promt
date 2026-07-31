# domain: productivity-tools

> Ghi chú, quản lý công việc (to-do/kanban), lịch, quản lý tài liệu, cộng tác nhóm, tính toán/theo dõi ngân sách cá nhân (không phải giao dịch tiền thật — xem `fintech-payment` nếu có).
> Dấu hiệu nhận biết trong PRD: có **danh sách mục việc/ghi chú do user tự tổ chức**, có **thao tác hàng loạt** (sắp xếp, gắn nhãn, lọc), có **đồng bộ nhiều thiết bị**, hoặc có **cộng tác nhiều người trên cùng 1 tài liệu**.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Danh sách/bảng chính | Điểm vào | Hỗ trợ nhiều chế độ xem nếu PRD yêu cầu (danh sách/kanban/lịch) — không ép 1 chế độ duy nhất |
| Tạo nhanh (quick add) | Nhập liệu tần suất cao | Phải **nhanh nhất có thể** — ít bước nhất trong toàn app, vì đây là thao tác lặp lại nhiều lần/ngày |
| Chi tiết mục việc/ghi chú | Chỉnh sửa sâu | Tự động lưu (autosave), không có nút "Lưu" tách biệt trừ khi PRD yêu cầu rõ |
| Sắp xếp/lọc/gắn nhãn | Tổ chức | Thao tác hàng loạt (chọn nhiều mục cùng lúc) cần có, không chỉ sửa từng cái |
| Lịch/timeline (nếu có) | Xem theo thời gian | Kéo-thả đổi hạn, không chỉ sửa qua form |
| Cộng tác/chia sẻ | Nhiều người dùng | Hiện rõ ai đang xem/sửa cùng lúc nếu là tài liệu chia sẻ realtime |
| Tìm kiếm toàn cục | Truy xuất | Tìm xuyên mọi danh sách/ghi chú, không giới hạn trong 1 thư mục đang mở |
| Cài đặt đồng bộ/sao lưu | Tin cậy dữ liệu | Trạng thái đồng bộ phải luôn nhìn thấy được, không ẩn trong menu sâu |

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `sync_conflict` — cùng 1 mục bị sửa ở 2 thiết bị khi offline rồi đồng bộ lại xung đột — phải cho user chọn giữ bản nào, **không tự động** chọn 1 bên rồi mất dữ liệu.
- `sync_pending` / `sync_failed` — đang chờ đồng bộ vs đồng bộ lỗi, khác nhau về hành động (chờ vs thử lại).
- `offline_edit_queued` — sửa khi offline, thay đổi xếp hàng chờ mạng — user cần biết là chưa lên cloud.
- `storage_limit_reached` — hết dung lượng lưu trữ (gói miễn phí) — chặn tạo mới, không chặn xem/sửa cái cũ.
- `permission_read_only` — cộng tác viên chỉ có quyền xem, không được sửa — nút sửa phải disabled rõ ràng kèm lý do, không ẩn đi làm tưởng tính năng không tồn tại.
- `undo_available` — sau xoá/sửa hàng loạt, có cửa sổ hoàn tác ngắn trước khi mất vĩnh viễn.
- `recurring_item_edit_scope` — sửa 1 mục lặp lại (recurring task) cần hỏi rõ: sửa mục này hay toàn bộ chuỗi lặp.
- `attachment_upload_failed` — đính kèm file/ảnh lỗi tải lên, không được mất nội dung text đã gõ cùng.
- `empty_state_first_use` — danh sách trống lần đầu dùng — cần hướng dẫn tạo mục đầu tiên, không phải màn trắng.
- `collaborator_left_or_removed` — người cộng tác rời/bị xoá khỏi tài liệu chia sẻ.

PRD từ brief thô hầu như luôn thiếu `sync_conflict`, `recurring_item_edit_scope`, và `permission_read_only`. Thấy thiếu → **hỏi `ba`**.

## 3. Pitfall UX riêng domain này

- **Tự động chọn 1 bên khi xung đột đồng bộ** (thường là "bản mới nhất thắng") mà không hỏi → mất dữ liệu người dùng đã nhập, đây là lỗi nghiêm trọng nhất có thể xảy ra với domain lưu trữ thông tin cá nhân.
- **Quick add không thực sự nhanh** (mở form đầy đủ field bắt buộc) → domain này thắng-thua ở tốc độ nhập, thêm field bắt buộc không cần thiết làm giảm tần suất dùng.
- **Không có autosave** cho ghi chú dài → mất nội dung nếu app bị hệ điều hành thu hồi bộ nhớ giữa lúc gõ (rất phổ biến trên mobile).
- **Sửa 1 mục trong chuỗi lặp lại (recurring) không hỏi phạm vi áp dụng** → sửa nhầm cả chuỗi hoặc chỉ sửa 1 lần trong khi user muốn cả chuỗi.
- **Trạng thái đồng bộ ẩn sâu trong cài đặt** → user không biết dữ liệu đã lên cloud an toàn chưa, mất niềm tin khi đổi thiết bị mà "mất" dữ liệu (thực ra chỉ chưa đồng bộ).
- **Thao tác hàng loạt không có bước xác nhận** khi xoá nhiều mục cùng lúc, nhưng lại **có** dialog xác nhận cho mỗi thao tác đơn lẻ nhỏ → ngược với mức độ rủi ro thực tế, nên đảo lại.
- **Không phân biệt "đã lưu local" và "đã đồng bộ cloud"** trong 1 icon duy nhất → 2 trạng thái có ý nghĩa khác nhau về an toàn dữ liệu.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Widget màn hình chính / màn khoá:** WidgetKit (iOS) vs App Widgets (Android) có giới hạn tương tác khác nhau (iOS widget hạn chế tương tác trực tiếp hơn) — nếu PRD muốn "tick việc ngay từ widget" cần kiểm khả năng thật của từng nền tảng trước khi vẽ.
- **Đồng bộ nền:** Background App Refresh (iOS) bị hệ thống giới hạn nghiêm ngặt hơn WorkManager (Android) — với app cần đồng bộ thường xuyên, độ trễ đồng bộ có thể khác nhau giữa 2 nền tảng, nêu rõ cho `client-shell`/`cto`.
- **Kéo-thả sắp xếp (kanban/lịch):** hành vi haptic feedback khi kéo khác nhau — cả 2 nền tảng đều cần, nhưng API triển khai khác.
- **Chia sẻ nhanh từ app khác vào (share extension/intent):** iOS Share Extension và Android Share Intent là 2 cơ chế khác nhau hoàn toàn — nếu PRD muốn "lưu nhanh từ app khác", cần thiết kế 2 luồng riêng.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- Kéo-thả sắp xếp (kanban, sắp xếp thứ tự) **bắt buộc** có cách thay thế bằng nút bấm (di chuyển lên/xuống) cho người không thao tác kéo-thả được.
- Trạng thái hoàn thành/chưa hoàn thành của task không được chỉ biểu diễn bằng checkbox màu — cần đọc được trạng thái qua screen reader.
- Bảng kanban (nhiều cột) cần có chế độ xem danh sách tuyến tính thay thế cho screen reader — bố cục dạng lưới 2D khó điều hướng bằng công nghệ hỗ trợ.
- Thao tác hàng loạt (chọn nhiều mục) cần công bố rõ số lượng đang chọn qua live region.
- Editor văn bản định dạng rich text cần đảm bảo mọi nút định dạng (đậm/nghiêng/danh sách) có nhãn đọc được, không chỉ icon.
