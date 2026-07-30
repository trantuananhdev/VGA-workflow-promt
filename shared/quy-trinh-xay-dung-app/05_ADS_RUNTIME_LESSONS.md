# 14 — Bài học VẬN HÀNH quảng cáo + build (thực chiến, BẮT BUỘC đọc)

> Tổng hợp các lỗi/insight gặp khi chạy thật vga31a/vga31b (và đối chiếu app mẫu vga23b).
> Đây là những thứ KHÔNG lộ ra lúc code/compile — chỉ hiện khi chạy debug/release trên máy.
> Ai pull project về làm app mới: đọc file này trước khi đụng phần ads.

---

## 1. ⚠️ LOG: lib STRIP `android.util.Log` ở release → DÙNG `println`

`base-application-1.0.0.aar` có proguard consumer:
```proguard
-assumenosideeffects class android.util.Log { v(...); d(...); i(...); w(...); e(...); wtf(...); println(...); }
```
→ Bản **release (R8)** **XÓA SẠCH mọi `android.util.Log`** của app. Debug thì còn, release thì mất → tưởng "không có log / app không chạy ads".

**Quy tắc:** log ads (và log cần thấy ở production) phải dùng **`println(...)`** (Kotlin → `System.out` → `java.io.PrintStream`, KHÔNG bị strip). KHÔNG dùng `android.util.Log`.

Đọc log production:
```bash
adb logcat -s System.out | grep -E "ADSLOT|ADS"
# ADSLOT load START native_home unit=...   (đang request)
# ADSLOT loaded native_home ad=true         (fill OK)
# ADSLOT ERR failed native_home (...) → ẩn slot   (no-fill → ẩn)
```
(Log GMS tag `Ads` — vd "Too many recently failed requests", HTTP 400, TimeoutException — là log nội bộ SDK, luôn có, không bị strip.)

---

## 2. ⚠️ NativeAdSlot: PHẢI ẩn slot khi fail (nếu không shimmer KẸT mãi)

Khi dùng cache `AdsViewModel` (port 23b): lúc native fail/no-fill **PHẢI** gọi `slot.onError()` + `suppressedAfterError=true` để **ẩn slot**. Thiếu → `isLoading` kẹt `true` → **shimmer đứng vĩnh viễn (>30s)**, chiếm chỗ.

```kotlin
onResolved = { loaded ->
    if (loaded) println("ADSLOT loaded $placement ad=true")
    else { println("ADSLOT ERR failed $placement → ẩn slot")
           slot.onError(); suppressedAfterError = true }   // <-- BẮT BUỘC
}
// when { suppressedAfterError -> Unit; isLoaded -> ...; isLoading -> Shimmer; else -> NativeLoader }
```

---

## 3. ⚠️ "Bản release/production KHÔNG có ads" = NO_FILL, KHÔNG phải lỗi code

App **chưa publish Play** + unit **THẬT** → AdMob không phục vụ:
```
E Ads: Too many recently failed requests for ad unit ID: ca-app-pub-.../...
E Ads: java.util.concurrent.TimeoutException  (HTTP timeout 60000ms)
W Ads: Received error HTTP response code: 400
```
→ không có ads (native slot tự ẩn, inter/open bỏ qua). **Bình thường.** Chỉ hết sau khi:
1. App **lên Play Store** (đúng package + ký đúng keystore).
2. Ad unit AdMob active, app liên kết, có traffic (vài giờ–vài ngày sau request thật đầu).

Kiểm chứng code ĐÚNG: bản **debug** dùng **unit test** Google → `ad=true` + Google báo "AdMob native ad validator: No implementation issues found".

**Debug = unit test (thấy ads); Release = unit thật (chờ publish).** Cơ chế: `Remote.adUnit()`:
```kotlin
fun adUnit(p) = if (BuildConfig.DEBUG) debugTestUnit(p) else frc.getAdsConfigValue(p)
// test: native 2247696110, inter 1033173712, open 9257395921
```
> Lưu ý: splash có thể chậm ở release vì open_splash/inter_splash unit thật timeout tới 60s.

---

## 4. Kiến trúc ads (port đầy đủ từ vga23b — 6 điểm)

| # | Điểm | File |
|---|---|---|
| 1 | **Cache native theo Activity** (`AdsViewModel` + `slot.prepareForEntry(interval)`) — không reload mỗi lần vào lại composition (đổi tab/back/scroll) | `advertisement/AdsViewModel.kt`, `NativeAdSlot.kt` |
| 2 | **Bind native 1 lần** `key(ad)` chỉ bind trong `factory` (KHÔNG cả `update`) → hết warning "bind 2 lần" | `NativeAdSlot.kt` |
| 3 | **AdScenario dọn key đếm >7 ngày** (SharedPreferences không phình) | `AdScenario.kt` |
| 4 | **Native-inter tính tần suất SAU khi inter đóng** (giống InterFlow 23b) — đếm đúng maxPerDay | `AdManager.kt` |
| 5 | **Preload native-inter** lúc inter đang hiển thị → đóng inter hiện gần tức thì | `AdManager.kt` + `NativeInter.kt` (preload/takePreloaded) |
| 6 | **positionIntrol A/B ở Intro**: `N`=native inline slide N, `NN`(11/22/33/44)=native MODAL toàn màn khi rời slide | `AdPositions.kt`, `NativeAdsFull.kt`, `OnboardingScreens.kt` |

**Layout native:**
- Slot thường (Home/Intro/Permission/Scan/detail): **full** `com.brian.base_application.R.layout.ads_native_bot_2` + shimmer `ads_native_bot_loading_2`.
- Slot màn LIST (User/System/Manager apps, Uninstall, History, UpdateAvailable): **gọn** `ads_native_bot_no_media_short_main` + shimmer `ads_native_loading_short_main` (`NativeAdSlot(..., isSmall = true)`).
- Native-inter / modal Intro: **layout tự dựng** `res/layout/ad_native_full.xml` + bind thủ công `NativeAdView` API (`setNativeAd`), KHÔNG `pushAdsToViewCustom`.

**Kịch bản inter (chain 2 quảng cáo):** tap tile Home / Uninstall → `AdManager.showInter`:
- inter HIỆN (ratio/max qua) → đóng → native-inter (ratio/max riêng, tính sau khi inter đóng) → điều hướng.
- inter KHÔNG → native-inter ngay (fallback). `onNext()` luôn gọi đúng 1 lần.
- Ratio: inter_screen **4/20**, native_inter_screen **2/20**, inter_splash 3/20, open_on_resume 2/20. Công thức `showCount % ratio == 0`.

---

## 5. Đặt tên hàm & gọi qua import — tránh nhầm lẫn khi đọc code

- **Không đặt tên hàm trùng API chuẩn thư viện chuẩn**: hàm `parse()` trong `AdPositions` dễ nhầm với `Uri.parse`/`SimpleDateFormat.parse` khi đọc log/stack trace. Đặt tên riêng, rõ nghĩa hơn: `parsePositions()`.
- **`NativeInterHost()` nên gọi qua `import`** (không viết FQN inline `com.x.advertisement.NativeInterHost()`) — giữ code sạch, dễ refactor package.

---

## 6. Ký (signing) khi phát hành

- **Keystore THẬT** ở `vga49a/keystore/VGA31B/keystore.jks` + `pass.txt` (storePassword/keyAlias/keyPassword). Điền vào `app/build.gradle.kts` signingConfig. Copy jks → `app/keystore/update.jks` (gitignore).
- Build **release** phải dùng đúng keystore thật trước khi publish Play Store (khác keystore = khác chữ ký = không update được app cũ trên máy, phải uninstall trước khi cài).

---

## 7. Test ads trên máy (adb) — cheat-sheet

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell pm clear <applicationId>          # reset onboarding/counter
adb logcat -c
adb shell monkey -p <applicationId> -c android.intent.category.LAUNCHER 1
adb shell input keyevent KEYCODE_BACK       # đóng inter (AdActivity) để đi tiếp
adb logcat -s System.out | grep -E "ADSLOT|ADS"     # log ads (println)
adb logcat -d | grep -E " Ads +:" | grep -iE "no fill|too many|400|timeout"  # log SDK GMS
adb shell dumpsys activity activities | grep topResumedActivity   # màn hiện tại
```
- Muốn xem test-ad trên **release** (chưa publish): thêm test device id vào `getListTestDeviceId()` của HostApplication (id lấy từ log `Use RequestConfiguration...setTestDeviceIds("<id>")`).
