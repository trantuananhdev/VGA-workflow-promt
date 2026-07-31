# domain: health-fitness

> Theo dõi tập luyện, dinh dưỡng, giấc ngủ, chu kỳ sức khoẻ, đặt lịch khám, nhắc uống thuốc, kết nối thiết bị đeo.
> Dấu hiệu nhận biết trong PRD: có **chỉ số cơ thể/sinh hiệu**, có **mục tiêu theo dõi theo thời gian**, có **nhắc nhở định kỳ**, hoặc có **dữ liệu từ cảm biến/thiết bị ngoài**.

**Nguyên tắc trùm cả domain:** dữ liệu ở đây là **dữ liệu sức khoẻ nhạy cảm** (HealthKit/Health Connect coi là loại dữ liệu riêng, có quy định pháp lý). Mọi pattern phải ưu tiên *rõ ràng về quyền riêng tư* và *không gây hoang mang y tế* hơn là *đẹp mắt*. Không được đưa ra kết luận mang tính chẩn đoán y khoa trừ khi PRD xác nhận đây là app y tế được cấp phép.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Tổng quan hôm nay | Điểm vào | Chỉ số chính (bước chân/calo/nhịp tim) dạng thẻ lớn, xu hướng nhỏ bên dưới — không nhồi 10 chỉ số ngang hàng |
| Ghi nhận thủ công (bữa ăn/cân nặng/triệu chứng) | Nhập liệu | Bàn phím số lớn, đơn vị đo rõ ràng (kg/lb, ml/oz) theo cài đặt vùng |
| Biểu đồ xu hướng theo thời gian | Xem lại | Chọn khoảng thời gian (ngày/tuần/tháng), có mốc so sánh trước đó |
| Mục tiêu & tiến độ | Động lực | Thanh tiến độ + trạng thái đạt/chưa đạt, không phán xét khi chưa đạt |
| Nhắc nhở/lịch trình | Định kỳ | Cho tuỳ chỉnh giờ, tắt tạm thời (snooze) không phải chỉ bật/tắt vĩnh viễn |
| Kết nối thiết bị đeo | Onboarding + settings | Trạng thái đồng bộ rõ ràng: đang đồng bộ / đồng bộ lần cuối lúc nào |
| Đặt lịch khám (nếu có) | Booking con | Dùng chung pattern `on-demand-booking` cho phần chọn giờ + xác nhận |
| Chia sẻ dữ liệu với bác sĩ/người thân (nếu có) | Quyền riêng tư | Màn riêng, liệt kê **chính xác** dữ liệu nào sẽ được chia sẻ trước khi bật |

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `sync_failed` — thiết bị đeo không đồng bộ được; phải nói rõ dữ liệu đang hiện là **cũ tới khi nào**, không hiện như dữ liệu mới.
- `no_device_connected` — chưa kết nối thiết bị, khác với đã kết nối nhưng lỗi.
- `data_gap` — có khoảng trống dữ liệu (quên đeo thiết bị 1 ngày) — biểu đồ phải thể hiện khoảng trống, **không nội suy** làm giả liền mạch.
- `permission_denied_health_data` — user từ chối cấp quyền HealthKit/Health Connect — luồng vẫn phải dùng được ở mức tối thiểu (nhập tay), không chặn hoàn toàn.
- `goal_not_realistic_warning` — mục tiêu user đặt vượt ngưỡng an toàn khuyến nghị (nếu app tính toán việc này) — cảnh báo, không tự ý hạ mục tiêu.
- `reminder_missed` — bỏ lỡ 1 lần nhắc (uống thuốc, tập luyện) — hiện trung lập, không dùng ngôn ngữ tạo cảm giác tội lỗi.
- `data_export_pending` / `data_export_ready` — nếu cho xuất dữ liệu sức khoẻ.
- `subscription_required_for_metric` — nếu 1 số chỉ số chỉ mở khi trả phí — phải nói rõ **trước khi** user tưởng tính năng bị lỗi.
- `emergency_disclaimer` — với app có cảnh báo chỉ số bất thường: luôn kèm khuyến cáo liên hệ cơ sở y tế, không tự kết luận tình trạng bệnh.

PRD từ brief thô hầu như luôn thiếu `data_gap`, `sync_failed`, và `permission_denied_health_data`. Thấy thiếu → **hỏi `ba`**.

## 3. Pitfall UX riêng domain này

- **Dùng màu đỏ/cảnh báo mạnh cho việc "chưa đạt mục tiêu hôm nay"** → tạo áp lực tiêu cực, nhiều user bỏ app vì cảm giác bị phán xét. Ngôn ngữ và màu sắc nên trung lập, tập trung vào "còn thiếu bao nhiêu" chứ không phải "thất bại".
- **Biểu đồ nội suy (interpolate) qua khoảng trống dữ liệu** → trông như có dữ liệu liên tục trong khi thực ra thiết bị không đeo — gây hiểu nhầm nghiêm trọng nếu dữ liệu liên quan sức khoẻ.
- **Không nói rõ nguồn dữ liệu** (tự nhập tay vs từ cảm biến) khi hiển thị cùng 1 biểu đồ → độ tin cậy khác nhau nhưng trông như nhau.
- **Nhắc nhở dùng chuông báo động khẩn** cho việc không khẩn (nhắc uống nước) → gây "báo động giả" theo thời gian, user tắt hết thông báo kể cả cái quan trọng (nhắc thuốc).
- **Không cho sửa/xoá 1 lần ghi nhận sai** (lỡ nhập nhầm cân nặng) → dữ liệu sai kéo dài ảnh hưởng biểu đồ xu hướng mãi mãi.
- **Chia sẻ dữ liệu mặc định bật** thay vì opt-in rõ ràng — vi phạm kỳ vọng quyền riêng tư của domain nhạy cảm nhất trong toàn bộ danh sách domain.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Nguồn dữ liệu sức khoẻ:** iOS dùng HealthKit, Android dùng Health Connect — 2 hệ **khác nhau hoàn toàn** về model quyền (HealthKit xin quyền theo từng loại dữ liệu cụ thể qua 1 màn hệ thống; Health Connect có màn quản lý quyền tập trung riêng, không nằm trong Settings app). Layout onboarding kết nối phải tính 2 luồng khác nhau, không vẽ chung 1 màn "Cấp quyền" rồi coi là xong.
- **Thông báo nhắc nhở lặp lại:** giới hạn số lượng local notification đã lên lịch khác nhau giữa 2 nền tảng ở phiên bản cũ — với app nhắc nhiều lần/ngày cần nêu rõ cho `client-shell` kiểm tra giới hạn thật.
- **Đơn vị đo:** hiển thị theo locale hệ thống (kg/lb, cm/ft) — không hard-code 1 đơn vị.
- **Widget màn hình chính** (nếu có): cấu hình và kích thước khác nhau giữa WidgetKit (iOS) và App Widgets (Android) — không dùng chung 1 layout.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- Biểu đồ xu hướng **bắt buộc** có bảng số liệu hoặc tóm tắt bằng lời song song — biểu đồ trực quan gần như vô dụng với screen reader, và đây là dữ liệu quan trọng nhất của domain.
- Chỉ số sinh hiệu (nhịp tim, huyết áp) không được chỉ hiện bằng màu (xanh=tốt/đỏ=cảnh báo) — phải kèm nhãn chữ mô tả mức độ.
- Cỡ chữ cho số liệu chính phải hỗ trợ phóng to hệ thống tốt — người dùng lớn tuổi là nhóm dùng nhiều của domain này.
- Nút ghi nhận nhanh (log 1 ly nước, log cân nặng) cần tap target lớn hơn mức tối thiểu nếu là thao tác lặp lại nhiều lần/ngày.
