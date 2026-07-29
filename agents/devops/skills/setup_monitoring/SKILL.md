# skill_setup_monitoring

**Dùng bởi:** `devops` (phase `devops-release`, chạy 1 lần khi release đầu tiên, sau đó chỉ verify còn sống).

**Mục tiêu:** Kết nối app với Sentry/Crashlytics (hoặc tool tương đương) sao cho crash thật sinh ra event `crash_alert` — đây chính là đầu vào của Runtime Mode entry point `crash_alert` trong `kernel/rules/routing-table.md`.

**Quy trình:**
```
1. Tạo project trên Sentry/Crashlytics, lấy DSN/config key.
2. Tích hợp SDK vào code (theo skill lint/test riêng của dev-be/mobile để không phá build).
3. Cấu hình webhook: crash mới trên Sentry/Crashlytics → tạo message `type: handoff`
   vào kernel/mailbox/ với event: crash_alert, to: dev-be hoặc mobile (tuỳ stack trace).
4. Test bằng cách trigger 1 crash giả lập, xác nhận message xuất hiện trong mailbox trong vòng vài phút.
```

**Output:** DSN/config đã gắn vào code, webhook hoạt động.

**Verify bắt buộc:**
```
# Trigger crash giả lập
# Kiểm tra kernel/mailbox/ có message mới với event: crash_alert trong <5 phút
```
Không được báo "xong" nếu chưa thực sự trigger thử và thấy message xuất hiện — không suy diễn "chắc là sẽ hoạt động".
