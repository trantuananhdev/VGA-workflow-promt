# design_patterns: content-media

> Craft cho duyệt thư viện nội dung, trang chi tiết, trình phát audio/video. **Không** lặp state/pitfall — xem `skills/domain/content-media/SKILL.md`.

## 1. Bố cục màn hình chủ đạo

**Trang chủ = xếp tầng "shelf" ngang, cuộn dọc.** Mỗi shelf = 1 tiêu đề + 1 hàng cuộn ngang. Lý do dùng shelf chứ không grid phẳng: nội dung cần **nhãn lý do** ("Tiếp tục xem", "Mới ra mắt") mới có nghĩa; grid phẳng mất hết ngữ cảnh đó.

| Khối | Vị trí | Tỉ lệ / ghi chú |
|---|---|---|
| Hero / shelf đầu | Ngay dưới top bar | Shelf đầu **luôn** là "Tiếp tục xem/nghe" nếu có dữ liệu — đây là lý do quay lại app |
| Shelf tiếp theo | Cuộn dọc | Mỗi shelf hở ~15-20% thumbnail thứ n+1 ở mép phải để báo hiệu cuộn được |
| Mini-player | Neo trên bottom nav | Chiều cao ~1 hàng (≈ chiều cao nav), **không** che nav |
| Bottom nav | Dưới cùng | Mini-player + nav = 2 tầng cố định; chừa đủ padding đáy cho danh sách |

**Mật độ thumbnail — chọn theo tỉ lệ, không theo "số cột":**
- Tỉ lệ **dọc (2:3)** — phim/truyện/sách: 2.5-3 item nhìn thấy trên 1 hàng ngang. Ảnh bìa dọc mang nhiều thông tin nhận diện, không được nhỏ hơn.
- Tỉ lệ **vuông (1:1)** — nhạc/podcast/album: 2.5-3.5 item/hàng.
- Tỉ lệ **ngang (16:9)** — video/tin tức: 1.2-2 item/hàng; ảnh 16:9 nhỏ thì mất hết chi tiết, thà ít item hơn.
- **Grid dọc** (màn Tìm kiếm / Thư viện) dùng đúng tỉ lệ và đúng chiều rộng item của shelf tương ứng — đừng đổi tỉ lệ giữa 2 màn cho cùng loại nội dung.

**Trang chi tiết:** ảnh/backdrop tràn lề trên cùng (không inset — đây là nơi ảnh được phép chiếm chỗ) → khối tiêu đề + metadata → **nút Phát chính** → mô tả (thu gọn 2-3 dòng) → danh sách tập/track → nội dung liên quan. Nút Phát phải nằm **trên fold**.

**Trình phát full screen — 2 bố cục khác nhau, đừng dùng chung:**
- **Video:** khung video canh giữa theo chiều dọc, ưu tiên landscape; chrome đè lên video.
- **Audio:** artwork vuông chiếm ~45-55% chiều cao, canh giữa trên; dưới là tiêu đề/nghệ sĩ → scrubber → hàng transport → hàng action phụ (queue/output/like). Chrome **không** đè artwork.

## 2. Hierarchy & emphasis

**Màn duyệt: primary duy nhất = artwork/thumbnail của nội dung.** Tiêu đề shelf là `low` (nhỏ, không đậm quá mức) — nó là nhãn, không phải nội dung. Sai thường gặp: gán primary cho tiêu đề shelf hoặc nút "Xem tất cả".

**Trang chi tiết: primary duy nhất = nút Phát.** Đây là màn duy nhất trong domain mà 1 **nút** được làm primary — vì màn này tồn tại chỉ để dẫn tới hành động đó. Mọi thứ khác (Lưu, Tải, Chia sẻ) tụt xuống `low`, dạng icon + nhãn nhỏ trên 1 hàng, **không** cùng kiểu nút với Phát.

**Trình phát: primary = nút Play/Pause.** Cụ thể hoá: Play/Pause lớn hơn nút tua ~1.4-1.6×, tua lớn hơn next/prev, các nút phụ (queue/output/speed) nhỏ nhất và tương phản thấp. Scrubber là `medium` — nó quan trọng nhưng phải mảnh (đường ray rất mỏng, chỉ núm kéo đủ lớn).

**Thumbnail và metadata:** tiêu đề tối đa 2 dòng rồi ellipsis, cỡ body nhỏ; metadata (thời lượng/năm/nghệ sĩ) nhỏ hơn 1 bậc **và** tương phản thấp hơn. Badge (đã tải / cần thuê bao / mới) là phần tử duy nhất được đè lên artwork, đặt góc, **rất** nhỏ.

**Scrim khi chrome đè lên ảnh/video bất kỳ:** bắt buộc, vì không kiểm soát được frame bên dưới. Dùng scrim gradient ~40% đen → trong suốt, điểm giữa lệch ~3/10 về phía đậm để không có mép cắt gắt; scrim **trên** cho hàng nút đầu và **dưới** cho scrubber, chừa giữa video sạch. Thanh tiến độ trên thumbnail (đã xem tới đâu) đặt sát mép dưới artwork, cao ~2-3dp, không nằm trong scrim.

## 3. Cấu trúc bên trong từng component chủ đạo

**`content_card` (item trong shelf)** — 3 phần:
1. `artwork`: bo góc nhẹ, tỉ lệ **cố định theo loại nội dung** (mục 1), overlay badge góc + progress bar mép dưới nếu đang xem dở.
2. `title`: ≤ 2 dòng, ngay dưới artwork, khoảng cách nhỏ hơn gap giữa 2 card.
3. `metadata`: 1 dòng, ellipsis, tương phản thấp. **Bỏ được** — nếu artwork đã tự nói (album art có tên), cắt hẳn dòng này thay vì nhồi.

Gap ngang giữa 2 card **nhỏ hơn** gap dọc giữa 2 shelf (tỉ lệ ~1:2) — mắt phải đọc "một hàng" trước khi đọc "nhiều hàng".

**`media_frame` (khung video)** — giữ **đúng tỉ lệ gốc của nguồn**, letterbox/pillarbox nếu lệch với khung khả dụng, nền vùng thừa là đen đặc (không dùng surface màu). Tuyệt đối không crop video ở màn phát. Không tự thêm padding letterbox vào bên trong frame nội dung — hệ điều hành cần frame sạch để scale đúng ở full-screen/fit-to-screen/PiP.

**`player_chrome`** — 3 tầng rời, ẩn/hiện **cùng lúc** như một khối:
- tầng trên: đóng | tiêu đề (≤1 dòng) | output picker + overflow
- tầng giữa: prev | rewind | **play/pause** | forward | next — canh giữa, khoảng cách đều
- tầng dưới: thời gian đã phát | scrubber | tổng thời lượng, và dưới nữa là hàng action phụ

**`mini_player`** — cấu trúc cố định 1 hàng: artwork vuông nhỏ (bằng chiều cao hàng, sát mép trái) | cột 2 dòng (tiêu đề / nghệ sĩ, cả 2 đều 1 dòng ellipsis) | play/pause | (tuỳ chọn) next. **Chỉ 2 nút, tối đa.** Thanh tiến độ là đường mảnh sát **mép trên** mini-player, chạy hết chiều ngang, không có núm kéo. Tap vào bất kỳ đâu trừ 2 nút = mở full player; tap vào nút **không** mở full player.

**`queue_item`**: handle kéo (mép trái) | artwork rất nhỏ hoặc số thứ tự | tiêu đề + nghệ sĩ | thời lượng. Item đang phát đổi màu chữ tiêu đề (không đổi nền cả hàng — dễ đọc sai thành "đã chọn").

## 4. Interaction & motion

- **Play phải phản hồi tức thì:** icon đổi sang pause **ngay** khi chạm, trạng thái buffering hiện **trong** vùng nút đó (spinner thay chỗ icon), không phải overlay che cả màn.
- **Chrome trình phát tự ẩn** sau ~3 giây không tương tác khi đang phát; **không** tự ẩn khi đang pause (user pause là để nhìn). Chạm bất kỳ đâu → hiện lại toàn khối. Fade ~200ms, tất cả tầng cùng nhịp; đừng slide từng tầng lệch nhau.
- **Mini-player ↔ full player** là **một** phần tử biến hình, không phải 2 màn: artwork nhỏ giãn ra thành artwork lớn tại đúng đường đi, tiêu đề trượt về vị trí mới, chrome còn lại fade vào. Vuốt xuống trên full player = thu về mini-player theo đúng đường ngược lại, có thể huỷ giữa đường.
- **Mini-player không bao giờ mất khi điều hướng.** Chuyển tab, mở màn chi tiết, back — nó ở nguyên đó.
- Shelf cuộn ngang: cuộn tự do (momentum), **không** snap từng item — snap gây cảm giác kẹt khi item hẹp. Chỉ snap ở carousel hero 1-item-1-trang.
- Scrubber: kéo thì hiện preview/nhãn thời gian **phía trên** ngón tay (ngón che mất vị trí), và tăng độ chính xác khi kéo chậm. Nhả tay mới seek thật.
- Xoay ngang trong lúc phát video → vào full screen; xoay dọc → ra. Vị trí phát **không** được reset.
- Vào màn chi tiết từ 1 card: backdrop nở ra từ artwork của card đó, phần còn lại của trang trượt lên theo.

## 5. Nguồn tham chiếu + ranh giới IP

- **Tier 1:** Apple HIG (Playing video) — chốt cứng nguyên tắc *hiển thị video đúng tỉ lệ gốc* và *không nhúng padding letterbox/pillarbox vào frame nội dung*, vì làm vậy khiến hệ điều hành không scale đúng ở full-screen/fit-to-screen/PiP; đây là căn cứ cho quyết định letterbox ở mục 3. Apple HIG (Playing audio) — Now Playing/route picker là lý do output picker có chỗ cố định ở `player_chrome`. Material 3 — tập tỉ lệ khuyến nghị (16:9, 3:2, 4:3, 1:1, 3:4, 2:3) là tập chọn tỉ lệ thumbnail; scrim = "text protection" với gradient dài, điểm giữa lệch ~3/10 về phía đậm; thang type 5 vai trò cho quan hệ cỡ chữ; card padding/gutter theo bậc 8-16-24dp cho nhịp gap.
- **Tier 4 / không có nguồn — SUY ĐOÁN, cần người review:** các con số mật độ ("2.5-3 item/hàng", "hở 15-20%"), "artwork chiếm 45-55% chiều cao ở player audio", "play/pause lớn hơn tua 1.4-1.6×", "auto-hide ~3 giây và không auto-hide khi pause", tỉ lệ gap ngang:dọc ~1:2, và giới hạn "mini-player tối đa 2 nút" — đều do file này lượng hoá từ convention quan sát được, **không** trích từ spec chính thống. Điều chỉnh theo `tokens.json`.
- **IP:** chỉ lấy cấu trúc/tỉ lệ/quan hệ. KHÔNG lấy: hex màu thương hiệu của app streaming nào, bộ icon transport độc quyền, hình dạng logo/badge nhận diện, ảnh bìa hay copy nguyên văn. Không viết "làm giống <app>" ở bất kỳ đâu trong layout JSON.
