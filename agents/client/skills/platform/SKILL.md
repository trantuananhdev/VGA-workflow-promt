# skill_platform — index chọn platform pack

**Dùng bởi:** `client`, cả 2 phase (`client-shell`, `client-screen`). Đây là **bước 0** của agent.

**Mục tiêu:** Trả lời đúng 1 câu hỏi — *"project này đang làm nền tảng gì, và tri thức nền tảng đó nằm ở file nào"* — rồi nạp **đúng 1 pack**.

> File này là **spec cho người VIẾT pack**, không phải tri thức để làm việc. Lúc chạy bình thường
> agent chỉ đọc `platform/<pack>/SKILL.md`; chỉ mở file index này khi cần **bootstrap 1 pack mới**
> (bước 3). Cùng cơ chế `agents/designer/skills/domain/SKILL.md` đã dùng cho domain skill.

---

## Bước 1 — Tra pack từ tech-stack (KHÔNG đoán)

```
entry = shared/contracts/tech-stack.json -> entries[] có story_id="PROJ" và "client" ∈ roles
pack  = entry.platform_pack          # vd "mobile-native", "web-spa"
target= entry.delivery_target        # mobile_native | web_app
đọc agents/client/skills/platform/<pack>/SKILL.md
```

Không tìm được entry, hoặc `platform_pack` rỗng → **emit `doc_drift_detected` về `cto`**, dừng. Tuyệt đối không suy ra pack từ tên project, từ ảnh reference, hay từ "thường thì app kiểu này là mobile". Đề bài → stack là việc của `cto` (`agents/cto/skills/decide_tech_stack/SKILL.md`) và đã khoá ở Gate 1; agent này chỉ **tra bảng**.

## Bước 2 — Pack đang có trên đĩa

| Pack | `delivery_target` | Nội dung |
|---|---|---|
| `mobile-native/` | `mobile_native` | Vỏ native (manifest/plist, permission, min OS, push, deep link), compliance nền tảng, release checklist. Chứa **stack pack** con `vga31-kotlin/` cho Android/Kotlin dựng từ template nội bộ. |
| `web-spa/` | `web_app` | App shell web (routing, entry bundle, biến môi trường), SSR/SEO mode, CSP + security header, browser support matrix, PWA/offline nếu đề bài cần. |

Danh sách này **suy từ tên thư mục thật**, không phải từ bảng cứng ở đây — thêm pack mới thì thêm thư mục, bảng này chỉ là chú giải.

## Bước 3 — Khi stack đã chốt mà CHƯA có pack (bootstrap `draft`)

Xảy ra khi `cto` chốt 1 stack chưa từng làm (vd `desktop_app`/Tauri, `cli_tool`). KHÔNG được:
- lấy pack gần giống rồi làm theo (pack mobile áp cho web sinh ra vỏ sai từ gốc), hoặc
- bỏ bước 0 rồi tự nhớ ra cách làm (tri thức không ở đâu = story sau lại làm khác).

Đường đúng: tạo `platform/<pack-mới>/SKILL.md` với `draft: true` ở dòng đầu, **đủ 5 mục** dưới đây, rồi khai `draft_pack: true` trong handoff để lớp Evolution review (`shared/lessons_learned.md`).

## Khuôn bắt buộc của 1 pack (5 mục, ~90 dòng, không dài hơn)

1. **Vỏ gồm những gì** — danh sách thành phần `client-shell` phải dựng, mỗi cái kèm *bằng chứng đã dựng* kiểm được (file thật/log thật), không phải câu "đã cấu hình".
2. **STACK BINDING** — lệnh thật: build, serve/run, lint, unit test, và lệnh chạy ở **bậc responsive hẹp nhất** + **cỡ chữ 200%**. `run_lint`/`run_unit_test` của agent lấy lệnh từ đây, không hard-code.
3. **Map `type` của hợp đồng layout → widget/element thật** của nền tảng (enum `type` trong `kernel/contracts/screen-layout.schema.json` là đóng, chính vì để việc map này quyết định **1 lần cho mỗi nền tảng** thay vì mỗi story đoán lại).
4. **Cách thực hiện khối `responsive`/`safe_area`/`text_overflow`** bằng primitive thật của nền tảng — kèm **cái gì SAI** tương ứng (vd chiều cao cố định, hàng ngang không wrap).
5. **Compliance + capability** — ngưỡng bắt buộc của nền tảng (`violations: []` mới được qua Gate 3), và những gì phải khai vào `shared/capabilities/client.json`. Ghi rõ mục nào là **SUY ĐOÁN chưa có spec chống lưng** để người sau đọc lại.

## Vì sao tri thức nền tảng nằm ở pack, không nằm trong AGENT.md

`AGENT.md` mô tả **vai trò** (bất biến giữa mọi project); pack mô tả **nền tảng** (thay theo đề bài). Trộn 2 thứ vào 1 file thì mỗi project mới phải sửa AGENT.md — và sửa AGENT.md là sửa hợp đồng vai trò, thứ mà `dag.json`/gate đang dựa vào. Đây đúng là lý do agent này **hết** tên `mobile`: khi tri thức Android nằm thẳng trong `skills/`, một project web nhận nguyên bộ skill sai mà không có cơ chế nào báo.
