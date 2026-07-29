# Gate 4 — QA → Release

**Chạy khi:** `qa` emit `type: handoff` báo kết quả test cho 1 story/release.

**Điều kiện PASS (tất cả phải đúng):**
1. Mọi acceptance criteria + edge case trong `shared/PRD.md` (story liên quan) có test tương ứng, kết quả pass — `artifact_refs` trỏ file log thật (không dán nguyên văn vào body — sẽ nổ context của `devops`).
2. Điều kiện phi-chức-năng liên quan trong `shared/system-spec.md` đã được test riêng.
3. Test coverage đạt ngưỡng đã thống nhất của dự án (`skill_check_coverage`).
4. Smoke test: app khởi động không crash.
5. **Điều kiện bổ sung nếu story có `Monetization: true`:** `skill_check_ad_policy` (agent `ads`) trả `violations: []` — xem `agents/ads/skills/check_ad_policy/SKILL.md`. Story monetization không được pass Gate 4 nếu thiếu điều kiện này, dù 1-4 đã đạt.

**Khi FAIL:** `qa` emit `bug_report.md` + `type: handoff` về đúng agent gây lỗi (`dev-be` cho lỗi backend, `mobile` cho lỗi client, `ads` cho vi phạm điều 5) — vòng quay lại Gate 3.

**Khi PASS:** trigger `devops` (phase `devops-release`) — merge vào `main` chính là hành động trigger pipeline release (xem `skills/git_workflow/SKILL.md`), không có bước "deploy tay" riêng.
