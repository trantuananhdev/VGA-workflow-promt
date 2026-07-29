# lessons_learned.md — Ghi bởi Evolution protocol (xem ORCHESTRATOR.md §9)

Chỉ ghi khi: 1 pattern có thể tái dùng, trái trực giác, hoặc gây tốn nhiều turns/gate-fail. Mỗi mục nêu rõ nguyên nhân gốc và rule/skill nào đã được cập nhật để tránh lặp lại — không ghi chung chung.

---

<!-- Ví dụ format:
## [YYYY-MM-DD] US-014 — Sync Session BA-CTO vượt max_turns 2 lần liên tiếp
Nguyên nhân gốc: PRD thiếu acceptance criteria cho case OTP hết hạn, khiến CTO phải hỏi lại nhiều lần.
Đã cập nhật: agents/ba/rules/_role_policy.md — bắt buộc mỗi story phải có acceptance criteria
cho MỌI edge case liệt kê, không chỉ happy path, trước khi emit handoff sang CTO.
-->
