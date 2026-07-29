# design_patterns: health-fitness

> Craft: bố cục / hierarchy / nhịp / motion cho app theo dõi sức khoẻ. State bắt buộc, pitpall pháp lý, a11y → xem `skills/domain/health-fitness/SKILL.md`, **không lặp ở đây**.

## 1. Bố cục màn hình chủ đạo

**Màn "Hôm nay" (điểm vào)** — 5 dải theo thứ tự dọc:

| Dải | Chiếm | Nội dung |
|---|---|---|
| A | ~8% viewport | Chọn ngày / khoảng thời gian. Mảnh, không cạnh tranh với hero |
| B (hero) | 30–38% viewport | **ĐÚNG 1** chỉ số chủ: ring tiến độ hoặc số lớn + thanh ngang |
| C | tự nhiên, **trên fold** | "Hành động kế tiếp duy nhất hôm nay" — 1 khối full-width |
| D | grid 2 cột | Tường chỉ số phụ, mỗi ô cao ≈ 1/3 hero |
| E | dưới fold | Xu hướng tuần + streak |

Ring hero đường kính **40–48% chiều rộng màn**: nhỏ hơn ~30% thì số ở tâm hết đọc được → đổi sang thanh ngang với số đặt **ngoài** thanh. Không bao giờ xếp 2 ring ngang hàng cùng cỡ: 2 ring bằng nhau = không có hero.

**Màn xu hướng:** segmented range dính top → **tóm tắt bằng lời + delta so kỳ trước đặt NGAY TRÊN chart** (đọc trước khi nhìn) → plot 45–55% viewport, tối thiểu ~200dp → trục X → chú thích khoảng trống + nguồn dữ liệu.

**Chart ở bề rộng điện thoại** (~360dp khả dụng): tối đa 5–7 nhãn trục X. Thứ tự **bỏ khi hẹp**: (1) gridline phụ → (2) nhãn trục Y trung gian, giữ min/max → (3) nhãn X còn đầu · cuối · hôm nay → (4) *cuối cùng mới* giảm mật độ điểm dữ liệu. Không bao giờ giảm dữ liệu trước khi giảm nhãn. Sparkline trong ô tile thì bỏ **hết** trục và gridline; ngược lại chart có scrub tương tác thì **bắt buộc** có trục + nhãn (HIG).

**Khoảng trống dữ liệu:** line → ngắt nét, dải gap nền sọc mờ; bar → ô viền nét đứt cao bằng khung plot, **không** bar cao 0 (bar 0 đọc là "đã đo, kết quả bằng 0"). Kèm 1 dòng caption dưới chart.

## 2. Hierarchy & emphasis

- **Primary duy nhất = hành động kế tiếp** (ghi nhận / bắt đầu buổi tập), **không** phải tường số. Hero ring lớn về *diện tích* nhưng emphasis chỉ `secondary` — nó là thông tin, không phải điểm tap.
- State "đang trong buổi tập" → primary chuyển sang Tạm dừng/Kết thúc; hero số liệu real-time vẫn secondary.
- Tỉ lệ type: số hero ≈ **2.5–3×** nhãn của nó; số trong tile phụ ≈ **1.4–1.6×** nhãn tile; đơn vị đo ≈ **50–60%** cỡ số, cùng baseline.
- **Thiếu so với mục tiêu** biểu đạt bằng *hình học*: ring chưa đóng + caption "còn X" dùng **cùng hue accent ở tint nhạt hơn**. Đã đạt: ring đóng kín + tick nhỏ. Khác biệt đạt/chưa = **độ đầy + nhãn chữ**, không phải đổi màu.
- Đúng **1 accent** toàn app. Nguồn dữ liệu (nhập tay vs cảm biến) phân biệt bằng pattern/viền/icon nhỏ, tuyệt đối không tiêu thêm 1 accent thứ 2.

## 3. Cấu trúc bên trong từng component chủ đạo

**Ring card** (5 phần, từ ngoài vào): track dày **8–12% đường kính** đầu tròn → arc active cùng độ dày → số ở *optical center* (dịch lên nếu có nhãn dưới) → nhãn đơn vị cách số 2–4dp → caption "còn X / mục tiêu Y" cách nhãn ≥ **1.5×** khoảng số↔nhãn. Padding trong card ≥16dp; **khoảng giữa 2 card > padding trong card**.

**Metric tile:** nhãn (nhỏ, 1 dòng, không wrap) + delta badge cùng dòng bên phải → số + đơn vị → sparkline chiếm **30–35%** chiều cao tile, full-width tile, không trục.

**Chart block:** [range control] / [tóm tắt lời + delta] / [plot 60–70% chiều cao block] / [trục X] / [caption gap + nguồn].

**Streak block:** 7 ô ngày đều nhau của tuần hiện tại; ô hôm nay có ring viền; ô đạt = fill đặc; ô chưa đạt = **viền mảnh** (không dấu X, không xám "chết"). Số chuỗi đặt *trên* hàng ô, cỡ ≈ số hero / 1.5. Huy hiệu chưa đạt hiển thị dạng **outline + vòng tiến độ đang chạy**, không dạng ổ khoá.

**Quick-log row:** [−] [giá trị + đơn vị] [+], tap target ≥48dp (M3) / 44pt (HIG); thao tác lặp nhiều lần/ngày → ≥56dp.

## 4. Interaction & motion

- **Fill tiến độ:** ease-out 400–600ms từ giá trị cũ → mới, chạy **1 lần** khi khối vào viewport lần đầu; không loop, không chạy lại mỗi lần scroll ngang qua.
- **Đạt mục tiêu:** đúng 1 lần, ≤800ms — ring scale 1.0 → 1.04 → 1.0 + haptic success. Không confetti toàn màn, không âm thanh mặc định. Ăn mừng lớn để dành cho mốc thật (chuỗi dài, hoàn thành chương trình), không cho mỗi ngày.
- **Chưa đạt: không có motion nào.** Không pulse, không rung, không lắc để "nhắc".
- **Scrub chart:** kéo ngang → dot + tooltip đi theo ngón, tooltip đặt **phía trên** ngón (ngón che phía dưới), haptic nhẹ khi vượt mốc. Đổi khoảng thời gian: cross-fade dữ liệu + morph trục 200–300ms, không slide cả chart.
- **Ghi nhận nhanh:** cập nhật lạc quan ngay + snackbar hoàn tác 5s. Sync lỗi thì gắn badge "chưa đồng bộ" lên chính record, không rollback im lặng.
- **Reduce-motion:** bỏ animation fill, hiện thẳng giá trị cuối; giữ lại haptic.

## 5. Nguồn tham chiếu + ranh giới IP

- **Tier 1** — Material 3 *Progress indicators* (linear mặc định track 4dp, biến thể dày 8dp, stop indicator cuối track, wavy variant của M3 Expressive → chọn determinate khi biết mục tiêu); M3 touch target 48dp. Apple HIG *Charting data* + WWDC22 *Design an effective chart* (mật độ gridline/nhãn tuỳ mục đích chart; trend preview bỏ trục & nhãn; chart tương tác phải có trục + nhãn); HIG tap target 44pt.
- **Tier 3** (ảnh store công khai): bố cục "1 ring hero + tường tile 2 cột" là convention phổ biến của nhóm app này.
- **SUY ĐOÁN của tôi, chưa có tier 1–3 chống lưng** (đọc lại khi review): mọi con số % viewport và % chiều rộng ở mục 1; thứ tự bỏ nhãn khi hẹp; ngưỡng 56dp cho quick-log lặp; timing 400–600ms fill và ≤800ms celebration; quy ước ô ngày chưa đạt dùng viền mảnh; tỉ lệ track 8–12% đường kính ring.
- **KHÔNG trích:** hex màu thương hiệu, logo/wordmark, bộ icon độc quyền, copy nguyên văn, tên app cụ thể. Mô tả cấu trúc — không viết "làm giống \<app\>".
