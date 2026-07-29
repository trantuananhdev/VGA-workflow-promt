# domain: fintech-payment

> Ví điện tử, chuyển tiền, thẻ, vay/trả góp, đầu tư, theo dõi chi tiêu.
> Dấu hiệu nhận biết trong PRD: có **số dư**, có **giao dịch không thể hoàn tác**, có **xác thực bổ sung** (OTP/sinh trắc học/PIN), có yêu cầu **KYC**.

**Nguyên tắc trùm cả domain:** đây là domain duy nhất mà **thao tác không thể hoàn tác được là chuyện thường**. Vì vậy mọi pattern đều nghiêng về *xác nhận rõ ràng trước khi làm* thay vì *cho phép hoàn tác sau*. Áp mẫu "undo thay vì confirm" của các domain khác vào đây là sai.

## 1. Màn hình / pattern chuẩn

| Màn | Vai trò | Ghi chú layout |
|---|---|---|
| Tổng quan số dư | Điểm vào | Số dư + **nút ẩn/hiện số dư** (dùng ở nơi công cộng). Không auto-hiện nếu PRD không nói rõ |
| Danh sách giao dịch | Tra cứu | Nhóm theo ngày; mỗi dòng: bên đối tác, số tiền có dấu +/−, trạng thái |
| Chi tiết giao dịch | Đối chiếu | **Mã giao dịch copy được** — đây là thứ user cần khi khiếu nại |
| Nhập số tiền | Bắt đầu luồng | Bàn phím số riêng, hiển thị số tiền đang nhập rất lớn; kiểm tra vượt số dư **ngay khi nhập** |
| Chọn người nhận / nguồn tiền | Trước xác nhận | Hiển thị đủ để nhận diện (tên + 4 số cuối), không chỉ số tài khoản trần |
| **Xem lại trước khi chuyển** | Bắt buộc, màn riêng | Số tiền + người nhận + phí, **tách dòng**. Đây là điểm dừng cuối |
| Xác thực (PIN/sinh trắc/OTP) | Bảo mật | Màn riêng, có đường đi khi sinh trắc học thất bại |
| Kết quả | Đóng luồng | 3 kết cục khác nhau: thành công / thất bại / **đang xử lý** |
| KYC | Mở tính năng | Nhiều bước, phải cho **lưu nháp và quay lại** |

## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)

- `insufficient_funds` — kiểm **ngay khi nhập**, không chờ tới lúc xác nhận.
- `limit_exceeded` — vượt hạn mức ngày/giao dịch. Khác `insufficient_funds`, phải nói rõ hạn mức là bao nhiêu và khi nào reset.
- `pending` / `processing` — giao dịch **chưa biết kết quả**. State nguy hiểm nhất của domain: nút "Thử lại" ở đây có thể gây chuyển tiền 2 lần → phải **chặn** thao tác lại, chỉ cho xem/làm mới.
- `failed_retryable` vs `failed_final` — 2 state khác nhau: một cái cho thử lại, một cái không.
- `auth_required` / `auth_failed` / `auth_locked` — sinh trắc học thất bại, PIN sai, và bị khoá sau N lần. Cả 3 đều thường xảy ra thật.
- `otp_expired` / `otp_wrong` / `otp_resend_cooldown` — 3 lý do khác nhau, không gộp thành "OTP không hợp lệ".
- `session_expired` — phiên hết hạn **giữa** luồng chuyển tiền. Phải giữ lại dữ liệu đã nhập sau khi đăng nhập lại, hoặc nói rõ là mất.
- `kyc_required` / `kyc_pending_review` / `kyc_rejected` — chưa làm / đang chờ duyệt / bị từ chối (kèm lý do và cách sửa).
- `account_frozen` — tài khoản bị khoá bởi phía hệ thống.
- `balance_stale` — không lấy được số dư mới nhất. **Không** được hiện số dư cũ như thể là mới.

PRD từ brief thô gần như luôn thiếu `pending`, `auth_locked`, `session_expired` giữa luồng, và việc tách `failed_retryable`/`failed_final`. Thấy thiếu → **hỏi `ba`**.

## 3. Pitfall UX riêng domain này

- **Cho "Thử lại" ở state `pending`** → chuyển tiền 2 lần. Đây là lỗi tốn tiền thật, không phải lỗi thẩm mỹ. Ở `pending` chỉ được có: xem chi tiết, làm mới trạng thái, liên hệ hỗ trợ.
- **Không có màn xem lại riêng** trước khi chuyển (gộp vào màn nhập số tiền) → chuyển sai người/sai số. Màn xem lại là bắt buộc, không phải tuỳ chọn.
- **Số tiền hiển thị không có định dạng phân cách** → user nhập 10.000.000 tưởng 1.000.000. Định dạng ngay khi đang nhập.
- **Phí ẩn trong tổng** → mất tin cậy tức thì. Phí luôn là 1 dòng riêng, kể cả khi bằng 0 (ghi "Miễn phí").
- **Số dư luôn hiện mặc định** → user không dám mở app ở chỗ đông. Cần nút ẩn/hiện và nhớ lựa chọn.
- **Mã giao dịch không copy được** → user phải chụp màn hình khi khiếu nại.
- **Sinh trắc học là đường duy nhất** → điện thoại lỗi cảm biến là mất truy cập hoàn toàn. Luôn có đường dự phòng bằng PIN.
- **Empty state "chưa có giao dịch" giống hệt state lỗi tải** → user không biết là chưa có hay là app lỗi. Phải khác nhau rõ.
- **Danh sách giao dịch không phân biệt tiền vào/ra bằng gì ngoài màu** → xem mục 5.

## 4. Quy ước platform (chỉ chỗ iOS và Android KHÁC nhau)

- **Sinh trắc học:** iOS Face ID / Touch ID có dialog hệ thống với văn bản do app cấp; Android BiometricPrompt khác về hình dạng và cho phép fallback thiết bị. Layout phải chừa chỗ cho state "đang chờ dialog hệ thống", không tự vẽ dialog sinh trắc.
- **Ảnh chụp màn hình:** iOS không chặn được, Android chặn được bằng `FLAG_SECURE`. Nếu PRD yêu cầu chặn chụp màn hình ở màn số dư thì hành vi 2 nền tảng **khác nhau** — nêu rõ, đừng để `mobile-screen` tự quyết.
- **Autofill OTP:** iOS tự điền OTP từ SMS ở ô `oneTimeCode`; Android qua SMS Retriever API. Ô OTP phải là 1 field hỗ trợ autofill, **không** phải 6 ô rời rạc (6 ô rời làm autofill hỏng ở cả 2 nền tảng).
- **Bàn phím số:** iOS `decimalPad` không có nút xoá riêng như một số bàn phím Android — nút xoá phải nằm trong UI của app nếu thiết kế bàn phím tự tạo.

## 5. Accessibility đặc thù (ngoài `a11y_contract` nền)

- **Tiền vào/ra không được chỉ phân biệt bằng màu** xanh/đỏ. Phải có dấu `+`/`−` **và** nhãn đọc được ("nhận 500.000 đồng" / "chuyển 500.000 đồng"). Đây là ràng buộc cứng: mù màu đỏ-xanh là dạng phổ biến nhất, và đây là dữ liệu tài chính.
- Số tiền phải được screen reader đọc thành **đơn vị**, không đọc từng chữ số ("năm trăm nghìn đồng", không phải "năm không không không không không").
- Ô nhập PIN phải đọc được số ký tự đã nhập mà **không** đọc ra giá trị.
- State `pending` phải được thông báo cho screen reader ngay khi xuất hiện (live region) — user không thấy được vòng xoay.
- Không dùng thời gian giới hạn quá ngắn cho OTP mà không cho gia hạn: user dùng screen reader cần nhiều thời gian hơn.
