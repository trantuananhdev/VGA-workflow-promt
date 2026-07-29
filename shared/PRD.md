# PRD.md — Single Source of Truth nghiệp vụ

> Quy ước bắt buộc: mỗi block User Story PHẢI có anchor tag comment ngay phía trên, để `skill_context_compile`
> trích đúng lát cắt (Tier 2) cho từng agent — không phải đọc cả file này mỗi lần.
>
> Format tag: `<!-- tier:2 role:<role1>,<role2> story:<STORY_ID> -->`

---

<!-- tier:2 role:ba,cto,designer,dev-be,mobile,qa story:US-000 -->
### US-000: (ví dụ mẫu — xoá khi có story thật)

**Mô tả:** <như một người dùng, tôi muốn...>

**Edge cases:**
- <case 1>
- <case 2>

**Acceptance criteria:**
- <tiêu chí 1>
- <tiêu chí 2>

**Monetization:** true | false — bắt buộc có ở MỌI story (không để trống). `true` → `generate_wbs` tạo thêm node `ads-placement` cho story này (chỉ khi capability-agent `ads` đang active — xem `kernel/memory/project-profile.json`). Nếu `true`, phải nêu rõ loại quảng cáo mong muốn (banner/interstitial/rewarded) và tần suất trong Acceptance criteria — `ads` không tự quyết loại/tần suất.

**Trạng thái:** draft | ba-cto-signoff | in-dev | in-qa | released
