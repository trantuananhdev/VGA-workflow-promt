# Hướng dẫn chuyển Ads: bản GỐC (Google GMA SDK) → bản LIB (`com.nlbn.ads`)

> **Dành cho AI**: Đây là hướng dẫn cơ học để convert một project Android (Kotlin + Jetpack
> Compose) đang **tự gọi Google Mobile Ads SDK** (AdLoader / NativeAdView dựng tay /
> InterstitialAd.load / AppOpenAd…) sang **dùng thư viện `com.nlbn.ads`** (qua AAR
> `base-application`) — thư viện đã hỗ trợ **load + show** ads.
>
> Nguyên tắc vàng: **không gọi GMA SDK trực tiếp nữa**. Mọi load/show đi qua
> `Admob.getInstance()` của lib; consent/open/resume/khởi tạo SDK do lib tự lo.

---

## 0. Phân biệt 2 bản

| | Bản GỐC (GMA SDK trực tiếp) | Bản LIB (`com.nlbn.ads`) |
|---|---|---|
| Load native | `AdLoader.Builder(ctx,id).forNativeAd{}.withAdListener{}.build().loadAd(AdRequest())` | `Admob.getInstance().loadNativeAd(ctx, id, NativeCallback())` |
| Show native | Dựng `NativeAdView` + `ConstraintLayout/MediaView/...` bằng code, rồi `view.setNativeAd(ad)` | Inflate **layout của lib** thành `NativeAdView` rồi `Admob.getInstance().pushAdsToViewCustom(ad, view)` |
| Interstitial | `InterstitialAd.load(...).show()` | `Admob.getInstance().loadAndShowInter(activity, id, true, AdCallback())` |
| Banner | `AdView` + `adView.loadAd(...)` | `Admob.getInstance().loadBanner(activity, id, container, BannerCallBack())` |
| App Open / Resume | `AppOpenAd.load(...).show()` tự quản | **Lib tự lo** (qua splash + `enableAdsResume()`); app KHÔNG viết |
| Consent (UMP) | `GoogleMobileAdsConsentManager` tự viết | **Lib tự lo** ở splash; app KHÔNG viết |
| Khởi tạo SDK | `MobileAds.initialize(...)` | **Lib tự lo** trong `BaseApplication`; app KHÔNG gọi |
| Unit id | `AdConfig` / RemoteConfig tự đọc | `FirebaseRemoteConfigUtil.getInstance().getAdsConfigValue(key)` (remote key `ads_config` → fallback `assets/default_ads_config.json`) |

---

## 1. Quy tắc chuyển đổi (AI làm theo)

1. **XÓA** mọi khởi tạo & manager tự viết cho thứ lib đã lo:
   - `MobileAds.initialize(...)`, `GoogleMobileAdsConsentManager`, `AppOpenManager`/AppOpen tự viết,
     `InterstitialAdManager`/`RewardedInterstitialAdManager` tự viết (nếu chỉ load-and-show).
2. **THAY** load/show GMA bằng API `Admob.getInstance()` (xem §3–§5).
3. **THAY** các `NativeAdViewWrapper/Small/Mini/Full` (dựng view tay) bằng **inflate layout lib** +
   `pushAdsToViewCustom`.
4. **GIỮ NGUYÊN toàn bộ kịch bản/logic điều phối ads** của bản gốc — chỉ thay **primitive
   load/show của GMA** bằng lib. Bao gồm: cache `AdsViewModel`, state machine `NativeAdSlot`
   (suppress-error → skeleton → cache → load), skeleton shimmer, **và cả logic inter**:
   tần suất (`AdFrequencyManager`), fallback inter→native (`AdHelper.showInterWithNativeFallback`),
   các cấu hình (`AdConfig.INTER_SETTING/NATIVE_INTER_SETTING`)… **Đừng viết lại những thứ này** —
   chỉ đổi lời gọi SDK bên trong (xem §4, §3).
   - ⚠️ **Ngoại lệ: BỎ loading dialog khi gọi inter** — `Admob.getInstance().loadAndShowInter(...)`
     **tự hiện loading** trong lúc nạp ad. Đừng giữ loading dialog / `loadingViewModel` tự viết
     cho inter (sẽ chồng 2 loading).
5. **Unit id**: thay nguồn đọc id bằng `getAdsConfigValue(key)`; có fallback `default_ads_config.json`.
6. **Không** đổi `applicationId`; giữ `google-services.json` khớp.
7. **Premium**: thay cờ tự chế `Global.isPremiumUser` → `IAPUtils.isPremium()` của lib; **đã trả phí
   → ẩn TẤT CẢ ads** (xem §6.1).

---

## 2. Setup project (1 lần)

`app/build.gradle`:
```gradle
dependencies {
    api project(':base-application')   // chứa com.nlbn.ads + layout ads_native_bot_*
    implementation 'androidx.lifecycle:lifecycle-viewmodel-compose:<ver>'
    implementation 'androidx.activity:activity-compose:<ver>'
}
```
- Host **Activity là `ComponentActivity`**.
- `assets/default_ads_config.json`: `{ "<placement>": "<ad-unit-id>", ... }` làm fallback local.
- `HostApplication extends BaseApplication` (lib lo init/consent/open/resume — xem doc tích hợp AAR).

---

## 3. NATIVE AD — phần chính

### 3.1 LOAD: trước → sau

**TRƯỚC (GMA SDK):**
```kotlin
val adLoader = AdLoader.Builder(context, unitId)
    .withNativeAdOptions(NativeAdOptions.Builder()...build())
    .forNativeAd { ad -> nativeAd = ad /* ... */ }
    .withAdListener(object : AdListener() {
        override fun onAdFailedToLoad(e: LoadAdError) { ... }
        override fun onAdImpression() { ... }
    })
    .build()
adLoader.loadAd(AdRequest.Builder().build())
```

**SAU (lib nlbn):**
```kotlin
import com.nlbn.ads.callback.NativeCallback
import com.nlbn.ads.util.Admob
import com.google.android.gms.ads.nativead.NativeAd

Admob.getInstance().loadNativeAd(context, unitId, object : NativeCallback() {
    override fun onNativeAdLoaded(ad: NativeAd) { /* cache ad, set loaded */ }
    override fun onAdFailedToLoad() { /* set error */ }
    override fun onAdImpression() { /* optional */ }
})
```
> Bỏ `NativeAdOptions/VideoOptions/AdRequest/AdLoader/AdListener`. `NativeCallback` chỉ có
> `onNativeAdLoaded(ad) / onAdFailedToLoad() / onAdImpression() / onAdClicked()`.

### 3.2 SHOW: trước → sau

**TRƯỚC (dựng view tay):**
```kotlin
val nativeAdView = NativeAdView(context)
// ... tạo ConstraintLayout, MediaView, headline, body, CTA bằng code ...
nativeAdView.mediaView = mediaView
nativeAdView.headlineView = headline
// ...
nativeAdView.setNativeAd(ad)
```

**SAU (inflate layout lib + pushAdsToViewCustom):**
```kotlin
import com.google.android.gms.ads.nativead.NativeAdView

val layoutRes = if (isMini || isSmall)
    com.brian.base_application.R.layout.ads_native_bot_no_media_short
else
    com.brian.base_application.R.layout.ads_native_bot_2

val view = LayoutInflater.from(ctx).inflate(layoutRes, null) as NativeAdView
Admob.getInstance().pushAdsToViewCustom(ad, view)   // lib tự map + bind
```
> **Xóa** toàn bộ `NativeAdViewWrapper/Small/Mini/Full` dựng view tay. `isSmall/isMini` giờ chỉ
> để **chọn layout của lib**.

### 3.5 Khi lib CHƯA có layout phù hợp (vd native full-screen / `NativeAdsFull`)

`com.brian.base_application.R.layout` hiện chỉ có native dạng bottom
(`ads_native_bot_2`, `ads_native_bot_no_media_short`). Nếu bản gốc có giao diện native **không
khớp** layout của lib (điển hình là `NativeAdsFull` — native full màn hình), thì:

- **GIỮ NGUYÊN giao diện custom** (tự dựng `NativeAdView` + `ConstraintLayout/MediaView/...`).
- **CHỈ đổi phần LOAD** sang lib: thay `AdLoader...loadAd()` → `Admob.getInstance().loadNativeAd(...)`.
- **Bind GIỮ chuẩn GMA**: `nativeAdView.setNativeAd(ad)` — **KHÔNG** dùng `pushAdsToViewCustom`
  (vì hàm đó cần layout của lib).

> Quy tắc chung: **lib có layout → `pushAdsToViewCustom` + layout lib; lib chưa có → giữ view
> custom + `setNativeAd`, chỉ đổi loader sang `Admob.loadNativeAd`.** Dù cách nào, **không** còn
> gọi `AdLoader`/`AdRequest` của GMA nữa.

---

## 4. INTERSTITIAL — trước → sau

**TRƯỚC:**
```kotlin
InterstitialAd.load(activity, unitId, AdRequest.Builder().build(), object : InterstitialAdLoadCallback() {
    override fun onAdLoaded(ad: InterstitialAd) { ad.show(activity) }
    override fun onAdFailedToLoad(e: LoadAdError) { ... }
})
```
**SAU:**
```kotlin
import com.nlbn.ads.callback.AdCallback
Admob.getInstance().loadAndShowInter(activity, unitId, true, object : AdCallback() {
    override fun onNextAction() { /* điều hướng tiếp sau khi ad đóng/không có ad */ }
    override fun onAdFailedToLoad(e: LoadAdError?) { /* fallback: đi tiếp */ }
})
```

### 4.1 GIỮ kịch bản inter phức tạp — chỉ đổi lời gọi SDK

Nhiều project gốc bọc inter trong các hàm điều phối (điều kiện hiện, cap tần suất, fallback
inter→native, callback `onAllAdsSkipped`…). → **GIỮ NGUYÊN** logic điều phối. **Chỉ thay bên
trong** các lời gọi GMA bằng lib.

> ⚠️ **BỎ loading dialog / `loadingViewModel` cho inter**: `loadAndShowInter(...)` của lib **tự
> hiện loading** khi nạp ad. (Hoặc dùng `showLoading=false` nếu app tự quản loading riêng — tránh
> chồng 2 lớp loading.)

| Bên trong hàm điều phối (gốc) | Đổi thành (lib) |
|---|---|
| `InterstitialAd.load(...).show()` | `Admob.getInstance().loadAndShowInter(activity, id, true, AdCallback())` |
| `AdLoader...forNativeAd{}.loadAd()` (nhánh native fallback) | `Admob.getInstance().loadNativeAd(ctx, id, NativeCallback())` |

> Tóm lại: **tầng "KHI NÀO hiện / fallback / cap / loading" = giữ nguyên; tầng "GỌI SDK thật" =
> đổi sang `Admob.getInstance()`.** Không đập đi viết lại `AdHelper`/`AdConfig`/`AdFrequencyManager`.

---

## 5. BANNER — trước → sau

**TRƯỚC:** `AdView(context).apply { adUnitId=...; setAdSize(...) }.loadAd(AdRequest())` + add vào container.
**SAU:**
```kotlin
import com.nlbn.ads.callback.BannerCallBack
Admob.getInstance().loadBanner(activity, unitId, bannerContainer, object : BannerCallBack() {
    override fun onBannerAdLoaded() {}
    override fun onBannerAdFailed() {}
})
```

---

## 6. APP OPEN / RESUME / CONSENT / INIT — XÓA hết

- **App Open & Resume ad**: lib tự hiển thị; app chỉ override `enableAdsResume(): Boolean = !isPurchased()`
  trong `HostApplication`. → **Xóa** `AppOpenManager`/`AppOpenAd.load` tự viết.
- **⚠️ MainActivity / Activity của app**: **bỏ MỌI logic Open App tự gọi** nếu có — vd
  `AppOpenAd.load/show`, observer `ProcessLifecycleOwner`/`ON_START` để show open-ad lúc resume,
  biến đếm/cờ show-open... Lib **đã xử lý open + resume ad**; giữ lại sẽ bị **chạy ad 2 lần / xung đột**.
- **Consent (UMP)**: lib lo ở splash. → **Xóa** `GoogleMobileAdsConsentManager`.
- **`MobileAds.initialize(...)`**: lib lo. → **Xóa**.

### 6.1 Premium / đã trả phí → ẩn TẤT CẢ ads

Bản gốc thường có cờ tự chế `Global.isPremiumUser`. → Đổi sang
**`com.brian.base_iap.utils.IAPUtils.isPremium()`** của lib (nguồn sự thật, đồng bộ billing).

| Bản gốc | Bản lib |
|---|---|
| `Global.isPremiumUser` | `IAPUtils.isPremium()` |
| `if (!Global.isPremiumUser) { showAd() }` | `if (!IAPUtils.isPremium()) { showAd() }` |

- **Đã trả phí → KHÔNG hiện bất kỳ ads nào** (native, inter, banner, open/resume…).
- Open/Resume: lib tự tắt qua `enableAdsResume(): Boolean = !isPurchased()` trong `HostApplication`.
- Native/banner **chiếm diện tích** → gate ngay ở cờ `enable`, để CẢ block (kể cả Spacer/padding/
  container bao quanh) bị bỏ, không chỉ ẩn nội dung ad:

```kotlin
import com.brian.base_iap.utils.FirebaseRemoteConfigUtil
import com.brian.base_iap.utils.IAPUtils

// Premium → false NGAY (không hiện, không chiếm chỗ); chưa trả phí mới đọc cờ Firebase.
fun isAdEnabled(key: String): Boolean {
    if (IAPUtils.isPremium()) return false
    return FirebaseRemoteConfigUtil.getInstance().getBoolean(key)
}
```
```kotlin
if (isAdEnabled("native_setting_enable")) {   // premium → false → CẢ BLOCK bị bỏ
    NativeAdSlot(slotName = "native_setting", unitId = AdManager.getAdUnitId(context, "native_setting"), isSmall = true)
}
```

---

## 7. Unit id & Remote Config

```kotlin
fun getAdUnitId(context: Context, key: String): String = try {
    FirebaseRemoteConfigUtil.getInstance().getAdsConfigValue(key)   // remote 'ads_config' → fallback asset
} catch (e: Exception) {
    JSONObject(context.assets.open("default_ads_config.json").bufferedReader().use { it.readText() }).optString(key, "")
}
```
- ⚠️ **KHÔNG** đọc id qua param top-level từng placement (`getString("native_xxx")`). Lib lưu TẤT CẢ
  id trong **một** key `ads_config` (JSON), đọc qua `getAdsConfigValue(key)`.
- Bật/tắt 1 placement: tự thêm cờ riêng (vd `getBoolean("<key>_enable")`) và bọc `if (enabled) { NativeAdSlot(...) }`.

### 7.1 Đổi Remote Config: `RemoteConfigManager` (gốc) → `FirebaseRemoteConfigUtil` (lib)

**Quy tắc cơ học: thay `RemoteConfigManager.instance` → `FirebaseRemoteConfigUtil.getInstance()`.**

| Bản gốc | Bản lib |
|---|---|
| `RemoteConfigManager.instance.getBoolean(k)` | `FirebaseRemoteConfigUtil.getInstance().getBoolean(k)` |
| `RemoteConfigManager.instance.getString(k)` | `FirebaseRemoteConfigUtil.getInstance().getString(k)` |
| `RemoteConfigManager.instance.getLong(k)` | `FirebaseRemoteConfigUtil.getInstance().getLong(k)` |
| `RemoteConfigManager.instance.getString("<unit_id_key>")` | **`getAdsConfigValue("<unit_id_key>")`** ⚠️ |

> ⚠️ **Ngoại lệ AD UNIT ID**: dùng **`getAdsConfigValue(key)`**, KHÔNG `getString(key)`.
> Các cờ khác (enable/log/customtext/interval…) dùng `getBoolean/getString/getLong` bình thường.

**Đăng ký default** (thay default của `RemoteConfigManager` gốc) — trong `HostApplication.onCreate()`
**SAU** `super.onCreate()`:
```kotlin
FirebaseRemoteConfigUtil.getInstance().setAppDefaults(mapOf("native_menu_enable" to true, /* … */))
// hoặc: setAppDefaultsFromXml(R.xml.remote_config_defaults)   // (hoặc R.xml.config của app)
```
> Lib **tự fetch** (đừng gọi fetch tay).
> ❌ **KHÔNG** gọi `FirebaseRemoteConfig.setDefaultsAsync(...)` trực tiếp — sẽ **xoá** default `ads_config` của lib.
>
> Mẹo ít rủi ro nhất: **giữ facade `RemoteConfigManager` cũ nhưng đổi RUỘT** để ủy quyền sang
> `FirebaseRemoteConfigUtil` (getString thử `getAdsConfigValue` trước, fallback `getString`).
> Như vậy mọi call-site cũ không phải sửa.

---

## 8. ProGuard / R8 (bản release minify)

```proguard
# Thư viện ads
-keep class com.nlbn.** { *; }
-keep class com.brian.** { *; }
# AdMob mediation (reflection) — tránh ClassNotFoundException
-keep class com.google.ads.mediation.** { *; }
-keep class com.facebook.ads.** { *; }
-dontwarn com.facebook.ads.**
# Gson generic (nếu dùng) — tránh "TypeToken must be created with a type argument"
-keepattributes Signature, InnerClasses, EnclosingMethod, *Annotation*
-keep,allowobfuscation,allowshrinking class * extends com.google.gson.reflect.TypeToken
# Crashlytics deobfuscate
-keepattributes SourceFile,LineNumberTable
```
Giữ `proguard-android-optimize.txt`, **đừng** `-dontoptimize`.

---

## 9. Checklist nghiệm thu (AI tự kiểm)

- [ ] Không còn `import com.google.android.gms.ads.AdLoader` / `AdRequest` / `InterstitialAd.load` /
      `AppOpenAd` / `MobileAds.initialize` trong code app.
- [ ] Native load qua `Admob.getInstance().loadNativeAd`, show qua `pushAdsToViewCustom` + layout lib
      (hoặc giữ view custom + `setNativeAd` nếu lib chưa có layout — §3.5).
- [ ] Inter qua `loadAndShowInter`, banner qua `loadBanner`.
- [ ] Đã xóa `GoogleMobileAdsConsentManager`, AppOpen/Inter manager tự viết.
- [ ] Unit id qua `getAdsConfigValue(key)`; có `default_ads_config.json`.
- [ ] Host Activity là `ComponentActivity`; native không `as ComponentActivity` thẳng (dùng `findComponentActivity`).
- [ ] Không `ad.destroy()` ở composable (ViewModel lo vòng đời).
- [ ] ProGuard có keep `com.nlbn.**`, `com.brian.**`, mediation, Gson Signature.
- [ ] `RemoteConfigManager` KHÔNG còn gọi `setDefaultsAsync` trực tiếp.
- [ ] `Global.isPremiumUser` → `IAPUtils.isPremium()`.
