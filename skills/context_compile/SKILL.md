# skill_context_compile

**Mục tiêu:** Trích đúng Tier 2 context (đúng story/role) từ `shared/*.md` — KHÔNG dùng LLM để tóm tắt, chỉ parse anchor tag xác định.

**Input:** `role`, `story_id` (hoặc `task_id`), danh sách file nguồn (`shared/PRD.md`, `shared/architecture.md`, ...)

**Quy trình (xác định, không phải suy luận):**
```
1. Với mỗi file nguồn, tìm block có comment
   <!-- tier:2 role:<...> story:<story_id> -->
   mà role cần khớp với role đang request.
2. Trích nguyên block đó (từ tag tới tag/heading tiếp theo cùng cấp).
3. Gộp các block trích được thành 1 bundle.
4. Nếu KHÔNG tìm thấy tag nào khớp -> trả lỗi rõ ràng
   "no tier-2 context found for role=<x> story=<y>", KHÔNG tự bịa nội dung,
   KHÔNG fallback đọc nguyên file.
5. Cache bundle vào kernel/memory/ (hoặc context/<task_id>.context.json nếu dự án
   cần) kèm checksum nguồn — nếu nguồn không đổi, dùng lại cache lần sau.
```

**Output:** bundle text (Tier 2) sẵn sàng ghép với Tier 0 (kernel digest) + Tier 1 (role policy) thành boot context.

**Verify:** đếm token bundle, PHẢI nằm trong `max_context_tokens` của `manifest.json` role đó — nếu vượt, báo lỗi cho Orchestrator thay vì tự cắt bớt ngẫu nhiên.
