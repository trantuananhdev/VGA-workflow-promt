# skill_generate_wireframe

**Dùng bởi:** `designer`, phase `designer-screen` (riêng, không dùng chung role khác).

**Mục tiêu:** Từ 1 User Story (PRD slice) + data shape (`api-contracts.json` slice) + design token đã khoá (`tokens.json`) + domain của story (`domain-map.json`), sinh layout JSON — không phải ảnh/prose mô tả, để `mobile` (phase `mobile-screen`) parse trực tiếp thay vì phải "đọc hiểu" mô tả bằng lời.

**Input:** anchor-tag slice của `shared/PRD.md` + `shared/system-spec.md` (story_id đang xử lý) + slice `shared/contracts/api-contracts.json` + slice `shared/contracts/domain-map.json` + `token_keys` từ handoff của `design-system`

**Output:** `shared/design/screens/<story_id>.json`

---

## Quy trình

```
0. NẠP NGỮ CẢNH DOMAIN TRƯỚC KHI VẼ  (bước mới — xem agents/designer/skills/domain/SKILL.md)
   domains = domain-map.json.stories[story_id].domains        # có thể NHIỀU domain
   với mỗi domain: đọc agents/designer/skills/domain/<tag>/SKILL.md
   -> lấy: pattern UX chuẩn, pitfall, quy ước platform, checklist a11y đặc thù
   Domain `primary` quyết định layout chính; domain phụ chỉ bổ sung state/pitfall.
   KHÔNG có thư mục skill cho 1 tag -> cơ chế bootstrap `draft: true`, xem domain/SKILL.md.

1. Với mỗi acceptance criteria trong story, xác định 1 màn hình/trạng thái UI tương ứng.

2. Với mỗi error state liệt kê trong shared/system-spec.md (cùng story_id), PHẢI có 1 UI state
   tương ứng — không được chỉ vẽ happy path.

3. ĐỐI CHIẾU VỚI DOMAIN: domain skill liệt kê state mà app loại này LUÔN cần
   (vd on-demand-booking luôn cần "chờ đối tác xác nhận" + "huỷ/đổi lịch").
   State nào domain đòi mà PRD KHÔNG nêu -> KHÔNG tự thêm vào layout, cũng KHÔNG bỏ qua:
   mở Sync Session với `ba` (max_turns: 3) hỏi story có cần state đó không.
   Đây là giá trị chính của domain skill: phát hiện thiếu sót của PRD TRƯỚC khi vẽ,
   thay vì để QA phát hiện ở Gate 4.

4. Sinh layout JSON:
   { screen_id, states: [...], components: [...], data_bindings: [...], ad_slots: [...] }
   - data_bindings PHẢI khớp field thật trong api-contracts.json slice — không bịa field.
   - MỌI giá trị style là chuỗi "token:<nhóm>.<key>" trỏ key phẳng trong tokens.json.
     ĐÚNG:  "bg": "token:color.surface", "pad": "token:spacing.md"
     SAI:   "bg": "#FFFFFF",            "pad": 16
     Không có key phù hợp -> KHÔNG tự thêm token (không phải writer của tokens.json)
     và KHÔNG hard-code tạm; emit doc_drift_detected.

5. Ghi vào shared/design/screens/<story_id>.json
```

## Vì sao token là TÊN chứ không phải giá trị

Handoff từ `design-system` cố ý chỉ mang **tên** key. Nếu layout mang giá trị thật thì 20 story sẽ có 20 bản sao của cùng 1 mã màu — và không có cách nào (ngoài mắt người nhìn app đã build) biết được chúng có còn khớp nhau hay không. Trỏ tên thì tính nhất quán **kiểm được bằng máy** (Gate 5 điều 5), và đổi theme về sau chỉ sửa `tokens.json`, không phải sửa N file layout.

## Verify trước khi emit handoff sang `mobile`

- Số UI state ≥ số (acceptance criteria + error state) liệt kê cho story đó — thiếu là chưa xong.
- Mọi `data_bindings` trỏ tới field **tồn tại** trong `api-contracts.json` slice — field lạ = lỗi, sửa trước khi handoff.
- **Tự quét lại toàn bộ layout tìm giá trị style hard-code** (chuỗi bắt đầu `#`, số trần ở field spacing/radius/size). Còn 1 chỗ = Gate 5 fail. Đừng để gate bắt việc mình tự kiểm được.
- Mọi `token:` trỏ key **tồn tại** trong `token_keys` đã nhận từ handoff.
- Handoff body đủ field theo cạnh `designer-screen → mobile-screen` trong `kernel/rules/handoff-contracts.md`: `ui_states_count`, `data_bindings_summary`, `domains_applied` (+ `draft_domains` nếu có), `token_keys_used`, có slot quảng cáo hay không.
