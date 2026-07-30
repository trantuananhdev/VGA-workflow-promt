# 12 — Logic hiển thị màn Intro (onboarding)

> App không hiện Intro theo kiểu "lần đầu 1 lần" đơn giản. Nó gate theo **số lần mở app** + **nguồn cài đặt** (ad campaign vs organic) để tối ưu review Google Play.

## 1. Quy tắc gate Intro

Biến & remote config:
- `goToHomeNumber` — bộ đếm số lần vào Home, bắt đầu **1**, **+1 mỗi lần** khởi động chính (lưu SharedPreferences). Tức = số thứ tự lần mở.
- `count_app_open` (default 3), `organic_number_not_guide` (default 3) — từ Remote Config.
- `isAdsCampaign` — từ **InstallReferrer** (native), không phải remote config.

Công thức:
```kotlin
val goToHomeStatus = if (isAdsCampaign) n >= countAppOpen
                     else n < organic || n >= countAppOpen + organic
// goToHomeStatus == true  → vào Home
// goToHomeStatus == false → hiện Intro
```

Bảng chân trị (count=3, organic=3):

| Nguồn cài | Lần 1–2 | Lần 3–5 | Lần 6+ |
|---|---|---|---|
| **Ad campaign** | **Intro** | Home | Home |
| **Organic** | Home | **Intro** | Home |

Ý nghĩa: user organic / các lần mở đầu thấy Home sạch; chỉ user từ chiến dịch ads (hoặc sau vài lần mở) mới thấy onboarding.

## 2. Vị trí trong luồng khởi động

- **Lib sở hữu màn Language** (Splash→Inter→**Language**→IAP→Home). Logic gate ở đây chỉ chi phối **màn Intro của app** (nằm sau các màn của lib).
- `isAdsCampaign` được xác định qua **InstallReferrer**.

## 3. Cài đặt (implementation)

### `core/InstallReferrerHelper.kt`
Query InstallReferrer **1 lần duy nhất trong đời app** rồi cache (nguồn cài không đổi). Chạy **async fire-and-forget** trong `Application.onCreate` → **không block splash**.

Quy tắc phân loại (mọi nhánh lỗi → coi là **ads=true**):
- có `gclid` → ads
- không có `utm_medium` / `(not set)` → organic
- `utm_medium == "organic"` → organic
- còn lại (cpc/banner/…) → ads

**3 tầng cache** khi đọc:
1. In-memory (`@Volatile cached`) — mỗi tiến trình đọc/tính 1 lần.
2. SharedPreferences (`is_ads_campaign` + `ads_campaign_resolved`) — bền qua các lần mở.
3. InstallReferrer — chỉ kết nối 1 lần (khi `ads_campaign_resolved==false`).

### `core/AppStorage.kt`
- `goToHomeNumber(ctx)` (default 1) / `setGoToHomeNumber(ctx, n)`.
- `isAdsCampaign(ctx)` (default **true** = fallback ads) / `setAdsCampaign(ctx, isAds)` / `isAdsCampaignResolved(ctx)`.

### `MyApplication.onCreate`
```kotlin
InstallReferrerHelper.resolve(this)   // async, cache; bỏ qua nếu đã resolve
```

### `core/MainActivity.resolveStartRoute()`
```kotlin
val n = AppStorage.goToHomeNumber(this)
AppStorage.setGoToHomeNumber(this, n + 1)          // +1 cho lần sau
val countAppOpen = remote.getInt("count_app_open").let { if (it <= 0) 3 else it }
val organic      = remote.getInt("organic_number_not_guide").let { if (it < 0) 0 else it }
val isAds        = InstallReferrerHelper.isAdsCampaign(this)   // cache in-memory
val goToHomeStatus = if (isAds) n >= countAppOpen
                     else n < organic || n >= countAppOpen + organic
return if (goToHomeStatus) Screen.Home.route else Screen.Intro.route
```

### `res/xml/config.xml`
Thêm `count_app_open` (=3) và `organic_number_not_guide` (=3). Các key này đọc/ghi bình thường qua Remote Config → điều chỉnh được từ xa.

## 4. Cách test bằng adb

```bash
# fresh install → xem quyết định:
adb shell pm clear <applicationId>
adb logcat -c
adb shell monkey -p <applicationId> -c android.intent.category.LAUNCHER 1
adb logcat -d -s InstallReferrer     # xem rawRef + isAds decision
# xem counter + nguồn cài đã cache:
adb shell run-as <applicationId> cat /data/data/<applicationId>/shared_prefs/AppStorage.xml
```
- Sideload (adb) thường trả `utm_medium=organic` → nhánh organic (lần 1–2 vào thẳng Home).
- Muốn test nhánh Intro: cold-launch nhiều lần cho `goToHomeNumber` chạm ngưỡng (organic: lần 3).

## 5. Checklist

- [ ] InstallReferrer chỉ kết nối 1 lần (cache 3 tầng), async, không block splash.
- [ ] `goToHomeNumber` +1 mỗi lần mở vào Home.
- [ ] `count_app_open` + `organic_number_not_guide` đọc từ Remote Config.
- [ ] Fallback `isAdsCampaign = true` khi chưa resolve.
- [ ] Bảng chân trị đúng như thiết kế (test bằng adb).
