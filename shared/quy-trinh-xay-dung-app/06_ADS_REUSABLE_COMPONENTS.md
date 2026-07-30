# 15 — Thành phần ADS DÙNG LẠI (copy sang project khác)

> "Lõi ads" dưới đây gần như KHÔNG đổi giữa các app. Khi làm app mới: **copy nguyên các file "core"**,
> chỉ **đổi `package`** (sed) + import `R`/`BuildConfig` cho đúng, rồi chỉnh **cấu hình + giao diện màn hình** riêng app.
> Nguyên tắc: **sửa core-logic → hầu như không; chỉ sửa config (placement/ratio/unit) + UI màn hình.**

## A. FILE COPY NGUYÊN (chỉ đổi package + R/BuildConfig)

Thư mục `app/src/main/java/<pkg>/advertisement/` (+ vài file kèm):

| File | Vai trò | Đổi gì khi copy |
|---|---|---|
| `AdsViewModel.kt` | Cache native theo Activity (Slot: isLoading/isLoaded/nativeAd + prepareForEntry) | chỉ `package` |
| `NativeAdSlot.kt` | Slot native (cache + shimmer + bind 1 lần key(ad) + tự ẩn khi fail + isSmall) | `package`; layout lib giữ nguyên (`ads_native_bot_2` / `..._no_media_short_main` / shimmer) |
| `AdManager.kt` | Điều phối inter + **chain native-inter** (giả intent) + tần suất sau khi inter đóng | chỉ `package` |
| `AdScenario.kt` | Tần suất `showCount % ratio` + `maxPerDay` + dọn key >7 ngày | chỉ `package` |
| `NativeInter.kt` | `NativeInterController` (show/preload/takePreloaded) + `NativeInterHost` (Dialog fullscreen, đếm ngược) + bind `ad_native_full` | `package` + import `R` |
| `NativeAdsFull.kt` | Composable native fullscreen (dùng cho MODAL Intro) + `bindFull` | `package` + import `R` |
| `AdPositions.kt` | Parse `positionIntrol` (A/B: N inline, NN modal) | chỉ `package` (đổi tên hàm parse → KHÔNG trùng stdlib) |
| `firebase/Remote.kt` | Facade Remote Config (adUnit/getBoolean/isAdEnabled) + **debug test-unit** | `package` + import `BuildConfig` |
| `core/InstallReferrerHelper.kt` | isAdsCampaign (gate Intro) — cache 3 tầng | chỉ `package` |
| `res/layout/ad_native_full.xml` | Layout native fullscreen tự dựng | đổi màu `backgroundTint` CTA theo primary app |

**Copy nhanh (ví dụ):**
```bash
SA=vga31b-kotlin/app/src/main/java/com/supportsoftware/checkerpro
SB=<app-mới>/app/src/main/java/<pkg-path>
for f in advertisement/*.kt firebase/Remote.kt core/InstallReferrerHelper.kt; do
  sed 's/com\.supportsoftware\.checkerpro/<pkg.mới>/g' "$SA/$f" > "$SB/$f"
done
cp .../res/layout/ad_native_full.xml <app-mới>/.../res/layout/   # rồi đổi màu CTA
```

## B. FILE COPY RỒI CHỈNH THEO APP (cấu hình + màn hình)

| File | Chỉnh gì |
|---|---|
| `res/xml/config.xml` | Danh sách placement `*_enable` + `inter_*_ratio/max` + `native_inter_*` + `positionIntrol` + count_app_open/organic |
| `assets/default_ads_config.json` | **Ad unit THẬT** của app (8 placement lib + placement app) |
| `ui/theme/Theme.kt` | Màu Primary/Secondary theo thiết kế của app |
| `ui/screen/onboarding/OnboardingScreens.kt` (IntroScreen) | **Chỉ đổi nội dung slide** (ảnh/emoji/chuỗi) + danh sách `native_introN`. Logic positionIntrol (inline/modal) + nút Next (bấm được khi ad fill/lỗi) GIỮ NGUYÊN |
| `core/MainActivity.kt` | Giữ `NativeInterHost()` ở root + `resolveStartRoute` gate Intro; chỉ đổi route nếu app khác |
| `MyApplication.kt` | IAP keys (id gói/subscription thật của app), test device id, notification/IAP resources |

## C. NƠI GỌI (điểm ráp vào màn hình)

- **Native slot**: `NativeAdSlot("native_home")` / `NativeAdSlot("native_x", isSmall = true)` (màn list).
- **Inter + native-inter (ads kép)**: `AdManager.showInter(activity, "inter_home") { onNavigate() }` tại điểm chuyển màn.
- **Native-inter host**: đặt `NativeInterHost()` ở root `setContent` của MainActivity (BẮT BUỘC, gọi qua import — KHÔNG FQN inline).
- **Intro modal**: `NativeAdsFull(unitId, onClose, onError)` overlay trong IntroScreen (đã có sẵn).

## D. LƯU Ý BẮT BUỘC khi copy (kẻo gãy) — chi tiết ở `05_ADS_RUNTIME_LESSONS.md`
- Log ads dùng `println` (KHÔNG `android.util.Log` — lib strip ở release).
- NativeAdSlot khi fail phải `slot.onError()` + `suppressedAfterError` (kẻo shimmer kẹt).
- Tên hàm mới nên tránh trùng tên API chuẩn (vd đừng đặt `parse` — dễ nhầm `Uri.parse`, khó đọc log/trace).
- `NativeInterHost()` gọi qua import, không viết FQN inline.
- IAP: nếu app không có gói tuần → tự điền `"weekly"` làm key mặc định.
