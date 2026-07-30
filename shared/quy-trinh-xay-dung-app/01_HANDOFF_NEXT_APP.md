# TỔNG QUAN — Kiến trúc chung & bài học khi làm app Android mới (Kotlin, Compose)

> Nén kinh nghiệm thực chiến từ các app đã làm (vga31a, vga31b...) để làm app tiếp theo nhanh & không vấp lại lỗi cũ.
> Đọc file này TRƯỚC. Chi tiết cấu trúc app mẫu: `09_KIEN_TRUC_APP_vga31b-kotlin.md`.

---

## 0. TÀI SẢN CÓ SẴN (tái dùng)

- **App Kotlin mẫu hoàn chỉnh**: `vga31b-kotlin` (com.supportsoftware.checkerpro) — dùng làm **khuôn** khi bắt đầu app mới (mới nhất, đủ mọi fix).
- **Keystore**: `vga49a/keystore/VGA<xx>/keystore.jks` + `pass.txt` (storePassword/keyAlias/keyPassword) cho từng app.
- **Publisher AdMob chung**: `ca-app-pub-9405071173323068`.
- **Lib dùng chung**: `base-application-1.0.0.aar` (sở hữu Splash→Inter→Language→IAP→getHomeActivity; ads/consent/FCM/IAP). Abstract methods TÊN ĐỌC ĐƯỢC. Xem `08_HUONG_DAN_TICH_HOP_base-application.md` (spec đầy đủ) + `02_PLAYBOOK_TICH_HOP.md` (quy trình tích hợp).

---

## 1. KIẾN TRÚC (không đổi giữa app)

Lib = vỏ khởi động/monetize (launcher SplashActivity). App: `MyApplication : BaseApplication()` (@HiltAndroidApp) + các màn tính năng (Compose, single-Activity) + tầng ads riêng + Intro. App **KHÔNG** khai MAIN/LAUNCHER, không tự init ads/consent/FCM. Ad unit đọc qua 1 key Remote Config `ads_config` (`FirebaseRemoteConfigUtil.getAdsConfigValue`).

Chi tiết cấu trúc thư mục/package, luồng điều hướng, cách xây 1 chức năng mới: xem `09_KIEN_TRUC_APP_vga31b-kotlin.md`.

## 2. ⚠️ GOTCHAS BẮT BUỘC NHỚ (đã trả giá)

1. **Log**: dùng `println` cho log ads, KHÔNG `android.util.Log` — lib có `-assumenosideeffects android.util.Log` → release xóa hết Log. Đọc: `adb logcat -s System.out | grep -E "ADSLOT|ADS"`.
2. **NativeAdSlot fail**: phải `slot.onError()` + `suppressedAfterError=true` → ẩn slot; thiếu = shimmer kẹt >30s.
3. **Tên hàm không trùng stdlib**: vd hàm tên `parse` trùng `Uri.parse`/`DateFormat.parse` → dễ nhầm/khó trace khi debug. Đặt tên riêng, rõ nghĩa (vd `parsePositions`).
4. **IAP**: lấy key sản phẩm/gói từ nguồn cấu hình riêng của app (không dùng `defaultIap*Key()` mặc định của lib nếu app đã có key thật).
5. **Ads NO_FILL / HTTP 400 ở release** = app CHƯA publish (AdMob chưa nhận diện) — KHÔNG phải lỗi code. Debug dùng **unit test** (fill OK) qua `Remote.adUnit()` guard `BuildConfig.DEBUG`. Chỉ hết sau publish Play + AdMob duyệt.
6. **⭐ Dark mode = chữ/icon xám không đọc được**: nếu `AppTheme(darkTheme: Boolean = isSystemInDarkTheme())` để mặc định tự đổi theo hệ thống, máy bật dark mode → `colorScheme` chuyển sang `DarkColors` (onBackground/onSurface tông sáng) trong khi nền window thật vẫn trắng (app không có bản dark riêng) → chữ/icon xám mờ. **Fix chuẩn**: khoá cứng `darkTheme: Boolean = false` trong `AppTheme()` (KHÔNG gọi `isSystemInDarkTheme()`), giữ nhánh `if (darkTheme) DarkColors else LightColors` để dự phòng chứ không xoá luôn. Ngoài ra: bất kỳ `xxxColorScheme(...)` nào set `background` phải luôn set kèm `onBackground`/`onSurface` tương phản (nếu thiếu, Compose tự điền token M3 mặc định — dễ lệch tông với `background` tuỳ chỉnh).

## 3. LÕI ADS DÙNG LẠI (copy — chỉ đổi package/R/BuildConfig) — xem `06_ADS_REUSABLE_COMPONENTS.md`

`advertisement/{AdsViewModel, NativeAdSlot, AdManager, AdScenario, NativeInter, NativeAdsFull, AdPositions}.kt` + `firebase/Remote.kt` + `core/InstallReferrerHelper.kt` + `res/layout/ad_native_full.xml`.

6 điểm ads: (1) cache native theo Activity, (2) bind 1 lần key(ad), (3) dọn key >7 ngày, (4) native-inter tính tần suất sau khi inter đóng, (5) preload native-inter, (6) positionIntrol A/B Intro. Native list dùng `ads_native_bot_no_media_short_main` + shimmer `ads_native_loading_short_main`; native full-screen dùng `ad_native_full.xml` (bind thủ công setNativeAd).

## 4. NGHIỆM THU (mỗi lần build, đặc biệt release)

- Intro: nút Next bấm được khi ad **fill HOẶC lỗi** (timeout 5s + onResolved).
- Ads kép: tap tile → inter → native-inter fullscreen → điều hướng (+ fallback).
- Build release → **cài máy test lại + đọc log** (`System.out` + GMS `Ads`).
- Slot fail → ẩn (không kẹt shimmer). Đổi ngôn ngữ/night mode không restart splash.

## 5. CẦN CHUẨN BỊ TRƯỚC KHI BẮT ĐẦU APP MỚI khi release (chỉ cần khi release)

- `public_license_key` (Google Play), `facebook_app_id`/`client_token` (nếu dùng Meta Audience Network).
- Keystore folder VGA<xx> + pass.
- Xác nhận ad unit thật (AdMob), gói IAP (subscription id) của app.
