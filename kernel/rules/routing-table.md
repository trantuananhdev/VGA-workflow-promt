# routing-table.md — Macro DAG & Entry Points

> Đây là "văn phạm hợp lệ" của hệ thống — định nghĩa Agent nào được phép theo Agent nào.
> `wbs.json` (sinh động, theo từng project) PHẢI tuân thủ grammar này — Gate 2 kiểm tra điều đó.
>
> ⚠️ **File này là bản GIẢI THÍCH CHO NGƯỜI.** Bản máy đọc là `kernel/contracts/dag.json` —
> Gate 0 và Gate 2 kiểm bằng lookup vào đó, không đọc hiểu bảng markdown ở đây.
> **Sửa 1 trong 2 file thì PHẢI sửa file kia** (2 file này là cùng 1 sự thật ở 2 dạng biểu diễn).
>
> DAG ở đây mô tả **quan hệ giữa các unit**. Còn việc unit nào thực sự có node, và node đó
> phụ thuộc node nào, thì tuỳ **track** — xem `ORCHESTRATOR.md` §7a (3 track: `intake`/`build`/`runtime`
> + quy tắc giao tập `depends_on`). Cùng 1 DAG này sinh ra sub-DAG khác nhau cho mỗi track.
>
> **KHÔNG CỐ ĐỊNH LOẠI SẢN PHẨM.** Vai trò client-side do agent `client` đảm nhiệm cho **mọi**
> nền tảng, với 2 phase (`client-shell` + `client-screen`) và **platform pack** chọn theo
> `shared/contracts/tech-stack.json` (`agents/client/skills/platform/<pack>/`). Không có `dev-fe`
> riêng, vì trong 1 team thật thì vỏ và màn hình luôn là cùng 1 người.
>
> **Unit nào thực sự có node phụ thuộc `delivery_targets`** (do `cto` suy ra từ đề bài, xem
> `agents/cto/skills/decide_tech_stack/SKILL.md`). DAG dưới đây là **hình dạng ĐẦY ĐỦ** (project
> có cả client và backend); 2 hình dạng còn lại là **tập con** của nó:
>
> | `delivery_targets` | Nhánh có node | Nhánh bị tắt |
> |---|---|---|
> | `[mobile_native, backend_service]` hoặc `[web_app, backend_service]` | tất cả | — |
> | `[web_app]` / `[mobile_native]` (local-first) | design + client + devops + qa | `dev-be` |
> | `[backend_service]` (API thuần) | dev-be + devops + qa | `design-system`, `designer-screen`, `client-shell`, `client-screen`, `ads-*` |
>
> Quy tắc **giao tập** của `depends_on` (xem `ORCHESTRATOR.md` §7a) tự lo phần còn lại: `qa` của
> project web chỉ chờ `client-screen`, của project API thuần chỉ chờ `dev-be` — không cần logic riêng.
>
> File này có 2 phần: **Core DAG** (backbone, luôn chạy) và **Capability Plug-in Points**
> (agent `core:false`, chỉ ghép vào khi `kernel/memory/project-profile.json` khai).

---

## Core DAG (size L/XL)

```
Client idea
   │
   ▼
po  (triage, viết pain-point + epics.json, ghi project-profile.json:
     active_capability_agents + product_signals — TÍN HIỆU THÔ, không phải công nghệ)
   │
   ▼
[ba + cto]  ◄── Sync Session hội tụ, không phải handoff 1 chiều
   │  Gate 1 (dual signoff) → chốt: PRD.md, architecture.md, db-schema.md,
   │                                api-contracts.json, system-spec.md,
   │                                tech-stack.json (delivery_targets + stack, cto
   │                                suy ra từ product_signals — quyết định các nhánh
   │                                dưới đây nhánh nào THỰC SỰ có node)
   ▼
generate_wbs  (skill, đọc project-profile.json + tech-stack.json + sinh wbs.json —
   │           2 bộ lọc: (a) agent core:true hoặc nằm trong active_capability_agents,
   │           (b) only_if theo delivery_targets thoả)
   ▼ Gate 2 (WBS hợp lệ theo grammar này + đúng role_set đã tính)
   │
   ├──────────────┬──────────────┬────────────────┐
   ▼              ▼              ▼                ▼
design-system  devops         dev-be         client-shell
(chỉ khi có                    (chỉ khi có     (chỉ khi có client)
 client)                        backend)
(1 lần/project) (devops-infra:  (cần: db-schema  (cần: architecture
 tokens.json +   chỉ cần        + api-contracts)  + system-spec —
 theme-preview   architecture)      │             permission, push,
 .html)           │                │             deep link, min OS)
   │              │                │                │
   ▼ Gate 7 — NGƯỜI chọn 1 phương án theme            │
   │  (node → `awaiting_human_decision`, KHÔNG phải lỗi;│
   │   nhả slot concurrency, 3 nhánh kia chạy bình thường)
   │              │                │                │
   ▼              │                │                │
designer-screen   │                │                │
(per story —      │                │                │
 layout JSON,     │                │                │
 trỏ token)       │                │                │
   │              │                │                │
   └──────┬───────┼────────────────┼────────────────┘
          ▼       │                │
    client-screen │                │   ◄── cần: wireframe (designer-screen) + client-shell xong
    (per story)   │                │       + api-contracts freeze. KHÔNG chờ dev-be code xong
          │       │                │       (contract-first, dùng mock)
          ▼       │                │
   [ads-placement]│                │   ◄── CHỈ story có Monetization:true (xem plug-in table)
          │       │                │
          │  (devops-infra chờ    │
          │   rảnh tới khi qa     │
          │   pass mới release)   │
          └───────────┬────────────┘
                       ▼
                      qa   (Gate 3: lint/test pass; Gate 4: coverage + no-crash
                       │     + điều kiện bổ sung của `ads` nếu story monetization)
                       ▼
                devops (devops-release)
```

**Lưu ý:** `devops` KHÔNG feed vào `client` — 2 nhánh độc lập hoàn toàn, chỉ cùng xuất phát từ Gate 1. `devops-infra` chạy xong sớm rồi rảnh chờ tới khi `qa` pass Gate 4 mới kích hoạt phase `devops-release` (xem `agents/devops/AGENT.md` — 2 phase trong cùng 1 agent).

**Quy tắc phụ thuộc Core (grammar — `wbs.json` không được vi phạm):**
- **Unit chỉ tồn tại khi `only_if` thoả** (mảng biểu thức, AND — văn phạm đóng ở `dag.json` → `_only_if_grammar`). Node cho nhánh project không có = việc không ai làm được, nằm `ready` mãi (`validate.py` `C35`); nhánh đáng lẽ phải có mà thiếu = cả nhánh bị bỏ im lặng (`C36`).
- `design-system`, `devops-infra`, `dev-be`, `client-shell` chỉ phụ thuộc `ba+cto signoff` — được phép chạy song song.
- **`designer-screen` phụ thuộc `design-system` HOÀN THÀNH** (tức Gate 7 pass = người đã chọn theme và token đã khoá) — **đây là NGOẠI LỆ CÓ CHỦ ĐÍCH** so với nguyên tắc "nhánh nào cũng chỉ chờ Gate 1" của toàn hệ thống. Lý do: nếu `designer-screen` chạy trước khi có `shared/design/tokens.json` đã khoá, nó lại tự quyết màu/spacing riêng cho từng story — đúng vấn đề mà tầng token sinh ra để giải quyết, và Gate 5 điều 5 sẽ fail hàng loạt. Đánh đổi: story đầu tiên chờ thêm 1 vòng người-chọn-theme, **1 lần/project**, không lặp per-story; 3 nhánh song song còn lại không bị ảnh hưởng. Xem `kernel/gates/gate7-design-system-lock.md`.
- `client-screen` phụ thuộc `designer-screen` HOÀN THÀNH (story đó) + `client-shell` HOÀN THÀNH (1 lần đầu) + `api-contracts.json` freeze — KHÔNG phụ thuộc `dev-be` hoàn thành.
- `qa` phụ thuộc cả `dev-be` và `client-screen` hoàn thành (điểm tích hợp bắt buộc tuần tự) — cộng `ads-placement` nếu story có `Monetization: true`.
- `devops-release` phụ thuộc `qa` pass (Gate 4).

---

## Capability Plug-in Points (agent `core:false` — chỉ active theo `project-profile.json`)

| Capability Agent | Điều kiện activate | Plug vào DAG ở đâu | Feed vào |
|---|---|---|---|
| `ads` (phase `ads-setup`) | nằm trong `active_capability_agents` | Song song `design-system`/`devops-infra`/`dev-be`/`client-shell`, chỉ cần Gate 1 | Không chặn ai — chạy xong rồi chờ |
| `ads` (phase `ads-placement`) | như trên, VÀ chỉ cho story có `Monetization: true` trong PRD | SAU khi `client-screen` build xong screen của ĐÚNG story đó (không phải sau toàn bộ `client`) | `qa` CHỜ thêm `ads-placement` cho story monetization trước khi coi integration-ready |

**Lưu ý hướng phụ thuộc:** `ads-setup` chạy song song ngay từ đầu, còn `ads-placement` đi SAU `client-screen` — 2 phase cùng 1 agent nhưng vị trí trong DAG hoàn toàn khác nhau. `generate_wbs` phải đọc đúng bảng này khi tạo node, không suy diễn theo tên agent.

**Thêm capability-agent mới trong tương lai (vd `i18n`, `payment`):** copy `agents/_template/`, đặt `core: false` trong `manifest.json`, rồi thêm 1 dòng vào bảng trên nêu rõ plug vào đâu/feed vào đâu — KHÔNG sửa Core DAG.

---

## Runtime Mode — Entry point theo loại sự kiện (khi app đã live)

| Event | Entry point | Sub-DAG | Bỏ qua |
|---|---|---|---|
| `bug_report` | `dev-be`/`client`/`ads` (tuỳ vị trí lỗi, **trong số unit project này có**) | agent tương ứng → qa → devops(hotfix) | po, ba, cto, designer (cả 2 phase) |
| `crash_alert` (tự động từ Sentry/Crashlytics) | `client` hoặc `dev-be` (theo stack trace) | agent tương ứng → qa → devops(hotfix) | po, ba, cto, designer |
| `feature_request` size S | `po` (triage) | po → `dev-be`/`client` thẳng → qa → devops | ba, cto, designer |
| `feature_request` size M/L/XL | `po` | Chạy lại Core DAG đầy đủ từ `[ba+cto]` (+ capability plug-in nếu cần) | — |
| `feature_request` cần capability nền tảng chưa khai (vd quyền Bluetooth, hoặc quyền browser mới) | `client` (phase `client-shell`) | Sync Session `client`↔`cto` → cập nhật `capabilities/client.json` → `client-screen` | po, ba, designer |
| `feature_request` đòi **đổi `delivery_targets`** (vd "làm thêm bản web") | `po` → `ba+cto` | KHÔNG phải việc của track runtime: đổi target là đổi hình dạng DAG → chạy lại `intake` → Gate 1 → `generate_wbs` sinh nhánh mới | — |
| `doc_drift_detected` | `ba+cto` | Cập nhật lại PRD.md/architecture.md cho khớp code thực tế | agent phát hiện không tự sửa doc |

**Quy tắc chọn entry point:** Orchestrator xác định event type từ nguồn phát sinh (issue tracker, crash monitor, PO triage) — KHÔNG bao giờ mặc định chạy full DAG cho mọi việc. Việc nhỏ đi đường ngắn nhất hợp lệ trong bảng trên.

**Runtime Mode cũng có node trong `wbs.json`** (track `runtime`, `node_id` = `BUG042-*` / `CRASH017-*` / `FR009-*`) — không phải cơ chế riêng. Tập unit của track = đóng gói xuôi dòng từ entry unit; `depends_on` = quy tắc giao tập, nên nó **tự loại** unit không tham gia. Ví dụ track `BUG042` sửa lỗi ở `client-screen`: `qa` chỉ `depends_on` `BUG042-client-screen`, không chờ `dev-be` (vốn không có node trong track này). Chi tiết: `ORCHESTRATOR.md` §7a.

**Ngoại lệ:** `feature_request` size M/L/XL **không** tạo track `runtime` — nó chạy lại đủ track `intake` → Gate 1 → track `build` như một feature mới.
