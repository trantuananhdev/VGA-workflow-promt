# skill_configure_language_screen

**Dùng bởi:** `mobile` (riêng — phase `mobile-shell`, TUỲ CHỌN).

**Mục tiêu:** Cấu hình màn chọn ngôn ngữ — dùng màn mặc định của thư viện HOẶC thay bằng
màn Language riêng của app. Skill này chỉ cần gọi khi app muốn custom UI Language.

## Tiền đề

- `setup_host_application` đã chạy xong.

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

```
shared/quy-trinh-xay-dung-app/vga31-kotlin/base-application/HUONG_DAN_TICH_HOP.md  (§8.2)
```

## Lựa chọn

### Option A: Dùng màn Language mặc định (KHÔNG CẦN LÀM GÌ THÊM)

Thư viện đã có sẵn màn chọn ngôn ngữ. Khi user chọn xong, thư viện gọi
`notifyLanguageSaved(languageCode)` trên HostApplication. Chỉ cần implement hàm đó:

```kotlin
override fun notifyLanguageSaved(languageCode: String) {
    getSharedPreferences(packageName, MODE_PRIVATE).edit()
        .putString("language_pres", languageCode).apply()
}
```

### Option B: Màn Language riêng — Cách `customActivityClass` (khuyên dùng)

```kotlin
// HostApplication.onCreate()
LanguageRouter.customActivityClass = MyLanguageActivity::class.java
super.onCreate()
```

```kotlin
// MyLanguageActivity.kt
class MyLanguageActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_my_language)

        binding.btnDone.setOnClickListener {
            val selectedCode = adapter.selectedCode
            LanguageRouter.confirmLanguageSelection(this, selectedCode)
        }
    }
}
```

### Option C: Màn Language riêng — Cách `launcher` (toàn quyền)

```kotlin
// HostApplication.onCreate()
LanguageRouter.launcher = LanguageScreenLauncher { activity, nextScreen ->
    val intent = Intent(activity, MyLanguageActivity::class.java)
    nextScreen?.let { intent.putExtra("next_screen", it.name) }
    activity.startActivity(intent)
}
super.onCreate()
```

```kotlin
// MyLanguageActivity — khi user xong:
val nextScreen = intent.getStringExtra("next_screen")
    ?.let { Class.forName(it) as Class<out Activity> }
LanguageRouter.confirmLanguageSelection(this, selectedCode, nextScreen = nextScreen)
```

⚠️ Với cách C PHẢI truyền `nextScreen` vào `confirmLanguageSelection`. Bỏ qua = bỏ qua IAP.

### Đổi ngôn ngữ từ Settings (không phải lần đầu)

```kotlin
LanguageRouter.confirmLanguageSelection(activity, selectedCode, navigate = false)
// Sau đó tự recreate()/refresh UI nếu cần
```

### Preload native ad cho màn Language

- Lib TỰ preload vào `TemporaryStorage.preloadedLanguageNativeAd`.
- Custom LanguageActivity CHỈ CẦN ĐỌC (read-and-clear pattern):

```kotlin
val preloaded = TemporaryStorage.preloadedLanguageNativeAd
TemporaryStorage.preloadedLanguageNativeAd = null

if (preloaded != null) {
    bindInstantly(preloaded)       // hot path — không shimmer
} else {
    loadInlineWithShimmer()        // fallback
}
```

## KHÔNG ĐƯỢC LÀM

- ❌ Đừng tự gọi `Locale.setDefault` / `Configuration.setLocale`.
- ❌ Đừng tự ghi prefs ngôn ngữ của lib.
- ❌ Đừng `finish()` Splash từ tay bạn.
- ❌ Đừng bind NativeAd 2 lần.
- ❌ Đừng giữ reference dài hạn tới `preloadedLanguageNativeAd`.
- ❌ Đừng ghi vào `preloadedLanguageNativeAd` — host chỉ đọc-xong-xoá.
- ❌ Đừng đặt MAIN/LAUNCHER trên MyLanguageActivity.

## Pitfall

Nếu user thoát màn Language mà KHÔNG gọi `confirmLanguageSelection`, lần mở app sau
lib sẽ lặp lại Splash → Language. Fix: gọi `confirmLanguageSelection(this, "en")` ở
handler back, hoặc disable back.

## Output

- Luồng ngôn ngữ hoạt động: chọn → áp locale → IAP → Home.
- Đổi ngôn ngữ từ Settings không restart từ Splash.
