# skill_setup_monitoring

**Dùng bởi:** `devops` (phase `devops-release`, chạy 1 lần khi release đầu tiên, sau đó chỉ verify còn sống).

**Mục tiêu:** Kết nối sản phẩm với Sentry/Crashlytics (hoặc tool tương đương) sao cho lỗi thật sinh ra event `crash_alert`/`error_alert` — đây chính là đầu vào của Runtime Mode entry point trong `kernel/rules/routing-table.md`.

**Áp dụng cho MỌI `delivery_target`** (đây là mối nối duy nhất giữa Build Mode và Runtime Mode nên nó không rẽ nhánh theo loại sản phẩm), nhưng nguồn event khác nhau: `mobile_native` → crash SDK trên thiết bị; `web_app` → lỗi JS phía browser + lỗi render phía server; `backend_service` → exception chưa bắt + tỉ lệ 5xx + health check trượt.

**Quy trình:**
```
1. Tạo project trên Sentry/Crashlytics, lấy DSN/config key.
2. Tích hợp SDK vào code (theo skill lint/test riêng của dev-be/client để không phá build).
   Với web: nhớ upload source map, nếu không stack trace vô dụng (lỗi này chỉ lộ ra khi có
   crash thật đầu tiên — đúng lúc không muốn phát hiện thêm vấn đề).
3. Cấu hình webhook: crash mới trên Sentry/Crashlytics → tạo message `type: handoff`
   vào kernel/mailbox/ với event: crash_alert, to: dev-be hoặc client (tuỳ stack trace).
4. Test bằng cách trigger 1 crash giả lập, xác nhận message xuất hiện trong mailbox trong vòng vài phút.
```

**Output:** DSN/config đã gắn vào code, webhook hoạt động.

**Verify bắt buộc:**
```
# Trigger crash giả lập
# Kiểm tra kernel/mailbox/ có message mới với event: crash_alert trong <5 phút
```
Không được báo "xong" nếu chưa thực sự trigger thử và thấy message xuất hiện — không suy diễn "chắc là sẽ hoạt động".
