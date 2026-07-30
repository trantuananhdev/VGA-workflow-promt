# Hướng dẫn tích hợp thư viện `base-application-1.0.0.aar`

Tài liệu này hướng dẫn lập trình viên tích hợp thư viện vào một app Android mới.
Cách tích hợp chính: **tạo một lớp `Application` kế thừa `BaseApplication`** và cung cấp
tài nguyên (icon, chuỗi, cấu hình quảng cáo). Thư viện sẽ tự lo phần còn lại
(màn splash, chọn ngôn ngữ, màn mua gói/IAP, hiển thị quảng cáo).

- Artifact: `base-application-1.0.0.aar`
- Package gốc để kế thừa: `com.brian.base_application.BaseApplication`
- Kèm sẵn: `splash_loading.json` (mẫu Lottie), thư mục `sample/` (file mẫu để copy)

## 1. Tổng quan

Thư viện đóng gói sẵn nhiều thành phần. Việc phân chia trách nhiệm như sau:

| Thư viện (AAR) cung cấp sẵn | App (host) phải cung cấp |
|---|---|
| Màn Splash + luồng khởi động (là launcher của app) | Lớp `HostApplication : BaseApplication()` |
| Màn chọn ngôn ngữ (Language) | Màn Home của app (qua `getHomeActivity()`) |
| Màn mua gói / Paywall (IAP) | Tài nguyên: icon, ảnh, chuỗi, bản dịch |
| Màn xin quyền thông báo, màn Uninstall | `assets/default_ads_config.json` (ad unit id) |
| Foreground service + quyền liên quan | `google-services.json`, khoá IAP |
| Tự quản lý việc hiển thị quảng cáo & consent | Thương hiệu (màu, tên app) |

App **không** cần tự gọi khởi tạo quảng cáo hay consent — thư viện tự chạy trong luồng splash.

## 2. Yêu cầu môi trường

| Mục | Giá trị |
|---|---|
| `minSdk` | 28 |
| `compileSdk` / `targetSdk` | 35 |
| Java / Kotlin JVM target | 17 |
| Android Gradle Plugin | 8.12.0 |
| Kotlin Gradle Plugin | 2.1.20 |
| Plugin đặc biệt | `fat-aar` (consume AAR), `google-services`, `firebase-crashlytics` |

## 3. Thiết lập Gradle

### 3.1 Tạo module phẳng chứa AAR

Tạo thư mục `base-application/` đặt cạnh module `app`, bỏ vào đó file
`base-application-1.0.0.aar` và file `base-application/build.gradle`:

```
<project>/
├── app/
└── base-application/
    ├── base-application-1.0.0.aar
    └── build.gradle
```

Nội dung `base-application/build.gradle` (dùng đúng file `build.gradle` kèm theo bộ này):

```groovy
configurations.maybeCreate("default")
artifacts.add("default", file('base-application-1.0.0.aar'))

dependencies {
    "default"("androidx.core:core-ktx:1.16.0")
    "default"("androidx.appcompat:appcompat:1.7.1")
    "default"("com.google.android.material:material:1.13.0")
    "default"("androidx.preference:preference:1.2.1")
    "default"("androidx.work:work-runtime:2.10.3")
    "default"("com.android.billingclient:billing:7.1.0")
    "default"("com.google.android.gms:play-services-ads:25.2.0")
    "default"('com.google.android.ump:user-messaging-platform:4.0.0')
    "default"("com.google.ads.mediation:facebook:6.21.0.2")
    "default"(platform("com.google.firebase:firebase-bom:34.1.0"))
    "default"("com.google.firebase:firebase-analytics")
    "default"("com.google.firebase:firebase-crashlytics")
    "default"("com.google.firebase:firebase-messaging-ktx:24.1.2")
    "default"("com.google.firebase:firebase-firestore:26.0.2")
    "default"("com.google.firebase:firebase-appcheck-playintegrity:19.0.0")
    "default"("com.google.firebase:firebase-config:23.0.0")
    "default"("com.intuit.sdp:sdp-android:1.1.1")
    "default"("com.intuit.ssp:ssp-android:1.1.1")
    "default"("com.facebook.shimmer:shimmer:0.5.0")
    "default"("com.airbnb.android:lottie:6.6.7")
    "default"("androidx.media:media:1.0.0")
    "default"('com.appsflyer:purchase-connector:2.1.2')
    "default"('de.hdodenhof:circleimageview:3.1.0')
    "default"('com.github.castorflex.smoothprogressbar:library-circular:1.3.0')
    "default"("org.jsoup:jsoup:1.21.2")
    "default"("com.squareup.okhttp3:okhttp:5.2.1")
    "default"('com.akexorcist:localization:1.2.11')
    "default"('androidx.lifecycle:lifecycle-process:2.9.4')
    "default"('com.appsflyer:af-android-sdk:6.18.0')
    "default"('com.adjust.sdk:adjust-android:5.6.1')
    "default"('com.android.installreferrer:installreferrer:2.2')
    "default"('com.facebook.android:facebook-android-sdk:18.1.3')
    "default"('com.github.bumptech.glide:glide:4.16.0')
    "default"('com.github.ybq:Android-SpinKit:1.4.0')
    "default"(platform("androidx.compose:compose-bom:2024.12.01"))
    "default"("androidx.compose.ui:ui")
    "default"("androidx.compose.foundation:foundation")
    "default"("androidx.compose.material3:material3")
    "default"("androidx.activity:activity-compose:1.9.3")
    "default"("com.airbnb.android:lottie-compose:6.6.7")
}
```

> ⚠️ AAR này không kèm POM/metadata, nên TẤT CẢ dependency ở trên phải khai báo lại
> trong module phẳng. Thiếu một dependency sẽ gây lỗi `NoClassDefFoundError` lúc chạy
> hoặc lỗi link lúc build.

### 3.2 `settings.gradle`

```groovy
include ':app', ':base-application'
```

### 3.3 Root `build.gradle`

```groovy
buildscript {
    repositories {
        google(); mavenCentral()
        maven { url 'https://jitpack.io' }
        maven { url 'https://dl.google.com/dl/android/maven2' }
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.12.0'
        classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:2.1.20'
        classpath 'com.github.aasitnikov:fat-aar-android:1.4.1'
        classpath 'com.google.gms:google-services:4.4.3'
        classpath 'com.google.firebase:firebase-crashlytics-gradle:3.0.6'
    }
}

allprojects {
    repositories {
        google(); mavenCentral()
        maven { url 'https://jitpack.io' }
        maven { url 'https://dl.google.com/dl/android/maven2' }
    }
}
```

### 3.4 `app/build.gradle`

`minSdk >= 28`. Bản release BẮT BUỘC **cả hai**: `minifyEnabled true` **và**
`shrinkResources true` (Kotlin DSL: `isMinifyEnabled = true` + `isShrinkResources = true`).
`shrinkResources` đòi `minifyEnabled` đã bật, nên nếu thiếu cái thứ hai AGP sẽ báo lỗi.

```groovy
plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
    id 'com.google.gms.google-services'
    id 'com.google.firebase.crashlytics'
}

android {
    compileSdkVersion 35
    defaultConfig {
        applicationId "<APPLICATION_ID_CUA_BAN>"
        minSdkVersion 28
        targetSdkVersion 35
        versionCode 1
        versionName "1.0.0"
        multiDexEnabled true
        vectorDrawables.useSupportLibrary = true
    }
    buildTypes {
        debug   { manifestPlaceholders = [crashlyticsCollectionEnabled: "false"] }
        release {
            minifyEnabled true                          // BẮT BUỘC
            shrinkResources true                        // BẮT BUỘC (đi cặp với minifyEnabled)
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
            manifestPlaceholders = [crashlyticsCollectionEnabled: "true"]
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = '17' }
    buildFeatures { viewBinding true; buildConfig = true }
    packagingOptions { exclude 'META-INF/atomicfu.kotlin_module' }
    namespace '<NAMESPACE_CUA_BAN>'
}

dependencies {
    api project(':base-application')
}
```

### 3.5 ProGuard / R8 — quy tắc `-keep`

> **TL;DR:** Bạn **KHÔNG** cần thêm `-keep` cho class của thư viện. AAR đã đóng gói sẵn
> toàn bộ consumer rules (file `proguard.txt` bên trong AAR) và R8 của app **tự động áp
> dụng** khi build `minifyEnabled true`. App chỉ cần thêm rule cho **SDK bên thứ ba của
> riêng app** — đặc biệt là **AdMob mediation** (xem mục (b)).

#### (a) Thư viện đã tự lo phần của nó — không cần khai báo lại

`base-application-1.0.0.aar` được build với `consumerProguardFiles`, nên `proguard.txt`
bên trong AAR **merge tự động** vào R8 của app. Nó giữ sẵn (bạn KHÔNG cần lặp lại):

- `com.nlbn.ads.**` (toàn bộ SDK ads nhúng trong thư viện) + `com.google.android.gms.ads.nativead.**`
- Các Activity vào-bằng-tên: `LanguageActivity.start(...)`, `IapActivity`,
  `RequestNotificationPermissionActivity.start(...)`, `FullScreenActivity`
- JNI bridge: `NativeCodecSnowFlakeCortexAI`, `SnowflakeMachineLearning`, `SnowflakeCortexAI`,
  `native <methods>`
- Cấu hình / service / router: `FirebaseRemoteConfigUtil`, `TemporaryStorage`,
  `PreferencesHelper`, `NotificationForegroundService`, navigation router, ViewBinding
  layout ads…

> ⚠️ **Nếu bạn dùng bản AAR cũ** và sau khi build release `minifyEnabled true` bị
> `ClassNotFoundException` / `NoSuchMethodError` hoặc ads không load: hãy lấy **bản AAR mới
> nhất**. Bản cũ thiếu consumer rules nên R8 của app strip nhầm class của thư viện — bản
> mới đã bổ sung đầy đủ (parity với lib thật).

> ❌ ĐỪNG tự thêm `-keep class com.nlbn.ads.** { *; }` … vào `proguard-rules.pro` của app:
> đã có trong AAR, thêm lại chỉ gây trùng (vô hại nhưng thừa).

#### (b) BẮT BUỘC app tự thêm — SDK bên thứ ba

**Nguyên nhân phổ biến nhất của "build product minify bị miss class" với ads:** adapter
mediation (vd Facebook/Meta) được **nạp bằng reflection** (`Class.forName(...)`), R8 không
thấy ai gọi trực tiếp nên xoá/đổi tên → khi GMA SDK khởi tạo adapter thì
`ClassNotFoundException`. Thư viện chỉ chứa `com.nlbn.ads`; còn **adapter mediation + SDK
mạng quảng cáo là dependency của app**, nên app phải tự giữ. Dán khối sau vào
`app/proguard-rules.pro`:

```proguard
# --- AdMob mediation (Meta Audience Network) — nạp bằng reflection ---
-keep class com.google.ads.mediation.** { *; }
-keep class com.facebook.ads.** { *; }
-dontwarn com.facebook.ads.**
-dontwarn com.facebook.ads.internal.**

# --- Crashlytics: giữ stack trace đọc được (chỉ ảnh hưởng deobfuscation, không phải chức năng) ---
-keepattributes SourceFile,LineNumberTable

# --- Model JSON/Gson của riêng app (ĐỔI package cho đúng) ---
-keep class <package.model.cua.app>.** { *; }
-keepclassmembers,allowobfuscation class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# --- Cảnh báo lành tính (chỉ thêm nếu build fail vì nó) ---
-dontwarn de.hdodenhof.circleimageview.**
```

Bật `firebaseCrashlytics { mappingFileUploadEnabled true }` trong `buildType release` để
trace được deobfuscate trên server.

Các SDK còn lại — **GMA core, Firebase (analytics/crashlytics/messaging/firestore/config/
appcheck), Play Billing 7.x, Glide, Lottie, WorkManager, coroutines, SpinKit, Shimmer,
sdp, circleimageview, smoothprogressbar** — đều đã đóng gói consumer rules riêng hoặc không
có reflection → **không cần thêm gì**.

#### (c) Bắt buộc dùng cấu hình R8 CÓ tối ưu

Giữ nguyên `proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), …` như
§3.4. Rule strip log (`-assumenosideeffects android.util.Log`) trong AAR chỉ có hiệu lực
khi R8 bật tối ưu — **đừng** thêm `-dontoptimize`.

## 4. AndroidManifest.xml

> File mẫu đầy đủ: `sample/AndroidManifest.snippet.xml`.

### 4.1 ⚠️ Khai báo `android:name` (quan trọng nhất)

AAR **không** đặt `android:name` cho `<application>`. Nếu app không trỏ tới lớp
`HostApplication`, app vẫn build/cài/chạy được nhưng **mọi tính năng của thư viện sẽ
không hoạt động** mà không hề báo lỗi.

```xml
<application
    android:name=".HostApplication"
    android:allowBackup="true"
    android:icon="@mipmap/ic_launcher"
    android:label="@string/app_name"
    android:roundIcon="@mipmap/ic_launcher_round"
    android:supportsRtl="true"
    android:theme="@style/Theme.MyApp"
    tools:replace="android:theme">
    ...
</application>
```

### 4.2 Quyền (permissions)

**AAR đã khai báo sẵn** (host **không cần** thêm lại): `ACCESS_NETWORK_STATE`,
`INTERNET`, `WAKE_LOCK`, `WRITE_EXTERNAL_STORAGE`, `READ_EXTERNAL_STORAGE`,
`USE_FULL_SCREEN_INTENT`, `RECEIVE_BOOT_COMPLETED`, `VIBRATE`.

**App BẮT BUỘC tự khai báo trong `app/src/main/AndroidManifest.xml`** (real-lib AAR
KHÔNG ship sẵn 3 quyền này — nếu thiếu thì runtime sẽ throw `SecurityException` khi
lib gọi `startForegroundService` / `startForeground`, và notification không hiện trên
Android 13+):

```xml
<!-- FGS — cần để NotificationForegroundService của lib chạy được trên Android 9+ -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />

<!-- Type cho FGS — cần cho android:foregroundServiceType="specialUse" trên Android 14+ -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />

<!-- Notification runtime permission trên Android 13+; lib's Splash sẽ tự xin -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

<!-- AdMob trên Android 13+ -->
<uses-permission android:name="com.google.android.gms.permission.AD_ID" />
```

> **Lưu ý parity:** dummy AAR **cũng KHÔNG** ship 3 quyền `FOREGROUND_SERVICE` /
> `FOREGROUND_SERVICE_SPECIAL_USE` / `POST_NOTIFICATIONS` — giống hệt real-lib AAR (cả hai
> đều ship 0 quyền nhóm này; AAR chỉ có sẵn `USE_FULL_SCREEN_INTENT` cùng vài quyền cơ bản).
> Nhờ vậy hành vi khi test với dummy **khớp y hệt** production với real lib: nếu host quên
> khai, app sẽ crash ngay ở `startForegroundService` / không hiện notification trên **cả
> hai** build — chứ không còn cái bẫy "test dummy chạy ngon → swap real lib mới crash".
> Vì vậy **app phải tự khai đủ 4 quyền trên** (`FOREGROUND_SERVICE`,
> `FOREGROUND_SERVICE_SPECIAL_USE`, `POST_NOTIFICATIONS`, `AD_ID`) ngay từ đầu.

### 4.3 Meta-data AdMob & Facebook

```xml
<meta-data android:name="com.google.android.gms.ads.APPLICATION_ID"
    android:value="@string/admob_app_id" />
<meta-data android:name="com.facebook.sdk.ApplicationId"
    android:value="@string/facebook_app_id" />
<meta-data android:name="com.facebook.sdk.ClientToken"
    android:value="@string/facebook_client_token" />
```

### 4.4 KHÔNG khai báo MAIN/LAUNCHER

AAR đã cung cấp launcher (màn Splash). App **không** được khai báo
`intent-filter` `MAIN`/`LAUNCHER` cho bất kỳ Activity nào của mình.

### 4.5 Trả lời khai báo quyền trên Google Play Console

- `USE_FULL_SCREEN_INTENT` → chọn **"Other"**.
- `FOREGROUND_SERVICE_SPECIAL_USE` (mục **Documents**): mô tả app chạy tác vụ nền dài
  (chuyển đổi/quét/tải/đồng bộ tài liệu lớn) cần chạy liên tục với thông báo hiển thị,
  chỉ chạy khi người dùng thao tác và dừng ngay khi hoàn tất.

## 5. Tài nguyên bắt buộc

### 5.1 Màu — `res/values/colors.xml` (và `values-night/`)

`primaryColor` và `accentTone` phải được định nghĩa và **bằng nhau**. `text1` đặt cố
định ở cả `values/` và `values-night/` (giá trị giống nhau, không đổi theo theme).

```xml
<color name="primaryColor">#XXXXXX</color>
<color name="accentTone">#XXXXXX</color>   <!-- giống primaryColor -->
<color name="text1">#00091D</color>        <!-- giống nhau ở values/ và values-night/ -->
```

### 5.2 Drawable

| Đường dẫn | Ghi chú |
|---|---|
| `res/drawable/icon_app.xml` hoặc `.png` | Icon app dùng cho splash |
| `res/drawable-{m,h,xh,xxh,xxxh}dpi/icon_notification.png` | Đủ 5 mật độ, cùng tên. Icon status-bar 24×24dp, chỉ dùng kênh alpha (nền trong suốt, hình trắng) |
| `res/drawable/img_document_preview.png` | 365 × 174 dp |
| `icon_1_iap` … `icon_5_iap` (32×32dp) | 5 icon cho 5 tính năng trên màn IAP |
| `icon_noti_1` … `icon_noti_5` (32×32dp) | Ảnh minh hoạ thông báo của app: **đúng 5 icon**, mỗi icon cho 1 thông báo, chọn icon hợp chủ đề app (xem ô lưu ý dưới) |

> **Thông báo của app — 4 phần ghép theo chỉ số.**
> `getNotificationImages()` và 3 mảng `notification_title2` / `notification_message2` /
> `notification_button2` (mục 5.4) được **ghép theo index**: phần tử thứ *i* của cả 4 tạo
> thành **một** thông báo — `icon[i]` + tiêu đề `title[i]` + nội dung `message[i]` + nút `button[i]`.
>
> - **Số lượng phải bằng nhau, chuẩn là 5** (`noti_1`…`noti_5`). Mảng icon **ngắn hơn** mảng
>   tiêu đề sẽ gây **crash** (`ArrayIndexOutOfBoundsException`) khi bắn thông báo.
> - **Mọi phần (icon + tiêu đề + nội dung + nút) phải hợp chủ đề app của bạn.** App đọc tài
>   liệu nói về tài liệu (icon pdf, "PDF mới sẵn sàng", nút "Mở"); app TV nói về kênh/điều khiển;
>   app tải nói về tải/video. **Đừng** bê nguyên nội dung mẫu kiểu tài liệu sang app khác chủ đề.
> - Tiêu đề và nội dung là **1 dòng**, ngắn gọn (bị cắt nếu dài).

### 5.3 Raw

| Đường dẫn | Ghi chú |
|---|---|
| `res/raw/splash_loading.json` | Lottie thanh loading ở splash (màu nên khớp `primaryColor`). Có file mẫu kèm theo. |

### 5.4 Chuỗi — `res/values/strings.xml`

```xml
<string name="app_name">...</string>
<string name="app_flyer_id">...</string>
<string name="admob_app_id">ca-app-pub-XXXXXXXXXXXXXXXX~YYYYYYYYYY</string>
<string name="facebook_app_id">...</string>
<string name="facebook_client_token">...</string>
<string name="public_license_key">...</string>   <!-- Google Play license key -->
```

Ngoài ra cần khai báo mọi chuỗi/`string-array` mà `HostApplication` tham chiếu ở mục 6
(tiêu đề/nội dung thông báo, text tính năng IAP…), gồm các `string-array`:
`notification_title2`, `notification_message2`, `notification_button2` — **mỗi mảng 5 phần tử**,
khớp 1-1 với `getNotificationImages()` và phải hợp chủ đề app (xem ô lưu ý ở mục 5.2).

### 5.5 `assets/default_ads_config.json`

Chứa toàn bộ ad unit id. Các key bắt buộc (xem file mẫu `sample/default_ads_config.json`):
`open_splash`, `inter_splash`, `splash_uninstall` (open-ads), `native_language`, `open_all`,
`native_keep_user`, `native_survey_user`, `native_exit_app`.

Lúc khởi động, `BaseApplication` nạp file này vào Remote Config dưới **một key duy nhất
tên `ads_config`** (giá trị là chuỗi JSON `{placement → ad-unit-id}` phẳng này). Thư viện
và mọi code host đọc placement qua
`FirebaseRemoteConfigUtil.getInstance().getAdsConfigValue("<placement>")` — đọc key
`ads_config` từ FRC, fallback xuống asset này.

> ⚠️ **Đây là nguồn ad-unit DUY NHẤT thư viện đọc (key `ads_config`).** ĐỪNG dựng lớp
> config ads song song — manager riêng, key RC khác (vd. `ad_config_json`), hay gọi thẳng
> `FirebaseRemoteConfig.setDefaultsAsync(...)`: thư viện không đọc key đó (→ **vô hình** với
> `open_splash`, `open_all`, `native_*`…), **và** `setDefaultsAsync` trực tiếp sẽ **xoá**
> default `ads_config` của lib. Muốn đổi/A-B unit từ xa: override đúng key **`ads_config`**
> trên Firebase console (xem mục 8.5).

### 5.6 Bản dịch

Cung cấp `strings.xml` đa ngôn ngữ cho càng nhiều locale càng tốt:
`en-US, en-UK, en-AU, en-IN, pt, vi, ru, hi, ja, ko, tr, fr, es, zh, zh-TW, fa, nl, uk,
it, fr-CA, de, iw-IL, es-US, es-MX, pt-BR`.

## 6. Lớp HostApplication (kế thừa BaseApplication)

> File mẫu đầy đủ: `sample/HostApplication.kt`.

```kotlin
class HostApplication : BaseApplication() {
    override fun onCreate() {
        // (tuỳ chọn) khởi tạo thứ getHomeActivity() cần TRƯỚC super.onCreate()
        super.onCreate()
    }
    override fun getHomeActivity(): Class<out Activity> = MainActivity::class.java
    override fun initAppFlyerId() {
        AppFlyer.getInstance().initAppFlyer(this, getString(R.string.app_flyer_id),
            BuildConfig.DEBUG, false, true)
    }
    override fun setupKoin() { /* để trống nếu không dùng Koin */ }
    // ... (xem bảng bên dưới cho đầy đủ các hàm)
}
```

### 6.1 Các hàm BẮT BUỘC override (`abstract`)

Thiếu bất kỳ hàm nào dưới đây sẽ **không biên dịch được**.

| Nhóm | Hàm | Mục đích / ví dụ |
|---|---|---|
| Splash & thương hiệu | `getAppNameRes(): Int` | Tên app (`R.string.app_name`) |
| | `getIconSplashRes(): Int` | Icon app ở splash (`R.drawable.icon_app`) |
| | `getSplashLoadingRes(): Int` | Lottie loading (`R.raw.splash_loading`) |
| Định tuyến | `getHomeActivity(): Class<out Activity>` | Màn Home sau splash |
| Năng lực | `hasForegroundServicePermission(): Boolean` | App có quyền foreground service không |
| Khởi tạo | `initAppFlyerId()` | Khởi tạo AppsFlyer (gọi `AppFlyer.getInstance().initAppFlyer(...)`) |
| | `setupKoin()` | Cấu hình Koin (để trống nếu không dùng) |
| Ngôn ngữ | `notifyLanguageSaved(code: String)` | Thư viện **gọi lại** hàm này khi người dùng chọn ngôn ngữ ở màn Language dựng sẵn — bạn implement để **nhận và lưu** mã ngôn ngữ (chỉ persist). Xem mục 8.2 |
| Khoá IAP | `iapPremiumKey()/iapPremiumWeeklyKey()/iapPremiumMonthlyKey()/iapPremiumYearlyKey()` | Id sản phẩm/gói subscription. Có thể dùng `defaultIapPremiumKey()`… của thư viện |
| | `iapPublicKey(): String` | Google Play license key (`R.string.public_license_key`) |
| Icon IAP (đi **cặp** với text) | `getFeature1IconRes()` … `getFeature5IconRes(): Int` | 5 icon tính năng; mỗi icon N đi cùng `getFeatureNTextRes` tương ứng (cùng mô tả 1 dòng trên màn IAP) |
| Dialog thông báo | `getNotiTitleRes(): Int` / `getNotiContentRes(): Int` | Tiêu đề/nội dung dialog xin quyền thông báo |
| Bộ thông báo (ghép theo chỉ số) | `getNotificationImages(): IntArray` | **Đúng 5** icon minh hoạ (`noti_1`…`noti_5`), mỗi icon 1 thông báo, hợp chủ đề app — khớp 3 mảng dưới |
| | `getNotificationIconRes(): Int` | Icon status-bar |
| | `getNotificationChannelPrefix(): String` | Tiền tố tên kênh thông báo |
| | `getNewFileNotiContentRes(): Int` | Nội dung thông báo khi phát hiện file/nội dung mới trên máy |
| | `getScreenshotNotiTitleRes(): Int` | Tiêu đề thông báo khi phát hiện ảnh chụp màn hình mới |
| | `getRecentDocumentsTitleRes(): Int` | Tiêu đề thông báo dạng widget "nội dung gần đây" |
| | `getOpenTextRes(): Int` / `getScanDocumentRes(): Int` | Nhãn 2 nút trên widget đó: nút chính (vd "Mở") / nút phụ (vd "Quét") |
| | `getWidgetButtonBackgroundRes(): Int` | Drawable: nền cho nút trên thông báo widget |
| | `getDailyCallOpenAppContentRes(): Int` / `getCheckNowTextRes(): Int` | Thông báo nhắc dùng app hằng ngày: nội dung / nhãn nút (vd "Kiểm tra ngay") |
| | `getDocumentPreviewRes(): Int` | Drawable: ảnh xem trước trong thông báo toàn màn hình (365×174dp) |
| | `getFullScreenNoti1Res(): Int` / `getFullScreenNoti2Res(): Int` | 2 dòng chữ trong thông báo toàn màn hình |
| | `getNotificationTitles2ArrayRes(): Int` | `R.array.notification_title2` (**5 phần tử**, khớp icon) |
| | `getNotificationMessages2ArrayRes(): Int` | `R.array.notification_message2` (**5 phần tử**) |
| | `getNotificationButtons2ArrayRes(): Int` | `R.array.notification_button2` (**5 phần tử**) |
| | `getNotificationOutAppTitleRes(): Int` / `getNotificationOutAppContentRes(): Int` | Tiêu đề / nội dung thông báo hiển thị khi người dùng rời app |

> Các chuỗi thông báo ở trên đang ví dụ theo kiểu app tài liệu (file, ảnh chụp màn hình,
> tài liệu gần đây…) — hãy thay bằng nội dung **hợp chủ đề app của bạn**.

### 6.2 Các hàm TUỲ CHỌN override (`open`, đã có mặc định)

| Hàm | Mặc định | Khi nào override |
|---|---|---|
| `isPurchased(): Boolean` | `false` | Nối với billing thật: `= IAPUtils.isPremium()` |
| `enableAdsResume(): Boolean` | `true` | Tắt resume ad cho user trả phí: `= !IAPUtils.isPremium()` |
| `getListTestDeviceId(): List<String>?` | rỗng | Khai báo test device id để hiện quảng cáo test |
| `buildDebug(): Boolean?` | `false` | `= BuildConfig.DEBUG` |
| `isForceShowFullAdsTest(): Boolean?` | `false` | Ép luôn hiện full ad khi test |
| `getKeyRemoteIntervalShowInterstitial(): String?` | `null` | Đổi key remote điều khiển khoảng cách giữa 2 inter |
| `getFeature1TextRes()`…`getFeature5TextRes(): Int?` | `null` | Text tính năng IAP, **đi cặp với `getFeatureNIconRes`** (feature N = text N + icon N); null = dùng text mặc định. Khai báo theo từng cặp để text & icon luôn khớp |
| `enableAdjustTracking(): Boolean` / `getAdjustToken(): String` | `false` / `""` | Nếu dùng Adjust |
| `attachBaseContext` / `onConfigurationChanged` | gọi super | Nếu app tự quản lý locale |

### 6.3 Hàm helper có sẵn (gọi được từ HostApplication)

- `defaultIapPremiumKey()`, `defaultIapPremiumWeeklyKey()`, `defaultIapPremiumMonthlyKey()`,
  `defaultIapPremiumYearlyKey()` — trả về khoá mặc định của thư viện.
- `getDefaultString(resId)` — đọc string resource.

### 6.4 Lưu ý quan trọng

- **PHẢI** gọi `super.onCreate()` — thư viện làm toàn bộ khởi tạo trong đó.
- Nếu `getHomeActivity()` đọc SharedPreferences/biến gì thì khởi tạo chúng **trước**
  `super.onCreate()`.
- KHÔNG cần tự khởi tạo quảng cáo/consent ở `HostApplication`.

## 7. Cắt bỏ & bắt buộc khi tích hợp

### 7.1 Cắt bỏ ở phía app (vì AAR đã có sẵn)

- Bỏ màn **Splash** và layout splash của app.
- Bỏ màn **Uninstall** (`UninstallActivity`) + layout.
- Xóa `res/xml/shortcuts.xml` **và** entry `<meta-data android:name="android.app.shortcuts">` trong manifest.
- Bỏ toàn bộ code lập lịch **notification / tip & tricks** của app.
- Bỏ `FirebaseMessagingService` riêng (nếu có) + entry `<service>` của nó trong manifest —
  **trừ khi** app có push riêng; khi đó **kế thừa** service của thư viện (xem **mục 8.6**).
- **Giữ lại** màn IAP — đừng bỏ; phải mở được từ Home & Settings (mục 8.3).

### 7.2 Bắt buộc

- `minSdk` 28; bản release `minifyEnabled true` + `shrinkResources true` (cả hai).
- Chuẩn bị đủ tài nguyên ở mục 5.
- Màn IAP phải mở được từ Home và Settings (mục 8.3).

## 8. Các luồng runtime

**Luồng khởi động (mặc định — dùng màn Language của thư viện):**

```
Splash  →  Interstitial (inter_splash)  →  Language  →  IAP (paywall)  →  Home
```

1. **Splash** — màn launcher của thư viện; xin **consent** (UMP) nếu cần (mục 8.1).
2. **Interstitial** — nạp & hiện inter `inter_splash` (ad unit id lấy từ
   `default_ads_config.json`). Nếu id **rỗng** hoặc **nạp lỗi / không có fill**, thư viện tự
   fallback sang **inter test id của Google** để vẫn hiện một lần (an toàn cho QA và ad unit
   mới chưa fill). Fallback chỉ thử **một lần** rồi đi tiếp dù thành công hay không.
3. **Language** — màn chọn ngôn ngữ (mục 8.2).
4. **IAP** — màn mua gói / paywall (mục 8.3); đóng IAP sẽ về Home.
5. **Home** — `getHomeActivity()` của app.

**Nếu app dùng màn Language của riêng mình** (đăng ký qua `LanguageRouter.customActivityClass`
hoặc `LanguageRouter.launcher` — mục 8.2.1): thư viện vẫn chạy **Splash → Inter → [màn Language
của app]** và truyền sẵn **IAP** làm "màn kế tiếp". Bước chuyển sang IAP sau đó **do app quyết
định** khi gọi `LanguageRouter.confirmLanguageSelection(...)` (mục 8.2.2):

- **`customActivityClass`:** thư viện đã gắn sẵn "màn kế tiếp = IAP" vào intent của màn bạn,
  nên chỉ cần gọi `confirmLanguageSelection(activity, code)` là tự sang IAP.
- **`launcher`:** phải **truyền tiếp** tham số `nextScreen` mà thư viện đưa cho bạn vào
  `confirmLanguageSelection(activity, code, nextScreen)`. Nếu bỏ qua, luồng đi thẳng về
  `getHomeActivity()` (bỏ qua IAP).

> Tóm lại: dùng màn Language **của thư viện** → luồng cố định **Splash → Inter → Language →
> IAP**. Dùng màn Language **của app** → điểm đến sau màn Language do app điều khiển qua
> `confirmLanguageSelection` (mục 8.2.2).

### 8.1 Consent (UMP/GDPR)

Thư viện tự xin consent trong luồng splash trước khi hiển thị quảng cáo. App
**không** tự gọi consent hay khởi tạo quảng cáo.

### 8.2 Chọn ngôn ngữ

**Thư viện đã có sẵn màn chọn ngôn ngữ (Language Activity)** và tự hiển thị trong luồng
splash — app **không cần tự dựng** màn này. Khi người dùng chọn xong ngôn ngữ, thư viện
**gọi lại** hàm `notifyLanguageSaved(languageCode)` trên lớp `HostApplication` của bạn.
Hãy implement hàm này để **nhận và lưu** mã ngôn ngữ người dùng đã chọn:

```kotlin
override fun notifyLanguageSaved(languageCode: String) {
    // languageCode = mã người dùng vừa chọn ở màn Language của thư viện, ví dụ "vi", "en-US"
    getSharedPreferences(packageName, MODE_PRIVATE).edit()
        .putString("language_pres", languageCode).apply()
}
```

> Thư viện đã tự áp locale cho toàn app; `notifyLanguageSaved` chỉ để app lưu lại lựa chọn
> (đồng bộ prefs/analytics nếu cần). Đừng làm gì nặng trong đây.

#### 8.2.1 (Tuỳ chọn) Dùng màn chọn ngôn ngữ của riêng app

Khi muốn thay màn Language mặc định bằng màn của riêng app, đăng ký **trước khi luồng
splash gọi mở Language** — vị trí khuyến nghị: `HostApplication.onCreate()` (trước hoặc
sau `super.onCreate()` đều OK, miễn là chạy trước Splash mở màn Language). Không đăng ký
gì thì thư viện dùng màn mặc định.

##### Hai cách đăng ký — chọn một

| Cách | Khi nào dùng | Bạn cần làm |
|---|---|---|
| `customActivityClass` *(khuyên dùng)* | Bạn có **một** `Activity` Language riêng | Set class; lib tự `startActivity`, propagate extras, gắn sẵn "màn kế tiếp = IAP" |
| `launcher` | Cần kiểm soát hoàn toàn (Fragment, Dialog, multi-step UI…) | Triển khai callback `(activity, nextScreen) -> Unit` và tự build intent |

Cả hai cùng đặt trên `LanguageRouter`. Lib ưu tiên `launcher` nếu cả hai cùng set, nên
chỉ chọn một.

##### Cách A — `customActivityClass` (đa số dùng)

```kotlin
import com.brian.base_application.BaseApplication
import com.brian.base_application.language.LanguageRouter

class HostApplication : BaseApplication() {
    override fun onCreate() {
        // Đăng ký trước khi Splash mở Language.
        LanguageRouter.customActivityClass = MyLanguageActivity::class.java
        super.onCreate()
    }
    // ... các override khác
}
```

```kotlin
// MyLanguageActivity.kt — FragmentActivity hoặc AppCompatActivity đều OK.
class MyLanguageActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_my_language)
        // ... bind RecyclerView danh sách ngôn ngữ ...

        binding.btnDone.setOnClickListener {
            val selectedCode = adapter.selectedCode   // vd "vi", "en-US"
            // Báo lib + chuyển sang IAP (xem mục 8.2.2). Lib tự đọc "màn kế tiếp"
            // từ intent extras nó đã gắn vào activity này, không cần bạn truyền tay.
            LanguageRouter.confirmLanguageSelection(this, selectedCode)
        }
    }
}
```

Khai báo trong `AndroidManifest.xml` (mọi Activity bình thường):

```xml
<activity
    android:name=".MyLanguageActivity"
    android:exported="false"
    android:screenOrientation="portrait" />
```

##### Cách B — `launcher` (kiểm soát toàn quyền)

```kotlin
import com.brian.base_application.language.LanguageScreenLauncher

override fun onCreate() {
    LanguageRouter.launcher = LanguageScreenLauncher { activity, nextScreen ->
        // activity = Splash đang chạy
        // nextScreen = Class<out Activity> mà lib muốn chuyển sau Language (= IapActivity)
        // PHẢI nhớ "nextScreen" và truyền lại khi gọi confirmLanguageSelection (xem dưới).
        val intent = Intent(activity, MyLanguageActivity::class.java)
        nextScreen?.let { intent.putExtra("next_screen", it.name) }
        activity.startActivity(intent)
    }
    super.onCreate()
}
```

Trong `MyLanguageActivity` khi user xong:

```kotlin
val nextScreen = intent.getStringExtra("next_screen")?.let { Class.forName(it) as Class<out Activity> }
LanguageRouter.confirmLanguageSelection(this, selectedCode, nextScreen = nextScreen)
```

> **Quan trọng:** với cách B bạn **phải tự truyền `nextScreen`** vào
> `confirmLanguageSelection`. Nếu bỏ qua, sau Language sẽ về thẳng `getHomeActivity()`
> (bỏ qua IAP). Với cách A thì không cần — lib gắn sẵn.

##### Yêu cầu cho màn Language của bạn

- Là `Activity` (lib `startActivity` nó). Nếu thực sự muốn dùng `Fragment` / `Dialog`,
  vẫn cần một `Activity` bao bên ngoài để mở.
- Mở rộng `FragmentActivity` (hoặc subclass — `AppCompatActivity` đạt yêu cầu).
- Đăng ký `<activity>` trong `AndroidManifest.xml`.
- KHÔNG đặt `MAIN/LAUNCHER` intent-filter (launcher của app là Splash của lib — xem mục 4.4).

##### Đừng

- ❌ Đừng tự gọi `Locale.setDefault` / `Configuration.setLocale` — `confirmLanguageSelection` đã làm.
- ❌ Đừng tự ghi prefs ngôn ngữ của lib — `confirmLanguageSelection` tự ghi. Muốn lưu thêm thì implement `notifyLanguageSaved(code)` (mục 8.2).
- ❌ Đừng `finish()` Splash từ tay bạn — lib tự `finish()` Splash sau khi `confirmLanguageSelection(..., navigate = true)` chạy.

##### Pitfall: vòng lặp lại màn Language

Nếu user thoát màn của bạn (back / X) mà **không** gọi `confirmLanguageSelection`, lần
mở app sau lib coi như chưa chọn lần đầu → lại chạy Splash → Language. Vì vậy ở handler
back, hoặc gọi `confirmLanguageSelection(this, defaultCode)` (vd `"en"`), hoặc disable back.

#### 8.2.2 Báo cho thư viện biết ngôn ngữ vừa chọn

Khi dùng màn của riêng bạn (hoặc đổi ngôn ngữ ở **bất kỳ đâu**, kể cả màn Settings), hãy
gọi **đúng một hàm** để báo cho thư viện — **đừng** tự ghi prefs hay tự đổi locale bằng tay:

```kotlin
LanguageRouter.confirmLanguageSelection(activity, selectedCode)   // vd "en-US", "vi", "pt-BR"
```

`confirmLanguageSelection` làm sẵn 3 việc cho bạn:

1. **Lưu mã ngôn ngữ** vào prefs của thư viện (để các màn của lib hiển thị đúng ngôn ngữ).
2. **Áp locale** cho toàn app.
3. **Gọi `notifyLanguageSaved(code)`** trên `HostApplication` của bạn (để app lưu/đồng bộ thêm).

> ⚠️ Ở màn ngôn ngữ **lần đầu**: nếu thoát mà **không** gọi `confirmLanguageSelection`,
> luồng splash sẽ lặp lại màn ngôn ngữ ở mỗi lần mở app.

**Đổi ngôn ngữ về sau (vd từ màn Settings):** vẫn gọi đúng hàm trên nhưng thêm
`navigate = false` để chỉ áp ngôn ngữ + báo cho lib, KHÔNG để lib tự chuyển màn (và **không**
khởi động lại app từ Splash):

```kotlin
LanguageRouter.confirmLanguageSelection(activity, selectedCode, navigate = false)
// ...sau đó tự recreate()/refresh lại UI của bạn nếu cần
```

Lưu ý điều hướng (chỉ áp dụng cho **lần đầu**): nếu tự điều hướng (`navigate = false` ở lần
đầu) thì màn bạn mở tiếp **phải** dẫn về `getHomeActivity()` — đó là điểm vào cố định của app.

#### 8.2.3 Preload native ad cho màn Language (`TemporaryStorage.preloadedLanguageNativeAd`)

Thư viện **tự preload** native ad của màn Language ngay từ Splash, song song với inter
splash. Kết quả lưu vào **đúng một slot** — `TemporaryStorage.preloadedLanguageNativeAd`.
Cả màn Language của thư viện **lẫn** màn Language của riêng app **đều đọc từ slot này**;
không có slot thứ 2 cần lo. Nhờ vậy khi user tới màn Language, ad **bind tức thì** (không
có shimmer + delay 1–2 s).

> **Customer không cần tự viết logic preload `native_language`** — lib's Splash đã
> preload sẵn. Custom LanguageActivity của host **chỉ cần đọc**
> `TemporaryStorage.preloadedLanguageNativeAd` (theo pattern *read-and-clear* ở mục
> "Pattern tiêu thụ" bên dưới). Đừng load lại `native_language` lần thứ 2 ở app side
> khi slot đã có ad — phí impression + có thể bị Admob đánh dấu invalid traffic.

- **Màn Language của thư viện**: tự đọc, **bạn không phải làm gì**.
- **Màn Language của riêng app** (Cách A / Cách B ở mục 8.2.1): đọc từ cùng slot, theo
  pattern bên dưới — hoặc bỏ qua nếu không cần ad.

##### Điều kiện preload chạy (tự gating, lib lo)

Lib chỉ phát ad request khi **đủ cả 3**:

- User **chưa premium** (`IAPUtils.isPremium() == false`).
- `IS_FIRST_TIME_LANGUAGE == true` — tức là user chưa chọn ngôn ngữ lần nào. Sau khi
  `confirmLanguageSelection` được gọi lần đầu (mục 8.2.2), flag flip sang `false`, Splash
  cũng sẽ skip màn Language ở lần mở app sau — nên preload bị bỏ qua, tránh phí impression.
- `FirebaseRemoteConfigUtil.getInstance().getAdsConfigValue("native_language")` **không
  rỗng** (key có trong `default_ads_config.json` hoặc Firebase console).

Nếu một trong ba fail (hoặc Admob load fail / no-fill) → `preloadedLanguageNativeAd = null`.
Code consumer **phải** check null và fallback sang inline load để màn Language vẫn có ad.

##### Pattern tiêu thụ (cho custom LanguageActivity)

```kotlin
import com.brian.base_iap.utils.TemporaryStorage
import com.google.android.gms.ads.nativead.NativeAd
import com.google.android.gms.ads.nativead.NativeAdView

class MyLanguageActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_my_language)
        showNativeAd()
    }

    private fun showNativeAd() {
        // Read-and-clear: lấy ad rồi set field về null NGAY để tránh bind lại
        // ở activity recreate (rotate / config change).
        val preloaded = TemporaryStorage.preloadedLanguageNativeAd
        TemporaryStorage.preloadedLanguageNativeAd = null

        if (preloaded != null) {
            bindInstantly(preloaded)              // hot path — không shimmer
        } else {
            loadInlineWithShimmer()               // fallback — preload skip / fail / hết hạn
        }
    }

    private fun bindInstantly(nativeAd: NativeAd) {
        val adView = layoutInflater
            .inflate(R.layout.my_native_ad_layout, null) as NativeAdView
        binding.adContainer.removeAllViews()
        binding.adContainer.addView(adView)
        Admob.getInstance().pushAdsToViewCustom(nativeAd, adView)
    }

    private fun loadInlineWithShimmer() {
        // ... shimmer placeholder ...
        Admob.getInstance().loadNativeAd(
            applicationContext,
            FirebaseRemoteConfigUtil.getInstance().getAdsConfigValue("native_language"),
            object : NativeCallback() {
                override fun onNativeAdLoaded(nativeAd: NativeAd?) {
                    if (isFinishing || isDestroyed) return
                    bindInstantly(nativeAd ?: return)
                }
                override fun onAdFailedToLoad() {
                    binding.adContainer.visibility = View.GONE
                }
            }
        )
    }
}
```

##### Đừng

- ❌ Đừng giữ reference dài hạn tới `preloadedLanguageNativeAd` — native ad có TTL ở
  Admob (~60 phút). Đọc xong bind ngay, set field `null`, không cache trong ViewModel /
  singleton.
- ❌ Đừng bind **2 lần** cùng một NativeAd — Admob log warning và có thể block impression
  tracking. Đó là lý do pattern trên là *read-and-clear*: lấy xong null hoá ngay.
- ❌ Đừng **ghi** vào `preloadedLanguageNativeAd` từ host code — đó là slot lib's Splash
  populate. Host chỉ đọc-xong-xoá (read-and-clear), không ghi.

### 8.3 Mở màn IAP (Paywall)

```kotlin
import com.brian.base_iap.utils.NativeCodecSnowFlakeCortexAI

// Mở màn IAP/paywall — gọi từ nút mua gói ở Home, Settings, hoặc khi chặn tính năng premium.
// (Tên app trên paywall lấy từ getAppNameRes() đã cấu hình ở HostApplication.)
NativeCodecSnowFlakeCortexAI.nativeAiStartIapActivity(this)
```

**Chặn tính năng premium (paywall gate) — mẫu khuyến nghị.** Khi một tính năng yêu cầu mua
gói: **chỉ cần mở màn IAP**, đừng cố tự chạy tính năng ngay trong/sau luồng paywall. Màn IAP
**tự đóng** sau khi người dùng mua xong. Lần bấm kế tiếp, `IAPUtils.isPremium()` đã là `true`
nên tính năng chạy thẳng, không còn hiện paywall:

```kotlin
fun onPremiumFeatureClick() {
    if (IAPUtils.isPremium()) {
        useFeature()                          // đã mua → dùng luôn, không chặn
    } else {
        NativeCodecSnowFlakeCortexAI.nativeAiStartIapActivity(this)  // chưa mua → mở paywall (tự đóng sau khi mua)
    }
}
```

Luồng: bấm lần 1 (chưa mua) → hiện paywall → mua xong → paywall **tự đóng** → bấm lần 2 →
đã premium → dùng tính năng, không bị chặn nữa.

### 8.4 Dialog xin quyền FullScreenIntent

Ở màn Home, hiển thị dialog mời người dùng cấp quyền "hiển thị trên màn hình khoá /
full-screen notification".

### 8.5 Remote Config cho key riêng của app

Nếu app cần thêm key Remote Config của riêng mình (chẳng hạn cờ bật/tắt feature, tham
số nội bộ, message chào…), đăng ký **default** cho key đó qua API của thư viện. Khi đó
giá trị console (sau khi fetch về) sẽ override default; nếu fetch chưa về hoặc thiếu
key trên console, getter trả về default vừa đăng ký.

#### Nguyên tắc (đọc trước khi viết code)

- ✅ Gọi qua `FirebaseRemoteConfigUtil.getInstance()` — **đừng** dùng
  `FirebaseRemoteConfig.getInstance()` trực tiếp. API của thư viện đã lo việc giữ
  default của nó (xem ô "Lib default được giữ nguyên" bên dưới); gọi trực tiếp sẽ ghi
  đè và làm vỡ feature của lib.
- ✅ Đăng ký ở `HostApplication.onCreate()` **sau** `super.onCreate()`. Mọi key mà
  app dùng nên có default tại đây.
- ✅ Truyền **toàn bộ** key của app trong **một** lần gọi `setAppDefaults`. Gọi lại
  sẽ **thay thế** (không cộng dồn) — chỉ key trong lần gọi mới nhất có default ở phía
  Firebase SDK.
- ✅ Đặt **tiền tố riêng** cho key của app (vd. `myapp_…`) để không đụng key thư viện.
- ❌ Đừng kỳ vọng giá trị console có ngay — fetch chạy bất đồng bộ. Lần đầu mở app, các
  screen mở rất sớm có thể đọc trúng default. Sau khi fetch xong (vài trăm ms tới vài
  giây), lần đọc kế tiếp sẽ trả giá trị console.
- ❌ Đừng đặt trùng tên với key của thư viện — lib sẽ **luôn thắng** cho key trùng
  (xem ô bên dưới), default của app bị bỏ qua.

#### Ví dụ A — đăng ký bằng Map (code)

```kotlin
import com.brian.base_iap.utils.FirebaseRemoteConfigUtil

class HostApplication : BaseApplication() {
    override fun onCreate() {
        super.onCreate()   // lib khởi tạo + tự fetch Remote Config ở đây

        // Đăng ký TẤT CẢ default của app trong MỘT lần gọi.
        FirebaseRemoteConfigUtil.getInstance().setAppDefaults(
            mapOf(
                "myapp_show_promo_banner" to false,
                "myapp_max_retry"         to 3L,
                "myapp_welcome_message"   to "Hello",
                "myapp_min_app_version"   to 100L,
            )
        )
    }
    // ... các override khác
}
```

#### Ví dụ B — đăng ký từ XML resource

`res/xml/remote_config_defaults.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<defaultsMap>
    <entry>
        <key>myapp_show_promo_banner</key>
        <value>false</value>
    </entry>
    <entry>
        <key>myapp_max_retry</key>
        <value>3</value>
    </entry>
    <entry>
        <key>myapp_welcome_message</key>
        <value>Hello</value>
    </entry>
</defaultsMap>
```

```kotlin
override fun onCreate() {
    super.onCreate()
    FirebaseRemoteConfigUtil.getInstance()
        .setAppDefaultsFromXml(R.xml.remote_config_defaults)
}
```

#### Đọc giá trị (ở bất kỳ Activity / ViewModel / class nào)

```kotlin
val frc = FirebaseRemoteConfigUtil.getInstance()

val showPromo = frc.getBoolean("myapp_show_promo_banner")  // false → default
val maxRetry  = frc.getLong   ("myapp_max_retry")          // 3
val welcome   = frc.getString ("myapp_welcome_message")    // "Hello"
```

Các hàm `getString` / `getBoolean` / `getLong` đọc theo thứ tự ưu tiên:
**giá trị console (đã fetch) → default app đã đăng ký → fallback rỗng (`""` / `false` /
`0`)** — và đã tự `try/catch` nên an toàn gọi sớm.

> **Lib default được giữ nguyên — bạn không phải lo.** Cả `setAppDefaults` lẫn
> `setAppDefaultsFromXml` được thư viện viết theo nguyên tắc *"app làm nền, lib re-apply
> ở trên đỉnh"*: với mỗi lần app đăng ký, thư viện tự merge `(app defaults) ∪ (lib
> defaults)` rồi `setDefaultsAsync` lại — lib thắng cho key trùng. Vì vậy bạn **không
> cần** copy lại default của lib (vd. `ads_config`); chỉ liệt kê key của app.

> 📦 **Ad unit nằm dưới key `ads_config` — đổi unit từ xa bằng chính key đó.** Toàn bộ ad
> unit (`open_splash`, `open_all`, `native_*`…) nằm trong **một** key Remote Config tên
> `ads_config` (chuỗi JSON = nội dung `assets/default_ads_config.json`), đọc bằng
> `getAdsConfigValue("<placement>")`. Muốn đổi/A-B từ xa: thêm tham số tên đúng
> **`ads_config`** trên Firebase console, value là chuỗi JSON cùng dạng — key có trong
> console thắng, key thiếu fallback về asset. **KHÔNG** tạo lớp config ads riêng dưới key
> khác (vd. `ad_config_json`) hay gọi `setDefaultsAsync(...)` trực tiếp: lib không đọc key
> đó, và `setDefaultsAsync` sẽ **xoá** default `ads_config` của lib (xem thêm mục 5.5).

> ⚠️ **CẢNH BÁO: KHÔNG tạo subclass `FirebaseRemoteConfigUtil` với companion
> `getInstance()` riêng** — sẽ tạo **singleton song song** mà thư viện không nhìn
> thấy. Lib's `BaseApplication.onCreate()` chỉ populate default JSON + trigger
> fetch trên `FirebaseRemoteConfigUtil.getInstance()` (singleton của lớp cha).
> Nếu bạn tạo `class MyConfigUtil : FirebaseRemoteConfigUtil() { companion object {
> private var instance: MyConfigUtil? = null; fun getInstance() = ... } }`, Kotlin
> tạo `MyConfigUtil.getInstance()` thành **method khác** với `Parent.getInstance()`
> (companion object không inherit) → instance `MyConfigUtil` ra đời với
> `defaultAdsConfigJson = ""` rỗng. Mọi `getAdsConfigValue(key)` gọi trên
> `MyConfigUtil` sẽ trả `""` cho tới khi FRC fetch về xong (vài trăm ms — quá trễ
> cho splash / resume ad load đầu tiên) → **ad ID rỗng → ad không load**.
>
> **Đúng:** dùng thẳng `FirebaseRemoteConfigUtil.getInstance()`. Nếu cần tên-alias
> riêng cho dễ đọc, làm `object` thuần (không kế thừa, không companion riêng):
> ```kotlin
> // ✓ ĐÚNG — alias mượn singleton của lib
> object MyConfigHelper {
>     @JvmStatic
>     fun getInstance(): FirebaseRemoteConfigUtil =
>         FirebaseRemoteConfigUtil.getInstance()
> }
>
> // ✗ SAI — singleton song song, default rỗng, ad ID rỗng
> class MyConfigPrime : FirebaseRemoteConfigUtil() {
>     companion object {
>         private var instance: MyConfigPrime? = null
>         fun getInstance() = instance ?: MyConfigPrime().also { instance = it }
>     }
> }
> ```

**Thư viện tự fetch Remote Config — app KHÔNG cần gọi fetch.** Trong
`BaseApplication.onCreate()` thư viện tự gọi:

```kotlin
FirebaseRemoteConfigUtil.getInstance().fetchRemoteConfig { ok ->
    Log.d("BaseApplication", "remote config fetched: $ok")
}
```

Nội bộ hàm này gọi `firebaseRemoteConfig.fetchAndActivate()`. Default đăng ký ở trên có
ngay; giá trị từ Firebase console về **bất đồng bộ** và overlay lên trên (lib defaults
vẫn thắng default app cho key trùng — xem `setAppDefaults` / `setAppDefaultsFromXml`).
Đọc giá trị bằng `getString(key)` / `getBoolean(key)` / `getLong(key)` /
`getAdsConfigValue(key)` — chúng đọc từ FRC trước, fallback xuống default lib.

**Force refetch (hiếm khi cần):** nếu muốn fetch lại ngay (vd. test giá trị console
mới), gọi cùng API:

```kotlin
FirebaseRemoteConfigUtil.getInstance().fetchRemoteConfig { ok -> /* ... */ }
```

> Lưu ý: `minimumFetchIntervalInSeconds` được lib đặt cố định 3600s (1 giờ) — Firebase
> sẽ trả cache nếu fetch lần nữa trong khoảng đó. Mở Firebase console hoặc đợi qua
> interval để thấy giá trị mới khi test.

### 8.6 (Tùy chọn) FCM service riêng của app

**Bỏ qua mục này** nếu app không có push riêng — thư viện đã khai báo sẵn FCM service trong
AAR và tự xử lý message của nó, bạn không phải làm gì.

Chỉ làm khi app **có push riêng** (deep link, thông báo riêng, đăng ký token…). Một tiến trình
chỉ được có **một** service `com.google.firebase.MESSAGING_EVENT`, nên không thể chạy song song
service của bạn cạnh service của thư viện — bạn phải **kế thừa** service của thư viện để cả hai
cùng chạy từ một chỗ.

**Bước 1 — Kế thừa `BaseFirebaseMessagingService`.** Gọi `super.onMessageReceived(...)` **đầu tiên**
(chạy pipeline của thư viện), rồi mới tới xử lý của bạn:

```kotlin
import com.brian.base_notification.gteg54g34b4t3.BaseFirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class MyMessagingService : BaseFirebaseMessagingService() {
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)   // pipeline của thư viện chạy ở đây
        // ...routing của bạn: dựng notification, deep link...
        // Bỏ qua payload bạn không nhận diện để 1 push của thư viện không bị xử lý 2 lần.
    }
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // ...đăng ký token với backend của bạn nếu cần...
    }
}
```

**Bước 2 — Trong manifest của app:** gỡ service mặc định của thư viện, rồi đăng ký service của bạn
(chỉ được tồn tại MỘT service `MESSAGING_EVENT`):

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">   <!-- cần cho tools:node -->
  <application>

    <!-- 1) Gỡ FCM service mặc định của thư viện (phải dùng tên đầy đủ) -->
    <service
        android:name="com.brian.base_notification.gteg54g34b4t3.BaseFirebaseMessagingService"
        tools:node="remove" />

    <!-- 2) Đăng ký service của bạn -->
    <service
        android:name=".MyMessagingService"
        android:exported="false">
        <intent-filter>
            <action android:name="com.google.firebase.MESSAGING_EVENT" />
        </intent-filter>
    </service>

  </application>
</manifest>
```

Lưu ý:
- `tools:node="remove"` khớp theo `android:name`, phải là **tên đầy đủ** (manifest app ưu tiên cao hơn AAR nên thắng).
- AAR không kèm metadata phụ thuộc → nếu subclass, app phải tự khai báo `com.google.firebase:firebase-messaging` (đã có trong `build.gradle` mẫu).
- `NotificationForegroundService` và các kênh thông báo vẫn do AAR cung cấp — bạn không khai báo lại; `super.onMessageReceived()` vẫn khởi động foreground service.
- Kiểm tra merge: chạy `./gradlew :app:processReleaseManifest` rồi grep `MESSAGING_EVENT` trong manifest đã merge — phải còn **đúng một** service (của bạn).

### 8.7 (Tuỳ chọn) Màn Intro / Onboarding của riêng app

Sau khi user xong **Language → IAP** và đóng IAP, lib mở `getHomeActivity()` của bạn. Nếu
muốn chèn **Intro / Onboarding** trước MainActivity, **đừng dựng router riêng** — thư
viện không có hook "Intro" tách riêng. Mẫu chuẩn: dùng chính `getHomeActivity()` để rẽ
nhánh theo state đã onboarding hay chưa.

#### Concept

```
Splash → Inter → Language → IAP → [getHomeActivity()] → MainActivity
                                          │
                                          ├─ chưa onboarding  → IntroActivity
                                          └─ đã onboarding   → MainActivity
```

`IntroActivity` tự mở `MainActivity` (kèm flag pop intro khỏi back stack) khi user xong.
Lib không tham gia bước đó.

#### Bước 1 — Khởi tạo storage **TRƯỚC** `super.onCreate()`

`BaseApplication.onCreate()` gọi `getHomeActivity()` ngay khi app khởi động để cài đặt
router IAP-close. Nếu `getHomeActivity()` đọc `SharedPreferences` / DataStore của app,
phải init nó **trước** `super.onCreate()` — không thì NPE lúc app start. (Quy tắc đã có
ở mục 6.4 — đây là một use case điển hình.)

```kotlin
class HostApplication : BaseApplication() {

    override fun onCreate() {
        // Init storage TRƯỚC super.onCreate vì getHomeActivity() đọc nó.
        MyAppPrefs.init(this)
        super.onCreate()
    }

    override fun getHomeActivity(): Class<out Activity> {
        return if (MyAppPrefs.isOnboardingDone()) {
            MainActivity::class.java
        } else {
            IntroActivity::class.java
        }
    }
    // ... các override khác
}
```

#### Bước 2 — IntroActivity tự chuyển sang MainActivity khi xong

```kotlin
class IntroActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_intro)
        // ... ViewPager slide intro, nút "Skip" / "Get started" ...

        binding.btnGetStarted.setOnClickListener {
            MyAppPrefs.setOnboardingDone(true)
            // Pop Intro khỏi back stack để BACK từ Main không quay lại Intro.
            startActivity(
                Intent(this, MainActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK or Intent.FLAG_ACTIVITY_NEW_TASK)
            )
            finish()
        }
    }
}
```

Khai báo trong `AndroidManifest.xml` (không đặt `MAIN/LAUNCHER` — launcher là Splash của lib):

```xml
<activity
    android:name=".IntroActivity"
    android:exported="false"
    android:screenOrientation="portrait" />
```

#### Đóng IAP đi đâu?

Khi user đóng IAP (nút X), lib gọi `IapRouter.navigationHandler.goToNextScreen()`. Target
này là class mà `getHomeActivity()` trả lúc **app khởi động**:

- **Lần đầu mở app** (chưa onboarding): `getHomeActivity()` → `IntroActivity` → đóng IAP về Intro ✓
- **Lần sau** (đã onboarding): `getHomeActivity()` → `MainActivity` → đóng IAP về Main ✓

Nhờ đó pattern hoạt động chính xác mà không cần thêm hook nào.

#### Pitfalls

- ❌ Đừng đặt `<intent-filter MAIN/LAUNCHER>` trên IntroActivity. Launcher là Splash của lib (mục 4.4).
- ❌ Đừng quên `FLAG_ACTIVITY_CLEAR_TASK | FLAG_ACTIVITY_NEW_TASK` khi đi từ Intro sang Main — thiếu thì BACK từ Main quay lại Intro thay vì exit.
- ❌ Đừng đọc state onboarding bằng class chưa init (lateinit/Koin) trong `getHomeActivity()` — sẽ NPE vì gọi rất sớm. Dùng SharedPreferences / DataStore init ngay đầu `onCreate()` (xem Bước 1).
- ❌ Đừng mở IAP **từ trong** Intro — màn IAP đã chạy **trước** Intro trong luồng. Nếu cần upsell trong Intro, gọi `NativeCodecSnowFlakeCortexAI.nativeAiStartIapActivity(this)` (mục 8.3).

## 9. Phụ lục A — Firebase / Crashlytics

- Bỏ `google-services.json` vào thư mục `app/`.
- Sau khi phát hành lên Play, liên kết Firebase với app trên store.
- Xuất file service-account JSON của Firebase, đổi tên theo application-id và lưu trữ
  theo quy ước của team.

## 10. Phụ lục B — Thiết lập IAP

Tạo 3 sản phẩm subscription trên Play Console khớp với:
`iapPremiumWeeklyKey()` (tuần), `iapPremiumMonthlyKey()` (tháng), `iapPremiumYearlyKey()` (năm),
cùng license key qua `iapPublicKey()` (`R.string.public_license_key`).

## 11. Phụ lục C — Hiển thị quảng cáo của riêng bạn

Ngoài quảng cáo thư viện tự hiển thị, app có thể tự hiển thị quảng cáo trên màn của mình
qua `Admob.getInstance()` (banner/inter/native/reward) và `AppOpenManager.getInstance()`.

### 11.1 Banner

```kotlin
Admob.getInstance().loadBanner(
    activity, "ca-app-pub-.../banner", bannerContainer,
    object : BannerCallBack() {
        override fun onBannerAdLoaded() {}
        override fun onBannerAdFailed() {}
        override fun onAdClicked() {}
    })
```

BannerPlugin (adaptive/collapsible/auto-refresh):

```kotlin
val config = BannerPlugin.Config().apply {
    defaultAdUnitId = "ca-app-pub-.../banner"
    defaultBannerType = BannerPlugin.BannerType.Adaptive  // Standard | Adaptive | CollapsibleTop | CollapsibleBottom | LargeBanner
    defaultRefreshRateSec = 30
    loadAdAfterInit = true
}
Admob.getInstance().loadBannerPlugin(activity, bannerContainer, shimmerContainer, config)
```

### 11.2 Interstitial

```kotlin
// Nạp rồi show riêng
Admob.getInstance().loadInterAds(context, "ca-app-pub-.../inter",
    object : AdCallback() {
        override fun onInterstitialLoad(ad: InterstitialAd?) {
            Admob.getInstance().showInterAds(context, ad,
                object : AdCallback() { override fun onNextAction() { goNext() } })
        }
        override fun onInterstitialLoadFaild() { goNext() }
    })

// Nạp-và-hiện một lần (tiện cho chuyển màn)
Admob.getInstance().loadAndShowInter(activity, "ca-app-pub-.../inter",
    /* showLoading */ true,
    object : AdCallback() { override fun onNextAction() { openNext() } })

// Giới hạn tần suất
Admob.getInstance().setIntervalShowInterstitial(15)   // tối thiểu 15s giữa 2 inter
```

Interstitial ở splash: `loadSplashInterAds(context, adUnitId, timeOut, timeDelay, callback)`.

### 11.3 Native

```kotlin
Admob.getInstance().loadNativeAd(context, "ca-app-pub-.../native",
    object : NativeCallback() {
        override fun onNativeAdLoaded(nativeAd: NativeAd) {
            val adView = layoutInflater.inflate(R.layout.your_native_ad, null) as NativeAdView
            Admob.getInstance().pushAdsToViewCustom(nativeAd, adView)
            nativeContainer.removeAllViews(); nativeContainer.addView(adView)
        }
        override fun onAdFailedToLoad() { nativeContainer.visibility = View.GONE }
    })
```

### 11.4 Rewarded

```kotlin
Admob.getInstance().initRewardAds(context, "ca-app-pub-.../reward")
Admob.getInstance().showRewardAds(activity, object : RewardCallback {
    override fun onEarnedReward(item: RewardItem) { grantReward() }
    override fun onAdClosed() {}
    override fun onAdFailedToShow(errorCode: Int) {}
})
// hoặc: Admob.getInstance().loadAndShowReward(activity, adUnitId, /*showLoading*/ true, callback)
```

### 11.5 App-Open / Resume

```kotlin
AppOpenManager.getInstance().init(application)
AppOpenManager.getInstance().setAppResumeAdId("ca-app-pub-.../open_resume")
// Tắt resume ad ở vài màn (splash/camera/ad…)
AppOpenManager.getInstance().disableAppResumeWithActivity(SplashActivity::class.java)
// Tắt hẳn resume ad: AppOpenManager.getInstance().setResumeAdsEnabled(false)
```

### 11.6 Bảng callback

| Callback | Method tiêu biểu |
|---|---|
| `AdCallback` | `onAdLoaded` / `onAdFailedToLoad` / `onInterstitialLoad` / `onNextAction` / `onAdClosed` / `onEarnRevenue` |
| `NativeCallback` | `onNativeAdLoaded` / `onAdFailedToLoad` / `onAdImpression` / `onAdClicked` |
| `BannerCallBack` | `onBannerAdLoaded` / `onBannerAdFailed` / `onAdClicked` |
| `RewardCallback` | `onEarnedReward` / `onAdClosed` / `onAdFailedToShow` |

### 11.7 Ad unit test của Google

| Loại | Test ad unit id |
|---|---|
| App Open | ca-app-pub-3940256099942544/9257395921 |
| Banner | ca-app-pub-3940256099942544/6300978111 |
| Interstitial | ca-app-pub-3940256099942544/1033173712 |
| Rewarded | ca-app-pub-3940256099942544/5224354917 |
| Native | ca-app-pub-3940256099942544/2247696110 |

## 12. Checklist QA trước khi phát hành

- Build release chạy được với `minifyEnabled true` + `shrinkResources true`, không có cảnh báo R8 strip class của AAR.
- Đã khai báo `android:name=".HostApplication"` và đủ 4 quyền `FOREGROUND_SERVICE` + `FOREGROUND_SERVICE_SPECIAL_USE` + `POST_NOTIFICATIONS` + `AD_ID` ở `app/AndroidManifest.xml` (mục 4.2).
- Không có `MAIN`/`LAUNCHER` ở app (AAR cung cấp launcher).
- Màn IAP mở được từ Home và Settings.
- Đổi ngôn ngữ / bật-tắt night mode không khởi động lại app từ màn Splash.
- Đầy đủ `assets/default_ads_config.json` (gồm key `open_all`).
- Test kỹ mọi luồng; bug chức năng phải sửa, bug UI nhỏ có thể tạm bỏ qua.
