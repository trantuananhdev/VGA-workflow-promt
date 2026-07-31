# skill_run_tests

**Dùng bởi:** `qa` (riêng).

**Input:** story_id, build artifact từ `dev-be` + `client` (phase `client-screen`)

**Quy trình:**
```
1. Liệt kê toàn bộ acceptance criteria + edge case của story_id (từ shared/PRD.md slice)
   và điều kiện phi-chức-năng liên quan (từ shared/system-spec.md slice).
2. Với MỖI mục, phải có ít nhất 1 test case tương ứng — nếu thiếu, tự bổ sung test trước khi chạy,
   không được bỏ qua mục nào.
3. Chạy test suite thật (lệnh cụ thể — STACK BINDING, điền khi chọn công nghệ):
   <TODO: điền lệnh test thật của dự án>
4. Nếu fail: viết bug_report.md kèm nguyên văn log lỗi + bước tái hiện.
5. Nếu pass: đính kèm log pass thật vào handoff envelope, KHÔNG chỉ ghi "tests passed".
```

**Verify:** đúng nguyên tắc "No LGTM without proof" trong `agents/qa/AGENT.md` — mọi PASS/FAIL đều phải có log đính kèm.
