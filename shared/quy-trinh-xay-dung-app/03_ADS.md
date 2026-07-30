# 10 — Luồng quảng cáo (kiến trúc & cách điều phối)

> Ads chạy trên lib `com.nlbn.ads` (Admob wrapper của `base-application`). Tài liệu này mô tả tầng điều phối ads phía app (tần suất hiện, cache, native-inter…) — phần app **tự viết**, khác với các màn splash/inter mặc định do lib lo.

## 1. Kiến trúc

| Vai trò | Cách gọi (Kotlin) |
|---|---|
| Tải/hiện inter | `Admob.getInstance().loadAndShowInter(activity, unit, true, cb)` |
| Tải native | `Admob.getInstance().loadNativeAd(ctx, unit, NativeCallback)` |
| Bind native vào view | `Admob.getInstance().pushAdsToViewCustom(nativeAd, nativeAdView)` + layout của lib |
| Ad unit id | `Remote.instance.adUnit(placement)` → `FirebaseRemoteConfigUtil.getAdsConfigValue()` (đọc key `ads_config`) |
| Premium tắt ads | `IAPUtils.isPremium()` |

**Ad unit KHÔNG nằm rải rác** — tất cả trong 1 key Remote Config `ads_config` (JSON `{placement: unit_id}`), default lấy từ `assets/default_ads_config.json`.

## 2. Các kịch bản điều phối (per placement)

Mỗi placement có 3 tham số cấu hình trong `res/xml/config.xml`:

- **enable** — bật/tắt: `{placement}_enable` (bool).
- **ratio (tỉ lệ xuất hiện)** — `{placement}_ratio` (hoặc `_showRatio`): chỉ hiện khi `showCount % ratio == 0`.
- **max/ngày (cap)** — `{placement}_max` (hoặc `_maxShowPerDay`): chỉ hiện khi `showCountAd < max`. Đếm theo **ngày** (reset mỗi ngày).

Cộng thêm **kịch bản native xen kẽ sau inter** (2 quảng cáo liên tiếp): khi inter đóng, nếu cấu hình `native_inter_*` bật thì hiện thêm 1 native full-screen.

### `advertisement/AdScenario.kt`
`shouldShow(context, type, ratio, maxPerDay, noCount)`:
- Lưu đếm theo ngày trong SharedPreferences, key = `date + type` (reset khi sang ngày mới).
- `ratio <= 0` coi như `1` (luôn qua cửa tỉ lệ).
- Logic: `pass = (showCount % ratio == 0) && (showCountAd < maxPerDay)`. `noCount=true` → không tăng đếm (cho lần điều hướng không tính).

### `advertisement/AdManager.kt`
`showInter(activity, interPlacement, onNext)`:
1. Nếu `!enable(interPlacement)` hoặc không qua ratio/max → gọi `onNext()` luôn (không ads).
2. Nếu qua → `Admob.loadAndShowInter(...)`; trong callback `onNextAction` → xét `native_{interPlacement}` (native-inter). Nếu bật → `NativeInterController.show(...)`; đóng xong mới `onNext()`.
3. **`onNext()` luôn được gọi đúng 1 lần** (dù ads lỗi/không hiện) — nếu không app sẽ kẹt điều hướng.

### `advertisement/NativeInter.kt`
- `NativeInterController` (object, `mutableStateOf<Req?>`) + `NativeInterHost()` (composable đặt ở **root** `MainActivity`).
- Khi có request → `Admob.loadNativeAd` → hiện `Dialog` fullscreen dùng layout lib `ads_native_bot_2` + `pushAdsToViewCustom`; nút ✕ bật sau 3s (giống inter). Lỗi load → bỏ qua, gọi tiếp điều hướng.

## 3. Slot native trong màn list — `advertisement/NativeAdSlot.kt`

- Dùng **layout của lib**: `ads_native_bot_2` (hiển thị) + `ads_native_bot_loading_2` (shimmer khi tải). Có thể dùng `ads_native_bot_no_media_short` cho slot thấp.
- `enabled = !IAPUtils.isPremium() && remote.isAdEnabled(placement) && adUnit.isNotBlank()`.
- Bind: inflate layout lib thành `NativeAdView` → `Admob.getInstance().pushAdsToViewCustom(ad, view)`.

```kotlin
AndroidView(factory = { ctx ->
    (LayoutInflater.from(ctx).inflate(com.brian.base_application.R.layout.ads_native_bot_2, null) as NativeAdView)
        .also { Admob.getInstance().pushAdsToViewCustom(ad, it) }
})
```

> ⚠️ **Truy cập layout lib từ app**: `com.brian.base_application.R.layout.ads_native_bot_2` (R của lib, không phải R app).

## 4. Bẫy đã gặp (đọc kỹ)

| Triệu chứng | Nguyên nhân | Sửa |
|---|---|---|
| Native trong `LazyColumn` load rồi biến mất, load lại 3 lần (rate-limited) | Item ads không có key ổn định → recompose dispose/reload | `item(key = "ad_$placement")` cho slot ads |
| Native hiện ở Home nhưng KHÔNG hiện ở màn list | Cùng lỗi key ở trên + đo sai enable | Key ổn định + kiểm tra `isAdEnabled` đọc đúng `{placement}_enable` |
| `native_home` no-fill lúc test | Hành vi ad-network tạm thời (không phải bug) | Thử lại/đợi; kiểm tra bằng test unit id |

## 5. Checklist

- [ ] Mỗi placement có đủ `{placement}_enable` (+ `_ratio`/`_max` cho inter) trong `res/xml/config.xml`.
- [ ] `default_ads_config.json` đủ **8 placement lib bắt buộc** (open_splash/inter_splash/splash_uninstall/native_language/open_all/native_keep_user/native_survey_user/native_exit_app) + placement riêng app, **dùng unit THẬT**.
- [ ] Không còn `import` GMA (`AdLoader/InterstitialAd/AppOpenAd/MobileAds.initialize`) trong code app — mọi lời gọi ads đi qua `Admob.getInstance()` của lib.
- [ ] `NativeInterHost()` đặt ở root `MainActivity` (qua **import**, không FQN inline).
- [ ] `onNext()` của `showInter` luôn gọi đúng 1 lần.

## 6. IAP product keys + Ads test unit (dev) — GHI CHÚ QUAN TRỌNG

**IAP product id** điền vào `MyApplication` (KHÔNG dùng `defaultIap*Key()` của lib khi app đã có key thật):
- `iapPremiumKey()` — id gói mua 1 lần / gỡ ads.
- `iapPremiumMonthlyKey()` / `iapPremiumYearlyKey()` — id gói theo tháng/năm.
- Thiếu gói tuần → `iapPremiumWeeklyKey()` để mặc định `"weekly"`.

**Ads NO_FILL khi app CHƯA publish** (AdMob error code 3): unit THẬT không có fill cho app mới/chưa publish → KHÔNG thấy ads dù code đúng (log `Ad failed to load : 3`).
→ `Remote.adUnit()` trả **unit TEST Google khi `BuildConfig.DEBUG`** (native `…/2247696110`, inter `…/1033173712`, app-open `…/9257395921`); release dùng unit thật. Nghiệm thu: `ADSLOT: loaded … ad=true` + Google báo "AdMob native ad validator: No implementation issues found".
Lưu ý: ads của LIB (open_splash/inter_splash/native_language…) đọc từ `ads_config` (unit thật) nên vẫn NO_FILL trong debug — chỉ placement do APP điều khiển (native slot, inter_home…) mới dùng test unit.
