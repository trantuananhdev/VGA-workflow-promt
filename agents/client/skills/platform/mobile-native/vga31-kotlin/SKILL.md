# stack pack: vga31-kotlin (Android / Kotlin / Compose)

**Nạp khi:** `shared/contracts/tech-stack.json` entry `PROJ` có `platform_pack: "mobile-native"` **và** `stack_pack: "vga31-kotlin"`. Stack Android khác template này (vd Android thuần không dùng `base-application`) thì **không** nạp pack con này — chỉ dùng `../SKILL.md`.

**Mục tiêu:** Dựng app Android mới từ template nội bộ `shared/quy-trinh-xay-dung-app/vga31-kotlin/` (+ AAR `base-application`), theo đúng thứ tự đã được kiểm nghiệm.

---

## Thứ tự bắt buộc — không tự đảo

| # | Skill | Bắt buộc? | Phụ thuộc | Phase | Mô tả |
|---|---|---|---|---|---|
| 1 | `clone_vga31_template/` | ✅ | — | `client-shell` | Clone template, rename package/appId/rootProject.name, verify build |
| 2 | `setup_host_application/` | ✅ | #1 | `client-shell` | `HostApplication` kế thừa `BaseApplication`, override đủ abstract method, tạo resource bắt buộc |
| 3 | `integrate_base_application/` | ✅ | #1 | `client-shell` | Verify Gradle, R8/ProGuard, manifest merge, catalog 11 lỗi thường gặp |
| 4 | `scaffold_app_architecture/` | ✅ | #1, #2 | `client-screen` | Kiến trúc MVVM/Hilt/Navigation/Theme + 6 bước pattern tạo feature mới |
| 5 | `configure_language_screen/` | ❌ | #2 | `client-shell` | Custom màn Language (thư viện đã có màn mặc định — chỉ gọi khi cần UI riêng) |
| 6 | `setup_intro_onboarding/` | ❌ | #2, #4 | `client-screen` | Chèn Intro/Onboarding + gate logic (InstallReferrer + đếm lần mở app) |
| 7 | `qa_release_checklist/` (ở pack cha) | ✅ | #1-#4 | trước release | Checklist QA + adb cheat-sheet, gọi ở cuối |

Luồng runtime của thư viện: `Splash → Inter → Language → IAP → Home`. Chèn bước riêng của app **phải** đi qua pattern `getHomeActivity()` (#6), KHÔNG dựng router song song — đó là nguồn lỗi "2 nguồn sự thật về màn kế tiếp".

## STACK BINDING (ghi đè bảng ở pack cha cho stack này)

```
build      : ./gradlew assembleDebug
lint       : ./gradlew lintDebug detekt
unit test  : ./gradlew testDebugUnitTest
bậc hẹp    : adb shell wm size 320x640
cỡ chữ 200%: adb shell settings put system font_scale 2.0
```

## Swappable

Mỗi skill là 1 `SKILL.md` độc lập: đổi version thư viện hay đổi template thì sửa **đúng** skill tương ứng, không lan sang skill khác. Đổi hẳn stack (vd sang Flutter) thì **không** sửa pack này — tạo stack pack mới cạnh nó, `tech-stack.json` trỏ sang.
