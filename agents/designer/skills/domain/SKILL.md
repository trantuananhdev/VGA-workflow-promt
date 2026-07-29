# skill_domain — thư viện tri thức UX theo domain (index)

**Dùng bởi:** `designer` (cả 2 phase). **Đây là file index, không phải skill thực thi** — skill thật là từng thư mục con `agents/designer/skills/domain/<tag>/SKILL.md`.

**Mục tiêu:** cấp **ngữ cảnh tư duy** trước khi vẽ, đúng cách `shared/capabilities/ads.json` cấp domain-knowledge cho agent `ads`. Nó **KHÔNG** thay `generate_wireframe` — quy trình sinh layout JSON không đổi; domain skill chỉ làm cho layout đó đúng convention của loại app đang làm, và phát hiện state mà PRD có thể bỏ sót.

---

## Nạp cái gì — quyết định bởi dữ liệu, không phải danh sách cứng

```
domains = shared/contracts/domain-map.json .stories[<story_id>].domains
for d in domains:
    doc agents/designer/skills/domain/<d.tag>/SKILL.md
```

**Nạp CHỌN LỌC, không nạp cả thư viện.** Ngân sách context của `designer` là 6000 token (`agents/designer/manifest.json`) — nạp 8 domain thì không còn chỗ cho PRD của story. 1 story có nhiều tag thì nạp nhiều file (vd "thanh toán trong app đặt phòng" = `on-demand-booking` + `fintech-payment`), nhưng chỉ những tag **có thật** trong `domain-map.json` của story đó.

`domain-map.json` do `ba` sinh (`agents/ba/skills/classify_domain/`) trước Gate 1 — nên khi node `designer-screen` chạy thì file đã có sẵn. Nếu slice rỗng: **KHÔNG tự đoán domain**, mở Sync Session với `ba` (`max_turns: 3`).

## Dùng để làm gì trong `generate_wireframe`

Nạp ở **bước 0** (trước khi liệt kê state), rồi dùng ở **bước 3** để đối chiếu:

| Domain skill cung cấp | Ảnh hưởng tới layout JSON |
|---|---|
| Pattern UX chuẩn của domain | Cấu trúc màn hình chính (thứ tự khối, vị trí CTA) |
| **State mà app loại này LUÔN cần** | Bước 3: state nào domain đòi mà PRD không nêu → **hỏi `ba`**, không tự thêm cũng không bỏ qua |
| Pitfall hay gặp riêng domain | Tránh sẵn, không chờ QA phát hiện ở Gate 4 |
| Quy ước platform (iOS HIG / Material) | Ghi rõ chỗ 2 nền tảng khác nhau, để `mobile-screen` không phải tự đoán |
| Checklist a11y đặc thù | Bổ sung ngoài `tokens.json` → `a11y_contract` (cái đó là mức nền cho mọi app) |

**Giá trị chính không phải "vẽ đẹp hơn" mà là bắt thiếu sót SỚM.** PRD viết từ brief thô gần như luôn thiếu state mà người trong nghề coi là hiển nhiên (huỷ đơn, hết hàng, phiên hết hạn). Domain skill là danh sách để đối chiếu — phát hiện ở `designer` rẻ hơn phát hiện ở QA rất nhiều.

## Cấu trúc bắt buộc của 1 file domain

Mọi `domain/<tag>/SKILL.md` phải có đúng 5 mục dưới, theo thứ tự (để `designer` đọc theo **số mục**, không theo tên):

```
## 1. Màn hình / pattern chuẩn
## 2. State BẮT BUỘC có (đối chiếu ở bước 3 của generate_wireframe)
## 3. Pitfall UX riêng domain này
## 4. Quy ước platform (chỉ ghi chỗ iOS và Android KHÁC nhau)
## 5. Accessibility đặc thù (ngoài a11y_contract nền)
```

Thiếu mục = `designer` sẽ đọc lệch số mục của domain khác. Thêm mục 6 = không ai đọc.

## Domain đã có (thư mục con của file này)

`e-commerce-marketplace` · `on-demand-booking` · `fintech-payment` · `social-community` · `health-fitness` · `education-learning` · `content-media` · `productivity-tools`

Đủ 8/8 domain trong `known_domains` (`shared/contracts/domain-map.json`). Domain **mới** ngoài danh sách này (project đặc thù không rơi vào 8 loại trên) → dùng cơ chế bootstrap dưới, và thêm tag vào `known_domains` (writer là `ba`, `designer` nhờ qua Sync Session).

---

## Bootstrap khi gặp domain MỚI chưa có skill

Ai làm: chính node `designer-screen` đang gặp story đó (không chờ ai, không tạo unit mới).

```
1. Sinh agents/designer/skills/domain/<tag>/SKILL.md theo ĐÚNG 5 mục trên,
   nội dung suy từ PRD của story + kiến thức chung về loại app đó.
2. Dòng đầu file PHẢI có:  > draft: true — chưa qua review người, xem shared/lessons_learned.md
3. Dùng nó cho story hiện tại, NHƯNG handoff phải khai `draft_domains: [<tag>]`
   (Gate 5 điều 6 kiểm field này).
4. Ghi 1 entry vào shared/lessons_learned.md theo format Evolution: domain nào, story nào
   sinh ra nó, phần nào tự tin / phần nào đoán.
5. Lần review Evolution kế tiếp (ORCHESTRATOR.md §9) người duyệt lại rồi BỎ cờ draft.
```

**Không được tự bỏ cờ `draft`.** Bản nháp do agent tự sinh có thể chứa "convention" không tồn tại trong thực tế; coi nó là chính thức nghĩa là mọi story sau của domain đó thừa hưởng cái sai mà không ai kiểm. Cờ `draft` là dấu để người biết chỗ nào cần đọc lại — bỏ cờ sớm là xoá đúng cái dấu đó.

Thêm domain mới thì thêm tag vào **cả** `shared/contracts/domain-map.json` → `known_domains` — writer của file đó là `ba`, nên `designer` phải nhờ qua Sync Session, không tự sửa (`kernel/contracts/data-ownership.json`).
