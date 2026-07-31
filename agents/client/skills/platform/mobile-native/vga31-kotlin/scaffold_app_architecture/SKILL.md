# skill_scaffold_app_architecture

**Dùng bởi:** `mobile` (phase `client-screen`, SAU `clone_vga31_template` + `setup_host_application`).

**Mục tiêu:** Dựng kiến trúc app theo khuôn mẫu `vga31b-kotlin` — package structure, Hilt DI,
Compose Navigation (single-Activity), MVVM StateFlow, tầng data, Theme.

## Tài liệu tham chiếu BẮT BUỘC ĐỌC

```
shared/quy-trinh-xay-dung-app/09_KIEN_TRUC_APP_vga31b-kotlin.md  (502 dòng — file chính)
shared/quy-trinh-xay-dung-app/01_HANDOFF_NEXT_APP.md  (§1, §2)
```

## 1. Package structure chuẩn

```
<APPLICATION_ID>/
├── MyApplication.kt           ← Điểm tích hợp base-application
├── core/                      ← Activity, storage, locale, shortcut, referrer, IAP opener
├── di/                        ← Hilt module (@Provides Room DB, DAO)
├── data/db/                   ← Room: Entity + DAO
├── data/model/                ← Data class dùng chung
├── data/repo/                 ← Repository (@Singleton @Inject, Dispatchers.IO)
├── firebase/                  ← Remote.kt — facade Remote Config (delegate FirebaseRemoteConfigUtil)
├── platform/                  ← IapLauncher.kt — gọi API tĩnh lib mở IAP
├── advertisement/             ← Lõi ads (copy từ template — xem copy_ads_reusable_components)
├── ui/theme/                  ← MaterialTheme (darkTheme khoá false nếu chưa dark)
├── ui/components/             ← Composable dùng lại (Card, Header, SearchBar...)
├── ui/nav/                    ← Screen.kt (enum route) + AppNavHost.kt
└── ui/screen/<feature>/       ← Mỗi feature 1 package con
```

## 2. Các khối chính

| Khối | Công nghệ | Ghi chú |
|---|---|---|
| UI | Jetpack Compose | Không XML layout (trừ ads) |
| Navigation | Compose Navigation | 1 NavHost, route enum |
| DI | Hilt | @HiltAndroidApp, @AndroidEntryPoint, @HiltViewModel |
| State | StateFlow (KHÔNG LiveData) | MutableStateFlow + collectAsState() |
| Data | Room + SharedPreferences + Repository | Repository chạy IO, trả model đơn giản |
| Ads/IAP/Splash | AAR base-application | App KHÔNG tự viết |

## 3. Quy trình dựng scaffold

```
1. Tạo package structure theo §1.
2. MainActivity.kt: @AndroidEntryPoint, setContent { AppTheme { AppNavHost ; NativeInterHost() } }
   - KHÔNG khai MAIN/LAUNCHER.
3. AppStorage.kt: SharedPreferences wrapper (first_open, language, go_to_home_number...).
4. Screen.kt: enum class Screen(val route: String) { Home("home"), Setting("setting"), ... }
5. AppNavHost.kt: @Composable NavHost với composable() cho mỗi route.
6. Theme.kt: darkTheme = false (khoá cứng nếu chưa dark design).
   ⚠️ isSystemInDarkTheme() + nền trắng = chữ xám không đọc được.
7. di/AppModule.kt: @Provides Room + DAO.
8. Repository: @Singleton, suspend, Dispatchers.IO, trả model.
9. ViewModel: @HiltViewModel, MutableStateFlow, viewModelScope.launch.
10. Composable screen: hiltViewModel(), collectAsState(), NativeAdSlot nếu cần ads.
```

## 4. Pattern tạo feature mới (6 bước lặp lại)

1. **MODEL** — data class (data/model/)
2. **REPOSITORY** — suspend fun, IO, trả model (data/repo/)
3. **ROOM/STORE** — (tuỳ chọn) lưu bền hoặc chuyển tạm singleton RAM
4. **VIEWMODEL** — @HiltViewModel, StateFlow, gọi Repository
5. **UI** — @Composable, collectAsState(), NativeAdSlot/AdManager nếu cần
6. **ROUTE** — thêm enum Screen, composable() trong AppNavHost, nối onClick

## 5. Luồng khởi động

```
OS → MyApplication.onCreate()
       super.onCreate() → lib init → Splash → Inter → Language → IAP
       → getHomeActivity() → MainActivity.onCreate()
       → resolveStartRoute() → Intro hay Home
       → setContent { AppTheme { AppNavHost(startRoute) ; NativeInterHost() } }
```

## 6. i18n

- `values/strings.xml` — config SDK (KHÔNG dịch)
- `values*/strings_i18n.xml` — chuỗi UI (CÓ dịch)
- Đổi ngôn ngữ: `LanguageRouter.confirmLanguageSelection(activity, code, navigate = false)` rồi `recreate()`.

## 7. Gotchas

1. Dark mode: khoá `darkTheme = false`, hardcode Color.White phải sửa nếu muốn dark thật.
2. Nav argument lớn: dùng singleton RAM, không nhồi list.
3. Tên hàm: không trùng stdlib (`parsePositions`, không `parse`).
4. `startDestination`: phải là Home (hoặc Intro), không Splash.

## KHÔNG ĐƯỢC LÀM

- ❌ KHÔNG viết Splash/Language/IAP/Consent.
- ❌ KHÔNG khai MAIN/LAUNCHER cho MainActivity.
- ❌ KHÔNG dùng LiveData (dùng StateFlow).
- ❌ KHÔNG gọi Android SDK từ Composable (đi qua Repository).
- ❌ KHÔNG subclass FirebaseRemoteConfigUtil.
