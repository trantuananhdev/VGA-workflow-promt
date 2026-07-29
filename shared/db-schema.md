# db-schema.md — SSOT cấu trúc dữ liệu (do CTO ghi)

> Cùng quy ước anchor tag như `PRD.md`/`architecture.md`: `<!-- tier:2 role:cto,dev-be story:<STORY_ID> -->`
> Dev-FE thường KHÔNG cần đọc file này — chỉ cần `api-contracts.json` (hình dạng dữ liệu qua API, không cần biết bảng DB thật).

---

<!-- tier:2 role:cto,dev-be story:US-000 -->
### US-000: (ví dụ mẫu — xoá khi có story thật)

**Bảng liên quan:** `<table_name>`

**Thay đổi:** `mới` | `thêm cột` | `đổi kiểu dữ liệu` | `không đổi`

```sql
-- Migration liên quan tới US-000
```

**Index/ràng buộc cần lưu ý:** <...>
**Ảnh hưởng ngược tới story khác (nếu có):** <liệt kê story_id khác dùng chung bảng này>
