# design_patterns: education-learning

> Craft: bố cục / hierarchy / nhịp / motion cho app học. State bắt buộc, pitfall, quy ước platform, a11y → xem `skills/domain/education-learning/SKILL.md`, **không lặp ở đây**.

## 1. Bố cục màn hình chủ đạo

**Màn chủ (điểm vào)** — thứ tự dọc, quan trọng nhất trước:

| Dải | Chiếm | Nội dung |
|---|---|---|
| A | ≤10% viewport | Chào + streak strip **mảnh**. Streak là gia vị, không phải hero |
| B (hero) | 22–28% viewport | Card **"Bài kế tiếp"** full-width, có CTA. Toàn bộ lý do màn này tồn tại |
| C | 1 hàng/khoá | Tiến độ khoá đang học: thanh ngang + "3/12 bài" |
| D | dưới fold | Khoá / lộ trình khác, đề xuất |

**Chi tiết khoá:** header (ảnh + mô tả) 25–30% viewport → **mục lục chương/bài phải xuất hiện ngay trong màn đầu**, không nằm sau 1 trang mô tả dài.

**Nhịp danh sách bài:** nhóm theo chương, header chương sticky. Row bài cao **56–72dp**. Rail dọc bên trái nối các row cùng chương (củng cố cảm giác tuần tự) → nội dung indent **40–48dp** chừa chỗ cho rail. Khoảng giữa 2 chương ≈ **2×** khoảng giữa 2 row — nhịp này là thứ khiến 40 bài đọc được mà không thành 1 khối chữ.

**Màn quiz** (1 câu / 1 màn): [thanh tiến độ "4/10" mảnh, dính top] → [câu hỏi, 30–40% viewport, tối đa ~4 dòng] → [khối đáp án] → [nút xác nhận dính bottom]. Đáp án **luôn 1 cột** full-width (2 cột chỉ khi đáp án là ảnh hoặc ≤3 ký tự), cao ≥56dp, khoảng giữa các option 8–12dp — **nhỏ hơn rõ rệt** khoảng câu hỏi↔option đầu (≥24dp), để 4 option đọc thành 1 khối chứ 4 vật thể rời.

**Chart tiến độ tuần:** 7 bar, chiếm 30–35% viewport. Hẹp thì bỏ theo thứ tự: gridline → nhãn Y trung gian → nhãn X còn đầu/cuối/hôm nay; giảm dữ liệu là phương án cuối. **Ngày không học = bar khuyết viền nét đứt, không phải bar cao 0** (bar 0 đọc là "đã học 0 phút").

## 2. Hierarchy & emphasis

- **Primary duy nhất ở mọi state = 1 hành động học kế tiếp:** "Tiếp tục bài X" (home), "Xác nhận" (quiz), "Bài tiếp theo" (kết quả). Streak, điểm, huy hiệu **tối đa `secondary`** — chúng mô tả quá khứ, primary luôn thuộc về bước kế tiếp.
- Màn kết quả: điểm số **to** nhưng emphasis `secondary`; primary là "Xem giải thích" / "Tiếp tục". Số điểm không phải nút.
- `content_locked`: giảm contrast + icon + **1 dòng lý do**; giữ row trong list, không ẩn — thấy được cái đang chờ mình mới là động lực.
- `streak_broken`: số chuỗi về 1 và hiển thị **bình thường**; bù lại bằng cách đẩy khối "bài hôm nay" lên emphasis primary rõ hơn. An ủi bằng **bố cục** (đưa hành động tới trước mặt), không bằng copy.
- Tỉ lệ type: tên bài trong row ≈ **1.3–1.5×** meta (thời lượng); câu hỏi ≈ **1.2–1.3×** text đáp án (chênh vừa đủ để phân vai, không đủ để câu hỏi thành banner); điểm kết quả ≈ **2.5–3×** nhãn của nó.

## 3. Cấu trúc bên trong từng component chủ đạo

**Card "Bài kế tiếp"** (4 tầng): eyebrow tên khoá (nhỏ, 1 dòng, ellipsis) → tên bài (≤2 dòng rồi ellipsis, phần tử nặng nhất card) → meta row `thời lượng · loại nội dung · "còn 4:12"` → thanh tiến độ trong bài mảnh **2–4dp** ngay dưới meta (**không** dùng ring: ring hàm ý "chỉ số", thanh hàm ý "đoạn đường") → CTA full-width đáy card.

**Lesson row** (3 vùng ngang): [rail dot / số thứ tự / icon trạng thái 24dp] · [tên bài 1–2 dòng + meta 1 dòng] · [affordance phải: thời lượng, hoặc tick/ổ khoá]. Trạng thái mã hoá bằng dot: fill đặc = xong, viền + fill một phần = đang học, viền mảnh = chưa học, icon = khoá.

**Progress card khoá:** thanh ngang 4–8dp (M3) + nhãn "3/12 bài" cùng dòng bên phải; chỉ hiện % khi không có số bài đếm được; caption thời gian còn lại phía dưới. Nhiều khoá song song thì **thanh so sánh dễ hơn ring** — ring chỉ dành cho chỉ số đơn của ngày.

**Answer option:** container viền → [chỉ mục A/B/C hoặc radio 24dp] · [text option, **wrap tự do, không ellipsis** — cắt đáp án là làm sai bài]. Sau khi trả lời: thêm icon + nhãn chữ ("Đúng"/"Sai") **vào chính option đó**, giữ nguyên thứ tự, không reorder, không ẩn option sai.

**Result block:** [điểm/tỉ lệ] → [1 thanh ngang chia đúng/sai] → [list câu sai, mỗi câu 1 dòng lý do, tap để mở giải thích] → [CTA].

## 4. Interaction & motion

- **Fill tiến độ bài/khoá:** ease-out 300–500ms, chạy 1 lần ngay sau khi hoàn thành bài, tại chỗ user đang nhìn.
- **Đáp án đúng:** đổi trạng thái viền + icon fade-in ≤200ms + haptic nhẹ. **Sai: không shake, không rung mạnh, không âm báo tiêu cực** — chỉ đổi viền + icon + expand khối giải thích 200–250ms. Sai là dữ liệu học, không phải hình phạt.
- **Chuyển câu:** slide ngang 250–300ms theo hướng tiến (LTR: nội dung mới vào từ phải) — giữ được cảm giác đi tới; fade thì mất chiều.
- **Mở khoá bài mới:** 1 lần ≤600ms, ổ khoá → dot, kèm scroll nhẹ để bài mới vào giữa viewport. Không confetti.
- **Hoàn thành khoá / chứng chỉ:** đây là **điểm ăn mừng lớn duy nhất được phép** — full-screen, ≤2s, và nút bỏ qua có mặt ngay từ frame đầu.
- **Mất chuỗi: không animation nào.** Không đếm ngược, không rơi vỡ, không đỏ nhấp nháy.
- **Resume video:** hiện marker vị trí đã dừng trên timeline + nhãn thời gian *trước* khi play, không auto-seek im lặng.
- **Reduce-motion:** bỏ slide chuyển câu và unlock, đổi nội dung tức thì; giữ haptic + icon trạng thái.

## 5. Nguồn tham chiếu + ranh giới IP

- **Tier 1** — Material 3 *Progress indicators* (linear determinate cho tiến độ đã biết, track mặc định 4dp / biến thể dày 8dp, stop indicator cuối track), M3 list + touch target 48dp. Apple HIG *Charting data* / WWDC22 *Design an effective chart* (mật độ gridline & nhãn tuỳ mục đích; trend preview không cần trục; chart tương tác phải có trục + nhãn), HIG *Progress indicators* (dùng determinate khi biết thời lượng), tap target 44pt.
- **Tier 3** (ảnh store công khai): bố cục "hero bài kế tiếp đặt trên tường thống kê" là convention phổ biến của nhóm app học.
- **SUY ĐOÁN của tôi, chưa có tier 1–3 chống lưng** (đọc lại khi review): mọi con số % viewport ở mục 1; row 56–72dp; rail indent 40–48dp; nhịp 2× giữa 2 chương; quy tắc "đáp án luôn 1 cột"; các mốc timing ở mục 4; hướng slide theo chiều tiến; tỉ lệ type 1.2–1.3× giữa câu hỏi và đáp án.
- **KHÔNG trích:** hex màu thương hiệu, logo/wordmark, linh vật/illustration độc quyền, bộ icon riêng, copy nguyên văn, tên app cụ thể. Mô tả cấu trúc — không viết "làm giống \<app\>".

## 6. Thich ung kich thuoc man hinh

> Dien `components[].responsive` theo muc nay; co che va thu tu degrade chung o `agents/designer/skills/responsive_layout/SKILL.md`. Cac con so duoi thuoc dien **SUY DOAN** cua muc 5 tru khi ghi ro tier 1.

**Cot:** dap an quiz **luon 1 cot full-width o moi bac** (2 cot chi khi dap an la anh hoac <=3 ky tu — muc 1). Day la rang buoc **khong** duoc noi long khi man rong hon: `columns` `compact_small: 1, compact: 1, medium: 1`.

**Dap an KHONG BAO GIO ellipsis:** text dap an `wrap_behavior: "wrap"` + `text_overflow.max_lines: null` — cat dap an la lam sai bai. Va vi vay khoi chua dap an PHAI `min_height_dp: null` du muc 1 goi y >=56dp; 56dp la san, khong phai tran.

**Degrade trong row bai hoc:** thoi luong -> icon loai noi dung -> mo ta phu. **Khong bao gio**: ten bai va trang thai hoan thanh. Indent rail 40-48dp o `compact_small` ha ve 32dp, KHONG bo rail (rail la thu tao cam giac tuan tu).

**Card "Bai ke tiep" (hero, 22-28% viewport):** `sizing: fill` + `min_height_dp: null` — o co chu 200% ten bai dai 3 dong phai day card cao ra, khong duoc cat.

**Thanh tien do "4/10":** `pinned: true` + `safe_area: "top"`. Nut xac nhan dinh bottom: `pinned: true` + `safe_area: "bottom"`, va `keyboard_avoidance: "scroll_content"` voi cau hoi dang nhap dap an.

**Landscape / medium:** man chi tiet khoa chuyen header + muc luc thanh 2 cot (header trai, muc luc phai). Man quiz giu 1 cot o moi huong — 2 cot lam mat quan he cau hoi -> dap an.
