# skill_setup_native_shell

**Dùng bởi:** `mobile` (riêng).

**Mục tiêu:** Dựng khung native project (permission, manifest, entitlements, min OS version) đúng theo yêu cầu trong `architecture.md`/`system-spec.md` — trước khi phase `mobile-screen` có thể build bất kỳ screen nào lên thiết bị thật.

**Input:** anchor-tag slice của `shared/architecture.md` + `shared/system-spec.md`

**Quy trình:**
```
1. Liệt kê toàn bộ permission/feature native cần thiết được nhắc tới trong 2 file trên
   (camera, location, notification, bluetooth...).
2. Khai báo đúng trong AndroidManifest.xml / Info.plist — kèm mô tả lý do sử dụng
   (bắt buộc với iOS, và là lý do reject phổ biến nếu thiếu — xem
   agents/devops/docs/store-keyword-blocklist.md để tham khảo case tương tự).
3. Set min SDK/OS version theo system-spec.md (nếu có ghi rõ), mặc định theo khuyến nghị
   hiện hành của Google Play/App Store nếu spec không nêu.
4. Ghi lại toàn bộ permission/feature đã khai vào shared/capabilities/native.json.
5. Build thử trên mọi platform mục tiêu — KHÔNG báo xong nếu build fail.
```

**Output:** `shared/capabilities/native.json`

**Verify:** `native.json` khớp 100% với manifest/plist thật (không phải danh sách suy diễn) — Gate 0 kiểm tra token budget như bình thường, nhưng nội dung này còn cần kiểm tra thủ công 1 lần đầu bởi `cto` trong Sync Session xác nhận đủ permission cần thiết cho toàn bộ Epic hiện tại.
