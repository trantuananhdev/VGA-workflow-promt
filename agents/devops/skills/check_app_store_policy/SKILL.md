# skill_check_app_store_policy

**Dùng bởi:** `devops` (riêng, phase `devops-release`).

**Mục tiêu:** Quét metadata (tên app, mô tả, từ khoá, screenshot text nếu có) trước khi submit App Store/Google Play, tránh bị reject vì từ khoá nhạy cảm hoặc thiếu field bắt buộc.

**Input:** metadata release (tên, mô tả, category, screenshots, privacy policy URL)

**Quy trình:**
```
1. Kiểm tra đủ field bắt buộc theo checklist store (tên, category, privacy policy URL, content rating).
2. Quét mô tả + tên app theo danh sách từ khoá cấm/nhạy cảm — danh sách này lưu ở
   agents/devops/docs/store-keyword-blocklist.md (cập nhật khi có case thực tế bị reject).
3. Kiểm tra permission khai báo (camera, location...) có mô tả lý do sử dụng rõ ràng không —
   thiếu mô tả là lý do reject phổ biến.
```

**Output:**
```json
{ "pass": true, "violations": [], "checked_at": "<timestamp>" }
```

**Verify:** nếu `violations` không rỗng, `devops` KHÔNG được submit — phải quay lại sửa metadata trước, không được submit "thử xem có bị reject không".

> Ghi chú: danh sách từ khoá cấm khác nhau theo từng store và thay đổi theo thời gian — đây là
> lý do file blocklist tách riêng ở `docs/`, không hard-code trong SKILL.md này (Layer 1, cập nhật
> độc lập không cần sửa logic skill).
