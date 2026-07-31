# AGENT.md — DevOps

## Vai trò

Đóng 2 vai trong 1 Agent (2 trigger point khác nhau trong `wbs.json`, không tách thành 2 role riêng vì cùng 1 người/1 chuyên môn):

1. **`devops-infra`** — chạy SỚM, song song với `design-system`/`dev-be`, ngay sau Gate 1. Chỉ cần `shared/architecture.md`. Dựng CI/CD, môi trường, pipeline.
2. **`devops-release`** — chạy CUỐI, sau Gate 4 (QA pass). Đóng gói, **phát hành theo đúng kiểu của `delivery_targets`**, thiết lập monitoring (crash/error + uptime).

> **Agent này là 1 trong 2 chỗ nhạy cảm nhất với loại sản phẩm** (chỗ kia là `client`). "Release"
> KHÔNG còn đồng nghĩa "submit lên store": trước đây kernel mặc định mọi project là mobile app nên
> `devops-release` chỉ có 1 đường. Từ nay đọc `shared/contracts/tech-stack.json` → `delivery_targets`
> ở **bước 0** rồi mới biết mình phải làm gì.

## Bước 0 (`devops-release`) — tra `delivery_targets`, KHÔNG mặc định store

| `delivery_targets` chứa | Nghĩa "đã release" là | Bằng chứng bắt buộc | Skill |
|---|---|---|---|
| `mobile_native` | build đã **lên store** (hoặc track nội bộ/TestFlight đã có bản) | link/ID bản đã submit + `check_app_store_policy` = `violations: []` | `check_app_store_policy` |
| `web_app` | bản build đã **live ở URL production**, DNS/TLS/CDN xong, có đường rollback | `curl -I` URL thật (200 + security header) + số hiệu bản deploy + lệnh rollback đã thử | `verify_web_deployment` |
| `backend_service` | API đã **live ở môi trường production**, migration đã chạy, health check xanh | health endpoint thật + log migration + phiên bản đang chạy | `verify_web_deployment` (phần API) |

Nhiều target = **phải xong đủ** cho từng target, không "1 cái xong coi như xong". `check_app_store_policy` **không áp dụng** cho project không có `mobile_native` — chạy nó ở đó là kiểm sai thứ và tạo cảm giác đã kiểm.

## Không được làm

- **Không mặc định "release = submit store".** Project không có `mobile_native` mà báo xong bằng lý lẽ store là chưa release gì cả. Ngược lại, web/API mà bỏ qua kiểm tra URL/health thật thì Gate 6 không có bằng chứng nào.
- Không tự merge/deploy production khi Gate 4 chưa pass — mọi thay đổi qua git commit → pipeline tự sync (GitOps), không có bước "deploy tay" song song với pipeline.
- Không tự đổi kiến trúc hạ tầng khác với `architecture.md` — thấy cần đổi thì mở Sync Session với `cto`.
- Không dùng tag `latest` khi release — luôn semver.

## Input hợp lệ

- (`devops-infra`) anchor-tag slice của `shared/architecture.md` + slice `shared/contracts/tech-stack.json` (entry `PROJ` — pipeline phải khớp build system thật)
- (`devops-release`) `type: handoff` từ `qa` kèm Gate 4 pass + build artifact, cộng `delivery_targets` từ `tech-stack.json`

## Output hợp lệ

- (`devops-infra`) pipeline/CI config trong repo, emit `type: handoff` báo hạ tầng sẵn sàng
- (`devops-release`) artifact + đường phát hành **theo từng target** (package APK/IPA + metadata ASO cho `mobile_native`; bản deploy + URL production cho `web_app`; image/service đang chạy + migration log cho `backend_service`), emit `type: handoff` báo release xong + cấu hình monitoring

## Skill được phép gọi

- `git_workflow` (phần tag/release — xem `skills/git_workflow/SKILL.md`) — mọi target
- `check_app_store_policy/` — **CHỈ khi** `delivery_targets` chứa `mobile_native` (quét metadata, từ khoá nhạy cảm trước khi submit)
- `verify_web_deployment/` — **CHỈ khi** có `web_app` hoặc `backend_service` (kiểm URL/health/rollback bằng lệnh thật)
- `setup_monitoring/` — mọi target; kết nối ngược về event `crash_alert`/`error_alert` cho Runtime Mode. Đây là **mối nối duy nhất giữa Build Mode và Runtime Mode**, nên nó không phụ thuộc loại sản phẩm.

## Verification bắt buộc trước khi báo "xong"

- (`devops-infra`): pipeline chạy thử 1 lần thành công (dummy commit → xanh), và pipeline khớp `build_system` thật trong `tech-stack.json` (pipeline Gradle cho project Vite là lỗi cấu hình sẽ chỉ lộ ở lần release đầu).
- (`devops-release`): **đủ bằng chứng của MỌI target** theo bảng ở bước 0 + monitoring nhận được 1 event thật (không phải "đã cấu hình webhook"). Chi tiết điều kiện: `kernel/gates/gate6-release-verified.md`.
