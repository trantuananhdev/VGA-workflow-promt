# skill_check_platform_compliance

**Dùng bởi:** `mobile`, phase `mobile-shell`.

**Khác gì `check_app_store_policy` của `devops`?** Cái đó soi **metadata** lúc submit (tên, mô tả, từ khoá, screenshot). Skill này soi **yêu cầu kỹ thuật nền tảng** của chính app — thứ phải đúng từ lúc dựng shell, không phải lúc submit mới sửa (sửa lúc đó thì phải build lại toàn bộ).

**Mục tiêu:** Đảm bảo native shell đáp ứng ngưỡng kỹ thuật bắt buộc hiện hành của Google Play/App Store TRƯỚC khi phase `mobile-screen` bắt đầu code lên trên.

**Input:** native project đã dựng (sau `setup_native_shell`) + `shared/system-spec.md` slice (nếu spec ghi rõ min OS version mong muốn)

**Quy trình:**
```
1. Target SDK / deployment target: kiểm tra đạt ngưỡng TỐI THIỂU mà store đang bắt buộc
   (2 store đều siết định kỳ hàng năm — tra ngưỡng hiện hành, KHÔNG tin số hard-code
   trong tài liệu cũ của repo).
2. Kiến trúc build: Android phải có 64-bit; kiểm tra không sót ABI nào chỉ 32-bit.
3. Khai báo bắt buộc theo nền tảng:
   - iOS: privacy manifest cho SDK dùng trong app; mô tả lý do cho MỌI permission
     trong Info.plist (thiếu mô tả = reject, không phải warning).
   - Android: data safety declaration khớp với permission thật đã khai;
     foreground service type nếu dùng service.
4. API deprecated: quét cảnh báo deprecated ở mức chặn build/submit (không phải mọi
   deprecated warning — chỉ loại store thật sự từ chối).
5.5. KÍCH THƯỚC MÀN HÌNH — đối chiếu shell với shared/design/tokens.json ->
   responsive_contract (do design-system chốt theo system-spec.md):
   - `screenOrientation`/`UISupportedInterfaceOrientations` của shell phải KHỚP
     `target_orientations`. Shell pin portrait mà contract khai có `landscape` (hoặc
     ngược lại) = vi phạm — và đây là loại lỗi mà mọi story build lên trên đều thừa hưởng.
   - Shell phải xử lý inset hệ thống ở tầng theme/window (edge-to-edge + safe area),
     không để từng story tự bù: `mobile-screen` khai `responsive.safe_area` theo
     component, nhưng nếu window không cấp inset thật thì mọi khai báo đó là giấy tờ.
   - Shell KHÔNG được chặn/ghi đè font scale hệ thống (vd fontScale = 1 cứng). Contract
     cam kết layout đúng tới `max_font_scale` (mặc định 2.0); shell khoá cỡ chữ là biến
     cam kết đó thành không kiểm được, và là 1 lỗi a11y thật.
6. Đối chiếu kết quả với shared/capabilities/native.json — mọi permission liệt kê ở đó
   phải có mô tả lý do hợp lệ; permission không có story_id nào cần = phải gỡ
   (least-privilege, xem AGENT.md).
```

**Output:**
```json
{ "pass": true, "violations": [], "target_sdk": null, "min_os": null, "checked_at": "<timestamp>" }
```

**Verify (điều kiện của Gate 3 cho phase `mobile-shell`):** nếu `violations` không rỗng, phase `mobile-shell` KHÔNG được emit handoff mở khoá `mobile-screen` — phải sửa shell trước. Lý do cứng: để `mobile-screen` code hàng loạt story lên trên 1 shell không đạt chuẩn thì lúc phát hiện phải sửa cả shell VÀ mọi story đã build trên đó.

> **STACK BINDING:** ngưỡng target SDK/min OS thay đổi theo thời gian và theo store —
> KHÔNG hard-code vào file này. Tra ngưỡng hiện hành lúc chạy; nếu đã từng bị reject vì
> mục nào, ghi vào `agents/devops/docs/store-keyword-blocklist.md` (mục kỹ thuật) +
> `shared/lessons_learned.md` để lần sau không lặp lại.
