# skill_generate_wireframe

**Dùng bởi:** `designer` (riêng, không dùng chung role khác).

**Mục tiêu:** Từ 1 User Story (PRD slice) + data shape (`api-contracts.json` slice), sinh layout JSON — không phải ảnh/prose mô tả, để `mobile` (phase `mobile-screen`) parse trực tiếp thay vì phải "đọc hiểu" mô tả bằng lời.

**Input:** anchor-tag slice của `shared/PRD.md` (story_id đang xử lý) + slice tương ứng trong `shared/contracts/api-contracts.json`

**Quy trình:**
```
1. Với mỗi acceptance criteria trong story, xác định 1 màn hình/trạng thái UI tương ứng.
2. Với mỗi error state liệt kê trong shared/system-spec.md (cùng story_id), PHẢI có 1 UI state
   tương ứng — không được chỉ vẽ happy path.
3. Sinh layout JSON: { screen_id, components: [...], data_bindings: [...] } —
   data_bindings phải khớp field thật trong api-contracts.json slice, không tự bịa field.
4. Ghi vào shared/design/<story_id>.json
```

**Output:** `shared/design/<story_id>.json`

**Verify trước khi emit handoff sang `mobile`:**
- Số UI state ≥ số (acceptance criteria + error state) liệt kê cho story đó — nếu thiếu, chưa được coi là xong.
- Mọi `data_bindings` phải trỏ tới field tồn tại trong `api-contracts.json` slice — field lạ = lỗi, phải sửa trước khi handoff.
