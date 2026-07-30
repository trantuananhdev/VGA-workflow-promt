# Kiến trúc app `vga31b-kotlin` (Software Update Checker Pro)

Tài liệu này dành cho người **hoàn toàn mới** với codebase, mục tiêu: đọc xong hiểu được app tổ chức thế nào, để có thể tự dựng một app Kotlin khác theo đúng khuôn mẫu này.

App: **Software Update Checker Pro** — package `com.supportsoftware.checkerpro`. App liệt kê ứng dụng đã cài trên máy, kiểm tra phiên bản mới trên Play Store, quản lý/gỡ app, xem thông tin thiết bị, lịch sử quét. Viết bằng **Kotlin + Jetpack Compose**, dùng **Hilt** để inject dependency, kiến trúc **single-Activity**.

---

## 1. Tổng quan kiến trúc

### 1.1 Các khối chính

| Khối | Công nghệ | Vai trò |
|---|---|---|
| UI | Jetpack Compose | Toàn bộ màn hình là `@Composable`, không dùng XML layout (trừ vài layout Android View được lib quảng cáo/ads dùng lại) |
| Điều hướng | Compose Navigation (`NavHost`) | 1 `NavHost` duy nhất, khai báo route dạng enum |
| DI | Hilt (`@HiltAndroidApp`, `@AndroidEntryPoint`, `@HiltViewModel`) | Cung cấp Room DB, Repository, ViewModel |
| Kiến trúc tầng | MVVM nhẹ | Màn hình (Composable) quan sát `StateFlow` từ `ViewModel`; `ViewModel` gọi `Repository` |
| Dữ liệu | Room (SQLite), SharedPreferences | Room lưu lịch sử quét; SharedPreferences lưu cấu hình app (ngôn ngữ, số lần mở app…) |
| Ads/IAP/Splash/Consent/Notification | thư viện AAR ngoài `base-application` (`com.brian.base_application`) | App **không tự viết** các phần này — chỉ implement điểm tích hợp (xem mục 6) |

### 1.2 Single-Activity là gì và vận hành thế nào

App chỉ có **một `Activity` do app tự khai báo**: `MainActivity` (package `core`). Toàn bộ UI (Intro, Home, danh sách app, Settings...) đều là các **route** bên trong một `NavHost` render trong `MainActivity`, không phải các Activity riêng. Đây là mô hình "single-Activity + nhiều Composable screen" chuẩn của Compose.

Thư viện `base-application` sở hữu và tự quản lý các Activity riêng của nó (Splash, màn chọn ngôn ngữ đầu tiên, IAP/paywall) — các Activity đó **không nằm trong package của app**, app không cần biết code bên trong, chỉ cần biết cách gọi vào (mục 6).

### 1.3 Luồng khởi động — ai gọi ai

```
Hệ điều hành khởi chạy app
        │
        ▼
MyApplication.onCreate()          (com.supportsoftware.checkerpro.MyApplication : BaseApplication)
   1. super.onCreate()             ← lib init Ads/Consent/IAP/Notification, tự fetch Remote Config
   2. FirebaseRemoteConfigUtil.getInstance().setAppDefaultsFromXml(R.xml.config)
                                    ← đăng ký default Remote Config RIÊNG của app (cờ bật/tắt ads, ratio, max/ngày...)
   3. Remote.instance.fetchAndActivate()
                                    ← app tự fetch lại + activate cache
   4. InstallReferrerHelper.resolve(this)
                                    ← xác định sớm app được cài từ nguồn ads hay organic (cache lại,
                                      dùng để quyết định có hiện Intro không)
        │
        ▼
Lib tự mở luồng của nó: Splash → (Interstitial) → (màn chọn ngôn ngữ lần đầu) → (màn IAP nếu cần)
        │  lib gọi getHomeActivity() khi xong luồng trên
        ▼
MainActivity.onCreate()
   1. Áp lại ngôn ngữ đã lưu (AppStorage.language)
   2. Đăng ký shortcut "Uninstall" trên launcher
   3. resolveStartRoute() → tính route bắt đầu (Screen.Intro hay Screen.Home)
   4. setContent { AppTheme { AppNavHost(startRoute) ; NativeInterHost() } }
        │
        ▼
AppNavHost render toàn bộ cây điều hướng của APP (Intro/Home/... — xem mục 3)
```

Điểm quan trọng: **MainActivity không khai báo `MAIN`/`LAUNCHER`** trong `AndroidManifest.xml` — Activity khởi chạy đầu tiên là `SplashActivity` của thư viện. Thư viện mở `MainActivity` thông qua `MyApplication.getHomeActivity()`.

---

## 2. Cấu trúc thư mục/package

Toàn bộ code nằm dưới `app/src/main/java/com/supportsoftware/checkerpro/`:

| Package | Nhiệm vụ chính |
|---|---|
| *(root)* | `MyApplication.kt` — điểm tích hợp thư viện `base-application` |
| `core/` | Hạ tầng: Activity chính, storage cấu hình, locale, shortcut, install-referrer, mở IAP |
| `di/` | Module Hilt cung cấp Room DB |
| `data/db/` | Room: Entity + DAO cho lịch sử quét |
| `data/model/` | Data class (model) dùng chung toàn app |
| `data/repo/` | Repository — nơi thực sự gọi Android API (PackageManager, UsageStatsManager…) và mạng (jsoup) |
| `firebase/` | Facade Remote Config của app |
| `platform/` | Cầu nối gọi API cấp thấp của thư viện AAR (mở màn IAP) |
| `advertisement/` | Toàn bộ logic hiển thị quảng cáo (native ad, interstitial, native-interstitial) |
| `ui/theme/` | Màu sắc, `MaterialTheme` |
| `ui/components/` | Composable dùng lại nhiều nơi (Card, Header, SearchBar, AppIcon…) |
| `ui/nav/` | Khai báo route (`Screen`) và `NavHost` |
| `ui/screen/<feature>/` | Mỗi feature 1 package con: `onboarding/`, `home/`, `apps/`, `scan/`, `history/`, `device/`, `settings/`, `uninstall/`, `testads/` |

### 2.1 `core/` — chi tiết từng file

| File | Trách nhiệm |
|---|---|
| `MainActivity.kt` | Activity duy nhất của app. `onCreate()` áp locale, đăng ký shortcut, tính route bắt đầu (`resolveStartRoute()`), gọi `setContent`. Logic `resolveStartRoute()` quyết định hiện màn Intro hay vào thẳng Home, dựa trên số lần mở app (`AppStorage.goToHomeNumber`) và nguồn cài (`InstallReferrerHelper.isAdsCampaign`) đối chiếu với 2 tham số Remote Config `count_app_open` và `organic_number_not_guide`. |
| `AppStorage.kt` | Wrapper `SharedPreferences` tên `"AppStorage"`. Lưu: `first_open`, `onboarding_done`, `agree_permission`, `language`, `go_to_home_number` (đếm số lần mở app), `is_ads_campaign` (+ cờ đã resolve). Đây là "nguồn sự thật" cho toàn bộ trạng thái first-open/onboarding. |
| `InstallReferrerHelper.kt` | Dùng Google Play `InstallReferrerClient` để hỏi 1 lần duy nhất (mỗi lần cài) xem app được cài từ chiến dịch quảng cáo (`gclid`, `utm_medium`) hay cài tự nhiên (organic). Kết quả cache in-memory + `AppStorage`, mọi nhánh lỗi mặc định coi là "ads". |
| `LocaleHelper.kt` | Áp locale theo-app (per-app locale): API 33+ dùng `LocaleManager`, thấp hơn dùng `AppCompatDelegate.setApplicationLocales`. |
| `ShortcutHelper.kt` | Tạo dynamic shortcut "Uninstall" trên launcher bằng `ShortcutManagerCompat`; đọc lại `shortcutId` từ Intent khi app mở qua shortcut để điều hướng thẳng tới màn tương ứng. |
| `IapOpener.kt` | Hàm tiện ích mở màn IAP/paywall của thư viện + hàm `gate()` để chặn 1 tính năng cho tới khi user mua premium. |

### 2.2 `data/` — chi tiết

| File | Trách nhiệm |
|---|---|
| `data/db/AppDatabase.kt` | `RoomDatabase` khai báo entity `ScanHistory`, version 1. |
| `data/db/ScanHistory.kt` | Entity: 1 lần quét gồm `date`, `installedCount`, `updateCount`. |
| `data/db/ScanHistoryDao.kt` | `insert`, `observeAll()` (trả `Flow`), `page()`, `deleteAll()`. |
| `data/model/AppModels.kt` | `AppInfo` (thông tin 1 app cài), `UsageInfo` (thống kê dùng), `AppPermissions` (quyền cấp/từ chối), `VersionCheckResult` (kết quả so sánh version). |
| `data/repo/AppInventoryRepository.kt` | Bọc toàn bộ `PackageManager`/`UsageStatsManager`/`AppOpsManager` của Android: liệt kê app cài (user/system), lấy icon lazy, quyền app, thống kê thời gian sử dụng (thuật toán ghép cặp event RESUMED/PAUSED), kiểm tra/ mở Settings xin quyền Usage Access, build `Intent` gỡ app. |
| `data/repo/VersionCheckRepository.kt` | Dùng `jsoup` để crawl trang Play Store của 1 package, tìm version bằng vài `Regex` fallback (HTML Play Store hay đổi cấu trúc nên có nhiều pattern), so sánh với version đang cài. |
| `data/repo/ScanResultStore.kt` | Singleton giữ kết quả quét gần nhất trong RAM để màn `UpdateAvailable` đọc lại sau khi màn `ScanNow` quét xong (tránh phải truyền list qua nav argument). |

### 2.3 `di/AppModule.kt`

Module Hilt duy nhất — chỉ cần cung cấp Room (`@Provides @Singleton provideDatabase`, `provideScanHistoryDao`) vì các Repository khác đã dùng `@Inject constructor` trực tiếp (Hilt tự biết cách tạo).

### 2.4 `firebase/Remote.kt`

Facade cho Remote Config, xem chi tiết ở mục 6.

### 2.5 `platform/IapLauncher.kt`

Hàm `open(context)` tìm `Activity` từ `Context` rồi gọi API tĩnh của thư viện để mở màn IAP.

---

## 3. Điều hướng & màn hình

### 3.1 Khai báo route — `ui/nav/Screen.kt`

Route được khai báo bằng `enum class Screen(val route: String)`, ví dụ:

```kotlin
enum class Screen(val route: String) {
    Intro("intro"), Home("home"),
    UserApp("user_app"), DetailUserApp("detail_user_app"), // arg: packageName
    SystemApp("system_app"), ManagerApp("manager_app"), DetailManagerApp("detail_manager_app"),
    ScanNow("scan_now"), UpdateAvailable("update_available"),
    RemoveApp("remove_app"), Uninstall("uninstall"), InfoDevice("info_device"), History("history"),
    Setting("setting"), LanguageSetting("language_setting"), TestAds("test_ads");

    companion object {
        const val ARG_PACKAGE = "packageName"
        fun detailUserApp(pkg: String) = "${DetailUserApp.route}/$pkg"
    }
}
```

Route có tham số (ví dụ package name) được nối trực tiếp vào path (`"detail_user_app/$pkg"`), không dùng query string.

### 3.2 `NavHost` — `ui/nav/AppNavHost.kt`

Một `@Composable fun AppNavHost(startRoute: String, navController = rememberNavController())` khai báo toàn bộ cây `composable(...)`. Mỗi route map tới 1 hàm `@Composable` của feature tương ứng, ví dụ:

```kotlin
composable(Screen.Home.route) {
    HomeScreen(
        onNavigate = { route -> navController.navigate(route) },
        onOpenSettings = { navController.navigate(Screen.Setting.route) },
    )
}
composable(
    route = "${Screen.DetailUserApp.route}/{${Screen.ARG_PACKAGE}}",
    arguments = listOf(navArgument(Screen.ARG_PACKAGE) { type = NavType.StringType }),
) { DetailUserAppScreen(onBack = ::back) }
```

`AppNavHost` được đặt bên trong `AppTheme { }` ở `MainActivity.setContent`, cùng với `NativeInterHost()` (overlay quảng cáo toàn màn, xem mục 5).

### 3.3 Luồng chuyển màn (Intro → Home → các màn con)

- **Intro** (`Screen.Intro`): pager 4 slide giới thiệu app (dùng `HorizontalPager`), có thể kèm quảng cáo native theo A/B test (`AdPositions`). Bấm "Start" ở slide cuối → `toHome()`: đánh dấu `AppStorage.setOnboardingDone()` rồi `navController.navigate(Screen.Home.route) { popUpTo(0) { inclusive = true } }` — xoá sạch back-stack Intro, không cho back về lại Intro.
- **Home** (`Screen.Home`): màn hub — lưới ô (`LazyVerticalGrid`) dẫn tới các tính năng: Quản lý app theo user/system/manager, Quét cập nhật, Gỡ app, Thông tin thiết bị, Lịch sử.
- Từ Home, mỗi tile gọi `go(route)` — hàm này hiện interstitial (`AdManager.showInter(activity, "inter_home")`) rồi mới điều hướng, xem mục 5.
- **Scan → UpdateAvailable**: `ScanNowScreen` chạy quét, khi xong bấm "Xem cập nhật" → `navigate(Screen.UpdateAvailable.route) { popUpTo(Screen.ScanNow.route) { inclusive = true } }` (xoá luôn màn Scan khỏi back-stack).
- **Setting**: từ Home (icon bánh răng) → `SettingScreen`, trong đó có mục đổi ngôn ngữ (mở màn Language của thư viện AAR, không phải màn tự viết) và mục Premium (mở màn IAP của thư viện).
- **Deep-link shortcut**: khi user long-press icon app trên launcher chọn shortcut "Uninstall", `MainActivity.resolveStartRoute()` phát hiện qua `ShortcutHelper.consumeShortcutId(intent)` và trả về `Screen.Uninstall.route` ngay — bỏ qua toàn bộ logic đếm mở app/Intro.

---

## 4. Tầng dữ liệu/logic

### 4.1 Room

Chỉ dùng cho 1 bảng: `scan_history` (lịch sử các lần quét). Truy cập qua `ScanHistoryDao`, cung cấp qua Hilt (`di/AppModule.kt`).

### 4.2 SharedPreferences

Dùng trực tiếp (không qua DataStore) cho 2 mục đích:
- `AppStorage` ("AppStorage" prefs) — cấu hình/trạng thái app (ngôn ngữ, first-open, đếm mở app, nguồn cài).
- `AdScenario` ("ad_scenario" prefs, trong package `advertisement/`) — đếm số lần "cơ hội hiện ads" theo ngày cho từng loại quảng cáo, dùng để tính tỉ lệ/giới hạn hiển thị (mục 5).

### 4.3 Repository pattern

App theo pattern Repository rõ ràng: **Composable/ViewModel không bao giờ gọi trực tiếp Android SDK (PackageManager, UsageStatsManager...) hay mạng** — luôn đi qua `AppInventoryRepository` / `VersionCheckRepository` / `ScanHistoryDao`. Repository:
- `@Singleton` + `@Inject constructor`, Hilt tự cấp instance.
- Luôn chạy tác vụ nặng trên `Dispatchers.IO` qua `withContext`.
- Trả model đơn giản (`AppInfo`, `UsageInfo`...), không leak kiểu Android (trừ `Intent` khi tác vụ *cần* Activity thực hiện, ví dụ mở màn gỡ app — Repository trả `Intent`, màn hình tự `launch` qua `ActivityResultLauncher`).

### 4.4 ViewModel liên kết UI thế nào

Mỗi feature có 1 (hoặc vài) `@HiltViewModel`, theo khuôn:

```kotlin
@HiltViewModel
class XxxViewModel @Inject constructor(
    private val repo: SomeRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(XxxState())
    val state: StateFlow<XxxState> = _state.asStateFlow()

    fun doSomething() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true)
            val result = repo.fetch()
            _state.value = _state.value.copy(loading = false, data = result)
        }
    }
}
```

Composable lấy ViewModel bằng `hiltViewModel()` (thư viện `androidx.hilt.navigation.compose`), quan sát state bằng `collectAsState()`:

```kotlin
@Composable
fun XxxScreen(vm: XxxViewModel = hiltViewModel()) {
    val state by vm.state.collectAsState()
    ...
}
```

Không dùng `LiveData` trong tầng ViewModel của app (dù thư viện `androidx.lifecycle.livedata` có khai trong Gradle cho tương thích với thư viện AAR) — toàn bộ state app tự viết dùng `StateFlow`.

---

## 5. Tầng quảng cáo (`advertisement/`)

Đây là tầng phức tạp nhất về logic (không phải về UI). Toàn bộ được viết thủ công trên nền SDK quảng cáo `com.nlbn.ads` (đi kèm thư viện `base-application`) + Google Mobile Ads SDK.

| File | Vai trò |
|---|---|
| `AdScenario.kt` | Thuật toán quyết định "có nên hiện ad không" cho **1 loại placement**, đếm theo **ngày**: `showCount % ratio == 0` (tỉ lệ xuất hiện) **và** `showCountAd < maxPerDay` (giới hạn số lần/ngày). Đếm lưu trong `SharedPreferences("ad_scenario")`, tự dọn key cũ >7 ngày. |
| `AdPositions.kt` | Chọn ngẫu nhiên 1 biến thể A/B cho vị trí quảng cáo trong màn Intro (đọc Remote Config key `positionIntrol`, dạng JSON mảng-các-mảng số). |
| `AdManager.kt` | Điều phối **Interstitial**: gọi `Admob.getInstance().loadAndShowInter(...)`; nếu interstitial không hiện (tắt/hết ratio) → fallback sang "native-interstitial" (native ad hiển thị full-screen giả làm interstitial). Có preload native-interstitial song song lúc interstitial đang hiện để chuyển tiếp mượt. |
| `AdsViewModel.kt` | `ViewModel` cache native ad **theo Activity** (không theo từng Composable) — mỗi `Slot` giữ trạng thái loading/loaded + đối tượng `NativeAd`, để khi user điều hướng qua-lại hoặc list bị recycle thì ad không load lại liên tục. |
| `NativeAdSlot.kt` | `@Composable` chính để nhúng 1 ô native-ad vào bất kỳ màn hình nào. Tự quản lý load/cache qua `AdsViewModel`, tự ẩn khi: user đã mua premium, placement bị tắt trên Remote Config, hoặc load lỗi (không retry). |
| `NativeAdsFull.kt` | Native ad full-screen dùng cho modal trong Intro (đóng được sau X giây đếm ngược). |
| `NativeInter.kt` | `NativeInterController` (object giữ request hiện tại) + `NativeInterHost()` (Composable đặt ở root `MainActivity`, lắng nghe request và hiện `Dialog` full-screen). Đây là cơ chế native-interstitial dùng chung, được `AdManager` gọi vào. |

### 5.1 Một màn hình gọi vào tầng ads như thế nào

**Native ad tĩnh trong màn hình** — chỉ cần gọi Composable, không cần biết logic bên trong:

```kotlin
NativeAdSlot("native_home")                       // full, có media
NativeAdSlot("native_history", isSmall = true)     // gọn, không media — dùng trong list
```

**Interstitial trước khi điều hướng** (ví dụ `HomeScreen.go()`):

```kotlin
fun go(route: String) {
    if (activity != null) AdManager.showInter(activity, "inter_home") { onNavigate(route) }
    else onNavigate(route)
}
```

`onNext` callback (ở đây `{ onNavigate(route) }`) luôn được gọi đúng 1 lần, dù ad có hiện hay không — nhờ vậy code gọi ads không cần biết ad có thật sự hiện hay không, chỉ cần biết "sau cùng sẽ đi tiếp".

Placement (`"native_home"`, `"inter_home"`...) là 1 chuỗi khoá, tra ra ad-unit-id + trạng thái bật/tắt qua `Remote` (mục 6). Muốn thêm 1 vị trí quảng cáo mới, chỉ cần: đặt tên placement mới, khai trong `res/xml/config.xml` cờ `<placement>_enable` (+ `_ratio`/`_max` nếu là inter), rồi gọi `NativeAdSlot("<placement>")` hoặc `AdManager.showInter(activity, "<placement>") {...}` ở màn cần.

---

## 6. Điểm tích hợp thư viện `base-application`

App không tự viết splash/ads-init/consent/IAP/notification — toàn bộ nằm trong AAR `com.brian.base_application`. App chỉ cần implement điểm nối:

### 6.1 `MyApplication : BaseApplication()`

```kotlin
@HiltAndroidApp
class MyApplication : BaseApplication() {
    override fun onCreate() {
        super.onCreate()   // BẮT BUỘC — lib init ads/consent/IAP/notification trong này
        FirebaseRemoteConfigUtil.getInstance().setAppDefaultsFromXml(R.xml.config)
        Remote.instance.fetchAndActivate()
        InstallReferrerHelper.resolve(this)
    }

    override fun getAppNameRes(): Int = R.string.app_name
    override fun getHomeActivity(): Class<out Activity> = MainActivity::class.java
    override fun iapPremiumKey(): String = "release_premium_access"
    override fun isPurchased(): Boolean = IAPUtils.isPremium()
    override fun enableAdsResume(): Boolean = !IAPUtils.isPremium()
    // ... nhiều override khác: icon splash, bộ ảnh/tiêu đề notification, icon feature màn IAP, v.v.
}
```

Các nhóm hàm override chính:
- **Thương hiệu/Splash**: `getAppNameRes`, `getIconSplashRes`, `getSplashLoadingRes`.
- **Định tuyến**: `getHomeActivity()` — lib gọi hàm này để biết mở Activity nào sau khi xong luồng splash/ads/IAP.
- **IAP**: `iapPremiumKey()`, `iapPremiumWeeklyKey/MonthlyKey/YearlyKey()`, `iapPublicKey()`, `isPurchased()` — khai product-id trên Play Console + trạng thái đã mua hay chưa (đọc qua `IAPUtils.isPremium()` của lib).
- **Ngôn ngữ**: `notifyLanguageSaved(languageCode)` — lib gọi hàm này mỗi khi user chọn xong ngôn ngữ (cả lần đầu và từ Settings); app phải tự lưu vào `AppStorage` **và** gọi `LocaleHelper.updateLocale()` để `MainActivity` (AppCompat/Compose, không tự nghe locale của lib) đổi theo.
- **Notification/quảng cáo cục bộ khác**: một loạt `getNotification...Res()` cung cấp resource ảnh/chuỗi cho thông báo tự động của lib (nhắc mở app, phát hiện file mới...).
- **Cấu hình quảng cáo tổng**: `buildDebug()`, `getListTestDeviceId()`.

### 6.2 Remote Config facade — `firebase/Remote.kt`

App **không** subclass `FirebaseRemoteConfigUtil` của lib (sẽ tạo ra 1 singleton song song, mất hết default `ads_config` của lib) và **không** gọi `FirebaseRemoteConfig.setDefaultsAsync` trực tiếp. Thay vào đó `Remote` là 1 class riêng, **ủy quyền (delegate)** mọi lệnh đọc sang `FirebaseRemoteConfigUtil.getInstance()`:

```kotlin
class Remote private constructor() {
    private val frc get() = FirebaseRemoteConfigUtil.getInstance()

    fun adUnit(placement: String): String =
        if (BuildConfig.DEBUG) debugTestUnit(placement) else frc.getAdsConfigValue(placement)

    fun getBoolean(key: String): Boolean {
        if (IAPUtils.isPremium() && key.endsWith("_enable")) return false   // ẩn ad cho user premium
        return frc.getBoolean(key)
    }

    fun isAdEnabled(placement: String): Boolean = getBoolean("${placement}_enable")

    companion object { val instance: Remote by lazy { Remote() } }
}
```

Ở chế độ Debug, `adUnit()` trả về ad-unit-id **test** của Google (interstitial/app-open/native test id cố định) để luôn có ad hiển thị khi kiểm thử UI, tránh tình trạng ad-unit thật của app chưa publish bị "no-fill".

### 6.3 Mở màn IAP của lib — `platform/IapLauncher.kt`

```kotlin
object IapLauncher {
    fun open(context: Context) {
        val activity = context.findActivity() ?: return
        NativeCodecSnowFlakeCortexAI.nativeAiStartIapActivity(activity)
    }
}
```
Gọi trực tiếp API tĩnh của lib để mở `IapActivity` (Activity riêng của lib, tự đóng sau khi mua/hủy).

### 6.4 Mở màn đổi ngôn ngữ của lib

`SettingScreen` không tự vẽ màn chọn ngôn ngữ đầy đủ — gọi thẳng `LanguageActivity.start(activity, MainActivity::class.java)` của lib. Khi cần đổi ngôn ngữ mà **không** để lib tự điều hướng (ví dụ màn `LanguageSettingScreen` tự vẽ list ngôn ngữ riêng), app gọi `LanguageRouter.confirmLanguageSelection(activity, code, navigate = false)` rồi tự `activity.recreate()`.

---

## 7. Theme/UI system — `ui/theme/Theme.kt`

```kotlin
val Primary = Color(0xFF007BFF)
val Secondary = Color(0xFF00C9FF)
val BgLight = Color(0xFFF4F6F8)

@Composable
fun AppTheme(
    darkTheme: Boolean = false,   // luôn sáng — xem giải thích dưới
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = Typography(),
        content = content,
    )
}
```

Điểm cần chú ý — **`darkTheme` bị khoá cứng `false`, không đọc theo `isSystemInDarkTheme()`**. Đây là quyết định thiết kế có chủ đích, không phải thiếu sót: nền của toàn app (`windowBackground` trong theme XML gốc, các Card, header...) được thiết kế cố định là **nền sáng** và không có biến thể tối tương ứng. Nếu để `MaterialTheme` tự đổi `colorScheme` theo hệ thống trong khi nền vật lý vẫn trắng, chữ/icon (vốn được set màu cho nền sáng) sẽ đổi sang tông sáng hơn để "hợp" dark mode → xám trên trắng, gần như không đọc được. Vì vậy `AppTheme` cố định `LightColors` làm mặc định; muốn hỗ trợ dark mode thật thì phải thiết kế lại đồng bộ cả `DarkColors` **và** toàn bộ màu cứng (hardcode `Color.White`, `Color.Black`...) đang nằm rải rác trong các Composable (`AppCard`, `AppHeader`...).

`AppCard` (trong `ui/components/AppCard.kt`) là ví dụ: nó override `containerColor = Color.White` cứng vì Material3 `Card` mặc định dùng `surfaceVariant` (xám) — muốn đổi theme cho đúng phải sửa cả những chỗ hardcode này, không chỉ đổi `colorScheme`.

---

## 8. i18n/đa ngôn ngữ

### 8.1 Cấu trúc file string

Mỗi ngôn ngữ có 1 folder `res/values-<mã>/` (vd `values-vi`, `values-fr`, `values-ja`...). Tách 2 file:

| File | Nội dung | Có dịch không |
|---|---|---|
| `values/strings.xml` | Khoá cấu hình SDK/bí mật cấu hình app (admob app id, app-flyer id, facebook id, public license key, nội dung notification của lib...) | **Không** — chỉ có ở `values/` mặc định, không lặp lại ở `values-xx/` |
| `values*/strings_i18n.xml` | Toàn bộ chuỗi hiển thị UI của app (`userApp`, `intro1`, `scanForUpdate`, `update`, thông báo lỗi...) | **Có** — mỗi ngôn ngữ có bản dịch riêng trong `values-<mã>/strings_i18n.xml` |

Tách riêng để rõ ràng: chuỗi nào cần dịch (nội dung UI) vs chuỗi nào là cấu hình kỹ thuật cố định (không bao giờ dịch).

### 8.2 Cách đổi ngôn ngữ hoạt động trong code

1. Danh sách ngôn ngữ hỗ trợ khai tay trong `SettingScreens.kt` (`private val languages = listOf(Lang("en-US","English"), Lang("vi-VN","Tiếng Việt"), ...)`), mỗi item là mã locale kiểu `ll-CC`.
2. Có 2 đường để đổi ngôn ngữ:
   - Qua màn Language **của lib** (`LanguageActivity.start(...)`) — dùng khi vào từ Settings và muốn để lib tự vẽ UI + tự điều hướng.
   - Qua màn `LanguageSettingScreen` **tự vẽ** trong app — khi chọn 1 dòng, gọi `LanguageRouter.confirmLanguageSelection(activity, code, navigate = false)` (báo cho lib biết + không tự chuyển màn) rồi `activity.recreate()` để áp lại ngay.
3. Bất kể đường nào, cuối cùng lib đều gọi `MyApplication.notifyLanguageSaved(languageCode)` → app lưu `languageCode` vào `AppStorage` (`SharedPreferences`) và gọi `LocaleHelper.updateLocale(context, languageCode)` để set **per-app locale** (AndroidX `LocaleManager`/`AppCompatDelegate`).
4. Mỗi lần `MainActivity.onCreate()` chạy (kể cả sau `recreate()`), nó đọc lại `AppStorage.language(this)` và gọi `LocaleHelper.updateLocale()` lại — đảm bảo toàn bộ chuỗi trong `AppNavHost` hiển thị đúng ngôn ngữ đã chọn, không phụ thuộc ngôn ngữ hệ thống.

---

## 9. Ví dụ minh hoạ: xây dựng chức năng "Quét & kiểm tra cập nhật" (Scan)

Đây là feature điển hình để thấy pattern lặp lại **data → logic → UI** khi tự làm 1 màn mới.

### Bước 1 — Model (data/model)

`data/model/AppModels.kt` định nghĩa hình dạng kết quả:

```kotlin
data class VersionCheckResult(
    val packageName: String,
    val currentVersion: String?,
    val storeVersion: String?,
    val needsUpdate: Boolean,
    val storeUrl: String,
)
```

### Bước 2 — Repository (data/repo)

Hai repository cộng tác:
- `AppInventoryRepository.getInstalledApps(systemApps = false)` — lấy toàn bộ app user đã cài (`PackageManager`).
- `VersionCheckRepository.check(packageName, currentVersion)` — crawl trang Play Store bằng `jsoup`, parse version, so sánh, trả `VersionCheckResult`.

Cả 2 đều `@Singleton @Inject constructor`, chạy trên `Dispatchers.IO`.

Kết quả quét được lưu tạm ở `ScanResultStore` (singleton RAM) để màn kế tiếp đọc lại — tránh phải nhồi cả list vào nav argument (nav argument chỉ nên chứa dữ liệu nhỏ như 1 packageName).

### Bước 3 — Room (data/db) — lưu lịch sử

`ScanHistoryDao.insert(ScanHistory(date, installedCount, updateCount))` — mỗi lần quét xong ghi 1 dòng, để màn History sau này hiển thị lại (`observeAll()` trả `Flow`).

### Bước 4 — ViewModel (ui/screen/scan/ScanViewModel.kt)

```kotlin
@HiltViewModel
class ScanViewModel @Inject constructor(
    private val inventory: AppInventoryRepository,
    private val versionCheck: VersionCheckRepository,
    private val historyDao: ScanHistoryDao,
    private val store: ScanResultStore,
) : ViewModel() {
    private val _state = MutableStateFlow(ScanState())
    val state: StateFlow<ScanState> = _state.asStateFlow()

    fun startScan() {
        viewModelScope.launch {
            val apps = inventory.getInstalledApps(systemApps = false)
            _state.value = ScanState(scanning = true, total = apps.size)
            val updates = ArrayList<VersionCheckResult>()
            apps.forEachIndexed { index, app ->
                val result = versionCheck.check(app.packageName, app.versionName)
                if (result.needsUpdate) updates.add(result)
                _state.value = _state.value.copy(scanned = index + 1, updates = updates.toList())
            }
            historyDao.insert(ScanHistory(System.currentTimeMillis(), apps.size, updates.size))
            store.lastUpdates = updates.toList()
            _state.value = _state.value.copy(scanning = false, done = true)
        }
    }
}
```

ViewModel là nơi **duy nhất** biết thứ tự gọi Repository + cách tổng hợp state tiến trình (`scanned`/`total` để vẽ progress bar) — UI không biết gì về `jsoup` hay `PackageManager`.

### Bước 5 — UI (ui/screen/scan/ScanScreens.kt)

```kotlin
@Composable
fun ScanNowScreen(onBack: () -> Unit, onFinished: () -> Unit, vm: ScanViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) { vm.startScan() }       // bắt đầu quét ngay khi vào màn
    val state by vm.state.collectAsState()

    AppScreen(title = stringResource(R.string.scanForUpdate), onBack = onBack) { m ->
        // vòng tròn CircularProgressIndicator(progress = state.progress) ...
        // 3 dòng trạng thái (đang quét/đã quét, tổng app, số bản cập nhật)
        Button(onClick = { if (state.updates.isNotEmpty()) onFinished() },
               enabled = state.done && state.updates.isNotEmpty()) { Text(stringResource(R.string.seeUpdate)) }
        NativeAdSlot("native_scan_update", Modifier.padding(top = 16.dp))   // ads chỉ 1 dòng gọi
    }
}
```

Màn `UpdateAvailableScreen` kế tiếp có `ViewModel` riêng (`UpdateAvailableViewModel`) chỉ đọc `ScanResultStore.lastUpdates` — không gọi lại Repository, không quét lại.

### Bước 6 — Nối route (ui/nav)

Thêm route vào `Screen` enum, thêm `composable(...)` trong `AppNavHost`, gọi điều hướng từ Home:

```kotlin
// Screen.kt
ScanNow("scan_now"), UpdateAvailable("update_available"),

// AppNavHost.kt
composable(Screen.ScanNow.route) {
    ScanNowScreen(onBack = ::back, onFinished = {
        navController.navigate(Screen.UpdateAvailable.route) {
            popUpTo(Screen.ScanNow.route) { inclusive = true }
        }
    })
}
```

### Tóm tắt pattern lặp lại cho 1 feature mới

1. **Model** — data class mô tả dữ liệu (nếu feature cần dạng dữ liệu mới).
2. **Repository** — hàm `suspend` gọi Android API/network, chạy `Dispatchers.IO`, trả model ở bước 1. Singleton, `@Inject constructor`.
3. **(Tuỳ chọn) Room/Store** — nếu cần lưu lâu dài (Room) hoặc chuyển tạm giữa 2 màn (Store singleton RAM).
4. **ViewModel** — `@HiltViewModel`, giữ `MutableStateFlow<XxxState>`, gọi Repository trong `viewModelScope.launch`.
5. **UI Composable** — nhận `vm = hiltViewModel()`, `collectAsState()`, vẽ theo state; chèn `NativeAdSlot`/`AdManager.showInter` nếu màn cần quảng cáo.
6. **Route** — thêm entry vào `Screen`, thêm `composable(...)` trong `AppNavHost`, nối `onClick`/`onNavigate` từ màn gọi tới.
