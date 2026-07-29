# PRD.md — Single Source of Truth nghiệp vụ

> Quy ước bắt buộc: mỗi block User Story PHẢI có anchor tag comment ngay phía trên, để `skill_context_compile`
> trích đúng lát cắt (Tier 2) cho từng agent — không phải đọc cả file này mỗi lần.
>
> Format tag: `<!-- tier:2 role:<role1>,<role2> story:<STORY_ID> -->`
>
> **`story:PROJ` là STORY_ID đặc biệt** — dành cho thông tin cấp project (không thuộc story nào).
> `context_compile.py` dùng khoá `PROJ` để trích Tier 2 cho node `scope: project`/`release`
> (`design-system`, `mobile-shell`, `devops-infra`, `ads-setup`) — trước đây những node này
> nhận Tier 2 **rỗng** vì anchor-tag chỉ có trục `story:`.

---

<!-- tier:2 role:ba,cto,designer story:PROJ -->
### PROJ: Design intent cấp project

> Do `ba` viết **1 lần/project**, trước Gate 1. Đây là input DUY NHẤT của phase `design-system` —
> thiếu câu nào thì nó sẽ tự bịa câu đó. Checklist đầy đủ: `agents/ba/AGENT.md` mục B.
> (Ví dụ mẫu — xoá và điền thật khi có project.)

**1. Đối tượng người dùng chính:** <độ tuổi, mức thông thạo công nghệ, hoàn cảnh dùng app — ngoài đường / trong nhà / tay đang bận?>

**2. Tông cảm xúc mong muốn:** <2-3 tính từ> — **KHÔNG** muốn: <2-3 tính từ phản đề>

**3. App tham chiếu (nếu là bài clone/làm giống):** <tên app gốc + giống tới mức nào: giống hoàn toàn | giống luồng nhưng khác nhận diện | chỉ lấy cảm hứng> — hoặc `không có`. Có ảnh chụp thật thì đặt vào `shared/design/references/` (xem README ở đó), **không** dán ảnh vào file này.

**4. Ràng buộc nhận diện:** <màu/logo/font bắt buộc từ brand sẵn có> — hoặc `không có, design-system được tự đề xuất`

**5. Mức accessibility yêu cầu:** `mặc định theo a11y_contract trong shared/design/tokens.json` — hoặc nêu yêu cầu cao hơn

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
