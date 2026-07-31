# skill_run_unit_test (phase `client-screen`)

**Mục tiêu:** Chạy unit/widget test cho đúng phạm vi story đang xử lý trước khi emit handoff sang `qa`.

> Chỉ dùng cho phase `client-screen`. Phase `client-shell` verify bằng build/serve thật của platform pack (mobile: build native + push/deep-link thật; web: build + header/route thật) — xem skill dựng vỏ trong pack.

## LỆNH LẤY TỪ PLATFORM PACK — không hard-code ở đây

```
pack = shared/contracts/tech-stack.json -> entry PROJ (roles chứa `client`) -> platform_pack
lệnh = agents/client/skills/platform/<pack>/SKILL.md, mục 2 "STACK BINDING"
```

Gợi ý theo pack: `mobile-native` → `./gradlew testDebugUnitTest` / `xcodebuild test` / `flutter test`; `web-spa` → `vitest run` (+ `playwright test` cho route).

## STACK BINDING (giữ lại để tham chiếu — bản chuẩn ở pack)

```
<TODO: điền lệnh test thật>
# Flutter:        flutter test
# React Native:   jest
# Native Android: ./gradlew test
# Native iOS:     xcodebuild test -scheme <scheme> -destination <simulator>
```

**Verify:** toàn bộ test liên quan story phải pass, đính kèm log thật vào handoff envelope — không tóm tắt bằng lời "tests pass". Nếu dùng mock server (chống `api-contracts.json`) do `dev-be` chưa xong, phải nêu rõ trong handoff là đã test với mock, chưa phải integration thật (integration thật diễn ra ở bước `qa`).
