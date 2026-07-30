# TTS — Tài liệu đào tạo dev Kotlin/Android (dựa trên app mẫu vga31b-kotlin)

Bộ tài liệu này dạy **kiến trúc & cách xây một app Android (Kotlin + Compose)** dựa trên app mẫu
`vga31b-kotlin`, KHÔNG đề cập tới quy trình chuyển đổi từ React Native hay các cơ chế mã hoá/obfuscate
mã nguồn khi build release — những phần đó đã được lược bỏ vì không cần thiết cho người mới học kiến trúc.

Project `vga31b-kotlin` (đầy đủ mã nguồn) vẫn để **riêng**, không copy vào đây — chỉ đọc tài liệu ở đây rồi
mở trực tiếp source code tại `vga49a/vga31b-kotlin/` khi cần đối chiếu.

## Thứ tự đọc khuyến nghị

1. `01_HANDOFF_NEXT_APP.md` — tổng quan kiến trúc chung + các gotcha thực chiến quan trọng nhất.
2. `09_KIEN_TRUC_APP_vga31b-kotlin.md` — **đọc kỹ file này** — cấu trúc thư mục/package, luồng điều hướng, tầng dữ liệu, ví dụ xây 1 chức năng mới từ đầu đến cuối.
3. `02_PLAYBOOK_TICH_HOP.md` + `08_HUONG_DAN_TICH_HOP_base-application.md` — cách tích hợp thư viện `base-application` (splash/ads/IAP/consent/notification có sẵn) vào app.
4. `10_MIGRATE_ADS_TO_LIB.md` — nếu cần chuyển ads đang gọi trực tiếp SDK Google sang dùng lib.
5. `03_ADS.md` → `04_INTRO_CHECK.md` → `05_ADS_RUNTIME_LESSONS.md` → `06_ADS_REUSABLE_COMPONENTS.md` — chi tiết tầng quảng cáo (điều phối tần suất, logic Intro, bài học vận hành, thành phần dùng lại được).
6. `07_CHECKLIST.md` — checklist mẫu trước khi phát hành (tham khảo, không cần làm đúng số liệu của app mẫu).

## Ghi chú
- Project mẫu `vga31b-kotlin` để nguyên, không đụng vào — mọi trích dẫn file/class trong tài liệu đều trỏ vào đó.
- Tài liệu ở đây là bản đã lược bớt phần "port từ React Native" và phần "mã hoá/obfuscate khi build" so với tài liệu gốc trong `vga31b-kotlin/docs/` — vì hai phần đó không cần cho việc học kiến trúc & tự xây app Kotlin mới.
