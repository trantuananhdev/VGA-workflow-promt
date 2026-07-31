# skill_clone_vga31_template

**Dùng bởi:** `mobile` (riêng — phase `client-shell`).

**Mục tiêu:** Clone template Android project `VGA-workflow-promt\shared\quy-trinh-xay-dung-app\vga31-kotlin` ra một folder mới, rename
package/applicationId/rootProject.name, đảm bảo project build được trên Android Studio
trước khi bắt tay vào viết code app mới.

## Template gốc

```
shared/quy-trinh-xay-dung-app/vga31-kotlin/
├── app/                        # Module chính (Kotlin + Compose)
│   ├── build.gradle.kts        # Plugins, namespace, dependencies
│   ├── proguard-rules.pro      # R8/ProGuard (đã có rule cho lib + mediation)
│   ├── google-services.json    # Firebase config (CẦN THAY cho app mới)
│   └── src/main/
│       ├── AndroidManifest.xml # Permissions, meta-data, Application class
│       ├── assets/default_ads_config.json  # Ad unit config
│       ├── java/com/...        # Source code Kotlin
│       └── res/                # Resources (drawable, values, layout, raw...)
├── base-application/           # Module phẳng chứa AAR + transitive deps
│   ├── base-application-1.0.0.aar
│   ├── build.gradle            # Flat module exposing AAR
│   └── HUONG_DAN_TICH_HOP.md  # Tài liệu tích hợp đầy đủ (1302 dòng)
├── gradle/
│   ├── libs.versions.toml      # Version catalog (AGP 8.12.0, Kotlin 2.1.20, Hilt, Room...)
│   └── wrapper/                # Gradle wrapper 
├── build.gradle.kts            # Root plugins (google-services, crashlytics)
├── settings.gradle.kts         # Plugin management + include :app, :base-application
├── gradle.properties           # JVM args, R8 fullMode=false, nonTransitiveRClass
├── gradlew / gradlew.bat       # Gradle wrapper scripts
└── .gitignore
```

## Input bắt buộc

| Tham số | Mô tả | Ví dụ |
|---|---|---|
| `NEW_APP_DIR` | Đường dẫn folder mới (tuyệt đối hoặc tương đối từ workspace root) | `android-app` hoặc `c:\projects\my-new-app` |
| `APPLICATION_ID` | applicationId mới | `com.example.mynewapp` |
| `APP_NAME` | Tên app hiển thị | `My New App` |
| `ROOT_PROJECT_NAME` | Tên project trong settings.gradle.kts | `My New App` |

## Input tuỳ chọn

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `MIN_SDK` | `28` | minSdk (tối thiểu 28, yêu cầu của base-application) |
| `TARGET_SDK` | `35` | targetSdk |
| `COMPILE_SDK` | `35` | compileSdk |
| `JAVA_VERSION` | `17` | JVM target |

## Quy trình

```
1. COPY toàn bộ nội dung template vào NEW_APP_DIR.
   - Copy: gradlew, gradlew.bat, gradle/, build.gradle.kts, settings.gradle.kts,
     gradle.properties, .gitignore, app/, base-application/ (gồm .aar + build.gradle + docs).
   - KHÔNG copy: screenshoot/, .idea/, .gradle/, build/, *.iml.
   - Giữ nguyên quyền execute của gradlew (chmod +x nếu trên macOS/Linux).

2. RENAME package / applicationId trong folder mới:
   a) app/build.gradle.kts:
      - namespace = "APPLICATION_ID"
      - applicationId = "APPLICATION_ID"
      - Xoá hoặc comment khối signingConfigs.release{} (keystore của app cũ).
      - Reset versionCode = 1, versionName = "1.0.0".
   b) settings.gradle.kts:
      - rootProject.name = "ROOT_PROJECT_NAME"
   c) app/src/main/AndroidManifest.xml:
      - android:name giữ ".MyApplication" (hoặc tên HostApplication mới).
      - android:label = "@string/app_name"
      - Xoá quyền đặc thù của app cũ (QUERY_ALL_PACKAGES, PACKAGE_USAGE_STATS,
        REQUEST_DELETE_PACKAGES) — chỉ giữ quyền bắt buộc cho lib:
        FOREGROUND_SERVICE, FOREGROUND_SERVICE_SPECIAL_USE, POST_NOTIFICATIONS,
        AD_ID, INTERNET, ACCESS_NETWORK_STATE, RECEIVE_BOOT_COMPLETED.
   d) Đổi tên thư mục source java/com/... cho khớp APPLICATION_ID.
      Ví dụ: com.supportsoftware.checkerpro → com.example.mynewapp.
   e) Thay package declaration ở đầu mọi file .kt trong app/src/main/java/...
   f) Thay toàn bộ import cũ "com.supportsoftware.checkerpro" → APPLICATION_ID
      trong mọi file .kt và .xml.

3. CẬP NHẬT resources:
   a) res/values/strings.xml: app_name = APP_NAME.
   b) res/values/colors.xml: giữ nguyên hoặc thay primaryColor/accentTone theo brief.
   c) Thay google-services.json bằng file của project Firebase mới.
      - Nếu chưa có, để placeholder và ghi TODO.
   d) assets/default_ads_config.json: giữ nguyên cấu trúc, thay ad unit id khi có.
   e) app/proguard-rules.pro:
      - Dòng "-keep class com.supportsoftware.checkerpro.data.**" → APPLICATION_ID.data.**

4. VERIFY BUILD:
   cd NEW_APP_DIR
   ./gradlew :app:assembleDebug
   - Build PHẢI thành công (exit code 0). Nếu fail:
     - Thiếu google-services.json → tạo placeholder hoặc tắt plugin tạm.
     - Lỗi package name → kiểm tra lại bước 2.
     - Missing resource → kiểm tra res/ đã copy đủ.

5. GHI NHẬN output:
   - Log build thành công đính kèm.
   - Nếu có bug vặt (warning, deprecated API), ghi danh sách vào output nhưng
     KHÔNG chặn kết luận "đã clone xong".
```

## Lưu ý quan trọng

- **KHÔNG sửa `base-application/`**: module này giữ nguyên y hệt template (AAR +
  build.gradle + docs). Mọi thay đổi chỉ nằm ở `app/`.
- **KHÔNG đổi version trong `gradle/libs.versions.toml`** trừ khi có lý do rõ ràng
  (AGP 8.12.0 + Kotlin 2.1.20 + KSP 2.1.20-1.0.32 đã được kiểm tra tương thích).
- **Keystore**: KHÔNG commit keystore vào repo. Thư mục `app/keystore/` đã gitignored.
- **R8 fullMode**: `gradle.properties` đã set `android.enableR8.fullMode=false` — KHÔNG
  bật lại (gây ClassCastException/list rỗng ở bản release khi dùng Retrofit/Gson).

## Output

- Folder `NEW_APP_DIR` chứa project Android build-ready.
- Emit `type:handoff` nội bộ agent, mở khoá cho các skill tiếp theo:
  `setup_host_application`, `integrate_base_application`, `configure_ads_iap`.

## Tài liệu tham chiếu (ĐỌC trước khi thực hiện)

- Template gốc: `shared/quy-trinh-xay-dung-app/vga31-kotlin/`
- Hướng dẫn tích hợp AAR: `shared/quy-trinh-xay-dung-app/vga31-kotlin/base-application/HUONG_DAN_TICH_HOP.md`
- Tổng quan kiến trúc: `shared/quy-trinh-xay-dung-app/01_HANDOFF_NEXT_APP.md`
- Kiến trúc chi tiết: `shared/quy-trinh-xay-dung-app/09_KIEN_TRUC_APP_vga31b-kotlin.md`
