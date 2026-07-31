# skill_run_lint (phase `client-screen`)

**Mục tiêu:** Kiểm tra static analysis trước khi báo "xong" 1 story — 0 lỗi mới được coi là qua Gate 3.

> Chỉ dùng cho phase `client-screen`. Phase `client-shell` verify bằng **build/serve thật** của platform pack — xem skill dựng vỏ của pack (`setup_native_shell/` hoặc `setup_web_shell/`).

## LỆNH LẤY TỪ PLATFORM PACK — không hard-code ở đây

```
pack = shared/contracts/tech-stack.json -> entry PROJ (roles chứa `client`) -> platform_pack
lệnh = agents/client/skills/platform/<pack>/SKILL.md, mục 2 "STACK BINDING"
       (stack pack ghi đè pack cha nếu có, vd platform/mobile-native/vga31-kotlin/)
```

Vì sao **không** để danh sách lệnh ở đây: skill này platform-agnostic, còn lệnh thì thuộc nền tảng. Giữ 2 nơi khai lệnh (ở đây + ở pack) là đúng lớp lỗi "2 nguồn sự thật" mà cả `manifest.depends_on` và `process-table.json` đã bị bỏ vì nó. Gợi ý theo pack: `mobile-native` → `./gradlew lintDebug detekt` / `swiftlint` / `flutter analyze`; `web-spa` → `eslint . --max-warnings=0`.

**Verify:** exit code = 0. Nếu có warning không phải lỗi cứng, ghi rõ trong handoff — không tự ý bỏ qua warning mà không nêu.

**Giới hạn cần biết — lint KHÔNG bắt được lớp lỗi nào:** nó chỉ soi cú pháp/style. Nó **không** thấy: quyền thiếu hoặc cấu hình vỏ sai (`shared/capabilities/client.json`), `on_null`/`text_overflow`/`disabled_when` bị bỏ trong hợp đồng layout, và **vỡ bố cục ở bề rộng nhỏ nhất hoặc cỡ chữ 200%**. Cả 3 chỉ lộ khi chạy thật trên thiết bị/browser. Vì vậy pass skill này KHÔNG đủ để báo "xong": phải cộng `run_unit_test`, checklist đếm của `implement_screen_contract`, lần chạy thật ở bậc hẹp nhất + cỡ chữ 200% (lệnh ở mục 2 của pack), và verify của `git_workflow`.
