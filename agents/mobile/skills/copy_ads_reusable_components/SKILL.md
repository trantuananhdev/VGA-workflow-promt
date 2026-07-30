# skill_copy_ads_reusable_components

**Dùng bởi:** `mobile` (riêng — phase `mobile-screen`, chạy SAU `clone_vga31_template` + `setup_host_application`).

**Mục tiêu:** Copy "lõi ads" — 10 file Kotlin + 1 layout XML — từ template `vga31-kotlin`
sang app mới, chỉ đổi package. Đây là tầng điều phối ads phía app (tần suất, cache, native-inter,
Intro A/B...), khác với các màn splash/inter mặc định do thư viện lo.

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

```
shared/quy-trinh-xay-dung-app/06_ADS_REUSABLE_COMPONENTS.md  (file chính)
shared/quy-trinh-xay-dung-app/03_ADS.md  (kiến trúc ads, kịch bản điều phối)
shared/quy-trinh-xay-dung-app/05_ADS_RUNTIME_LESSONS.md  (bài học vận hành, BẮT BUỘC đọc trước khi đụng ads)
```

## A. File copy nguyên (chỉ đổi package + import R/BuildConfig)

| # | File nguồn (trong template) | Vai trò | Đổi gì khi copy |
|---|---|---|---|
| 1 | `advertisement/AdsViewModel.kt` | Cache native theo Activity (Slot: isLoading/isLoaded/nativeAd + prepareForEntry) | chỉ `package` |
| 2 | `advertisement/NativeAdSlot.kt` | Slot native (cache + shimmer + bind 1 lần key(ad) + tự ẩn khi fail + isSmall) | `package`; layout lib giữ nguyên |
| 3 | `advertisement/AdManager.kt` | Điều phối inter + **chain native-inter** + tần suất sau khi inter đóng | chỉ `package` |
| 4 | `advertisement/AdScenario.kt` | Tần suất `showCount % ratio` + `maxPerDay` + dọn key >7 ngày | chỉ `package` |
| 5 | `advertisement/NativeInter.kt` | `NativeInterController` (show/preload/takePreloaded) + `NativeInterHost` (Dialog fullscreen) | `package` + import `R` |
| 6 | `advertisement/NativeAdsFull.kt` | Composable native fullscreen (modal Intro) + `bindFull` | `package` + import `R` |
| 7 | `advertisement/AdPositions.kt` | Parse `positionIntrol` (A/B: N inline, NN modal) | chỉ `package` (tên hàm `parsePositions`, KHÔNG `parse`) |
| 8 | `firebase/Remote.kt` | Facade Remote Config (adUnit/getBoolean/isAdEnabled) + **debug test-unit** | `package` + import `BuildConfig` |
| 9 | `core/InstallReferrerHelper.kt` | isAdsCampaign (gate Intro) — cache 3 tầng | chỉ `package` |
| 10 | `res/layout/ad_native_full.xml` | Layout native fullscreen tự dựng | đổi màu `backgroundTint` CTA theo primary app |

## B. Quy trình copy

```
1. XÁC ĐỊNH đường dẫn nguồn và đích:
   NGUỒN = shared/quy-trinh-xay-dung-app/vga31-kotlin/app/src/main/java/com/supportsoftware/checkerpro/
   ĐÍCH  = <NEW_APP_DIR>/app/src/main/java/<APPLICATION_ID_PATH>/

2. COPY + SED (đổi package):
   Với mỗi file .kt ở bảng A:
   a) Copy file vào đúng thư mục con tương ứng (advertisement/, firebase/, core/).
   b) Thay package declaration:
      com.supportsoftware.checkerpro → <APPLICATION_ID>
   c) Thay import:
      import com.supportsoftware.checkerpro.R → import <APPLICATION_ID>.R
      import com.supportsoftware.checkerpro.BuildConfig → import <APPLICATION_ID>.BuildConfig
   d) Giữ nguyên import thư viện (com.nlbn.ads.*, com.brian.base_application.*,
      com.google.android.gms.ads.*).

   Ví dụ (bash/PowerShell):
   ```bash
   SA=shared/quy-trinh-xay-dung-app/vga31-kotlin/app/src/main/java/com/supportsoftware/checkerpro
   SB=<app-mới>/app/src/main/java/<pkg-path>
   for f in advertisement/*.kt firebase/Remote.kt core/InstallReferrerHelper.kt; do
     sed 's/com\.supportsoftware\.checkerpro/<pkg.mới>/g' "$SA/$f" > "$SB/$f"
   done
   ```

3. COPY layout XML:
   cp .../res/layout/ad_native_full.xml <app-mới>/app/src/main/res/layout/
   → Đổi màu `backgroundTint` CTA button cho khớp primaryColor của app mới.

4. VERIFY: build phải thành công, không có unresolved import.
```

## C. File copy rồi CHỈNH theo app (cấu hình + UI)

| File | Chỉnh gì |
|---|---|
| `res/xml/config.xml` | Danh sách placement `*_enable` + `inter_*_ratio/max` + `native_inter_*` + `positionIntrol` + `count_app_open`/`organic_number_not_guide` |
| `assets/default_ads_config.json` | **Ad unit THẬT** của app (8 placement lib + placement app) |
| `ui/theme/Theme.kt` | Màu Primary/Secondary theo thiết kế app |
| `ui/screen/onboarding/OnboardingScreens.kt` | **Chỉ đổi nội dung slide** (ảnh/emoji/chuỗi). Logic positionIntrol + nút Next GIỮ NGUYÊN |
| `core/MainActivity.kt` | Giữ `NativeInterHost()` ở root + `resolveStartRoute` gate Intro |
| `MyApplication.kt` | IAP keys, test device id, notification/IAP resources |

## D. Nơi gọi (điểm ráp vào màn hình)

```kotlin
// Native slot — chèn vào bất kỳ Composable nào:
NativeAdSlot("native_home")                        // full, có media
NativeAdSlot("native_history", isSmall = true)     // gọn, cho list

// Inter + native-inter (ads kép) — trước khi điều hướng:
AdManager.showInter(activity, "inter_home") { onNavigate(route) }

// Native-inter host — BẮT BUỘC đặt ở root setContent của MainActivity:
NativeInterHost()   // gọi qua import, KHÔNG FQN inline

// Native full-screen modal — trong IntroScreen:
NativeAdsFull(unitId, onClose, onError)
```

## E. Về `firebase/Remote.kt` — Facade Remote Config

File này là **trung gian bắt buộc** giữa app và Remote Config của lib:

```kotlin
class Remote private constructor() {
    private val frc get() = FirebaseRemoteConfigUtil.getInstance()

    // Debug = test unit (luôn fill); Release = unit thật (cần publish Play)
    fun adUnit(placement: String): String =
        if (BuildConfig.DEBUG) debugTestUnit(placement) else frc.getAdsConfigValue(placement)

    // Premium → tắt hết ads (trả false cho mọi *_enable key)
    fun getBoolean(key: String): Boolean {
        if (IAPUtils.isPremium() && key.endsWith("_enable")) return false
        return frc.getBoolean(key)
    }

    fun isAdEnabled(placement: String): Boolean = getBoolean("${placement}_enable")

    companion object { val instance: Remote by lazy { Remote() } }
}
```

**Quan trọng:**
- ❌ KHÔNG subclass `FirebaseRemoteConfigUtil` (singleton song song, mất default ads_config)
- ❌ KHÔNG gọi `FirebaseRemoteConfig.getInstance()` trực tiếp
- ✅ Ủy quyền (delegate) qua `FirebaseRemoteConfigUtil.getInstance()`

## F. Layout native — chọn layout nào

| Nơi dùng | Layout lib | Shimmer lib |
|---|---|---|
| Slot thường (Home/Intro/Scan/detail) | `com.brian.base_application.R.layout.ads_native_bot_2` | `ads_native_bot_loading_2` |
| Slot LIST (apps/history/update) | `ads_native_bot_no_media_short_main` | `ads_native_loading_short_main` |
| Native-inter / modal Intro | `res/layout/ad_native_full.xml` (tự dựng, bind `setNativeAd`) | (không shimmer) |

⚠️ **Layout lib import bằng R của lib**: `com.brian.base_application.R.layout.ads_native_bot_2`

## G. Lưu ý BẮT BUỘC khi copy (chi tiết ở `05_ADS_RUNTIME_LESSONS.md`)

1. **Log ads dùng `println`** — KHÔNG `android.util.Log` (lib strip ở release).
2. **NativeAdSlot fail → `slot.onError()` + `suppressedAfterError`** — thiếu = shimmer kẹt >30s.
3. **Tên hàm tránh trùng stdlib** — `parsePositions()`, KHÔNG `parse()`.
4. **`NativeInterHost()` gọi qua import** — KHÔNG FQN inline.
5. **`onNext()` luôn gọi đúng 1 lần** — dù ads lỗi/không hiện, app KHÔNG kẹt điều hướng.
6. **Native trong `LazyColumn` cần `key` ổn định** — `item(key = "ad_$placement")`, tránh recompose reload.

## Output

- 10 file .kt + 1 layout .xml đã copy + đổi package thành công.
- Build pass, không unresolved import.
- `res/xml/config.xml` có đủ placement enable/ratio/max.

## KHÔNG ĐƯỢC LÀM

- ❌ KHÔNG viết lại logic điều phối ads — copy nguyên, chỉ đổi package.
- ❌ KHÔNG đổi tên class/hàm trong lõi ads (trừ fix tên trùng stdlib).
- ❌ KHÔNG import GMA SDK trực tiếp — mọi load/show qua `Admob.getInstance()`.
- ❌ KHÔNG giữ loading dialog riêng cho inter — `loadAndShowInter` tự hiện loading.
