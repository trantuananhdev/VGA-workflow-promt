# design_patterns: productivity-tools

> Craft: bố cục/nhịp/motion. State bắt buộc, pitfall, a11y → `skills/domain/productivity-tools/SKILL.md`, không lặp ở đây.
> Nguyên tắc trùm craft: **mật độ cao nhưng ít tín hiệu**. Domain này user nhìn cùng 1 danh sách 20 lần/ngày — mỗi chi tiết trang trí lặp lại 30 dòng sẽ thành nhiễu. Ngược với fintech: ở đây **tốc độ nhập** và **quét mắt** thắng, không phải sự long trọng.

## 1. Bố cục màn hình chủ đạo

- **Danh sách chính** — không có hero, không có khối tóm tắt to. Thứ tự: header (title lớn, co lại thành title nhỏ khi cuộn) → hàng chip lọc/chế độ xem cuộn ngang cao ~32–40dp → danh sách bắt đầu ngay. Dòng nội dung dày: 1 dòng ~48–56dp, 2 dòng ~72dp. FAB/nút tạo neo góc phải dưới, cách biên 16.
- **Quick add** — bottom sheet chiếm **≤40%** chiều cao, không bao giờ full screen. Cấu trúc: 1 field text tự focus ở trên → **một hàng ngang** icon tuỳ chọn (hạn / nhãn / ưu tiên / dự án) nằm **ngay trên bàn phím** → nút lưu ở cuối hàng đó. Tổng: 1 field bắt buộc, mọi thứ khác là 1 tap tuỳ ý.
- **Chi tiết mục việc** — 3 tầng progressive disclosure: (1) luôn hiện: title (là field editable inline, không phải label), trạng thái, hạn; (2) 1 tap: nhãn, ưu tiên, dự án, người được giao, nhắc nhở; (3) sau "Thêm tuỳ chọn": lặp lại, phụ thuộc, ước lượng thời gian, trường tuỳ chỉnh. Dưới cùng: mô tả / checklist / đính kèm / hoạt động. Không có nút "Lưu".
- **Kanban** — cột rộng ~80–85% viewport để cột kế tiếp **hé ~12–15%**: đó là tín hiệu "còn cột nữa" đúng và rẻ nhất. Header cột sticky, có số đếm. Khoảng cách giữa 2 cột **lớn hơn** khoảng cách giữa 2 card trong cột (ví dụ 12 vs 8) — nhờ vậy mắt tách cột trước khi tách card.
- **Lịch** — lưới tháng ~45–55% trên, danh sách của ngày đang chọn ở dưới, biên kéo được để đổi tỉ lệ. Ngày có việc đánh dấu bằng **1** dot nhỏ, không phải số đếm nhồi trong ô.
- **Tìm kiếm toàn cục** — field ở đỉnh, gợi ý gần đây trước khi gõ, kết quả nhóm theo loại (mục việc / ghi chú / dự án) với section header, mỗi nhóm hiện tối đa 3 rồi "Xem tất cả".

## 2. Hierarchy & emphasis

Quy tắc chốt: ở màn danh sách, `primary` là **nội dung do user tạo** (dòng title), không phải checkbox, không phải FAB, không phải chip lọc. Chrome của app phải lùi hết về sau.

| Screen state | `primary` duy nhất | Bị demote |
|---|---|---|
| Danh sách | Title của mục (trong từng dòng) | Checkbox, chip nhãn, hạn, avatar, FAB, chip lọc |
| Quick add | Field text đang nhập | Toàn bộ hàng icon tuỳ chọn, nút lưu |
| Chi tiết | Title editable | Mọi dòng thuộc tính, mô tả, đính kèm |
| Kanban | Title card | Header cột, số đếm, footer card |
| Bulk select | Dòng "Đã chọn N" | Các action icon, nội dung các mục |

**Làm số đếm dominant mà không hét:** đặt số **trong** nhãn nhóm / header cột, cùng cỡ chữ với nhãn nhưng weight cao hơn 1 bậc và màu on-surface đầy trong khi nhãn là màu variant. Đó là đủ. **Badge tròn có màu nền là ngân sách hữu hạn: tối đa 1 loại badge màu trên toàn màn**, và chỉ dành cho số cần hành động (quá hạn), không dành cho tổng số việc.

**Kỷ luật giảm nhiễu (áp cho mọi dòng danh sách):**
- Tối đa **3 vùng thông tin** mỗi dòng: leading / nội dung / trailing. Cần vùng thứ 4 → cắt bớt, đừng nhồi.
- Tối đa **2 chip metadata** hiển thị, phần còn lại gộp thành "+N".
- Ưu tiên mã hoá bằng **đúng 1 chỉ dấu** (thanh dọc 3–4dp cạnh trái dòng, **hoặc** chip chữ) — không dùng đồng thời màu chữ + icon + nền.
- Trong 1 dòng, chỉ **một** thứ được phép đổi màu khỏi thang xám: hạn đã quá. Không phải nhãn, không phải dự án.
- Mục đã hoàn thành: giảm opacity ~50–60% + gạch ngang **chỉ title** (không gạch metadata). Không ẩn ngay.
- Checkbox chưa xong: viền mảnh, nền trong suốt — tô đầy màu là hét vào 30 dòng cùng lúc.

## 3. Cấu trúc bên trong từng component chủ đạo

- **Dòng task:** *leading* checkbox 20–24dp trong hit target ≥48dp, cách biên trái 16. *Nội dung* (co giãn): dòng 1 title weight medium, 1 dòng, ellipsis cuối; dòng 2 metadata theo thứ tự cố định — hạn trước, rồi ≤2 chip — cỡ ~78–82% dòng 1, màu variant. *Trailing*: avatar 24dp **hoặc** handle kéo 24dp, không bao giờ cả hai. Thụt lề subtask: 1 bậc = rộng checkbox + gap (~32–40dp), chỉ hiển thị tối đa 2 bậc, sâu hơn thì gộp.
- **Card kanban:** ảnh cover (nếu có) 16:9 trên cùng, ≤35% chiều cao card; title tối đa 2 dòng; footer **1 dòng** chứa ≤3 signal (hạn, avatar, đếm checklist "3/5"). Padding trong card 12, gap giữa card 8.
- **Section / column header:** nhãn + số đếm cùng hàng (số ngay sau nhãn, cách 8, hoặc căn phải), chevron collapse 20dp cạnh trái nhãn. Cao ~36–40dp — **thấp hơn** dòng nội dung, để header không cạnh tranh với dữ liệu.
- **Dòng thuộc tính trong màn chi tiết:** dùng idiom **nhãn trái / giá trị phải + chevron** (kiểu hàng Settings của iOS), **không** dùng label-nổi-trên-field. Lý do: màn chi tiết có 6–8 thuộc tính, label-trên-field làm mỗi thuộc tính tốn gấp đôi chiều cao và ép user cuộn để thấy hết. Chỉ field gõ tự do dài (title, mô tả) mới dùng floating label / editable inline.
- **Nhóm field:** tối đa 4–5 field/nhóm, tách nhóm bằng khoảng trắng ~24dp + nhãn nhóm cỡ nhỏ màu variant; divider full-width **chỉ** giữa các nhóm, không giữa các field trong nhóm.
- **Thanh bulk-select:** neo đáy, trái là "Đã chọn N", phải là ≤4 icon action + "…" cho phần còn lại; header đổi thành "Huỷ" / "Chọn tất cả". Action phá huỷ đặt **xa nhất** khỏi ngón tay cầm máy.
- **Chỉ báo đồng bộ:** đúng 1 chỗ duy nhất trong header, 3 hình thái **khác hình dạng** (đã đồng bộ / đang chờ / lỗi), không chỉ đổi màu cùng 1 icon.
- **Empty state:** illustration ≤25% chiều cao, 1 câu, đúng 1 nút — và nút đó trùng hành động với FAB (không dạy user 2 đường vào khác nhau cho cùng việc).

## 4. Interaction & motion

- Domain này **được phép** sinh động, nhưng chỉ ở phản hồi thao tác nhỏ, không ở chuyển màn.
- **Tick hoàn thành:** phản hồi thị giác ≤100ms + haptic light; checkmark vẽ trong ~150ms. Dòng chỉ fade + collapse **sau delay 250–400ms** (hoặc chờ tới lần refresh danh sách kế tiếp) — biến mất tức thì làm user tưởng vừa mất dữ liệu.
- **Undo:** snackbar trồi lên từ đáy 200ms, tồn tại 5–7s, **đẩy FAB lên** thay vì đè lên FAB.
- **Kéo-thả:** nhấn giữ 150–200ms → card nâng lên (tăng elevation + scale 1.02–1.03) + haptic; ô trống placeholder co giãn 200ms easing emphasized; thả → 250–300ms decelerate về vị trí; auto-scroll khi ngón kéo vào ~15% biên trên/dưới.
- **Quick add:** sheet lên 250–300ms emphasized-decelerate, field focus + bàn phím bật **cùng lúc** với animation (không chờ sheet xong). Sau khi lưu: sheet **giữ mở**, xoá field, giữ nguyên context nhóm/ngày đang chọn — vì đây là thao tác lặp liên tiếp.
- **Autosave:** không toast, không dialog cho mỗi lần lưu. Chỉ 1 trạng thái mờ ở header đổi trong 100ms.
- **Swipe action trên dòng:** hé action ở ~25% chiều rộng, commit ở ~50%; icon + nhãn lộ dần theo khoảng kéo. Hành động phá huỷ phải cần commit toàn phần **và** có undo.
- **Đổi chế độ xem (list ↔ kanban ↔ lịch):** crossfade 150–200ms tại chỗ. **Không** slide ngang — slide ngang phải giữ riêng cho điều hướng tab/cấp, dùng lẫn thì user mất mô hình không gian.
- **Chip lọc:** áp dụng **ngay khi tap**, không có nút "Áp dụng"; danh sách reflow bằng fade 150ms chứ không animate từng dòng bay chỗ.
- **Reduced motion:** bỏ scale + elevation khi kéo (giữ haptic và placeholder), bỏ collapse (biến mất tức thì), thay mọi slide bằng crossfade.

## 5. Nguồn tham chiếu + ranh giới IP

**Tier 1 (chống lưng trực tiếp):** M3 Lists — chiều cao dòng 56/72/88dp theo số dòng text; divider tách **nhóm**, không tách từng dòng. M3 Easing & duration tokens — short2 ≈ 100ms cho đổi state nhỏ, medium2 ≈ 300ms cho chuyển lớn, emphasized-decelerate cho phần tử đi vào, emphasized cho phần tử đổi kích thước. M3 Snackbar — nổi trên nội dung, **đẩy** FAB thay vì che, tồn tại ngắn có 1 action. M3 Text field — floating label dành cho field gõ tự do. Apple HIG Entering data — giảm tối đa số field bắt buộc, cho chọn thay vì gõ, luôn có default hợp lý (cơ sở của thiết kế quick add 1-field). Apple HIG idiom hàng Settings (nhãn trái / giá trị phải / chevron) — nguồn của cấu trúc dòng thuộc tính ở mục 3. Touch target ≥48dp (M3) / 44pt (HIG).

**Tier 3:** ảnh store công khai của app to-do/note — xác nhận rằng *danh sách dày, không hero, FAB góc phải dưới, quick add dạng sheet* là convention phổ biến của domain.

**SUY ĐOÁN của file này (chưa có tier 1–3 chống lưng, cần người review):** mọi con số % viewport (≤40% sheet, 80–85% cột kanban + hé 12–15%, 45–55% lưới tháng, ≤35% ảnh cover, ≤25% illustration); quy tắc "gap giữa cột > gap giữa card"; delay 250–400ms trước khi collapse dòng vừa tick; "tối đa 3 vùng thông tin / 2 chip + N mỗi dòng"; "tối đa 1 loại badge màu mỗi màn"; "chỉ hạn quá hạn được đổi màu trong 1 dòng"; giữ quick-add sheet mở sau khi lưu; header nhóm thấp hơn dòng nội dung; cấm slide ngang khi đổi chế độ xem. Đây là suy luận từ nguyên tắc "mật độ cao nhưng ít tín hiệu", không phải điều khoản có sẵn trong M3/HIG.

**Ranh giới IP:** chỉ lấy cấu trúc, thứ tự, tỉ lệ, nhịp. Không hex màu thương hiệu, không logo/wordmark, không bộ icon hay illustration độc quyền, không copy nguyên văn. Màu chỉ mô tả ở dạng quan hệ ("thang xám cho metadata, đúng 1 accent cho trạng thái cần hành động"); giá trị thật do `tokens.json` của project sinh.
