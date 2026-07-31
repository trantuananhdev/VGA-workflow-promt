# skill_integrate_base_application

**Dùng bởi:** `mobile` (riêng — phase `client-shell`, chạy SAU `clone_vga31_template`).

**Mục tiêu:** Đảm bảo module `base-application` (AAR) được tích hợp đúng vào project mới —
bao gồm Gradle config, ProGuard/R8, manifest merge, và luồng runtime hoạt động đúng.

## Tiền đề

- Skill `clone_vga31_template` đã chạy xong.
- Skill `setup_host_application` đã (hoặc đang) chạy song song.

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

```
shared/quy-trinh-xay-dung-app/vga31-kotlin/base-application/HUONG_DAN_TICH_HOP.md  (§1-§4, §7, §9-§10)
shared/quy-trinh-xay-dung-app/02_PLAYBOOK_TICH_HOP.md
shared/quy-trinh-xay-dung-app/10_MIGRATE_ADS_TO_LIB.md  (nếu app có ads cũ cần migrate)
```

## Kiến trúc module base-application

```
base-application/
├── base-application-1.0.0.aar   # AAR đóng gói: Splash, Language, IAP, Ads, Consent,
│                                 # FCM, ForegroundService, Uninstall, Notification
├── build.gradle                  # Module phẳng: expose AAR + khai transitive deps
├── HUONG_DAN_TICH_HOP.md        # Spec tích hợp (1302 dòng)
└── HUONG_DAN_TICH_HOP.docx      # Phiên bản Word (nội dung giống .md)
```

AAR KHÔNG kèm POM → TẤT CẢ dependency phải khai trong `build.gradle` module phẳng.
Thiếu dependency = `NoClassDefFoundError` runtime hoặc link error build time.

## Quy trình kiểm tra & fix

```
1. VERIFY GRADLE STRUCTURE:
   a) settings.gradle.kts phải có: include(":base-application")
   b) app/build.gradle.kts phải có: api(project(":base-application"))
      (dùng api, KHÔNG implementation — vì app cần truy cập class của lib)
   c) Root build.gradle.kts phải có plugin:
      - com.google.gms.google-services (version 4.4.3)
      - com.google.firebase.crashlytics (version 3.0.6)

2. VERIFY base-application/build.gradle:
   Đối chiếu danh sách dependency với bản trong HUONG_DAN_TICH_HOP.md §3.1.
   Danh sách hiện tại (KHÔNG THAY ĐỔI trừ khi có chỉ đạo rõ ràng):
   - androidx.core:core-ktx:1.16.0
   - androidx.appcompat:appcompat:1.7.1
   - com.google.android.material:material:1.13.0
   - androidx.preference:preference:1.2.1
   - androidx.work:work-runtime:2.10.3
   - com.android.billingclient:billing:7.1.0
   - com.google.android.gms:play-services-ads:25.2.0
   - com.google.android.ump:user-messaging-platform:4.0.0
   - com.google.ads.mediation:facebook:6.21.0.2
   - Firebase BoM 34.1.0 + analytics/crashlytics/messaging/firestore/appcheck/config
   - com.intuit.sdp:sdp-android:1.1.1 + ssp-android:1.1.1
   - com.facebook.shimmer:shimmer:0.5.0
   - com.airbnb.android:lottie:6.6.7 + lottie-compose:6.6.7
   - com.appsflyer:af-android-sdk:6.18.0 + purchase-connector:2.1.2
   - com.adjust.sdk:adjust-android:5.6.1
   - com.facebook.android:facebook-android-sdk:18.1.3
   - com.github.bumptech.glide:glide:4.16.0
   - org.jsoup:jsoup:1.21.2
   - com.squareup.okhttp3:okhttp:5.2.1
   - Compose BoM 2024.12.01 + ui/foundation/material3/activity-compose
   - Và các lib nhỏ khác (circleimageview, smoothprogressbar, localization...)

   ⚠️ Android-SpinKit ĐÃ GỒM TRONG AAR (fat-aar) → KHÔNG khai lại.
   Khai lại gây R8 "Type ... is defined multiple times" khi build release.

3. VERIFY PROGUARD/R8 (app/proguard-rules.pro):
   a) AAR đã đóng gói consumer rules → KHÔNG cần -keep cho com.nlbn.*, com.brian.*
      (thêm lại vô hại nhưng thừa — template đã thêm "cho chắc").
   b) BẮT BUỘC app thêm:
      - AdMob mediation Meta: -keep class com.google.ads.mediation.** { *; }
                                -keep class com.facebook.ads.** { *; }
      - Gson TypeToken + SerializedName
      - Model/data class của app (-keep class APPLICATION_ID.data.** { *; })
      - Crashlytics: -keepattributes SourceFile,LineNumberTable
   c) KHÔNG thêm -dontoptimize (rule strip log trong AAR cần R8 optimization).

4. VERIFY gradle.properties:
   - android.enableR8.fullMode=false  (BẮT BUỘC — full mode gây lỗi Retrofit/Gson)
   - android.nonTransitiveRClass=true
   - android.useAndroidX=true

5. VERIFY MANIFEST MERGE:
   Chạy: ./gradlew :app:processDebugManifest
   Kiểm tra merged manifest:
   a) Chỉ có 1 MAIN/LAUNCHER (= SplashActivity của lib).
   b) Không có Activity trùng tên giữa app và lib.
   c) MESSAGING_EVENT service: chỉ 1 (lib mặc định, hoặc app's subclass — xem §8.6).

6. VERIFY RUNTIME FLOW:
   Luồng chuẩn: Splash → Inter(inter_splash) → Language → IAP → Home
   - Splash do lib cung cấp (launcher).
   - Language do lib cung cấp (hoặc custom — xem skill configure_language_screen).
   - IAP do lib cung cấp.
   - Home = getHomeActivity() của HostApplication.
   App KHÔNG tự init ads/consent/FCM — thư viện tự lo trong splash.
```

## Catalog lỗi thực chiến (02_PLAYBOOK_TICH_HOP.md §C)

Agent BẮT BUỘC tra cứu bảng này khi gặp lỗi tích hợp `base-application`:

| # | Lỗi / triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|---|
| C-1 | `Could not find com.google.firebase:firebase-analytics-ktx:` | Firebase **BoM 34.x đã bỏ artifact `-ktx`** | Bỏ hậu tố `-ktx` (`firebase-analytics`, `firebase-crashlytics`, `firebase-config`, `firebase-messaging`). |
| C-2 | R8 release: `Type com.github.ybq.android.spinkit... is defined multiple times` | **fat-AAR đã gói sẵn** SpinKit, mà module `:base-application` **khai lại** | **Gỡ** `Android-SpinKit` khỏi `base-application/build.gradle`. |
| C-3 | Server build: `Dangerous code: Hardcoded absolute path (starts with /)` | Linter chặn mọi string mở đầu `/` trong `build.gradle.kts` | Bỏ `/` đầu: `excludes += "META-INF/{AL2.0,LGPL2.1}"`. |
| C-4 | Build lib thật: lỗi merge manifest thiếu placeholder | Lib thật chứa `${crashlyticsCollectionEnabled}` trong manifest | Thêm `manifestPlaceholders["crashlyticsCollectionEnabled"]` = `"false"` (debug) / `"true"` (release). |
| C-5 | R8 strip / `ClassNotFoundException` mediation lúc release | Adapter Meta/Facebook nạp bằng reflection | Keep `com.google.ads.mediation.**` + `com.facebook.ads.**` trong ProGuard. |
| C-6 | Ads lib không load (`open_splash`/`native_language` rỗng) | Gọi `setDefaultsAsync` trực tiếp làm **xoá default `ads_config`** | Dùng `FirebaseRemoteConfigUtil`; KHÔNG `setDefaultsAsync` trực tiếp. |
| C-7 | App build/cài chạy nhưng **mọi tính năng lib chết im** | Quên `android:name=".MyApplication"` trong `AndroidManifest.xml` | Khai báo `android:name` trỏ HostApplication. |
| C-8 | Cold start vào màn trắng / crash | Bỏ `MAIN/LAUNCHER` nhưng quên đổi `startDestination` Compose sang Home | Đổi `startDestination` sang Home (hoặc Intro). |
| C-9 | `Cannot infer type` / unresolved khi xóa file | Xóa lầm file chứa data class / helper dùng chung | Grep tham chiếu trước khi xóa; khôi phục bằng `git checkout`. |
| C-10 | `okhttp`/`retrofit` version mismatch | Lib kéo okhttp 5.x, app pin 4.x | Để Gradle resolve hoặc đồng bộ version. |
| C-11 | Lệnh background build báo **exit 0 nhưng thực ra FAILED** | Lệnh `./gradlew ... ; echo done` trả exit code của `echo` | **Luôn grep `BUILD SUCCESSFUL` / `BUILD FAILED` trong log**, không tin exit code của lệnh nối `;` hay `| tail`. |

### Mẹo: lấy chữ ký chính xác hàm abstract của AAR (tránh sai override)

Dùng `javap` trong JDK để kiểm tra chữ ký class trong AAR:
```bash
unzip -o base-application-1.0.0.aar -d aardir
unzip -o aardir/classes.jar -d jardir
javap -p -classpath jardir com.brian.base_application.BaseApplication   # liệt kê hàm abstract
javap -p -classpath jardir com.nlbn.ads.util.Admob                      # loadNativeAd / loadAndShowInter
javap -p -classpath jardir com.nlbn.ads.callback.AdCallback             # onNextAction / onAdFailedToLoad
```

## Khi cần nâng cấp AAR

```
1. Thay file base-application-1.0.0.aar bằng phiên bản mới.
2. Cập nhật artifact name trong build.gradle nếu đổi tên file.
3. Cập nhật dependency list trong build.gradle nếu phiên bản mới yêu cầu.
4. Build + test lại toàn bộ luồng.
5. KHÔNG tự đoán dependency mới — hỏi team lib hoặc đọc changelog.
```

## Output

- Verification log (pass/fail cho từng bước).
- Danh sách warning/issue cần fix (nếu có).

## KHÔNG ĐƯỢC LÀM

- ❌ KHÔNG sửa file bên trong AAR.
- ❌ KHÔNG đổi version dependency trong base-application/build.gradle trừ khi có chỉ đạo.
- ❌ KHÔNG thêm dependency mới vào base-application/ (thêm vào app/ nếu cần).
- ❌ KHÔNG bật R8 fullMode.
- ❌ KHÔNG khai lại Android-SpinKit (đã gồm trong AAR).

