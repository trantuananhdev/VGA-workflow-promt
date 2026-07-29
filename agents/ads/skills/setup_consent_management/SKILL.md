# skill_setup_consent_management

**Dùng bởi:** `ads` (phase `ads-setup`) — đây là bước BẮT BUỘC phải xong TRƯỚC khi bất kỳ ad nào được request, không có ngoại lệ.

**Mục tiêu:** Thiết lập luồng xin sự đồng ý người dùng trước khi cá nhân hoá/hiển thị quảng cáo — theo GDPR (EU, dùng chuẩn IAB TCF/Google UMP) và App Tracking Transparency (iOS, bắt buộc từ iOS 14.5+).

**Quy trình:**
```
1. Tích hợp Google UMP SDK (hoặc CMP tương đương) cho luồng GDPR/consent.
2. Tích hợp prompt ATT (iOS) — hiển thị đúng thời điểm khuyến nghị của Apple
   (thường sau khi user đã hiểu giá trị app, không phải ngay lúc mở app lần đầu).
3. Test 3 case: user đồng ý toàn bộ / user từ chối / user ở khu vực không cần
   GDPR — xác nhận app xử lý đúng cả 3 case (không crash, không gọi ad request
   khi bị từ chối tracking).
```

**Output:** Consent flow hoạt động, log test 3 case.

**Verify bắt buộc:** Log chứng minh thứ tự đúng — consent flow chạy XONG trước khi `integrate_ad_sdk` cho phép request quảng cáo đầu tiên. Đây là điều kiện tiên quyết cứng của `check_ad_policy`, không phải tuỳ chọn.
