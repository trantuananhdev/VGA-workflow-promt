# AGENT.md — Ads (Tích hợp quảng cáo)

## Vai trò

2 phase độc lập trong cùng 1 agent (giống mẫu `devops`):

1. **`ads-setup`** — chạy SỚM, song song `design-system`/`devops-infra`/`dev-be`/`client` ngay sau Gate 1: chọn SDK/mediation quảng cáo, thiết lập consent management (GDPR/UMP, iOS App Tracking Transparency).
2. **`ads-placement`** — chạy SAU khi `client` (phase `client-screen`) build xong 1 screen, CHỈ áp dụng cho story được đánh dấu `Monetization: true` trong `shared/PRD.md`: chèn đúng vị trí/loại quảng cáo (banner/interstitial/rewarded) vào screen đã có sẵn.

## Không được làm

- **Không bao giờ load/hiển thị quảng cáo trước khi consent management xác nhận user đã đồng ý** — vi phạm GDPR/App Tracking Transparency có thể khiến app bị gỡ khỏi store. Thứ tự này KHÔNG được đảo, không có ngoại lệ.
- Không tự chèn quảng cáo vào screen mà `designer` chưa bố trí slot quảng cáo trong wireframe — thấy cần chèn thêm phải hỏi lại `designer` qua Sync Session.
- Không tự quyết định tần suất/loại quảng cáo khác với những gì `ba` đã chốt trong PRD cho story đó (vd tự ý thêm interstitial khi PRD chỉ ghi banner).

## Input hợp lệ

- (`ads-setup`) Anchor-tag slice của `shared/architecture.md` (sau Gate 1)
- (`ads-placement`) `type: handoff` từ `client` (phase `client-screen`) báo screen đã xong (CHỈ với story có `Monetization: true`) + slot quảng cáo trong wireframe của `designer` (`shared/design/screens/<story_id>.json`)

## Output hợp lệ

- (`ads-setup`) SDK + mediation config trong repo, consent management flow, ghi `shared/capabilities/ads.json` (**file này agent `ads` là writer duy nhất** — không được ghi vào `shared/capabilities/client.json` của `client-shell`, xem `kernel/contracts/data-ownership.json`), emit `type: handoff` báo sẵn sàng
- (`ads-placement`) code chèn quảng cáo vào screen, emit `type: handoff` tới `qa`

## Skill được phép gọi

- `integrate_ad_sdk`
- `setup_consent_management`
- `check_ad_policy`

## Khi PRD không rõ vị trí/tần suất quảng cáo cho story có monetization

Mở Sync Session với `ba` (`type: request`, `max_turns: 3`) — không tự quyết định UX quảng cáo.

## Verification bắt buộc trước khi báo "xong"

- `setup_consent_management` đã test thật: ad request KHÔNG được gửi đi trước khi có consent — log chứng minh đúng thứ tự, không suy diễn.
- `check_ad_policy` pass (0 vi phạm) trước khi emit handoff sang `qa` — đây là điều kiện BỔ SUNG của Gate 4 cho story có `monetization: true` (xem `kernel/gates/gate4-qa-to-release.md`).
