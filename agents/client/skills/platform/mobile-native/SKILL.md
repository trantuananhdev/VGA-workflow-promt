# platform pack: mobile-native

**`delivery_target`:** `mobile_native` · **Dùng bởi:** `client` (cả 2 phase), nạp ở bước 0.

**Phạm vi:** app chạy trên thiết bị, phân phối qua store (Google Play / App Store). Stack cụ thể (Kotlin/Compose, Swift/SwiftUI, Flutter) lấy từ `shared/contracts/tech-stack.json`; pack này giữ phần **đúng cho mọi mobile native**, phần đặc thù 1 stack nằm ở **stack pack** con.

**Stack pack có sẵn:** `vga31-kotlin/` — Android/Kotlin dựng từ template nội bộ `shared/quy-trinh-xay-dung-app/vga31-kotlin/`. Chỉ nạp khi `tech-stack.json` chốt Android/Kotlin **và** `stack_pack: "vga31-kotlin"`. iOS/Flutter chưa có stack pack → bootstrap `draft` theo `../SKILL.md` bước 3.

---

## 1. Vỏ gồm những gì (`client-shell`) — mỗi dòng phải có bằng chứng kiểm được

| Thành phần | Skill | Bằng chứng "đã dựng" |
|---|---|---|
| Native project scaffold, min OS, target SDK | `setup_native_shell/` | build log thành công + file manifest/plist thật trong repo |
| Permission matrix (least-privilege, mỗi quyền trỏ 1 story) | `setup_native_shell/` | `shared/capabilities/client.json` khớp 100% manifest/plist thật |
| Push notification + deep link plumbing | `setup_push_deep_link/` | log nhận 1 push thật + mở 1 deep link thật trên thiết bị/emulator |
| Ngưỡng kỹ thuật nền tảng hiện hành | `check_platform_compliance/` | `violations: []` (điều kiện Gate 3 của `client-shell`) |
| Checklist trước phát hành | `qa_release_checklist/` | gọi ở cuối, trước khi `devops-release` submit |

Với stack `vga31-kotlin`, thứ tự dựng vỏ + kiến trúc nằm ở `vga31-kotlin/SKILL.md` — **chạy theo đúng thứ tự đó**, không tự đảo.

## 2. STACK BINDING — điền theo `tech-stack.json`, KHÔNG hard-code trong `run_lint`/`run_unit_test`

| Việc | Android/Kotlin (Gradle) | iOS/Swift (SPM/Xcode) | Flutter |
|---|---|---|---|
| build | `./gradlew assembleDebug` | `xcodebuild -scheme <s> build` | `flutter build apk --debug` |
| lint | `./gradlew lintDebug detekt` | `swiftlint` | `flutter analyze` |
| unit test | `./gradlew testDebugUnitTest` | `xcodebuild test -scheme <s>` | `flutter test` |
| bậc hẹp nhất | emulator 320dp (`adb shell wm size`) | iPhone SE simulator | `flutter run -d <small>` |
| cỡ chữ 200% | `adb shell settings put system font_scale 2.0` | Accessibility Inspector → AX text size max | thiết lập OS như 2 cột trên |

2 dòng cuối **không** phải tuỳ chọn: chúng là cách duy nhất bắt được lớp lỗi mà `responsive`/`text_overflow` trong hợp đồng layout sinh ra để chặn — lint và unit test không bao giờ thấy chúng.

## 3. Map `type` (hợp đồng layout) → widget thật

| `type` | Compose | SwiftUI | Flutter |
|---|---|---|---|
| `section`/`column` | `Column` | `VStack` | `Column` |
| `row` | `Row` (`FlowRow` khi `wrap_behavior`) | `HStack` (`ViewThatFits`) | `Row`/`Wrap` |
| `list` | `LazyColumn` | `List` | `ListView.builder` |
| `grid` | `LazyVerticalGrid` | `LazyVGrid` | `GridView` |
| `card` | `Card` | `GroupBox`/custom | `Card` |
| `text`/`badge` | `Text` (+`maxLines`,`overflow`) | `Text` (+`lineLimit`) | `Text` (+`maxLines`,`overflow`) |
| `input`/`search_field` | `TextField` | `TextField` | `TextFormField` |
| `sheet`/`dialog`/`snackbar` | `ModalBottomSheet`/`AlertDialog`/`Snackbar` | `.sheet`/`.alert`/toast custom | `showModalBottomSheet`/`AlertDialog`/`SnackBar` |
| `app_bar`/`bottom_nav`/`tab_bar` | `TopAppBar`/`NavigationBar`/`TabRow` | `NavigationStack`/`TabView` | `AppBar`/`BottomNavigationBar`/`TabBar` |
| `progress_indicator`/`skeleton` | `CircularProgressIndicator`/shimmer | `ProgressView`/redacted | `CircularProgressIndicator`/shimmer |
| `ad_slot` | view của ads SDK — **KHÔNG** tự dựng, dùng đúng slot `ads-placement` chèn | như trên | như trên |

## 4. Thực hiện `responsive` / `safe_area` / `text_overflow`

| Hợp đồng khai | Làm đúng | Làm SAI (không lint/test nào bắt) |
|---|---|---|
| `min_height_dp: null` | để nội dung tự cao (`wrapContentHeight` / `.fixedSize(vertical:)`) | `Modifier.height(56.dp)` cứng → cắt chữ ở font_scale 2.0 |
| `wrap_behavior` | `FlowRow` / `ViewThatFits` / `Wrap`, hoặc `weight` chia phần | `Row` cứng + `width` cố định → tràn ngang ở 320dp |
| `safe_area` với khối `pinned` | `Modifier.windowInsetsPadding` / `.safeAreaInset` / `SafeArea` | padding số cứng → CTA nằm dưới gesture bar/notch |
| `text_overflow.max_lines` | `maxLines` + `overflow` đúng `behavior` | để mặc định → tên dài đẩy vỡ bố cục |
| bậc rộng (tablet/foldable) nếu layout khai | đổi `grid` số cột / master-detail theo bậc | phóng to layout điện thoại → cột chữ dài quá 75 ký tự |

## 5. Compliance + capability

- `check_platform_compliance/` phải trả `violations: []` **trước khi** `client-screen` bắt đầu — sửa vỏ sau khi đã build N story lên trên là đắt nhất trong cả pipeline (đây là điều kiện phase-specific của Gate 3).
- `shared/capabilities/client.json`: điền `target: "mobile_native"`, mảng `permissions` (mỗi quyền có `story_id` + `reason` — quyền không story nào cần thì **phải gỡ**), `min_os`, `target_sdk`, `push_notification`, `deep_linking`. File này là **bản khai của vỏ thật**, không phải bản mong muốn: lệch với manifest/plist = coi như chưa xong.
- Ngưỡng min/target SDK và policy store **thay đổi theo thời gian** — pack này không ghim con số, `check_platform_compliance/SKILL.md` chịu trách nhiệm tra ngưỡng hiện hành. Ghim số ở đây sẽ lặng lẽ hết hạn.
- **SUY ĐOÁN chưa có spec chống lưng** (đọc lại khi review): cột Flutter/iOS ở mục 2-3 viết theo quy ước phổ biến, chưa được chạy thật trong repo này; chỉ nhánh Android/Kotlin đã có đường chạy thật qua `vga31-kotlin/`.
