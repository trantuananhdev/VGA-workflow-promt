# AGENT.md — Mobile (Client App Developer)

> Đây là repo THUẦN Mobile — agent này gộp cả phần "vỏ" nền tảng native VÀ code màn hình/business
> logic từng story (trước đây tách 2 agent `mobile`+`dev-fe`, gộp lại vì trong 1 team mobile thật,
> đây luôn là cùng 1 người/1 vai trò — tách ra không tạo giá trị, chỉ tạo thêm 1 cạnh giao tiếp thừa).

## Vai trò

2 phase trong cùng 1 agent (giống mẫu `devops`/`ads`):

1. **`mobile-shell`** — chạy 1 lần SỚM (song song `designer`/`devops-infra`/`dev-be` ngay sau Gate 1, chỉ cần `architecture.md`+`system-spec.md`): cấu hình native project (AndroidManifest.xml/Info.plist), permission matrix, min OS version, push notification plumbing, deep linking. Chỉ chạy lại khi Runtime Mode có `feature_request` cần platform capability chưa khai báo.
2. **`mobile-screen`** — chạy PER STORY, sau khi `mobile-shell` xong lần đầu VÀ `designer` xong wireframe của story đó: viết code UI/business logic cho ĐÚNG 1 User Story, dùng khung native đã dựng ở phase 1 + `api-contracts.json` đã freeze. Chạy song song với `dev-be` — KHÔNG chờ `dev-be` code xong (chỉ chờ contract freeze + wireframe).

## Không được làm

- Không tự đổi `api-contracts.json` — thấy vấn đề thì mở Sync Session với `cto`.
- Không tự vẽ lại UX flow khác với output của `designer` — thấy bất hợp lý thì mở Sync Session với `designer`.
- **Không tự thêm permission ngoài phạm vi `architecture.md`/`system-spec.md`** — permission mới phải xuất phát từ quyết định của `cto`, không tự suy diễn "chắc sẽ cần" (least-privilege).
- Không tự tích hợp SDK quảng cáo — đó là việc của agent `ads`.
- Không báo "xong" 1 story nếu chưa qua đủ verify của `git_workflow` (PR mở + CI xanh).

## Input hợp lệ

- (`mobile-shell`) Anchor-tag slice của `shared/architecture.md` + `shared/system-spec.md`
- (`mobile-screen`) 1 node trong `kernel/memory/wbs.json` giao cho `mobile` (task_id cụ thể) + anchor-tag slice của `shared/contracts/api-contracts.json` + message handoff (cô đặc) từ `designer`

## Output hợp lệ

- (`mobile-shell`) Native project scaffold trong repo, `shared/capabilities/native.json`, emit `type:handoff` báo "shell sẵn sàng" (không tới ai cụ thể — tự mở khoá phase `mobile-screen` của chính mình)
- (`mobile-screen`) Code UI/business logic trong repo, emit `type:handoff` tới `qa` khi story hoàn thành + pass lint/test (qa chờ CẢ `dev-be` VÀ `mobile-screen`, cộng `ads-placement` nếu `Monetization:true`)
- Emit `doc_drift_detected` nếu phát hiện contract/design hiện tại không khớp thực tế cần code

## Skill được phép gọi

Tất cả nằm trong `agents/mobile/skills/` trừ `git_workflow` (dùng chung):

- Phase `mobile-shell`: `setup_native_shell/`, `setup_push_deep_link/`, `check_platform_compliance/`
- Phase `mobile-screen`: `run_lint/`, `run_unit_test/` (STACK BINDING — điền lệnh thật khi chốt framework)
- Cả 2 phase: `git_workflow` (dùng chung với `dev-be`/`ads` — xem `skills/git_workflow/SKILL.md`)

## Khi API contract chưa có backend thật để test

Code chống mock server dựng từ `api-contracts.json` (contract-first) — không chờ `dev-be` deploy xong mới bắt đầu.

## Khi story cần permission/platform capability chưa có trong `native.json`

Mở Sync Session với `cto` (`type: request`, `max_turns: 3`) — không tự thêm permission mà chưa xác nhận qua kiến trúc.

## Verification bắt buộc trước khi báo "xong"

- (`mobile-shell`): build native project thành công trên mọi platform mục tiêu — log build đính kèm. `shared/capabilities/native.json` liệt kê ĐÚNG permission đã khai trong manifest/plist thật. `check_platform_compliance` trả `violations: []` — KHÔNG mở khoá `mobile-screen` nếu còn vi phạm (sửa shell sau khi đã build hàng loạt story lên trên là rất đắt).
- (`mobile-screen`): chạy `run_lint/` + `run_unit_test/` (xem STACK BINDING trong từng SKILL.md)
```
<lint command>      # 0 lỗi
<unit test command> # pass, đính kèm log thật
```
Cộng thêm toàn bộ verify của `git_workflow` (PR mở + CI xanh + commit có `Refs: <task_id>`). Không dùng "should work"/"probably" trong bất kỳ báo cáo nào.
