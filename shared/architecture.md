# architecture.md — Quyết định kỹ thuật (SSOT, do CTO ghi)

> Cùng quy ước anchor tag như `PRD.md`: `<!-- tier:2 role:cto,dev-be,mobile,devops,ads story:<STORY_ID> -->`
>
> `story:PROJ` là khoá đặc biệt cho nội dung cấp project — `context_compile.py` dùng nó làm
> Tier 2 cho MỌI node `scope: project`/`release` (`mobile-shell`, `devops-infra`, `ads-setup`,
> `design-system`, `devops-release`). Thiếu khối này = các node đó nhận Tier 2 rỗng, và
> `context_compile.py` sẽ **chặn dispatch** (không còn âm thầm cho qua — xem `validate.py` mã `E9`).

---

<!-- tier:2 role:cto,dev-be,mobile,devops,ads story:PROJ -->
### PROJ: Ràng buộc kỹ thuật cấp project

> Do CTO ghi 1 lần/project, trước Gate 1. (Ví dụ mẫu — xoá khi có project thật.)

**Tech stack đã chọn:** <ngôn ngữ/framework mobile, backend, DB>
**Hạ tầng cần dựng (`devops-infra`):** <môi trường, CI/CD, dịch vụ ngoài>
**Platform + min OS (`mobile-shell`):** <vd iOS 15+, Android 8+>
**Mediation/network quảng cáo dự kiến (`ads-setup`, chỉ nếu project có monetization):** <hoặc `không áp dụng`>
**Rủi ro kỹ thuật cấp project đã biết:** <...>

---

<!-- tier:2 role:cto,dev-be,mobile,devops,ads story:US-000 -->
### US-000: (ví dụ mẫu)

**Tech stack liên quan:** <...>
**Thiết kế API liên quan:** xem `api-contracts.json`
**Thiết kế DB liên quan:** xem `db-schema.md`
**Rủi ro kỹ thuật đã biết:** <...>
