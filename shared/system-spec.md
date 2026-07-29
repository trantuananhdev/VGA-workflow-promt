# system-spec.md — Đặc tả hệ thống cấp phi-chức-năng (do CTO ghi)

> Cùng quy ước anchor tag: `<!-- tier:2 role:cto,designer,dev-be,mobile,devops,qa story:<STORY_ID> -->`
> Đây là nơi ghi những thứ KHÔNG thuộc 1 màn hình cụ thể (PRD) hay 1 quyết định kiến trúc cụ thể (architecture.md),
> mà là ràng buộc/hành vi hệ thống xuyên suốt: luồng lỗi, giới hạn, bảo mật, hiệu năng.

---

<!-- tier:2 role:cto,designer,dev-be,mobile,devops,qa story:US-000 -->
### US-000: (ví dụ mẫu — xoá khi có story thật)

**Luồng lỗi hệ thống (error states):**
- Mất kết nối mạng giữa lúc thao tác → <hành vi mong đợi>
- Timeout backend → <hành vi mong đợi, mã lỗi trả về>

**Giới hạn (rate limit, kích thước, số lượng):** <...>

**Yêu cầu bảo mật đặc thù (nếu có):** <vd mã hoá field nào, không log field nào>

**Yêu cầu hiệu năng (nếu có):** <vd P95 response time>

**Điều kiện QA phải test riêng cho mục này:** <liệt kê — QA dùng đúng mục này để bổ sung acceptance criteria phi-chức-năng ngoài PRD>
