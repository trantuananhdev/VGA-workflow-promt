# skill_setup_host_application

**Dùng bởi:** `mobile` (riêng — phase `client-shell`, chạy SAU `clone_vga31_template`).

**Mục tiêu:** Tạo lớp `HostApplication` (hoặc `MyApplication`) kế thừa
`com.brian.base_application.BaseApplication`, override đúng đủ các hàm abstract,
cung cấp tài nguyên bắt buộc — đảm bảo app chạy được qua luồng
`Splash → Inter → Language → IAP → Home` của thư viện.

## Tiền đề

- Skill `clone_vga31_template` đã chạy xong (project đã build được).
- `base-application/base-application-1.0.0.aar` + `base-application/build.gradle` ĐÃ có
  trong project (không sửa).

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

**Trước khi viết bất kỳ dòng code nào**, agent PHẢI mở và đọc toàn bộ file:

```
shared/quy-trinh-xay-dung-app/vga31-kotlin/base-application/HUONG_DAN_TICH_HOP.md
```

Đây là specification chính thức (1302 dòng) của `base-application` AAR. Mọi override,
resource name, luồng runtime, pitfall đều nằm ở đây.

## Quy trình

```
1. TẠO lớp HostApplication (ví dụ: MyApplication.kt):
   - Đặt trong package root (APPLICATION_ID).
   - Kế thừa BaseApplication(): import com.brian.base_application.BaseApplication
   - Nếu dùng Hilt: annotate @HiltAndroidApp.
   - PHẢI gọi super.onCreate() trong onCreate().

2. OVERRIDE tất cả hàm abstract (THIẾU MỘT = KHÔNG BIÊN DỊCH):

   ┌─────────────────────────────────────────────────────────────────┐
   │ NHÓM              │ HÀM                          │ GHI CHÚ    │
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ Splash & thương    │ getAppNameRes(): Int          │ R.string.  │
   │ hiệu              │ getIconSplashRes(): Int       │ R.drawable │
   │                    │ getSplashLoadingRes(): Int    │ R.raw.     │
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ Định tuyến         │ getHomeActivity()             │ MainActivity│
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ Năng lực           │ hasForegroundServicePermission│ true       │
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ Khởi tạo           │ initAppFlyerId()              │ AppFlyer   │
   │                    │ setupKoin()                   │ trống nếu  │
   │                    │                               │ không dùng │
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ Ngôn ngữ           │ notifyLanguageSaved(code)     │ Lưu prefs  │
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ IAP keys           │ iapPremiumKey()               │ Product ID │
   │                    │ iapPremiumWeeklyKey()         │ Subscription│
   │                    │ iapPremiumMonthlyKey()        │ Subscription│
   │                    │ iapPremiumYearlyKey()         │ Subscription│
   │                    │ iapPublicKey()                │ License key│
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ IAP icon (5 cặp)   │ getFeature1IconRes() →        │ R.drawable │
   │                    │ getFeature5IconRes()          │ 5 icon     │
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ Dialog thông báo   │ getNotiTitleRes()             │ R.string.  │
   │                    │ getNotiContentRes()           │ R.string.  │
   ├────────────────────┼───────────────────────────────┼────────────┤
   │ Bộ thông báo       │ getNotificationImages()      │ IntArray 5 │
   │ (ghép theo index)  │ getNotificationIconRes()     │ R.drawable │
   │                    │ getNotificationChannelPrefix()│ String     │
   │                    │ getNewFileNotiContentRes()    │ R.string.  │
   │                    │ getScreenshotNotiTitleRes()   │ R.string.  │
   │                    │ getRecentDocumentsTitleRes()  │ R.string.  │
   │                    │ getOpenTextRes()              │ R.string.  │
   │                    │ getScanDocumentRes()          │ R.string.  │
   │                    │ getWidgetButtonBackgroundRes()│ R.drawable │
   │                    │ getDailyCallOpenAppContentRes│ R.string.  │
   │                    │ getCheckNowTextRes()          │ R.string.  │
   │                    │ getDocumentPreviewRes()       │ R.drawable │
   │                    │ getFullScreenNoti1Res()       │ R.string.  │
   │                    │ getFullScreenNoti2Res()       │ R.string.  │
   │                    │ getNotificationTitles2ArrayRes│ R.array.(5)│
   │                    │ getNotificationMessages2Array │ R.array.(5)│
   │                    │ getNotificationButtons2Array  │ R.array.(5)│
   │                    │ getNotificationOutAppTitleRes │ R.string.  │
   │                    │ getNotificationOutAppContent  │ R.string.  │
   └─────────────────────────────────────────────────────────────────┘

   ⚠️ QUAN TRỌNG: Mọi string/array PHẢI hợp chủ đề app mới.
   ĐỪNG bê nguyên nội dung mẫu "tài liệu/PDF" sang app khác chủ đề.
   3 mảng notification (title2, message2, button2) PHẢI đúng 5 phần tử,
   khớp 1-1 với getNotificationImages() — lệch = crash ArrayIndexOutOfBounds.

3. TẠO tài nguyên bắt buộc (xem §5 trong HUONG_DAN_TICH_HOP.md):
   - res/values/colors.xml: primaryColor, accentTone (= primaryColor), text1
   - res/values-night/colors.xml: text1 (giá trị giống values/)
   - res/drawable/icon_app.xml hoặc .png (icon splash)
   - res/drawable-{m,h,xh,xxh,xxxh}dpi/icon_notification.png (5 mật độ, alpha-only)
   - res/drawable/img_document_preview.png (365×174dp)
   - icon_1_iap…icon_5_iap (32×32dp) — 5 icon tính năng IAP
   - icon_noti_1…icon_noti_5 (32×32dp) — 5 icon thông báo
   - res/raw/splash_loading.json (Lottie, màu khớp primaryColor)
   - assets/default_ads_config.json (ad unit config)
   - strings.xml: app_name, app_flyer_id, admob_app_id, facebook_app_id,
     facebook_client_token, public_license_key
   - string-array: notification_title2 (5), notification_message2 (5),
     notification_button2 (5)

4. CẬP NHẬT AndroidManifest.xml:
   - android:name=".MyApplication" (hoặc tên class vừa tạo)
   - meta-data AdMob + Facebook (§4.3)
   - KHÔNG khai MAIN/LAUNCHER (§4.4)
   - Đủ 4 quyền bắt buộc: FOREGROUND_SERVICE, FOREGROUND_SERVICE_SPECIAL_USE,
     POST_NOTIFICATIONS, AD_ID (§4.2)

5. (TUỲ CHỌN) Override hàm open (§6.2 trong HUONG_DAN_TICH_HOP):
   - isPurchased() → IAPUtils.isPremium()
   - enableAdsResume() → !IAPUtils.isPremium()
   - getListTestDeviceId() → danh sách test device
   - buildDebug() → BuildConfig.DEBUG
```

## Output

- File `MyApplication.kt` (hoặc tên HostApplication) biên dịch được.
- Resources đầy đủ theo §5.
- Manifest hợp lệ theo §4.
- Build `assembleDebug` pass.

## Verify

- Chạy `./gradlew :app:assembleDebug` thành công.
- Grep manifest merged: không có `MAIN/LAUNCHER` trùng, chỉ 1 launcher (Splash của lib).
- 3 string-array (notification) đều đúng 5 phần tử.

## KHÔNG ĐƯỢC LÀM

- ❌ KHÔNG sửa `base-application/` — module này giữ nguyên.
- ❌ KHÔNG tự init ads/consent — thư viện tự chạy trong splash.
- ❌ KHÔNG khai MAIN/LAUNCHER — launcher là Splash của lib.
- ❌ KHÔNG tạo subclass `FirebaseRemoteConfigUtil` với companion riêng — singleton song song.
- ❌ KHÔNG dùng `defaultIap*Key()` nếu app đã có key thật.
