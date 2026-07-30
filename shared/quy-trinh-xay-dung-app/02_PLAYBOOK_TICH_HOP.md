# PLAYBOOK: Tích hợp `base-application` AAR (ads/IAP/splash/language/notification) vào app Android bất kỳ

> File tổng hợp quy trình tích hợp thư viện `base-application` (lo splash/ads/consent/IAP/notification) vào một app Android Compose bất kỳ.
> Xem thêm `08_HUONG_DAN_TICH_HOP_base-application.md` để có **spec đầy đủ của thư viện** (API, hàm abstract, tài nguyên) khi cần chi tiết.
>
> Playbook này = **quy trình + catalog lỗi thực chiến**.

---

## A. BẢN CHẤT

Thư viện sở hữu **lớp vỏ khởi động/monetize**: là **launcher** (SplashActivity), chạy
`Splash → Interstitial → Language → IAP → getHomeActivity()`, tự lo **ads + consent(UMP) + init SDK +
FCM + notification + foreground service + app-open/resume**, đọc mọi ad-unit từ **một** key Remote
Config `ads_config` (`FirebaseRemoteConfigUtil.getAdsConfigValue`).

➡️ Tích hợp = **thay vỏ khởi động/monetize của app bằng vỏ lib, giữ các màn tính năng**. App chỉ:
1. Tạo `HostApplication : BaseApplication()` cấp icon/chuỗi/cấu hình.
2. Cung cấp tài nguyên (drawable/string/array/màu/`default_ads_config.json`/`splash_loading.json`).
3. Gỡ phần trùng của app (splash/language/consent/init-ads/notification…).
4. Chuyển ads tự-gọi-GMA sang `Admob.getInstance()` của lib (xem `10_MIGRATE_ADS_TO_LIB.md`).

---

## B. QUY TRÌNH (đã chốt cách build)

> **Quan trọng:** Phase 1→4 làm **một thể, KHÔNG build từng phase**. Xong hết rồi mới
> **build debug + sửa lỗi tới xanh**, **cài lên máy test bằng adb**, rồi mới sang **Phase 5 (R8/release)**.

### Phase 1 — Toolchain + module AAR
- `gradle-wrapper.properties`: Gradle **≥ 8.13** (AGP 8.12 yêu cầu).
- `libs.versions.toml` (hoặc nơi khai version): AGP **8.12.0**, Kotlin **2.1.20**, KSP **2.1.20-1.0.32**.
- Plugin compose (nếu Compose): **2.1.20**. `google-services` **4.4.3**, `firebase-crashlytics` **3.0.6**.
- `settings.gradle(.kts)`: `include(":base-application")` + repos `google()/mavenCentral()/jitpack/dl.google maven2`.
- Tạo module **`base-application/`**: bỏ `base-application-1.0.0.aar` vào + `build.gradle` (Groovy) khai
  **đủ transitive deps** (copy từ `drive-download-.../build.gradle`). AAR không kèm POM → thiếu dep = `NoClassDefFoundError`.
- `app/build.gradle(.kts)`: `minSdk 28`, Java/Kotlin **17**, `multiDexEnabled`, `viewBinding=true`, `buildConfig=true`,
  Firebase BoM **34.1.0**, `api(project(":base-application"))`. **GỠ** mọi dep trùng lib (play-services-ads, ump, facebook mediation/sdk, appsflyer, glide…).

### Phase 2 — HostApplication + Manifest + Resources
- `MyApplication : BaseApplication()` **giữ `@HiltAndroidApp`** (nếu app dùng Hilt). Implement **đủ hàm
  abstract** (lấy chữ ký chính xác bằng `javap` — xem §D-mẹo). `getHomeActivity()=MainActivity`.
- Manifest: **gỡ `MAIN/LAUNCHER`** khỏi MainActivity (lib là launcher); thêm meta-data
  `admob_app_id`/`facebook_app_id`/`facebook_client_token` (dùng `@string`); đủ 4 quyền
  `POST_NOTIFICATIONS`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE`, `AD_ID`.
- Tài nguyên: `assets/default_ads_config.json`, `res/raw/splash_loading.json`, strings (config + noti/IAP),
  string-array `notification_title2/message2/button2` (**đúng 5**), colors (`primaryColor==accentTone`, `text1`).
  Drawable placeholder tạm dùng icon có sẵn, thay ảnh đúng kích thước trước release.

### Phase 3 — Gỡ vỏ trùng + Ads migration + RemoteConfig + Premium
- Gỡ Splash/Uninstall/Language **startup** của app (lib lo). Đổi `startDestination` Compose sang Home
  (giữ Intro/Permission onboarding nếu có — rẽ nhánh theo cờ first-open).
- **RemoteConfig (R1!):** đừng gọi `FirebaseRemoteConfig.setDefaultsAsync(...)` trực tiếp (xoá `ads_config`).
  Cách ít rủi ro: **giữ facade `RemoteConfigManager` cũ, đổi ruột** ủy quyền `FirebaseRemoteConfigUtil`;
  `getString` cho ad-unit → `getAdsConfigValue`, fallback `getString`. Đăng ký default app qua
  `setAppDefaultsFromXml(R.xml.config)` trong `HostApplication.onCreate()` SAU `super.onCreate()`.
- **Ads:** theo `10_MIGRATE_ADS_TO_LIB.md` — xóa consent/MobileAds.init/AppOpen của app; native→`Admob.loadNativeAd`;
  inter→`Admob.loadAndShowInter`; giữ tầng điều phối; native full-screen giữ view custom + `setNativeAd`.
- **Premium:** `GlobalAds.isPremiumUser` → `IAPUtils.isPremium()`.

### Phase 4 — Notification (nếu quyết định bỏ hệ app)
- Xóa toàn bộ FCM service + scheduler + foreground service + receiver của app; gỡ lời gọi trong MainActivity;
  gỡ service/receiver/meta-data FCM + quyền `SCHEDULE_EXACT_ALARM` trong manifest. → còn **1 FCM + 1 FGS** của lib.

### → BUILD DEBUG + SỬA LỖI (xem §C catalog) + CÀI MÁY TEST (xem §D)

### Phase 5 — R8 / Release (BẮT BUỘC theo guide)
- `buildTypes.release`: `isMinifyEnabled = true` **và** `isShrinkResources = true` (thiếu cái 2 → AGP báo lỗi).
- `signingConfig` release (keystore app).
- `manifestPlaceholders["crashlyticsCollectionEnabled"]` = `"false"` (debug) / `"true"` (release) — **xem C-7**.
- `proguard-rules.pro`: keep `com.nlbn.**`, `com.brian.**`, `com.google.ads.mediation.**`, `com.facebook.ads.**`,
  Gson `TypeToken`/`Signature`/`@SerializedName`, **model app** (Room entity + DTO Gson/Retrofit), Crashlytics attrs.
- Build `assembleRelease` + **cài máy test runtime** (R8 chỉ lộ lỗi lúc chạy release).

---

## C. CATALOG LỖI ĐÃ GẶP (quan trọng nhất — đọc kỹ khi áp app mới)

| # | Lỗi / triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|---|
| C-1 | `Could not find com.google.firebase:firebase-analytics-ktx:` (version rỗng) | Firebase **BoM 34.x đã bỏ artifact `-ktx`** | Đổi `firebase-analytics-ktx`/`-crashlytics-ktx`/`-config-ktx`/`-messaging-ktx` → bản **không `-ktx`** (`firebase-analytics`, …). KTX API nằm trong artifact chính. |
| C-2 | R8 release: `Type com.github.ybq.android.spinkit... is defined multiple times` | **fat-AAR đã gói sẵn** SpinKit, mà module `:base-application` **khai lại** `Android-SpinKit` → trùng class | **Gỡ** dep bị trùng khỏi `base-application/build.gradle`. ⚠️ Kiểm tra dummy-vs-real: nếu lib THẬT không gói (NoClassDefFound runtime) → khai lại. Soi class bundled: `unzip -l classes.jar` trong AAR. |
| C-3 | Server build: `Dangerous code: Hardcoded absolute path (starts with /)` | Linter server chặn **mọi string mở đầu `/`** trong `build.gradle.kts` — kể cả `excludes += "/META-INF/..."` (mẫu Android Studio) | Bỏ `/` đầu: `excludes += "META-INF/{AL2.0,LGPL2.1}"` + `"META-INF/atomicfu.kotlin_module"`. AGP vẫn loại đúng. |
| C-4 | Build lib thật: lỗi merge manifest thiếu placeholder | Lib thật có `<meta-data ...="${crashlyticsCollectionEnabled}">`; app không định nghĩa placeholder | Thêm `manifestPlaceholders["crashlyticsCollectionEnabled"]` (debug `"false"`, release `"true"`) trong buildTypes. |
| C-5 | Build fail: `R8 strip` / `ClassNotFoundException` mediation lúc chạy release | Adapter mediation (Meta/Facebook) **nạp bằng reflection** → R8 xoá | proguard keep `com.google.ads.mediation.**` + `com.facebook.ads.**` (xem Phase 5). |
| C-6 | Ads lib không load (open_splash/native_language… rỗng) | App gọi `setDefaultsAsync` trực tiếp → **xoá default `ads_config`** của lib (R1) | RemoteConfigManager ủy quyền `FirebaseRemoteConfigUtil`; KHÔNG `setDefaultsAsync` trực tiếp. |
| C-7 | App build/cài chạy nhưng **mọi tính năng lib chết im** | Quên `android:name=".MyApplication"` (HostApplication) trong manifest | Khai `android:name` trỏ HostApplication. |
| C-8 | Cold start vào màn trắng / crash | Bỏ `MAIN/LAUNCHER` nhưng quên đổi `startDestination` Compose sang Home | Đổi startDestination sang Home (hoặc Intro nếu first-open). |
| C-9 | `Cannot infer type` / unresolved khi xóa file dùng chung | Xóa cả file chứa **data class / helper dùng chung** (vd `Language.kt` chứa `data class Language` + `CurrencyList` mà `LanguageSetting` dùng) | Trước khi xóa file: grep tham chiếu; tách phần dùng chung hoặc khôi phục file (`git checkout HEAD -- <file>`). |
| C-10 | `okhttp`/`retrofit` mismatch | Lib kéo okhttp 5.x, app pin 4.x | Để Gradle resolve hoặc đồng bộ version; build report lỗi cụ thể thì xử lý. |
| C-11 | (bẫy quy trình) background build báo **exit 0 nhưng thực ra FAILED** | Lệnh `./gradlew ... ; echo done` → exit code là của `echo` | **Luôn grep `BUILD SUCCESSFUL`/`BUILD FAILED` trong log**, đừng tin exit code của lệnh có `;`/`| tail`. |

### Mẹo: lấy chữ ký chính xác hàm abstract / API lib (tránh sai override)
`javap` trong JDK (vd `C:/Program Files/Java/jdk-21/bin/javap.exe`):
```bash
unzip -o classes.jar -d jardir   # classes.jar lấy từ trong AAR (giải nén AAR như zip)
javap -p -classpath jardir com.brian.base_application.BaseApplication   # liệt kê hàm abstract
javap -p -classpath jardir com.nlbn.ads.util.Admob                      # loadNativeAd/loadAndShowInter/...
javap -p -classpath jardir com.nlbn.ads.callback.AdCallback             # onNextAction/onAdFailedToLoad/...
```

---

## D. BUILD & TEST TRÊN MÁY (adb)

```bash
adb devices                                    # xác nhận có device
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb logcat -c
adb shell monkey -p <applicationId> -c android.intent.category.LAUNCHER 1   # mở launcher (Splash lib)
adb shell pm grant <applicationId> android.permission.POST_NOTIFICATIONS    # cấp quyền cho luồng splash đi tiếp
# kiểm tra activity hiện tại + còn sống + crash:
adb shell dumpsys activity activities | grep -i ResumedActivity
adb shell pidof <applicationId>
adb logcat -d | grep -iE "FATAL EXCEPTION|AndroidRuntime|NoClassDefFound|ClassNotFound"   # lọc crash THẬT của app (theo pid)
```
- Nghiệm thu đúng: luồng `SplashActivity (lib) → Inter ad → LanguageActivity → IAP → MainActivity`, process sống, không FATAL.
- Test **cả debug lẫn release(R8)** (R8 chỉ lộ lỗi lúc chạy). Cài release phải `adb uninstall` bản debug trước (khác chữ ký).

---

## F. CHECKLIST QA TRƯỚC PHÁT HÀNH

- [ ] Build **release** xanh với `minifyEnabled=true` + `shrinkResources=true`, không cảnh báo R8 strip lib.
- [ ] `app/build.gradle.kts` không có string mở đầu `/` (C-3); có `crashlyticsCollectionEnabled` placeholder (C-4).
- [ ] `android:name=".MyApplication"` + đủ 4 quyền FGS/POST_NOTIFICATIONS/AD_ID.
- [ ] Không còn `MAIN/LAUNCHER` ở app; cold start vào Splash lib.
- [ ] Luồng `Splash → Inter → Language → IAP → Home` chạy đúng trên máy thật (debug + release).
- [ ] Màn IAP mở được từ Home & Settings; mua xong premium tắt ads.
- [ ] `assets/default_ads_config.json` đủ key (8 placement lib + placement app); ad load thật.
- [ ] Không còn `import GMA AdLoader/InterstitialAd/AppOpenAd/MobileAds.initialize` trong code app.
- [ ] `RemoteConfigManager` không gọi `setDefaultsAsync` trực tiếp.
- [ ] Đổi ngôn ngữ / night mode không restart từ Splash.
- [ ] Thay drawable placeholder bằng ảnh thật đúng kích thước; điền giá trị thật (admob/fb/appsflyer/license/IAP).

---

## G. THỨ TỰ FILE THAM CHIẾU
1. **PLAYBOOK_TICH_HOP.md** (file này) — quy trình + lỗi.
2. **08_HUONG_DAN_TICH_HOP_base-application.md** — spec lib đầy đủ (hàm abstract, tài nguyên, luồng runtime, IAP, RemoteConfig).
3. **10_MIGRATE_ADS_TO_LIB.md** — công thức chuyển ads gọi trực tiếp SDK sang dùng lib.
