# skill_run_lint (Mobile — phase `mobile-screen`)

**Mục tiêu:** Kiểm tra static analysis trước khi báo "xong" 1 story — 0 lỗi mới được coi là qua Gate 3.

> Chỉ dùng cho phase `mobile-screen`. Phase `mobile-shell` verify bằng build native thật — xem `setup_native_shell/SKILL.md`.

## STACK BINDING — điền khi chọn công nghệ mobile

```
<TODO: điền lệnh lint thật>
# Flutter:        flutter analyze
# React Native:   eslint . --ext .js,.jsx,.ts,.tsx
# Native Android: ./gradlew lint
# Native iOS:     swiftlint
```

**Verify:** exit code = 0. Nếu có warning không phải lỗi cứng, ghi rõ trong handoff — không tự ý bỏ qua warning mà không nêu.

**Giới hạn cần biết (đặc thù mobile):** lint chỉ bắt lỗi cú pháp/style. Nó KHÔNG bắt được permission thiếu, native config sai, hay API cần quyền chưa khai trong `shared/capabilities/native.json` — loại lỗi đó chỉ lộ lúc build hoặc chạy trên thiết bị thật. Vì vậy pass skill này KHÔNG đủ để báo "xong": phải cộng `skill_run_unit_test` + verify của `git_workflow`, và nếu story dùng capability native thì đối chiếu lại `native.json` trước khi handoff.
