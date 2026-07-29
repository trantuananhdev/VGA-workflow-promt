# skill_classify_domain

**Dùng bởi:** `ba` (riêng). Chạy khi draft xong 1 Epic, **trước** khi emit handoff sang `cto` — tức trước Gate 1.

**Mục tiêu:** Suy luận **domain nghiệp vụ** của từng story từ chính đề bài (kể cả đề bài viết rất thô), ghi vào `shared/contracts/domain-map.json` để `designer` biết nạp đúng bộ tri thức UX cho story đó.

**Vì sao ở `ba` mà không phải unit/gate mới:** `ba` là agent duy nhất đọc hết PRD theo từng Epic trước Gate 1 — đúng thời điểm và đúng dữ liệu. Đặt ở `po` thì lúc đó chưa có story list; đặt ở `designer` thì phát hiện muộn (sau Gate 1) và mỗi story lại suy luận lại từ đầu. Không thêm node/cạnh/gate = không thêm phụ thuộc tuần tự.

**Input:** `shared/PRD.md` (Epic đang xử lý, mọi story) + `shared/system-spec.md` slice tương ứng + `kernel/memory/project-profile.json` (field `domain` nếu PO có khai)

**Output:** `shared/contracts/domain-map.json` — append/cập nhật entry cho từng story của Epic này

---

## Quy trình

```
0. Đọc known_domains trong shared/contracts/domain-map.json.
   Tag PHẢI lấy từ danh sách đó — không tự đặt tên tag mới.

1. Với MỖI story trong Epic:
   a. Tìm dấu hiệu domain trong 3 chỗ, KHÔNG chỉ đọc tiêu đề story:
        - động từ nghiệp vụ trong Mô tả  (đặt / mua / chuyển tiền / theo dõi / học / đăng bài)
        - tên field dữ liệu              (số dư, tồn kho, giờ hẹn, lượt thích, tiến độ bài học)
        - edge case đã liệt kê           (hết hàng / đối tác không nhận / OTP hết hạn)
   b. Mỗi dấu hiệu -> 1 candidate tag. Đếm số dấu hiệu ĐỘC LẬP cho mỗi tag.
   c. confidence:
        >= 3 dấu hiệu độc lập  -> 0.90
        2 dấu hiệu độc lập     -> 0.78
        1 dấu hiệu             -> 0.55
        chỉ suy từ tên project -> 0.40
      Trừ 0.10 nếu dấu hiệu là từ khoá DÙNG CHUNG nhiều domain
      (vd "giỏ hàng" có ở cả e-commerce và on-demand-booking; "ví" có ở cả fintech và e-commerce).
   d. Chọn ĐÚNG 1 domain primary = tag quyết định layout chính của story.
      Các tag còn lại primary: false.

2. Áp ngưỡng (xem _confidence_policy trong domain-map.json):
   primary >= 0.75            -> khoá luôn
   primary <  0.75            -> BẮT BUỘC mở Sync Session `ba` -> `po`
                                 (type: request, max_turns: 3) hỏi xác nhận TRƯỚC khi ghi file.
                                 Ghi request_id vào resolved_by_sync.
   phụ (primary:false) < 0.5  -> BỎ, không ghi.

3. Đối chiếu project-profile.json .domain (nếu PO có khai):
   Khác kết quả suy luận -> vẫn ghi kết quả SUY LUẬN, đặt conflicts_with_profile: true.
   KHÔNG lấy field PO khai để ghi đè — PO lúc đầu dự án chỉ nắm domain chính, không thấy
   domain phụ ẩn trong từng module (app giao đồ ăn có module chat = social, ví = fintech).

4. Ghi entry vào shared/contracts/domain-map.json .stories:
   { story_id, roles: ["designer"], domains: [...], conflicts_with_profile, resolved_by_sync }
   roles LUÔN là ["designer"] — đây là cơ chế slicing của context_compile.py:
   chỉ designer nhận entry này, agent khác không tốn context.

5. Tag nào không có thư mục agents/designer/skills/domain/<tag>/ -> vẫn ghi bình thường.
   designer sẽ tự bootstrap bản nháp (draft: true) — xem agents/designer/skills/domain/SKILL.md.
```

## Vì sao ngưỡng 0.75 cho primary

Domain rõ ràng thường để lại **nhiều hơn 1** bằng chứng độc lập trong PRD (tên module + động từ nghiệp vụ + field dữ liệu). Dưới mức đó thường chỉ suy từ 1 từ khoá — và 1 từ khoá thì dễ trùng giữa các domain. Sai domain **primary** = `designer` nạp sai cả bộ pattern cho cả story, và sai đó chỉ lộ ra ở Gate 5 hoặc muộn hơn; đắt hơn 1 câu hỏi cho `po` rất nhiều.

Ngược lại, domain **phụ** đoán sai chỉ làm `designer` đọc thêm 1 bộ pattern không dùng — thiệt hại là context, không phải thiết kế sai. Vì vậy chỉ `primary` được phép chặn pipeline bằng Sync Session.

## `evidence` là bắt buộc và phải TRÍCH THẬT

Mỗi domain phải kèm `evidence` = **câu/tên module trích nguyên từ PRD** dẫn tới suy luận đó. Không phải diễn giải, không phải "vì app này là app bán hàng". Lý do: đây là thứ duy nhất cho phép người audit lại quyết định của skill này — không có nó thì `domain-map.json` là hộp đen, và khi `designer` vẽ sai convention thì không ai truy được là do domain gán sai hay do designer làm sai.

**Bịa `evidence` nghiêm trọng hơn gán sai domain** — gán sai thì người sửa được, bịa evidence thì người tin là đúng.

## Verify trước khi emit handoff sang `cto`

- Mọi story trong Epic đều có entry trong `domain-map.json` — thiếu 1 story = `designer` của story đó không biết nạp gì, sẽ tự đoán.
- Mọi tag ∈ `known_domains`; mỗi story có **đúng 1** domain `primary`.
- Mọi domain có `evidence` trích được từ PRD thật (tự kiểm: mở PRD tìm lại đúng câu đó).
- Mọi domain `primary` có `confidence < 0.75` đều đã có `resolved_by_sync` khác `null` — chưa hỏi mà đã khoá là vi phạm.
- File `domain-map.json` **parse được** (nó là input máy đọc của `context_compile.py`).
