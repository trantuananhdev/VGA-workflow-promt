# skill_setup_intro_onboarding

**Dùng bởi:** `mobile` (riêng — phase `client-screen`, TUỲ CHỌN).

**Mục tiêu:** Chèn luồng Intro/Onboarding vào giữa IAP → Home, sử dụng pattern rẽ nhánh
`getHomeActivity()` theo state onboarding — KHÔNG dựng router riêng.

## Tiền đề

- `setup_host_application` đã chạy xong.
- App cần màn Intro/Onboarding trước khi vào MainActivity.

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

```
shared/quy-trinh-xay-dung-app/vga31-kotlin/base-application/HUONG_DAN_TICH_HOP.md  (§8.7)
shared/quy-trinh-xay-dung-app/04_INTRO_CHECK.md
```

## Luồng

```
Splash → Inter → Language → IAP → [getHomeActivity()] → MainActivity
                                          │
                                          ├─ chưa onboarding → IntroActivity
                                          └─ đã onboarding  → MainActivity
```

## Quy trình

```
1. TẠO IntroActivity (ViewPager + slides + nút "Skip"/"Get Started").

2. CẬP NHẬT HostApplication:

   override fun onCreate() {
       MyAppPrefs.init(this)      // TRƯỚC super.onCreate()!
       super.onCreate()
   }

   override fun getHomeActivity(): Class<out Activity> {
       return if (MyAppPrefs.isOnboardingDone()) {
           MainActivity::class.java
       } else {
           IntroActivity::class.java
       }
   }

   ⚠️ getHomeActivity() được gọi RẤT SỚM (trong super.onCreate()).
   Nếu đọc SharedPreferences/DataStore → init TRƯỚC super.onCreate().
   Dùng lateinit/Koin chưa init = NPE.

3. TRONG IntroActivity — khi user xong:

   binding.btnGetStarted.setOnClickListener {
       MyAppPrefs.setOnboardingDone(true)
       startActivity(
           Intent(this, MainActivity::class.java)
               .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK or Intent.FLAG_ACTIVITY_NEW_TASK)
       )
       finish()
   }

   ⚠️ FLAG_ACTIVITY_CLEAR_TASK | FLAG_ACTIVITY_NEW_TASK BẮT BUỘC.
   Thiếu = BACK từ MainActivity quay lại IntroActivity.

4. KHAI BÁO trong AndroidManifest.xml:

   <activity
       android:name=".IntroActivity"
       android:exported="false"
       android:screenOrientation="portrait" />

   KHÔNG đặt MAIN/LAUNCHER.

5. (TUỲ CHỌN) Tích hợp ads vào Intro:
   - Xem shared/quy-trinh-xay-dung-app/04_INTRO_CHECK.md cho pattern NativeAdSlot
     + timeout + fallback khi ad fail.
   - Nút Next phải bấm được khi ad fill HOẶC lỗi (timeout 5s + onResolved).
   - NativeAdSlot fail → slot.onError() + ẩn slot. Thiếu = shimmer kẹt >30s.
```

## Đóng IAP đi đâu?

Khi user đóng IAP (nút X), lib gọi router, target = `getHomeActivity()` lúc app khởi động:
- Lần đầu (chưa onboarding): → IntroActivity ✓
- Lần sau (đã onboarding): → MainActivity ✓

Pattern hoạt động chính xác mà không cần hook nào.

## KHÔNG ĐƯỢC LÀM

- ❌ Đừng đặt MAIN/LAUNCHER trên IntroActivity.
- ❌ Đừng quên CLEAR_TASK | NEW_TASK khi đi Intro → Main.
- ❌ Đừng đọc state bằng class chưa init trong getHomeActivity().
- ❌ Đừng mở IAP từ trong Intro (IAP đã chạy TRƯỚC Intro trong luồng).
  Nếu cần upsell: `NativeCodecSnowFlakeCortexAI.nativeAiStartIapActivity(this)`.

## Output

- IntroActivity hoạt động đúng luồng.
- getHomeActivity() rẽ nhánh đúng theo state.
- Build pass.

---

## PHẦN NÂNG CAO: Gate logic Intro theo nguồn cài + số lần mở

> Tài liệu chi tiết: `shared/quy-trinh-xay-dung-app/04_INTRO_CHECK.md`

Thay vì gate đơn giản "lần đầu 1 lần", app mẫu gate Intro theo **số lần mở app** +
**nguồn cài đặt** (ad campaign vs organic) để tối ưu review Google Play.

### Biến & Remote Config

- `goToHomeNumber` — đếm số lần vào Home (SharedPreferences, bắt đầu 1, +1 mỗi lần mở).
- `count_app_open` (default 3) — từ Remote Config.
- `organic_number_not_guide` (default 3) — từ Remote Config.
- `isAdsCampaign` — từ **InstallReferrer** (native), KHÔNG phải remote config.

### Công thức

```kotlin
val goToHomeStatus = if (isAdsCampaign) n >= countAppOpen
                     else n < organic || n >= countAppOpen + organic
// true  → vào Home
// false → hiện Intro
```

### Bảng chân trị (count=3, organic=3)

| Nguồn cài | Lần 1–2 | Lần 3–5 | Lần 6+ |
|---|---|---|---|
| **Ad campaign** | **Intro** | Home | Home |
| **Organic** | Home | **Intro** | Home |

### InstallReferrerHelper — cache 3 tầng

Tạo `core/InstallReferrerHelper.kt` (hoặc copy từ template):

```
1. In-memory (@Volatile cached) — mỗi tiến trình đọc/tính 1 lần.
2. SharedPreferences (is_ads_campaign + ads_campaign_resolved) — bền qua lần mở.
3. InstallReferrer API — chỉ kết nối 1 lần (khi chưa resolved).
```

Quy tắc phân loại:
- có `gclid` → ads
- không có `utm_medium` / `(not set)` → organic
- `utm_medium == "organic"` → organic
- còn lại (cpc/banner/…) → ads
- **Mọi nhánh lỗi → coi là ads=true** (fallback an toàn)

Gọi async trong `MyApplication.onCreate()`:
```kotlin
InstallReferrerHelper.resolve(this)   // async, cache; bỏ qua nếu đã resolve
```

### resolveStartRoute() trong MainActivity

```kotlin
fun resolveStartRoute(): String {
    val n = AppStorage.goToHomeNumber(this)
    AppStorage.setGoToHomeNumber(this, n + 1)
    val countAppOpen = remote.getInt("count_app_open").let { if (it <= 0) 3 else it }
    val organic      = remote.getInt("organic_number_not_guide").let { if (it < 0) 0 else it }
    val isAds        = InstallReferrerHelper.isAdsCampaign(this)
    val goToHomeStatus = if (isAds) n >= countAppOpen
                         else n < organic || n >= countAppOpen + organic
    return if (goToHomeStatus) Screen.Home.route else Screen.Intro.route
}
```

### res/xml/config.xml

Thêm key Remote Config:
```xml
<entry><key>count_app_open</key><value>3</value></entry>
<entry><key>organic_number_not_guide</key><value>3</value></entry>
```

### Test bằng adb

```bash
adb shell pm clear <applicationId>          # reset counter
adb logcat -s InstallReferrer               # xem rawRef + isAds decision
adb shell run-as <applicationId> cat .../shared_prefs/AppStorage.xml  # xem counter
```

### Checklist gate logic

- [ ] InstallReferrer chỉ kết nối 1 lần (cache 3 tầng), async, không block splash.
- [ ] `goToHomeNumber` +1 mỗi lần mở.
- [ ] `count_app_open` + `organic_number_not_guide` đọc từ Remote Config.
- [ ] Fallback `isAdsCampaign = true` khi chưa resolve.
- [ ] Bảng chân trị đúng (test bằng adb).

