# ✅ CHECKLIST MẪU — trước khi phát hành app (ví dụ thực tế: vga31b, Software Update Checker Pro)

> Ví dụ checklist thật đã dùng khi hoàn thiện app `vga31b-kotlin`. Dùng làm mẫu khi tự làm checklist cho app mới — copy khung, đổi giá trị cụ thể theo app của bạn.
> Bài học ads/build chi tiết: `05_ADS_RUNTIME_LESSONS.md`.

## A. Nền tảng & rebrand
- [x] Toolchain (AGP/Kotlin/KSP, base-application AAR) build được
- [x] package / namespace / applicationId = `com.supportsoftware.checkerpro`
- [x] `google-services.json` (project `checkerpro-software-update`)
- [x] admob app id `~2621217845` (strings.xml)
- [x] app_name = "Software Update Checker Pro" + rootProject.name
- [x] logo (icon_app 512²)
- [x] appsflyer devkey

## B. Giao diện
- [x] Theme `#007BFF` + phụ `#00C9FF`
- [x] Màn Scan: vòng tròn % (CircularProgressIndicator)
- [x] Native màn list dùng layout gọn `_main`
- [ ] Rà lại TỪNG màn (Home/list/detail/Setting) — chỉnh nếu còn thiếu chi tiết
- [ ] `native_setting`: thêm NativeAdSlot vào SettingScreen nếu thiết kế có ad

## C. Quảng cáo
- [x] `default_ads_config.json` — unit THẬT vga31b (đủ 8 placement lib + app)
- [x] config.xml ratios (inter 4/20, native_inter 2/20)
- [x] 6 cải tiến ads (cache/bind-once/dọn-key/native-inter-timing/preload/positionIntrol) — xem `06_ADS_REUSABLE_COMPONENTS.md`
- [x] Log ads dùng `println` (lib strip android.util.Log ở release)
- [x] NativeAdSlot tự ẩn khi fail (không kẹt shimmer)
- [x] Debug dùng unit test (nghiệm thu ads fill OK)
- [ ] **Publish Play → ads THẬT fill** (hiện NO_FILL vì chưa publish — KHÔNG phải lỗi)

## D. IAP
- [x] iapPremiumKey=`premium_remove_all_ads`, monthly/yearly/weekly
- [x] `public_license_key` THẬT (Play Console)

## E. Build / Ký
- [x] Keystore THẬT VGA31B (build.gradle.kts signingConfig)
- [x] Build debug XANH + R8 assembleRelease XANH
- [x] Cài máy test (debug + release)

## F. Còn thiếu trước phát hành (TODO)
- [ ] `facebook_app_id` + `facebook_client_token` (đang placeholder)
- [ ] i18n: rà đủ ngôn ngữ đã hỗ trợ (kiểm dịch)
- [ ] Branding: icon notification (5 density) / icon splash / ảnh preview IAP 365×174 (đang dùng logo placeholder)
- [ ] Publish Play Store (đúng package + keystore VGA31B)

## G. ⚠️ MỤC HAY QUÊN — KIỂM MỖI LẦN BUILD (đặc biệt ADS)
- [x] **Intro — nút Next/Continue**: phải **bấm được khi ad FILL *hoặc* LỖI** (không kẹt disabled khi ad treo). Có timeout fallback (5s) + `onResolved`. → Kiểm lại sau mỗi lần sửa Intro.
- [x] **Ads kép (chain)**: tap tile Home/Uninstall → inter → (đóng) → **native-inter (native giả intent) fullscreen** → điều hướng. Cả fallback (inter không hiện → native-inter ngay). Ratio inter 4/20, native_inter 2/20.
- [x] **Log ads + test bản THẬT**: log dùng `println` (lib strip android.util.Log). **Build release xong PHẢI cài máy test lại + đọc log**: `adb logcat -s System.out | grep -E "ADSLOT|ADS"` (+ `adb logcat -d | grep " Ads +:"` cho SDK). Release chưa publish → NO_FILL là bình thường.
- [x] **Gói đăng ký (IAP)**: key sản phẩm/subscription lấy từ cấu hình thật của app (Play Console). KHÔNG dùng `defaultIap*Key()` của lib nếu app đã có key thật.
- [x] Slot ad **tự ẩn khi fail** (không kẹt shimmer >30s) — `slot.onError()` + `suppressedAfterError`.

> Thành phần ads có thể **copy dùng lại cho app khác**: xem `06_ADS_REUSABLE_COMPONENTS.md`.
