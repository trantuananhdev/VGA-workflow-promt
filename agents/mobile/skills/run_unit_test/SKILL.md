# skill_run_unit_test (Mobile — phase `mobile-screen`)

**Mục tiêu:** Chạy unit/widget test cho đúng phạm vi story đang xử lý trước khi emit handoff sang `qa`.

> Chỉ dùng cho phase `mobile-screen`. Phase `mobile-shell` verify bằng build native thật + push/deep-link test thật — xem `setup_native_shell/SKILL.md` và `setup_push_deep_link/SKILL.md`.

## STACK BINDING — điền khi chọn công nghệ mobile

```
<TODO: điền lệnh test thật>
# Flutter:        flutter test
# React Native:   jest
# Native Android: ./gradlew test
# Native iOS:     xcodebuild test -scheme <scheme> -destination <simulator>
```

**Verify:** toàn bộ test liên quan story phải pass, đính kèm log thật vào handoff envelope — không tóm tắt bằng lời "tests pass". Nếu dùng mock server (chống `api-contracts.json`) do `dev-be` chưa xong, phải nêu rõ trong handoff là đã test với mock, chưa phải integration thật (integration thật diễn ra ở bước `qa`).
