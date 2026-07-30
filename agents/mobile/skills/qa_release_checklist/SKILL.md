# skill_qa_release_checklist

**Dùng bởi:** `mobile`, `qa` (cả hai có thể gọi).

**Mục tiêu:** Checklist kiểm tra trước khi phát hành app Android ra Google Play, đảm bảo
mọi yêu cầu của `base-application` AAR + best practice đã được thỏa mãn.

## Tài liệu tham chiếu

```
shared/quy-trinh-xay-dung-app/vga31-kotlin/base-application/HUONG_DAN_TICH_HOP.md  (§12)
shared/quy-trinh-xay-dung-app/07_CHECKLIST.md
```

## Checklist

### 🔨 Build & R8

- [ ] Build release: `./gradlew :app:assembleRelease` thành công.
- [ ] `minifyEnabled = true` VÀ `shrinkResources = true` (cả hai, BẮT BUỘC).
- [ ] `android.enableR8.fullMode=false` trong `gradle.properties`.
- [ ] Không có R8 warning strip class của AAR.
- [ ] ProGuard rules đủ: mediation Meta, Gson, model app, Crashlytics.

### 📋 Manifest & Permissions

- [ ] `android:name=".MyApplication"` (HostApplication kế thừa BaseApplication).
- [ ] Đủ 4 quyền: `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE`,
      `POST_NOTIFICATIONS`, `AD_ID`.
- [ ] KHÔNG có `MAIN/LAUNCHER` ở activity của app (AAR cung cấp launcher).
- [ ] Meta-data AdMob (`com.google.android.gms.ads.APPLICATION_ID`) khai báo.
- [ ] Meta-data Facebook (`ApplicationId`, `ClientToken`) khai báo (nếu dùng).
- [ ] Merged manifest: chỉ 1 `MESSAGING_EVENT` service.

### 🎨 Resources

- [ ] `res/values/colors.xml`: `primaryColor` = `accentTone`, `text1` cố định.
- [ ] `res/values-night/colors.xml`: `text1` giá trị giống `values/`.
- [ ] Drawable: `icon_app`, `icon_notification` (5 mật độ), `img_document_preview`,
      `icon_1_iap`…`icon_5_iap`, `icon_noti_1`…`icon_noti_5`.
- [ ] Raw: `splash_loading.json` (Lottie).
- [ ] Assets: `default_ads_config.json` (gồm key `open_all`).
- [ ] Strings: `app_name`, `app_flyer_id`, `admob_app_id`, `facebook_app_id`,
      `facebook_client_token`, `public_license_key`.
- [ ] String-array: `notification_title2` (5), `notification_message2` (5),
      `notification_button2` (5) — đúng 5 phần tử, khớp theme app.

### 🔐 Signing & Firebase

- [ ] Keystore file đúng cho app (KHÔNG commit vào repo).
- [ ] `google-services.json` đúng project Firebase.
- [ ] Firebase Crashlytics: `mappingFileUploadEnabled true` trong release buildType.
- [ ] Firebase linked với app trên Play Console.

### 🚦 Runtime Flows

- [ ] Luồng: Splash → Inter → Language → IAP → Home — chạy đúng.
- [ ] Màn IAP mở được từ Home VÀ Settings.
- [ ] Đổi ngôn ngữ KHÔNG restart từ Splash.
- [ ] Bật/tắt night mode KHÔNG restart từ Splash.
- [ ] `isPurchased()` liên kết đúng `IAPUtils.isPremium()`.
- [ ] Paywall gate hoạt động: chưa mua → paywall, đã mua → dùng tính năng.

### 📢 Ads

- [ ] All ad slots load được (banner/inter/native/open — ít nhất test unit).
- [ ] NativeAdSlot fail → ẩn (không kẹt shimmer >30s).
- [ ] Resume ad hoạt động (trừ premium user).
- [ ] Log ads dùng `println` (KHÔNG `android.util.Log`).

### 📱 UX

- [ ] Intro (nếu có): nút Next bấm được khi ad fill HOẶC lỗi (timeout 5s).
- [ ] Dark mode: nếu chưa support → khoá `darkTheme = false`.
- [ ] Back navigation: từ Main không quay lại Intro/Language/Splash.

### 🏪 Play Console

- [ ] `USE_FULL_SCREEN_INTENT` → chọn "Other".
- [ ] `FOREGROUND_SERVICE_SPECIAL_USE`: mô tả rõ (Documents → tác vụ nền dài).
- [ ] IAP products (3 subscription) đã tạo + match key trong code.

## Hướng dẫn test trên máy (adb Cheat-Sheet)

```bash
# 1. Cài đặt APK
adb devices                                          # Xác nhận thiết bị
adb install -r app/build/outputs/apk/debug/app-debug.apk   # Bản debug
# Với bản release (R8): phải gỡ bản debug trước vì khác chữ ký
adb uninstall <applicationId>
adb install -r app/build/outputs/apk/release/app-release.apk

# 2. Xoá data app (reset onboarding / counters / storage)
adb shell pm clear <applicationId>

# 3. Giả lập mở app từ launcher (qua SplashActivity của lib)
adb shell monkey -p <applicationId> -c android.intent.category.LAUNCHER 1
adb shell pm grant <applicationId> android.permission.POST_NOTIFICATIONS   # Cấp quyền noti

# 4. Kiểm tra Activity hiện tại & Process status
adb shell dumpsys activity activities | grep -i ResumedActivity
adb shell pidof <applicationId>

# 5. Đọc log ads (log dùng println)
adb logcat -c
adb logcat -s System.out | grep -E "ADSLOT|ADS"

# 6. Đọc log SDK GMS (kiểm tra no-fill / timeout / HTTP 400)
adb logcat -d | grep -iE "FATAL EXCEPTION|AndroidRuntime|NoClassDefFound|ClassNotFound"
adb logcat -d | grep -E " Ads +:" | grep -iE "no fill|too many|400|timeout"

# 7. Đóng Interstitial Ad để đi tiếp trong luồng test
adb shell input keyevent KEYCODE_BACK
```

> 💡 **Mẹo test ad thật trên bản release khi app chưa publish Play Store**:
> Lấy test device ID từ logcat (`Use RequestConfiguration...setTestDeviceIds("<id>")`),
> điền ID đó vào hàm `getListTestDeviceId()` trong HostApplication (`MyApplication.kt`).

## Output

- Checklist hoàn thành (all checked) → ready to publish.
- Test nghiệm thu trên thiết bị thật via `adb` pass (debug + release R8).
- Mục nào fail → ghi rõ reason + action cần fix.

