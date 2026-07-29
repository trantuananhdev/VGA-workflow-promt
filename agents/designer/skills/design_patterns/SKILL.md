# skill_design_patterns — thư viện pattern craft theo domain (index)

**Dùng bởi:** `designer` (cả 2 phase). **Đây là file index, không phải skill thực thi** — skill thật là từng thư mục con `agents/designer/skills/design_patterns/<tag>/SKILL.md`.

**Mục tiêu:** cấp **đầu vào craft** — "cái đẹp trông như thế nào" — chưng từ app best-in-class và design system chính thống của từng ngành.

---

## Vì sao là skill RIÊNG, không phải mục 6 của `domain`

`skills/domain/SKILL.md` chốt cứng **đúng 5 mục** và ghi rõ *"Thêm mục 6 = không ai đọc"* — vì `generate_wireframe` đọc domain skill theo **số mục**. Nhưng lý do tách còn quan trọng hơn chuyện format:

| | `skills/domain/<tag>/` | `skills/design_patterns/<tag>/` (file này) |
|---|---|---|
| Trả lời câu hỏi | **Cái gì SAI** — state nào thiếu, pitfall nào chết người | **Cái gì ĐẸP** — bố cục nào đọc được, tỉ lệ nào dễ chịu |
| Bản chất | Lưới an toàn (chức năng/pháp lý/a11y) | Tham chiếu craft (composition/hierarchy/motion) |
| Tự nhận | *"Giá trị chính không phải vẽ đẹp hơn"* (`domain/SKILL.md`) | Chính là phần "vẽ đẹp hơn" mà câu trên loại trừ |
| Hỏng thì hậu quả | App **lỗi** (mất tiền, rò dữ liệu, bị store từ chối) | App **dở** (dùng được nhưng rẻ tiền, không ai thích) |

2 mối quan tâm khác bản chất → 2 file khác nhau, nạp độc lập. **KHÔNG lặp lại nội dung của nhau:** file pattern **không** liệt kê state bắt buộc hay pitfall (đó là việc của `domain`); file domain **không** bàn tỉ lệ/nhịp/motion.

## Nạp cái gì — chỉ domain `primary`

```
primary = shared/contracts/domain-map.json .stories[<story_id>].domains[ .primary == true ].tag
doc agents/designer/skills/design_patterns/<primary>/SKILL.md
```

**Chỉ nạp `primary`, KHÔNG nạp domain phụ.** Căn cứ: `domain/SKILL.md` đã chốt *"Domain `primary` quyết định layout chính; domain phụ chỉ bổ sung state/pitfall"* — pattern craft là chuyện **bố cục**, nên chỉ domain quyết định bố cục mới cần. Story `on-demand-booking` + `fintech-payment` thì nạp pattern của `on-demand-booking` (primary), còn `fintech-payment` chỉ góp state/pitfall qua `domain` skill. Đây là điều kiện để vừa ngân sách context (`agents/designer/manifest.json`).

## Dùng để làm gì trong `generate_wireframe`

Nạp ở **bước 0** cùng lúc với `domain` skill, dùng ở **bước 3.5** (liệt kê `component_need`) và **bước 4** (chốt layout JSON):

| Mục của file pattern | Ảnh hưởng tới layout JSON |
|---|---|
| 1. Bố cục màn hình chủ đạo | Thứ tự khối, cái gì trên/dưới fold, `order` của component |
| 2. Hierarchy & emphasis | Field `emphasis` từng component — quyết định đâu là primary duy nhất |
| 3. Cấu trúc bên trong component | `component_need` chi tiết tới mức từng phần bên trong, không chỉ "1 cái card" |
| 4. Interaction & motion | Field `interaction` — trigger/action/target_state, và ghi chú motion cho `mobile-screen` |
| 5. Nguồn + ranh giới IP | Biết cái gì được lấy, cái gì tuyệt đối không |

## Cấu trúc bắt buộc của 1 file pattern

Mọi `design_patterns/<tag>/SKILL.md` phải có đúng 5 mục dưới, theo thứ tự (đọc theo **số mục**, không theo tên — cùng quy ước với `domain`):

```
## 1. Bố cục màn hình chủ đạo
## 2. Hierarchy & emphasis
## 3. Cấu trúc bên trong từng component chủ đạo
## 4. Interaction & motion
## 5. Nguồn tham chiếu + ranh giới IP
```

Thiếu mục = `designer` đọc lệch số mục. Thêm mục 6 = không ai đọc. **Giới hạn ~90 dòng/file** — dài hơn là tràn ngân sách context của `designer`, và dấu hiệu đang lặp nội dung `domain` skill.

## Trích cái gì / KHÔNG trích cái gì — ranh giới bắt buộc

Đây là **điều kiện của skill này**, không phải lời khuyên. Toàn ngành design đều học từ app có sẵn; pattern/convention/bố cục **không** thuộc sở hữu ai. Nhưng nhận diện thương hiệu thì có.

**ĐƯỢC trích** (pattern — dùng chung tự do): cấu trúc bố cục, thứ tự thông tin, cái gì dominant, nhịp spacing & mật độ, **quan hệ tỉ lệ** của type scale, idiom điều hướng (bottom sheet vs full screen vs tab), cách app tốt xử lý trạng thái rỗng/đang tải, motion language **mô tả bằng chữ**.

**KHÔNG được trích:**
- Logo / wordmark / tên thương hiệu (rule này đã có ở `shared/design/references/README.md`, đây là mở rộng cùng nguyên tắc)
- Bộ icon / illustration độc quyền, ảnh và nội dung có bản quyền, copy văn bản nguyên văn
- **Giá trị hex màu thương hiệu chính xác** — chỗ này tinh vi: copy đúng palette + đúng bố cục của 1 app nổi tiếng là rủi ro trade dress dù từng phần riêng lẻ đều vô hại. Màu chỉ trích ở dạng **quan hệ** ("CTA tương phản mạnh trên surface trầm, đúng 1 accent dùng tiết chế"), giá trị thật do `tokens.json` sinh từ brand của chính project.

## Nguồn — theo thứ tự ưu tiên

1. **Design system chính thống** (Material 3, Apple HIG) — sinh ra để được tuân theo, có thẩm quyền, rủi ro bằng 0. Đây là tier 1, **không phải** gallery.
2. **App open-source license permissive** — đọc được implementation thật, không chỉ ảnh.
3. **Ảnh trên Play Store / App Store** — tài liệu marketing công khai của chính app đó.
4. **Gallery (Mobbin/Dribbble/…)** — ToS thường hạn chế truy cập tự động; phù hợp để **người** tự tải vào `shared/design/references/` (cơ chế đã có, owner `__human__`) hơn là để agent scrape.

Mục 5 của mỗi file phải ghi nguồn thuộc tier nào. Pattern chỉ dựa trên tier 4 mà không có tier 1-3 chống lưng → ghi rõ là **suy đoán**, không ghi như convention đã được xác lập.

## Ghi mô tả CẤU TRÚC bằng chữ, không lưu ảnh

`generate_wireframe` xuất JSON chứ không xuất pixel — nó cần thứ dùng được ngay:

> ĐÚNG: "Card sản phẩm: ảnh 4:3 chiếm ~60% chiều cao card, giá đặt ngay dưới ảnh và là element `emphasis` cao nhất trong card, tên tối đa 2 dòng rồi ellipsis, rating nhỏ hơn giá rõ rệt, khoảng trắng giữa 2 card lớn hơn padding trong card."
>
> SAI: "xem ảnh screenshot đính kèm" / "làm giống Shopee".

Chữ thì diff được, review được, versioned được, và vừa ngân sách context. Ảnh thì không — và ảnh còn kéo theo rủi ro IP ở mục trên.

---

## Bootstrap khi gặp domain MỚI chưa có file pattern

Dùng **đúng** cơ chế `draft: true` mà `domain/SKILL.md` đã thiết lập (cùng lý do, không phát minh cơ chế mới):

```
1. Sinh agents/designer/skills/design_patterns/<tag>/SKILL.md theo ĐÚNG 5 mục trên.
2. Dòng đầu file PHẢI có:  > draft: true — chưa qua review người, xem shared/lessons_learned.md
3. Dùng cho story hiện tại, NHƯNG handoff phải khai draft_patterns: [<tag>]
   (song song draft_domains của domain skill — Gate 5 kiểm cả 2).
4. Ghi 1 entry vào shared/lessons_learned.md: pattern nào, story nào sinh ra, nguồn thuộc
   tier nào, phần nào tự tin / phần nào suy đoán.
5. Lần review Evolution kế tiếp (ORCHESTRATOR.md §9) người duyệt rồi BỎ cờ draft.
```

**Không được tự bỏ cờ `draft`.** Pattern craft do agent tự sinh mà không có nguồn tier 1-3 chống lưng rất dễ là "convention" nghe hợp lý nhưng không tồn tại — và khác với domain skill (sai thì lộ ra ở QA), pattern sai thì **không gate nào bắt được**, nó chỉ hiện ra khi người nhìn app thấy dở. Cờ `draft` là dấu duy nhất để người biết chỗ nào cần đọc lại.

## Domain đã có (thư mục con của file này)

`e-commerce-marketplace` · `on-demand-booking` · `fintech-payment` · `social-community` · `health-fitness` · `education-learning` · `content-media` · `productivity-tools`

Đủ 8/8 domain trong `known_domains` (`shared/contracts/domain-map.json`) — cùng tập tag với `skills/domain/`, cố ý: 1 tag thì có **cả** file domain (an toàn) **và** file pattern (craft).

## Xuất xứ của 8 file seed — đọc trước khi tin

8 file này **do AI viết** (seed lần đầu), không phải do designer người viết ra từ kinh nghiệm. Chúng **không** mang cờ `draft: true` vì cờ đó dành cho pattern agent tự bootstrap giữa lúc chạy story; nhưng điều đó **không** có nghĩa chúng đã qua review người.

Cách đọc đúng mức độ tin cậy:

| Trong mục 5 ghi | Nghĩa thật | Người cần làm gì |
|---|---|---|
| **Suy đoán** (mọi con số %, tỉ lệ, timing cụ thể) | File tự lượng hoá từ convention quan sát được. Không spec nào chốt các số này. | Đọc kỹ, chỉnh theo `tokens.json` của project |
| **Tier 1** (M3 / Apple HIG) | Trích từ **kiến thức về** spec, **không** phải từ trang web fetch được lúc viết — `m3.material.io` và `developer.apple.com` render bằng JS nên `WebFetch` trả rỗng (2 file đã ghi lại giới hạn này) | Vẫn nên đối chiếu lại với spec bản mới nhất |

Nói cách khác: **cả 2 loại đều cần người kiểm, chỉ khác mức độ ưu tiên** — đừng đọc "tier 1" thành "đã xác minh, khỏi kiểm". Ghi rõ ở đây vì đúng rủi ro mà mục bootstrap dưới cảnh báo: pattern craft sai thì **không gate nào bắt được**, nó chỉ hiện ra khi người nhìn app thấy dở.
