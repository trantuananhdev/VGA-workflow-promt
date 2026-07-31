# architecture.md — Quyết định kỹ thuật (SSOT, do CTO ghi)

> Cùng quy ước anchor tag như `PRD.md`: `<!-- tier:2 role:cto,dev-be,client,devops,ads story:<STORY_ID> -->`
>
> `story:PROJ` là khoá đặc biệt cho nội dung cấp project — `context_compile.py` dùng nó làm
> Tier 2 cho MỌI node `scope: project`/`release` (`client-shell`, `devops-infra`, `ads-setup`,
> `design-system`, `devops-release`). Thiếu khối này = các node đó nhận Tier 2 rỗng, và
> `context_compile.py` sẽ **chặn dispatch** (không còn âm thầm cho qua — xem `validate.py` mã `E9`).

---

<!-- tier:2 role:cto,dev-be,client,devops,ads story:PROJ -->
### PROJ: Ràng buộc kỹ thuật cấp project

> Do CTO ghi 1 lần/project, trước Gate 1. (Ví dụ mẫu — xoá khi có project thật.)

**Loại sản phẩm (`delivery_targets`):** <mobile_native | web_app | backend_service — 1 hoặc nhiều>
> Đây là bản prose của `shared/contracts/tech-stack.json` → `delivery_targets`, **suy ra từ đề bài**
> (`product_signals`) bằng `agents/cto/skills/decide_tech_stack/`. 2 file phải nói cùng 1 sự thật:
> file này cho người đọc hiểu **vì sao**, JSON cho máy đọc (kernel bật/tắt unit trong DAG).
> Nêu luôn tín hiệu quyết định + phương án đã loại, đừng chỉ ghi kết luận.

**Tech stack đã chọn:** <client: ngôn ngữ/framework + platform_pack | backend: ngôn ngữ/framework/DB — chỉ ghi phần project THẬT có>
**Hạ tầng cần dựng (`devops-infra`):** <môi trường, CI/CD, dịch vụ ngoài>
**Ngưỡng nền tảng tối thiểu (`client-shell`):** <mobile: vd iOS 15+/Android 8+ | web: browserslist + render mode (SPA/SSR/SSG) kèm lý do>
**Kiểu phát hành (`devops-release`, Gate 6):** <store submit | deploy URL production | deploy API + migration — theo từng target>
**Mediation/network quảng cáo dự kiến (`ads-setup`, chỉ nếu project có monetization):** <hoặc `không áp dụng`>
**Rủi ro kỹ thuật cấp project đã biết:** <...>

---

<!-- tier:2 role:cto,dev-be,client,devops,ads story:US-000 -->
### US-000: (ví dụ mẫu)

**Tech stack liên quan:** <...>
**Thiết kế API liên quan:** xem `api-contracts.json`
**Thiết kế DB liên quan:** xem `db-schema.md`
**Rủi ro kỹ thuật đã biết:** <...>
