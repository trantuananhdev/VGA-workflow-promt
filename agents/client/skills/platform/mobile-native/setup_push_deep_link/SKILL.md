# skill_setup_push_deep_link

**Dùng bởi:** `mobile` (riêng).

**Mục tiêu:** Thiết lập push notification (FCM/APNs) và deep linking (universal link/app link) ở tầng hạ tầng — KHÔNG phải nội dung push cụ thể cho 1 story (đó là `dev-be`/phase `client-screen` dùng hạ tầng này khi cần).

**Quy trình:**
```
1. Đăng ký app với FCM/APNs, lấy config key.
2. Cấu hình universal link (iOS)/app link (Android) trỏ về đúng domain đã thống nhất
   trong shared/architecture.md.
3. Test: gửi 1 push thử + mở 1 deep link thử, xác nhận app nhận đúng.
```

**Output:** Config key + routing deep link đã hoạt động, ghi vào `shared/capabilities/client.json`.

**Verify bắt buộc:** Push thử phải tới thiết bị thật (hoặc emulator có Google Play Service), deep link thử phải mở đúng màn hình — không suy diễn "chắc là cấu hình đúng" khi chưa test thật.
