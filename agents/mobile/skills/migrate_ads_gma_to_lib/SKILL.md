# skill_migrate_ads_gma_to_lib

**Dùng bởi:** `mobile` (riêng — TUỲ CHỌN, chỉ dùng khi migrate app CŨ có GMA SDK trực tiếp).

**Mục tiêu:** Chuyển đổi app đang gọi trực tiếp Google Mobile Ads SDK (AdLoader, InterstitialAd,
AppOpenAd, MobileAds.initialize...) sang dùng thư viện `com.nlbn.ads` qua AAR `base-application`.

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

```
shared/quy-trinh-xay-dung-app/10_MIGRATE_ADS_TO_LIB.md  (file chính — 315 dòng, 9 bước cơ học)
```

## Nguyên tắc vàng

**KHÔNG gọi GMA SDK trực tiếp nữa.** Mọi load/show đi qua `Admob.getInstance()`;
consent/open/resume/khởi tạo SDK do lib tự lo.

## Bảng chuyển đổi nhanh

| Thao tác | Bản GỐC (GMA SDK) | Bản LIB (com.nlbn.ads) |
|---|---|---|
| Load native | `AdLoader.Builder().forNativeAd{}.build().loadAd()` | `Admob.getInstance().loadNativeAd(ctx, id, NativeCallback())` |
| Show native | `view.setNativeAd(ad)` + dựng view tay | Inflate layout lib + `pushAdsToViewCustom(ad, view)` |
| Interstitial | `InterstitialAd.load().show()` | `Admob.getInstance().loadAndShowInter(activity, id, true, AdCallback())` |
| Banner | `AdView.loadAd()` | `Admob.getInstance().loadBanner(activity, id, container, BannerCallBack())` |
| App Open | `AppOpenAd.load().show()` | **Lib tự lo** — app KHÔNG viết |
| Consent | `GoogleMobileAdsConsentManager` | **Lib tự lo** — XÓA |
| Init SDK | `MobileAds.initialize()` | **Lib tự lo** — XÓA |
| Unit id | `RemoteConfigManager.getString()` | `getAdsConfigValue(key)` (key `ads_config`) |
| Premium | `Global.isPremiumUser` | `IAPUtils.isPremium()` |

## Quy trình 9 bước

```
1. XÓA init & manager tự viết:
   - MobileAds.initialize, GoogleMobileAdsConsentManager, AppOpenManager tự viết,
     InterstitialAdManager tự viết.

2. THAY load/show GMA → Admob.getInstance():
   - Native: loadNativeAd + pushAdsToViewCustom (hoặc giữ view custom + setNativeAd nếu lib chưa có layout)
   - Inter: loadAndShowInter (BỎ loading dialog riêng — lib tự hiện)
   - Banner: loadBanner

3. THAY NativeAdView dựng tay → inflate layout lib:
   - Full: com.brian.base_application.R.layout.ads_native_bot_2
   - Small: ads_native_bot_no_media_short
   - Full-screen custom: GIỮ view custom + setNativeAd, CHỈ đổi loader

4. GIỮ NGUYÊN logic điều phối:
   - Cache AdsViewModel, NativeAdSlot state machine, AdFrequencyManager,
     fallback inter→native, AdConfig — CHỈ đổi lời gọi SDK bên trong.

5. THAY unit id: getAdsConfigValue(key), default_ads_config.json.

6. GIỮ applicationId + google-services.json.

7. THAY premium flag: Global.isPremiumUser → IAPUtils.isPremium()

8. ĐỔI RemoteConfig:
   - RemoteConfigManager.instance → FirebaseRemoteConfigUtil.getInstance()
   - Ad unit: getAdsConfigValue(key), KHÔNG getString(key)
   - KHÔNG setDefaultsAsync trực tiếp
   - Mẹo: giữ facade cũ, đổi ruột delegate sang FirebaseRemoteConfigUtil

9. PROGUARD: keep com.nlbn.**, com.brian.**, mediation, Gson Signature
```

## Checklist nghiệm thu

- [ ] Không còn `import com.google.android.gms.ads.AdLoader/AdRequest/InterstitialAd.load/AppOpenAd/MobileAds.initialize`
- [ ] Native load qua `loadNativeAd`, show qua `pushAdsToViewCustom` + layout lib (hoặc view custom + `setNativeAd`)
- [ ] Inter qua `loadAndShowInter`, banner qua `loadBanner`
- [ ] Đã xóa `GoogleMobileAdsConsentManager`, AppOpen tự viết
- [ ] Unit id qua `getAdsConfigValue(key)`
- [ ] `Global.isPremiumUser` → `IAPUtils.isPremium()`
- [ ] RemoteConfigManager KHÔNG gọi `setDefaultsAsync` trực tiếp
- [ ] ProGuard có keep đủ

## KHÔNG ĐƯỢC LÀM

- ❌ KHÔNG viết lại tầng điều phối ads — chỉ đổi lời gọi SDK.
- ❌ KHÔNG giữ loading dialog riêng cho inter.
- ❌ KHÔNG gọi `ad.destroy()` ở composable (ViewModel lo vòng đời).
