# skill_configure_ads_iap

**Dùng bởi:** `mobile` (riêng — phase `mobile-shell`, chạy SAU `setup_host_application`).

**Mục tiêu:** Cấu hình hệ thống quảng cáo (ads) và mua hàng trong ứng dụng (IAP) cho
app mới, bao gồm: ad unit config, IAP product setup, Remote Config, hiển thị quảng cáo
riêng của app, và paywall gate pattern.

## Tiền đề

- `setup_host_application` đã chạy xong (HostApplication biên dịch được).
- `integrate_base_application` đã verify pass.

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

```
shared/quy-trinh-xay-dung-app/vga31-kotlin/base-application/HUONG_DAN_TICH_HOP.md  (§5.5, §8.3-§8.5, §10, §11)
shared/quy-trinh-xay-dung-app/03_ADS.md
shared/quy-trinh-xay-dung-app/05_ADS_RUNTIME_LESSONS.md
shared/quy-trinh-xay-dung-app/06_ADS_REUSABLE_COMPONENTS.md
shared/quy-trinh-xay-dung-app/01_HANDOFF_NEXT_APP.md  (§0, §2, §3)
```

## 1. Cấu hình Ad Units — `assets/default_ads_config.json`

File này là **nguồn ad-unit DUY NHẤT** thư viện đọc (qua key Remote Config `ads_config`).

### Cấu trúc JSON (các key bắt buộc):

```json
{
  "open_splash": "ca-app-pub-.../open_splash",
  "inter_splash": "ca-app-pub-.../inter_splash",
  "splash_uninstall": "ca-app-pub-.../open_uninstall",
  "native_language": "ca-app-pub-.../native_language",
  "open_all": "ca-app-pub-.../open_resume",
  "native_keep_user": "ca-app-pub-.../native_keep",
  "native_survey_user": "ca-app-pub-.../native_survey",
  "native_exit_app": "ca-app-pub-.../native_exit"
}
```

### Quy tắc:

- Khi chưa có ad unit thật → dùng test ad unit id của Google (§11.7 trong guide).
- ĐỪNG tạo key trùng key của thư viện dưới tên khác.
- Muốn đổi/A-B test từ xa: override key `ads_config` trên Firebase console.
- ĐỪNG gọi `FirebaseRemoteConfig.getInstance().setDefaultsAsync(...)` trực tiếp.

## 2. Cấu hình IAP (In-App Purchase)

### 2.1 Override trong HostApplication

```kotlin
override fun iapPremiumKey() = "premium"              // one-time purchase (nếu có)
override fun iapPremiumWeeklyKey() = "sub_weekly"      // subscription tuần
override fun iapPremiumMonthlyKey() = "sub_monthly"    // subscription tháng
override fun iapPremiumYearlyKey() = "sub_yearly"      // subscription năm
override fun iapPublicKey() = getString(R.string.public_license_key) // Base64 license key
```

### 2.2 Setup trên Google Play Console

Tạo 3 subscription products khớp với key ở trên (tuần/tháng/năm).
License key (Base64) lấy từ Play Console > Monetize > Monetization setup.

### 2.3 Paywall Gate Pattern (CHUẨN)

```kotlin
fun onPremiumFeatureClick() {
    if (IAPUtils.isPremium()) {
        useFeature()     // đã mua → dùng luôn
    } else {
        NativeCodecSnowFlakeCortexAI.nativeAiStartIapActivity(this)  // mở paywall
    }
}
```

Luồng: bấm → paywall → mua → paywall tự đóng → bấm lại → dùng tính năng.
KHÔNG cố tự chạy tính năng trong/sau luồng paywall.

## 3. Remote Config cho key riêng app

### 3.1 Đăng ký default (trong HostApplication.onCreate(), SAU super.onCreate()):

```kotlin
override fun onCreate() {
    super.onCreate()   // lib init + fetch Remote Config ở đây

    FirebaseRemoteConfigUtil.getInstance().setAppDefaults(
        mapOf(
            "myapp_show_promo_banner" to false,
            "myapp_max_retry"         to 3L,
            "myapp_welcome_message"   to "Hello",
        )
    )
}
```

### 3.2 Đọc giá trị (ở bất kỳ đâu):

```kotlin
val frc = FirebaseRemoteConfigUtil.getInstance()
val showPromo = frc.getBoolean("myapp_show_promo_banner")
val maxRetry  = frc.getLong("myapp_max_retry")
val welcome   = frc.getString("myapp_welcome_message")
```

### 3.3 Quy tắc:

- ✅ Dùng `FirebaseRemoteConfigUtil.getInstance()` — KHÔNG `FirebaseRemoteConfig.getInstance()`.
- ✅ Đăng ký SAU `super.onCreate()`, MỘT lần gọi `setAppDefaults`.
- ✅ Đặt tiền tố riêng (vd `myapp_`) tránh đụng key lib.
- ❌ KHÔNG tạo subclass `FirebaseRemoteConfigUtil` với companion riêng.
- ❌ KHÔNG gọi `setDefaultsAsync(...)` trực tiếp.
- ❌ KHÔNG tự fetch — lib đã fetch trong `BaseApplication.onCreate()`.

## 4. Hiển thị quảng cáo riêng của app (§11)

App có thể tự hiện ads qua API của thư viện:

### 4.1 Banner

```kotlin
Admob.getInstance().loadBanner(activity, adUnitId, container, BannerCallBack())
// Hoặc BannerPlugin (adaptive/collapsible/auto-refresh):
val config = BannerPlugin.Config().apply {
    defaultAdUnitId = adUnitId
    defaultBannerType = BannerPlugin.BannerType.Adaptive
    defaultRefreshRateSec = 30
}
Admob.getInstance().loadBannerPlugin(activity, container, shimmer, config)
```

### 4.2 Interstitial

```kotlin
// Load rồi show riêng:
Admob.getInstance().loadInterAds(context, adUnitId, AdCallback())
// Load-and-show một lần:
Admob.getInstance().loadAndShowInter(activity, adUnitId, true, AdCallback())
// Giới hạn tần suất:
Admob.getInstance().setIntervalShowInterstitial(15) // 15s giữa 2 inter
```

### 4.3 Native

```kotlin
Admob.getInstance().loadNativeAd(context, adUnitId, object : NativeCallback() {
    override fun onNativeAdLoaded(nativeAd: NativeAd) {
        val adView = layoutInflater.inflate(R.layout.ad_native, null) as NativeAdView
        Admob.getInstance().pushAdsToViewCustom(nativeAd, adView)
        container.removeAllViews(); container.addView(adView)
    }
    override fun onAdFailedToLoad() { container.visibility = View.GONE }
})
```

### 4.4 Rewarded

```kotlin
Admob.getInstance().initRewardAds(context, adUnitId)
Admob.getInstance().showRewardAds(activity, RewardCallback())
```

### 4.5 App-Open / Resume

```kotlin
AppOpenManager.getInstance().init(application)
AppOpenManager.getInstance().setAppResumeAdId(adUnitId)
AppOpenManager.getInstance().disableAppResumeWithActivity(SplashActivity::class.java)
```

## 5. Bài học vận hành ads (GOTCHAS)

1. **Log ads**: dùng `println`, KHÔNG `android.util.Log` — lib có
   `-assumenosideeffects android.util.Log` → release xoá hết Log.
2. **NativeAdSlot fail**: PHẢI `slot.onError()` + ẩn slot. Thiếu = shimmer kẹt >30s.
3. **NO_FILL / HTTP 400 ở release**: app CHƯA publish → AdMob chưa nhận diện → KHÔNG phải
   lỗi code. Debug dùng test unit id.
4. **Dark mode**: khoá cứng `darkTheme = false` trong `AppTheme()` nếu chưa có dark design.
5. **Ad ID rỗng**: nếu `getAdsConfigValue("key")` trả `""` → kiểm tra
   `default_ads_config.json` có key đó chưa.

## Output

- `assets/default_ads_config.json` với đúng cấu trúc.
- HostApplication override đúng IAP keys.
- Remote Config defaults đã đăng ký (nếu app cần).
- Quảng cáo riêng app đã tích hợp đúng API.

## KHÔNG ĐƯỢC LÀM

- ❌ KHÔNG tự init ads/consent — thư viện tự lo.
- ❌ KHÔNG tạo lớp config ads song song.
- ❌ KHÔNG gọi `setDefaultsAsync` trực tiếp.
- ❌ KHÔNG dùng key `ads_config` cho mục đích khác — đó là key của lib.
- ❌ KHÔNG dùng `android.util.Log` cho log ads (bị strip ở release).
