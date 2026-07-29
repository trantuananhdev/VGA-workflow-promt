# Mobile Factory OS — Workspace này là gì

Đây là "OS prompt" (khung kiến trúc) cho hệ thống multi-agent đưa 1 ý tưởng **mobile app** từ Client tới khi lên chợ, và duy trì mãi về sau — vận hành hoàn toàn bằng file `.md`/`.json`.

> **Repo này THUẦN Mobile.** Web-application dùng repo riêng — vì `devops` (submit App Store/Play Store vs deploy hosting/CDN), client-side stack, và quy trình release khác nhau về bản chất, nhét chung 1 repo sẽ buộc nhiều agent phải rẽ nhánh theo loại project bên trong.
>
> Không có agent `dev-fe` — vai trò client-side do `mobile` đảm nhiệm với 2 phase (`mobile-shell` + `mobile-screen`), vì trong 1 team mobile thật đó luôn là cùng 1 người.

**Đọc theo thứ tự này khi bắt đầu:**

1. [`ORCHESTRATOR.md`](ORCHESTRATOR.md) — kernel prompt, đọc đầu tiên và duy nhất nếu bạn đóng vai Orchestrator. **§7 Event Loop 2 pha** là trái tim của tầng điều phối.
2. `kernel/memory/wbs.json` — **BẢNG TIẾN TRÌNH DUY NHẤT** của scheduler. Mỗi node có `status`/`gate`; capacity đếm từ đây, không có file trạng thái thứ 2.
3. `kernel/contracts/dag.json` — **bản máy đọc** của DAG (Gate 0/Gate 2 lookup vào đây). `kernel/rules/routing-table.md` là bản giải thích cho người — 2 file phải khớp.
4. `kernel/contracts/` — **2 contract đối xứng**: `message.schema.json` + `message-examples.md` (agent→kernel; 3 field then chốt `node_id`/`processed_at`/`message_id`) và `boot-context.schema.json` (kernel→agent). Cùng với `data-ownership.json` (single-writer) và `dag.json`.
5. `kernel/rules/` — `scheduling-policy.md` (ưu tiên từng pha, capacity), `handoff-contracts.md` (mỗi cạnh truyền field gì), `routing-table.md`, `ssot-precedence.md`.
6. `kernel/gates/` — **7 Gate** (0-6), mỗi file nêu chính xác điều kiện pass + hành động khi fail. Số gate đánh theo thứ tự tạo ra, không theo DAG: thứ tự chạy thực tế là `gate0` (mọi dispatch) → `gate1` (cto) → `gate2` (sau `generate_wbs`) → `gate5` (designer) → `gate3` (dev-be/mobile/ads) → `gate4` (qa) → `gate6` (release).
7. `kernel/memory/project-profile.json` — capability-agent nào active cho project HIỆN TẠI. Do `po` ghi lúc intake.
8. `agents/_template/` — khuôn mẫu tạo agent mới. **8 agent core**: `po`, `ba`, `cto`, `designer`, `dev-be`, `mobile`, `devops`, `qa`. **1 capability-agent** (`core:false`): `ads`.
9. `shared/` — SSOT nghiệp vụ (`PRD.md`, `architecture.md`, `db-schema.md`, `system-spec.md`, `contracts/api-contracts.json`, `capabilities/native.json`, `capabilities/ads.json`) — **anchor tag `<!-- tier:2 role:... story:... -->` là nơi DUY NHẤT khai quyền đọc**: `context_compile.py` quét theo tag, không giữ danh sách riêng. Thêm file mới không cần sửa tool. `Monetization: true|false` bắt buộc trên mọi User Story.
10. `kernel/config/limits.json` — SSOT cho mọi ngưỡng số (giới hạn body, stale node, token/ký tự). Các file khác chỉ tham chiếu tên field, không lặp lại con số.
11. `skills/` — `generate_wbs` (sinh `wbs.json` sau Gate 1), `estimate_scope`, `git_workflow`, `context_compile` (đặc tả; bản thực thi ở `kernel/tools/context_compile.py`).

## Tầng điều phối — 5 câu hỏi cơ học và nơi trả lời

| Câu hỏi của scheduler | Trả lời ở đâu |
|---|---|
| Node **sinh ra từ đâu**? | PHA 0 — 3 track: `intake` (`/new-idea`), `build` (`generate_wbs` sau Gate 1), `runtime` (event Runtime Mode). Xem `ORCHESTRATOR.md` §7a |
| Node nào **sẵn sàng chạy**? | `wbs.json` → `nodes[*].status == "ready"`, tính bởi `RECOMPUTE_READY()` |
| Role đó **còn slot** không? | ĐẾM `nodes` có `status:running` cùng `role`, so với `manifest.concurrency` |
| Message vừa về **đóng node nào**? | `message.node_id` → tra thẳng `wbs.json` |
| Làm sao **không xử lý lặp**? | `message.processed_at` — chỉ Orchestrator set, vòng lặp lọc `== null` |

Thứ tự bắt buộc trong 1 vòng: **PHA 0** sinh node từ sự kiện ngoài → **PHA A** tiêu thụ hết message (`processed_at == null`) → cập nhật `status` → `RECOMPUTE_READY()` → **PHA B** dispatch mọi node `ready` trong giới hạn concurrency.

## 1 quy tắc `depends_on` dùng chung cho cả 3 track

```
depends_on = ( dag.units[unit].depends_on + conditional_depends_on thoả điều kiện )
             \ {gate1}
             ∩ { unit thực sự CÓ NODE trong cùng track }
```

Phép **giao tập** làm cả 3 track tự đúng, không cần logic riêng cho từng chế độ:

| Track | `qa.depends_on` | Vì sao đúng |
|---|---|---|
| `build`, story thường | `[US014-dev-be, US014-mobile-screen]` | cả 2 unit đều có node |
| `build`, `Monetization:true` | `+ [US014-ads-placement]` | conditional thoả |
| `runtime`, fix bug ở mobile | `[BUG042-mobile-screen]` | track không có `dev-be` → tự loại. QA chỉ chờ bản fix. |

## Công cụ kernel — chỉ Python stdlib, tool nào cũng chạy

```bash
python kernel/tools/validate.py --selftest        # kiểm control plane (Gate 0 phần A + Gate 2)
python kernel/tools/context_compile.py <node_id>  # sinh boot context (Gate 0 phần B)
python kernel/tools/digest.py                     # sinh lại today.md (Tier 0)
python kernel/tools/resume.py --list              # node nào đang chờ người can thiệp
```

**Cả 3 Gate cơ học đã thành code**, không còn là điều kiện chỉ ghi trong tài liệu: Gate 0 phần A + Gate 2 (`validate.py`), Gate 0 phần B (`context_compile.py`). Chi tiết: [`kernel/tools/README.md`](kernel/tools/README.md).

Script là **đường nhanh**, không phải phụ thuộc cứng — không có Python thì đọc checklist trong `kernel/gates/*.md` mà kiểm tay, chậm hơn nhưng Gate vẫn thoả được.

## 2 chiều của cùng 1 giao diện — đối xứng

| Chiều | Contract | Ví dụ | Check |
|---|---|---|---|
| Agent → Kernel | `kernel/contracts/message.schema.json` | `message-examples.md` (4 ví dụ) | `D*` |
| Kernel → Agent | `kernel/contracts/boot-context.schema.json` | `kernel/boot/<node_id>.md` (sinh thật) | `G*` |

Cả 2 dùng **cùng wire format** (YAML frontmatter + markdown body) — một khuôn dạng cho toàn hệ thống, không phát minh dạng thứ hai.

Boot context là **file thật trên đĩa**, không phải prompt vô hình: muốn biết agent thực sự nhận gì thì `cat kernel/boot/<node_id>.md`, không phải đoán.

**Không phụ thuộc AI tool nào** — Claude, Cursor, hay người đều chạy được. Đây là ràng buộc thiết kế: OS prompt phải portable giữa các tool, nên phần xác định không được viết bằng tính năng riêng của 1 tool.

## 3 invariant chống lỗi im lặng

Ba loại lỗi dưới đây **không tự báo** — hệ thống vẫn "chạy" nhưng sai. Mỗi cái có 1 cơ chế riêng:

| Lỗi im lặng | Cơ chế chống |
|---|---|
| 2 agent ghi cùng 1 file → mất dữ liệu | **Single-writer**: [`data-ownership.json`](kernel/contracts/data-ownership.json) khai đúng 1 writer/file; `F3` chặn file đơn bị unit `scope:story` có `concurrency > 1` ghi; agent memory dùng **1 file mỗi node** (`F6`) |
| Quên `RECOMPUTE_READY()` → treo im lặng | `C12` + `digest.py` in cảnh báo ngay đầu `today.md` |
| Quên `processed_at` → loop vô hạn | `D12` |
| Agent hang, node giữ slot `concurrency` mãi | `C28` đối chiếu `started_at` với `limits.json → node.stale_running_hours` |
| `message_id` trùng → ghi đè, mất message | quy ước `msg-<node_id>-<n>` khiến trùng **không thể xảy ra về mặt cấu trúc** (`D16`/`D17`) |
| Tier 2 rỗng → agent làm việc mù | `context_compile.py` chặn dispatch, phân biệt rõ "lỗi tag" vs "story chưa có nội dung" (`G11`) |
| Monitoring chưa gắn → `crash_alert` không bao giờ về, **Runtime Mode chết âm thầm** | Gate 6 bắt buộc thấy event thật đã đến, không nhận "đã cấu hình webhook" |

## Khi node hết lượt retry: `waiting_human`, không phải `failed`

Node treo **không chết vĩnh viễn** — nó chờ người. Đường quay lại duy nhất:

```bash
python kernel/tools/resume.py <node_id> --note "<đã sửa gì>"
```

Không sửa tay `wbs.json` để resume: rất dễ quên reset `gate.consecutive_fail`, node sẽ escalate lại ngay lần fail sau. Tool làm nguyên tử 4 việc và bắt buộc `--note`. Hệ thống **không cascade fail** — downstream ở lại `blocked`, nhánh song song khác chạy bình thường.

## Chỉ KERNEL ghi `wbs.json`

Orchestrator (track `intake`/`runtime` + mọi chuyển trạng thái) và kernel skill `generate_wbs` (append track `build`). **Agent không bao giờ sửa `wbs.json`** — kể cả `po` lúc triage chỉ emit message, kernel mới tạo node. Ngoại lệ duy nhất trong `kernel/memory/`: `po` được ghi `project-profile.json` vì đó là khai báo cấu hình, không phải trạng thái scheduler.

## Agent nhiều phase — 3 agent, mỗi phase là 1 node riêng trong `wbs.json`

Không tách thành agent riêng vì đó là cùng 1 chuyên môn/1 người thật, nhưng vị trí trong DAG khác hẳn nhau:

| Agent | Phase sớm (song song, chỉ cần Gate 1) | Phase muộn |
|---|---|---|
| `mobile` | `mobile-shell` — native config, permission, push, deep link (1 lần/project) | `mobile-screen` — code UI/logic per story, cần `designer` + `mobile-shell` xong |
| `ads` | `ads-setup` — SDK + consent management (1 lần/project) | `ads-placement` — chèn quảng cáo, chỉ story `Monetization: true`, cần `mobile-screen` xong |
| `devops` | `devops-infra` — CI/CD, môi trường | `devops-release` — build, ASO, monitoring; cần `qa` pass Gate 4 |

## Capability-agent — bật/tắt theo từng project

`agents/<role>/manifest.json` có field `core`:
- `core: true` (8 agent) — backbone, luôn active.
- `core: false` (hiện tại chỉ `ads`) — chỉ active khi `kernel/memory/project-profile.json` khai trong `active_capability_agents`.

Mobile app không cần quảng cáo? Để `active_capability_agents: []` — `ads` không bao giờ được spawn, không cần sửa gì trong `agents/` hay `routing-table.md`. Muốn thêm capability mới (payment, i18n...)? Copy `agents/_template/`, đặt `core:false`, thêm 1 dòng vào bảng "Capability Plug-in Points" trong `routing-table.md` — không sửa Core DAG.

## Quy tắc tổ chức skill — tránh trùng lặp khi thêm skill mới

- **≥ 2 role dùng giống hệt nhau** (vd `git_workflow` cho `dev-be`/`mobile`/`ads`, `context_compile`/`generate_wbs` cho Orchestrator) → đặt ở `skills/` cấp root, các `AGENT.md` chỉ tham chiếu tên, không copy nội dung.
- **Chỉ 1 role dùng, đặc thù nghiệp vụ của role đó** (vd `skill_generate_wireframe` của `designer`) → đặt trong `agents/<role>/skills/`.

## Trạng thái: hoàn chỉnh về CẤU TRÚC — còn 5 chỗ chờ quyết định thật

Mọi thứ ĐÃ CÓ đầy đủ hình dạng (contract, schema, quy trình, verify step) — các mục dưới đây đều được đánh dấu rõ `<TODO ...>` ngay trong file liên quan, không phải chỗ thiếu sót ẩn:

| Việc còn để trống | Ở đâu | Vì sao chưa điền |
|---|---|---|
| Lệnh lint/test/build thật | `agents/dev-be/skills/`, `agents/mobile/skills/{run_lint,run_unit_test}/`, `agents/qa/skills/run_tests/` (khối "STACK BINDING" — đã liệt kê sẵn lệnh gợi ý cho Flutter/RN/Native Android/iOS, chỉ cần chọn) | Chưa chốt Flutter/React Native/Native |
| Danh sách từ khoá cấm store | `agents/devops/docs/store-keyword-blocklist.md` | Cần dữ liệu thật, tích luỹ dần khi bắt đầu submit app đầu tiên |
| Tên kênh escalate thật | `kernel/config/escalation.json` | Cần bạn cung cấp kênh Slack/email thật của team |
| Ngưỡng coverage cụ thể | `agents/qa/skills/check_coverage/SKILL.md` | Tuỳ mức độ khắt khe bạn muốn cho dự án đầu tiên |
| Chọn ad network/mediation thật | `agents/ads/skills/integrate_ad_sdk/SKILL.md` | Quyết định 1 lần đầu dự án có `ads` active |

**Cân nhắc thêm (không bắt buộc):** `skill_generate_mock_server` sinh từ `api-contracts.json`, giúp `mobile-screen` test độc lập hoàn toàn với `dev-be` kể cả trước khi có backend thật chạy.
