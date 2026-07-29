# design_patterns: social-community

> Craft cho feed nội dung do user tạo, chat, hồ sơ. **Không** lặp state/pitfall — xem `skills/domain/social-community/SKILL.md`.

## 1. Bố cục màn hình chủ đạo

**Feed = 1 cột duy nhất, không grid.** Nội dung do user tạo có chiều cao không đoán trước được; grid 2 cột buộc phải crop và làm chết cả nhịp cuộn.

| Khối | Vị trí | Tỉ lệ / ghi chú |
|---|---|---|
| Top bar | Trên cùng, thu gọn khi cuộn | Chiều cao tối thiểu, **không** chiếm > ~7% chiều cao màn |
| Feed item | Thân màn, cuộn dọc | 1 item **không** vừa hết 1 viewport — luôn hở ~10-15% item kế tiếp để mắt biết còn nội dung |
| Bottom nav | Cố định | Feed chỉ 1 nút tạo nội dung, không nhiều CTA cạnh nhau |

**Media edge-to-edge vs inset — chọn 1 rồi giữ nguyên toàn app:**
- **Edge-to-edge** (ảnh tràn 2 lề, chỉ text có padding): ảnh là nội dung chính, feed thị giác. Ranh giới giữa 2 item phải do **khoảng trắng** (gap ≥ 2× padding trong item) tạo ra, vì không còn viền card.
- **Inset trong card** (bo góc, có lề 2 bên): text là nội dung chính, mỗi post là 1 đơn vị đọc rời. Bắt buộc khi feed trộn nhiều loại post (text-only, ảnh, link preview) — card giữ nhịp thống nhất khi chiều cao lệch nhau.

**Điểm mắt nghỉ:** trong 1 feed item, mắt nghỉ ở **mép trên của media**. Nên identity block (avatar + tên) phải mỏng, đặt **trên** media, để media dính sát vào nhịp cuộn.

**Chi tiết bài đăng:** post gốc giữ nguyên bố cục feed item, comment thread thụt lề **chỉ 1 cấp** (thụt 2 cấp trở lên là hết chiều ngang trên mobile), composer neo đáy trên bàn phím.
**Chat:** bong bóng lệch 2 bên, bề rộng tối đa ~75-80% (còn hở để mắt phân biệt bên gửi/nhận ngay cả khi bong bóng dài), composer neo đáy, danh sách cuộn từ dưới lên.
**Hồ sơ:** header danh tính (avatar lớn + số liệu) → hành động → grid/list nội dung. Grid ở đây thì được, vì nội dung của **1** người đã đồng nhất về loại.

## 2. Hierarchy & emphasis

**`emphasis` primary duy nhất trên feed = chính khối media/text của post, KHÔNG phải nút nào.** Mọi chrome (nav, top bar, nút tạo post) phải là `low`. Sai thường gặp: gán primary cho nút "Đăng" ở feed — nút đó là secondary, người vào feed để đọc.

Thứ tự nhấn trong 1 feed item (giảm dần): **media → nội dung text → tên người đăng → engagement row → timestamp/metadata**.

- **Engagement row (like/comment/share) không được cạnh tranh với nội dung.** Cụ thể: icon dùng dạng outline không tô đầy, cùng màu với text phụ (không dùng accent), chiều cao hàng nhỏ hơn hàng identity, **không** viền/không nền/không nút bo. Chỉ đúng **1** trạng thái được đổi sang accent màu: nút đã-like của chính mình.
- **Số đếm** (24 lượt thích) nhỏ hơn nhãn nội dung rõ rệt, không in đậm.
- **Tên người đăng** đậm hơn nhưng **cùng cỡ** với body text; timestamp nhỏ hơn 1 bậc **và** giảm độ tương phản.
- Màn soạn bài / chat: primary chuyển sang **vùng nhập**, nút Gửi là `medium` — nó nhỏ, nhưng là nơi duy nhất được dùng accent.

**Scrim khi có text/nút đè lên ảnh user (ảnh bất kỳ, không kiểm soát được):** không bao giờ đặt text trực tiếp trên ảnh. Dùng lớp scrim gradient từ ~40% đen → trong suốt, điểm giữa lệch ~3/10 về phía đậm để không có mép cắt gắt. Chiều cao scrim ≈ chiều cao khối text + 2× padding, **không** phủ toàn ảnh.

## 3. Cấu trúc bên trong từng component chủ đạo

**`feed_item`** — 4 phần rời, mỗi phần vẽ độc lập:
1. `identity_block`: avatar tròn (~40dp) | cột 2 dòng (tên đậm / dòng phụ: handle · timestamp · phạm vi hiển thị) | nút overflow đẩy sát mép phải. Chiều cao ≈ chiều cao avatar, padding ngang = padding chuẩn của item.
2. `content_text`: tối đa 3-4 dòng rồi "Xem thêm" **inline cuối dòng cuối**, không phải nút riêng 1 dòng.
3. `media_block`: xem dưới.
4. `engagement_row`: 3-4 action chia đều chiều ngang **hoặc** dồn trái với count kề bên — chọn dồn trái nếu số đếm quan trọng. Padding dọc nhỏ nhưng tap target vẫn ≥ 48dp (mở rộng vùng chạm ra ngoài phần vẽ).

**`media_block`** — quyết định tỉ lệ **trước** khi vẽ:
- Chốt **1** tỉ lệ khung cố định cho cả feed (1:1 hoặc 4:5 là 2 lựa chọn dùng được cho ảnh dọc-lẫn-ngang), ảnh lệch tỉ lệ thì **crop center-fill**, không letterbox trong feed — thanh đen trong feed làm nhịp cuộn nhảy.
- Letterbox chỉ dùng ở **màn xem full ảnh/video**, nơi phải giữ đúng tỉ lệ gốc.
- Nhiều ảnh: hiện ảnh 1 ở tỉ lệ chuẩn + badge "1/n" góc, **không** thu nhỏ thành hàng thumbnail (mất hết chi tiết).

**`comment_item`**: avatar nhỏ hơn feed item (~32dp) | bong bóng/khối text có tên đậm **inline cùng dòng đầu** của nội dung (không tách dòng riêng — tiết kiệm chiều dọc) | hàng action chỉ 2 phần tử (Thích · Trả lời) cỡ nhỏ nhất.

**`chat_bubble`**: nội dung | hàng metadata (giờ + trạng thái gửi) đặt **trong** bong bóng, góc dưới phải, cỡ nhỏ nhất, tương phản thấp. Bong bóng liên tiếp cùng người: gộp, chỉ bong bóng cuối mang metadata và avatar.

**`composer`**: nút phụ trợ (ảnh/emoji) | ô nhập cao **tự giãn tối đa ~5 dòng** rồi tự cuộn trong | nút Gửi. Nút Gửi chỉ hiện/kích hoạt khi có nội dung.

## 4. Interaction & motion

- **Cuộn feed phải là thứ nhanh nhất trong app.** Không animation nào chạy trong lúc cuộn; ảnh chưa tải hiện placeholder **đúng kích thước khung đã chốt** để không đẩy layout (layout shift giữa lúc cuộn là lỗi cảm giác nặng nhất của domain này).
- Top bar **thu gọn khi cuộn xuống, hiện lại ngay khi cuộn lên** dù chỉ 1 chút — không đợi về đầu danh sách. Bottom nav thì **không** ẩn.
- **Like phải phản hồi tức thì (optimistic)**: đổi trạng thái + tăng số ngay tại ngón tay, đồng bộ mạng chạy ngầm; lỗi thì hoàn tác lặng lẽ. Chờ server rồi mới đổi icon là cảm giác app rẻ tiền.
- Gửi tin nhắn: bong bóng xuất hiện **ngay** ở trạng thái `sending`, không chờ round-trip.
- **Mở ảnh full:** ảnh phóng từ đúng vị trí và tỉ lệ nó đang có trong feed ra full screen (shared-element), chrome mờ dần đi. Vuốt xuống để đóng — ảnh co lại về đúng ô cũ. Vuốt ngang chuyển ảnh trong cùng post.
- **Chrome trong màn xem full ảnh/video tự ẩn** sau khoảng 2-3 giây không tương tác, 1 lần chạm bất kỳ hiện lại. Fade nhanh (~150-200ms), không slide.
- Pull-to-refresh: nội dung mới chèn **phía trên** vị trí đang đọc và giữ nguyên offset — không tự nhảy về đầu.
- Chuyển giữa tab bottom nav: **không** transition, và **giữ vị trí cuộn** của từng tab.

## 5. Nguồn tham chiếu + ranh giới IP

- **Tier 1:** Material 3 — tập tỉ lệ media khuyến nghị (16:9, 3:2, 4:3, 1:1, 3:4, 2:3) nên chọn tỉ lệ khung feed trong tập này; nguyên tắc scrim làm "text protection" và cấu trúc gradient dài, điểm giữa lệch ~3/10 về phía đậm; thang type 5 vai trò (display/headline/title/label/body) là cơ sở cho quan hệ cỡ chữ ở mục 2. Apple HIG (Layout) — vùng an toàn, tap target.
- **Tier 4 / không có nguồn — SUY ĐOÁN, cần người review:** con số "hở 10-15% item kế tiếp", "bong bóng ≤ 75-80% bề rộng", "text 3-4 dòng rồi Xem thêm", "auto-hide 2-3 giây", ngưỡng "top bar ≤ 7% chiều cao màn", và mức "avatar 40dp / 32dp" — đều là quan sát convention chung được lượng hoá bởi chính file này, **không** trích từ spec chính thống nào. Điều chỉnh theo `tokens.json` của project.
- **IP:** mọi con số ở đây là **quan hệ tỉ lệ và cấu trúc**, dùng chung tự do. KHÔNG lấy: hex màu accent của app nào, bộ icon like/react độc quyền, hình dạng "reaction" đặc trưng của 1 nền tảng, copy nguyên văn nhãn/empty-state. Màu thật do `tokens.json` sinh từ brand của project.
