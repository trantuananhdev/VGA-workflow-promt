# design_patterns: fintech-payment

> Craft: bố cục/nhịp/motion. State bắt buộc, pitfall, a11y → `skills/domain/fintech-payment/SKILL.md`, không lặp ở đây.
> Nguyên tắc trùm craft: **số phải đọc được ở lần nhìn đầu, và mọi thứ liên quan tới tiền phải cảm giác đã-xong chứ không vui vẻ.**

## 1. Bố cục màn hình chủ đạo

- **Tổng quan số dư** — thứ tự dọc: khối số dư → hàng action ngang → danh sách giao dịch. Khối số dư chiếm ~25–30% viewport (đủ to để là điểm dừng mắt, không tràn màn). Hàng action 3–5 mục, icon-trên-nhãn, chia đều chiều ngang, cao ~72–88dp. Danh sách bắt đầu ở khoảng 60–65% chiều cao để **hé được 2–3 dòng** trên fold — đây là tín hiệu "có thể cuộn", không cần chevron.
- **Nhập số tiền** — đảo ngược mật độ: đúng **một** element ở trung tâm quang học (~30–35% trên), khoảng trắng lớn hai bên, bàn phím số chiếm 40–45% dưới, CTA nằm sát ngay trên bàn phím (không dính đáy màn — bàn phím đã ở đáy). Không nhồi thêm khối nào khác vào màn này.
- **Xem lại trước khi chuyển** — bảng key-value 1 cột: nhãn trái, giá trị phải căn phải. Phí là dòng riêng. Dòng tổng tách bằng khoảng trắng gấp đôi (padding-top ~2×) + 1 divider duy nhất trên nó; **không** tăng cỡ chữ của nhãn "Tổng", chỉ tăng của giá trị.
- **Danh sách giao dịch** — nhóm theo ngày bằng **sticky header** cao ~32–40dp; dòng 2 dòng (~72dp, đúng chuẩn two-line M3). Không kẻ divider giữa các dòng: nhịp do khoảng trắng + sticky header tạo ra, kẻ ngang trong danh sách dài chỉ thêm noise.
- **Kết quả** — trục dọc căn giữa: icon trạng thái → 1 dòng kết luận → số tiền → khối chi tiết (mã giao dịch copy được) → 1 CTA đóng luồng. Mã giao dịch đặt ở khối chi tiết, **không** nhét dưới CTA.
- Số nhiều bước (KYC, chuyển tiền) → progress dạng "bước i/n" dạng chữ ở header, không stepper vẽ đầy đủ (chiếm chiều cao mà không thêm thông tin trên mobile).

## 2. Hierarchy & emphasis

Quy tắc chốt: **`primary` thuộc về thông tin user phải xác minh, không thuộc về cái nút.** Nút giành chú ý bằng *diện tích + tương phản nền* (nút filled duy nhất trên màn), con số giành bằng *kích cỡ*. Nhờ vậy vẫn đúng 1 `primary` mà CTA không bị lẫn.

| Screen state | `primary` duy nhất | Bị demote xuống secondary/tertiary |
|---|---|---|
| Tổng quan | Con số số dư | Tên chủ tài khoản, banner khuyến mãi, hàng action, số tài khoản |
| Nhập số tiền | Số tiền đang nhập | Số dư khả dụng, chọn nguồn tiền, ghi chú |
| Xem lại | Dòng **tổng** phải trả | Người nhận, phí, nguồn tiền, tỉ giá |
| Xác thực | Ô nhập PIN / OTP | Số tiền (nhắc lại ở cỡ nhỏ), đường dự phòng |
| Kết quả | Icon + dòng kết luận | Số tiền, mã giao dịch, CTA |

**Legibility của số** — phần này quyết định app trông đắt hay rẻ:
- **Tabular figures (monospaced digits)** bắt buộc cho: mọi số nằm trong cột (danh sách giao dịch, bảng xem lại) và mọi số **tự cập nhật**. Chữ số proportional (mặc định của hệ) chỉ dùng cho **một** con số hero đứng riêng.
- Đơn vị tiền / ký hiệu: cỡ ~50–60% cỡ số, weight thấp hơn 1 bậc, baseline giữ nguyên — không superscript.
- Phần thập phân (khi tiền tệ có): cỡ ~70–75% phần nguyên hoặc cùng cỡ nhưng màu variant, baseline giữ nguyên. Tiền tệ **không** có phần thập phân (VND) → bỏ hẳn `,00`, đừng hiển thị số 0 vô nghĩa.
- Dấu `+`/`−` đứng **trước** số, **cùng cỡ** với số (nhỏ hơn là mất tín hiệu quan trọng nhất của dòng).
- Cột số tiền có chiều rộng cố định, căn phải; cột mô tả căn trái, co giãn. Hàng nghìn phải thẳng cột giữa các dòng — đây là lý do cần tabular.
- Dấu phân cách chèn **ngay khi đang gõ**, không chờ blur.

## 3. Cấu trúc bên trong từng component chủ đạo

- **Khối số dư:** (a) nhãn nhỏ trên, cỡ nhỏ nhất màn, màu variant, không uppercase; (b) số dư — 1 dòng, weight cao nhất màn; (c) nút mắt ẩn/hiện: icon 24dp trong hit target 48dp, cách số 8–12dp, **hit target riêng**, không nằm trong tap area của cả khối; (d) dòng phụ (••••4 số cuối) cỡ nhỏ nhất, màu variant. Khi ẩn → thay bằng chuỗi dot **cùng chiều rộng** để layout không giật.
- **Dòng giao dịch** (~72dp, padding ngang 16, dọc 8–12): *leading* icon/avatar 40dp tròn — bỏ hẳn nếu danh sách dài thuần chuyển khoản, để giảm noise. *Cột giữa* (co giãn): dòng 1 tên đối tác, weight medium, 1 dòng, ellipsis **giữa** nếu là số tài khoản (đuôi mới là phần nhận diện); dòng 2 loại + giờ, cỡ ~80–85% dòng 1, màu variant. *Cột phải* (rộng cố định): dòng 1 số tiền có dấu, tabular, weight cao nhất trong dòng, căn phải; dòng 2 **chỉ xuất hiện khi trạng thái ≠ thành công** — thành công là mặc định nên im lặng, mỗi dòng có nhãn "Thành công" là mỗi dòng thêm noise.
- **Ô nhập số tiền:** 1 dòng duy nhất, caret nhìn thấy, đơn vị là prefix/suffix **cố định chỗ** (không trôi khi số dài ra). Số dài → **auto-shrink theo bậc** (ví dụ 48→40→32sp) chứ không wrap, không ellipsis. Dưới nó **đúng 1 dòng helper**, dùng chung chỗ cho cả 3 nội dung (số dư khả dụng / vượt số dư / vượt hạn mức) — không stack nhiều dòng làm layout nhảy.
- **Dòng key-value (xem lại/chi tiết):** nhãn ~40% trái không đậm, giá trị ~60% phải căn phải và đậm hơn nhãn 1 bậc. Giá trị dài (tên người nhận) wrap sang dòng 2 vẫn căn phải, nhãn giữ ở dòng đầu.
- **Ô OTP:** **một** field duy nhất hỗ trợ autofill, tách nhóm chữ số bằng letter-spacing rộng + underline nền — không phải 6 view rời.
- **Bàn phím số tự tạo:** lưới 3×4, ô cao ≥48dp, chữ số cỡ lớn weight regular (không bold — bold ở đây cạnh tranh với số tiền), nút xoá là icon ở ô cuối phải, ô cuối trái là dấu thập phân hoặc để trống.

## 4. Interaction & motion

- **Ngân sách thời lượng ngắn:** 100ms cho state của ô/nút/toggle; 250–300ms cho chuyển màn; easing standard hoặc emphasized-decelerate khi vào. **Không** spring, không overshoot, không bounce ở bất kỳ điểm nào trên đường đi của tiền — nảy = không chắc chắn.
- **Số dư và số tiền KHÔNG được count-up/roll.** Xuất hiện đúng giá trị ngay, chỉ crossfade 100ms từ skeleton. Đếm số làm user không biết con số nào là con số thật.
- **CTA xác nhận:** disable **ngay ở lần nhấn đầu**, chuyển loading **tại chỗ** — giữ nguyên chiều rộng/chiều cao, thay label bằng indicator. Không ripple lan ra ngoài viền nút.
- **`pending`:** chỉ indicator vô hạn (indeterminate) + text. Tuyệt đối không progress bar có % — % giả ngụ ý hệ thống biết còn bao lâu.
- **Kết quả thành công:** không confetti, không animation ăn mừng. Icon check vẽ trong ≤200ms rồi **dừng hẳn**, màn giữ tĩnh để user đọc và copy mã giao dịch. Đây là chỗ sai phổ biến nhất của domain.
- **Ẩn/hiện số dư:** crossfade 100ms. Không animate blur (tốn GPU, và có frame nhìn thấy được số).
- **Bàn phím tự tạo:** hiện tức thì, không slide; haptic light mỗi phím; nhấn giữ nút xoá → xoá lặp sau delay ~500ms rồi ~60ms/ký tự.
- **Chuyển giữa các bước luồng chuyển tiền:** slide ngang, hướng nhất quán (tiến sang trái), 250–300ms; back bằng gesture cho phép ở mọi bước **trừ** sau khi xác thực đã xong.
- **Reduced motion:** thay toàn bộ slide bằng crossfade 100ms; giữ nguyên haptic.

## 5. Nguồn tham chiếu + ranh giới IP

**Tier 1 (chống lưng trực tiếp):** M3 Lists — chiều cao dòng 56/72/88dp theo số dòng text, divider dùng để tách **nhóm** chứ không tách từng dòng. M3 Easing & duration tokens — short2 ≈ 100ms cho đổi state nhỏ, medium2 ≈ 300ms cho chuyển lớn, emphasized-decelerate cho phần tử đi vào. M3 Text field — một nhãn + **một** dòng supporting text, error thay chỗ supporting text (cơ sở cho quy tắc "đúng 1 dòng helper"). Apple HIG Typography — chữ số mặc định là proportional, dùng monospaced digits khi số **thay đổi** hoặc cần **thẳng cột**. Apple HIG Entering data — giảm tối đa field, cho chọn thay vì gõ, có default hợp lý. Touch target ≥48dp (M3) / 44pt (HIG).

**Tier 3:** ảnh store công khai của app ví/ngân hàng — dùng để xác nhận rằng thứ tự *số dư trên → hàng action → hé danh sách giao dịch* là convention phổ biến, không phải phát minh riêng.

**SUY ĐOÁN của file này (chưa có tier 1–3 chống lưng, cần người review):** quy tắc "`primary` thuộc thông tin cần xác minh, không thuộc nút"; mọi con số % viewport (25–30%, 30–35%, 40–45%, 60–65%); bậc auto-shrink 48→40→32sp; tỉ lệ 70–75% cho phần thập phân và 50–60% cho ký hiệu tiền; bỏ hẳn divider trong danh sách giao dịch; cấm count-up cho số dư; cấm animation ăn mừng ở màn thành công; ẩn nhãn trạng thái khi giao dịch thành công. Tất cả suy ra từ nguyên tắc "thao tác không hoàn tác được" của domain — hợp lý nhưng **không** phải điều khoản có sẵn trong M3/HIG.

**Ranh giới IP:** chỉ lấy cấu trúc, thứ tự, tỉ lệ, nhịp. Không hex màu thương hiệu, không logo/wordmark, không bộ icon độc quyền, không copy nguyên văn. Màu chỉ mô tả ở dạng quan hệ ("đúng 1 nút filled trên màn, tương phản mạnh trên surface trầm"); giá trị thật do `tokens.json` của project sinh.

## 6. Thich ung kich thuoc man hinh

> Dien `components[].responsive` theo muc nay; co che va thu tu degrade chung o `agents/designer/skills/responsive_layout/SKILL.md`. Cac con so duoi thuoc dien **SUY DOAN** cua muc 5 tru khi ghi ro tier 1.

**Cot:** hang action duoi so du `axis: horizontal` + `columns` `compact_small` **3** / `compact` 4-5 (5 muc tren 320dp thi moi muc ~60dp, nhan bi cat) — muc vuot bo vao sheet "Tat ca", khong thu nho nhan. Ban phim so luon **grid 3x4**, o >=48dp o moi bac; day la lop duy nhat KHONG duoc wrap/shrink.

**Khoi so du:** `min_height_dp: null` (~25-30% viewport la goi y, khong phai khoa). Chuoi dau che so du phai **cung be rong** voi so that o moi co chu — neu khong layout nhay khi bat/tat che.

**Degrade trong dong giao dich:** timestamp tuong doi -> icon danh muc -> nhan phu (ten nguoi nhan rut gon **ellipsis GIUA** voi so tai khoan, khong cat duoi). **Khong bao gio**: so tien va dau +/-.

**Man nhap so tien:** CTA nam sat **tren ban phim**, nen `responsive_declared.keyboard_avoidance: "pin_cta_above_keyboard"` — khong `pinned` vao day man (ban phim da o day). Bang key-value man "Xem lai" o co chu 200%: nhan va gia tri chong nhau -> `wrap_behavior: "stack_vertical"` (nhan tren, gia tri duoi) thay vi cho gia tri co lai.

**Landscape / medium:** ban phim so chiem 40-45% chieu cao la khong kha thi o landscape — o huong nay chuyen sang layout 2 cot (so tien trai, ban phim phai). Neu app pin portrait thi khai `orientations: ["portrait"]` va bo qua muc nay.
