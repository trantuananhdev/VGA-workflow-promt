# <role>_policy.md — Layer 0, luôn nạp khi agent này chạy

Luật riêng của role này — ngắn gọn, cụ thể, không lặp lại luật global đã có trong `ORCHESTRATOR.md`.

Ví dụ cấu trúc:
- Việc bắt buộc phải làm trước khi báo xong
- Việc tuyệt đối không được tự quyết (phải hỏi role khác qua Sync Session)
- Định dạng output bắt buộc
