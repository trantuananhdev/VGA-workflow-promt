# skill_integrate_ad_sdk

**Dùng bởi:** `ads` (phase `ads-setup`, chạy 1 lần đầu dự án).

**Input:** `shared/architecture.md` slice (platform, ngôn ngữ/stack đã chọn)

**Quy trình:**
```
1. Chọn ad network chính + mediation (nếu cần nhiều network) — quyết định 1 lần,
   ghi rõ lý do chọn vào shared/capabilities/ads.json (phần "ads").
2. Tích hợp SDK theo docs chính thức của network đã chọn.
3. Cấu hình test ad unit ID trước — KHÔNG dùng ad unit ID thật cho tới khi qua Gate 4.
4. Build thử, xác nhận SDK khởi tạo không lỗi (log khởi tạo SDK đính kèm).
```

**Output:** SDK + mediation config trong repo, `shared/capabilities/ads.json` cập nhật phần `ads`.

**Verify:** Build thành công + log khởi tạo SDK không lỗi. KHÔNG được gọi request quảng cáo thật ở bước này — đó là việc của `ads-placement`, và chỉ sau khi `setup_consent_management` đã xong (xem thứ tự bắt buộc trong `AGENT.md`).
