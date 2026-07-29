# shared/design/references/ — ảnh chụp app tham chiếu (chỉ cho người + AI xem trực tiếp)

**Owner:** `__human__` (`kernel/contracts/data-ownership.json`) — người đặt file vào đây, không agent nào ghi.

## Dùng khi nào

Khi đề bài là **clone/làm giống 1 app có sẵn**. Đặt ảnh chụp màn hình (PNG/JPG, bao nhiêu tuỳ) trực tiếp vào thư mục này — không cần đặt tên theo quy ước, không cần tag.

## Vì sao KHÔNG đi qua anchor-tag như các file khác

Toàn bộ hệ thống dùng anchor-tag (`<!-- tier:2 role:... story:... -->`) để `context_compile.py` **trích chọn lọc** nội dung — nhưng đó là cơ chế cho **text**. Ảnh không tag được theo cách đó, và cũng không cần: `design-system` (phase project-scope, chạy đúng 1 lần) đọc **trực tiếp** toàn bộ ảnh trong thư mục này bằng công cụ đọc file đa phương thức (không phải qua `context_compile.py`), y như người sẽ tự mở ảnh ra xem.

## Bắt buộc kèm mô tả bằng chữ ở `shared/PRD.md#PROJ` mục 3

Ảnh cho biết **trông như thế nào**, không cho biết **giống tới mức nào bạn muốn** (giống hoàn toàn / chỉ giống luồng / chỉ lấy cảm hứng) hay **có được phép giữ y hệt nhận diện thương hiệu của app gốc hay không** (rủi ro bản quyền/thương hiệu). 2 thứ đó bắt buộc `ba` viết thành chữ ở `PRD.md#PROJ`, ảnh không thay thế được.

## Verify trước khi `design-system` dùng ảnh để dựng phương án

- Đã đọc **hết** ảnh trong thư mục này bằng công cụ đọc file, không suy đoán từ tên file.
- 3 phương án theme trong `theme-preview.html` phải **nêu rõ** yếu tố nào lấy cảm hứng từ ảnh nào (màu chủ đạo, kiểu bố cục, kiểu component) — để người chọn biết đang so sánh với cái gì, không phải "tự nhiên ra 3 màu".
- **Không** copy y nguyên logo/wordmark/tên thương hiệu của app gốc vào theme — đó là rủi ro pháp lý ngoài phạm vi thẩm mỹ, `design-system` phải tự chặn, không đợi người nhắc.
