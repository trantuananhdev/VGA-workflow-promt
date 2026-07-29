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
> **Repo này THUẦN Mobile.** Không có agent `dev-fe` (web frontend) — vai trò client-side do
> agent `mobile` đảm nhiệm với 2 phase (`mobile-shell` + `mobile-screen`), vì trong 1 team mobile
> thật đó luôn là cùng 1 người. Web-application dùng repo riêng.
>
> File này có 2 phần: **Core DAG** (backbone, luôn chạy) và **Capability Plug-in Points**
> (agent `core:false`, chỉ ghép vào khi `kernel/memory/project-profile.json` khai).

---

## Core DAG (size L/XL)

```
Client idea
   │
   ▼
po  (triage, viết pain-point + epics.json, ghi kernel/memory/project-profile.json)
   │
   ▼
[ba + cto]  ◄── Sync Session hội tụ, không phải handoff 1 chiều
   │  Gate 1 (dual signoff) → chốt: PRD.md, architecture.md, db-schema.md,
   │                                api-contracts.json, system-spec.md
   ▼
generate_wbs  (skill, đọc project-profile.json + sinh wbs.json — CHỈ tạo node cho
   │           agent core:true + agent core:false nằm trong active_capability_agents)
   ▼ Gate 2 (WBS hợp lệ theo grammar này + đúng role_set đã tính)
   │
   ├──────────────┬──────────────┬────────────────┐
   ▼              ▼              ▼                ▼
designer       devops         dev-be         mobile-shell
(cần: PRD      (devops-infra:  (cần: db-schema  (cần: architecture
 user-flow +    chỉ cần        + api-contracts)  + system-spec —
 api-contracts) architecture)      │             permission, push,
   │              │                │             deep link, min OS)
   │              │                │                │
   └──────┬───────┼────────────────┼────────────────┘
          ▼       │                │
    mobile-screen │                │   ◄── cần: wireframe (designer) + mobile-shell xong
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

**Lưu ý:** `devops` KHÔNG feed vào `mobile` — 2 nhánh độc lập hoàn toàn, chỉ cùng xuất phát từ Gate 1. `devops-infra` chạy xong sớm rồi rảnh chờ tới khi `qa` pass Gate 4 mới kích hoạt phase `devops-release` (xem `agents/devops/AGENT.md` — 2 phase trong cùng 1 agent).

**Quy tắc phụ thuộc Core (grammar — `wbs.json` không được vi phạm):**
- `designer`, `devops-infra`, `dev-be`, `mobile-shell` chỉ phụ thuộc `ba+cto signoff` — được phép chạy song song.
- `mobile-screen` phụ thuộc `designer` HOÀN THÀNH (story đó) + `mobile-shell` HOÀN THÀNH (1 lần đầu) + `api-contracts.json` freeze — KHÔNG phụ thuộc `dev-be` hoàn thành.
- `qa` phụ thuộc cả `dev-be` và `mobile-screen` hoàn thành (điểm tích hợp bắt buộc tuần tự) — cộng `ads-placement` nếu story có `Monetization: true`.
- `devops-release` phụ thuộc `qa` pass (Gate 4).

---

## Capability Plug-in Points (agent `core:false` — chỉ active theo `project-profile.json`)

| Capability Agent | Điều kiện activate | Plug vào DAG ở đâu | Feed vào |
|---|---|---|---|
| `ads` (phase `ads-setup`) | nằm trong `active_capability_agents` | Song song `designer`/`devops-infra`/`dev-be`/`mobile-shell`, chỉ cần Gate 1 | Không chặn ai — chạy xong rồi chờ |
| `ads` (phase `ads-placement`) | như trên, VÀ chỉ cho story có `Monetization: true` trong PRD | SAU khi `mobile-screen` build xong screen của ĐÚNG story đó (không phải sau toàn bộ `mobile`) | `qa` CHỜ thêm `ads-placement` cho story monetization trước khi coi integration-ready |

**Lưu ý hướng phụ thuộc:** `ads-setup` chạy song song ngay từ đầu, còn `ads-placement` đi SAU `mobile-screen` — 2 phase cùng 1 agent nhưng vị trí trong DAG hoàn toàn khác nhau. `generate_wbs` phải đọc đúng bảng này khi tạo node, không suy diễn theo tên agent.

**Thêm capability-agent mới trong tương lai (vd `i18n`, `payment`):** copy `agents/_template/`, đặt `core: false` trong `manifest.json`, rồi thêm 1 dòng vào bảng trên nêu rõ plug vào đâu/feed vào đâu — KHÔNG sửa Core DAG.

---

## Runtime Mode — Entry point theo loại sự kiện (khi app đã live)

| Event | Entry point | Sub-DAG | Bỏ qua |
|---|---|---|---|
| `bug_report` | `dev-be`/`mobile`/`ads` (tuỳ vị trí lỗi) | agent tương ứng → qa → devops(hotfix) | po, ba, cto, designer |
| `crash_alert` (tự động từ Sentry/Crashlytics) | `mobile` hoặc `dev-be` (theo stack trace) | agent tương ứng → qa → devops(hotfix) | po, ba, cto, designer |
| `feature_request` size S | `po` (triage) | po → `dev-be`/`mobile` thẳng → qa → devops | ba, cto, designer |
| `feature_request` size M/L/XL | `po` | Chạy lại Core DAG đầy đủ từ `[ba+cto]` (+ capability plug-in nếu cần) | — |
| `feature_request` cần platform capability chưa khai (vd quyền Bluetooth mới) | `mobile` (phase `mobile-shell`) | Sync Session `mobile`↔`cto` → cập nhật `native.json` → `mobile-screen` | po, ba, designer |
| `doc_drift_detected` | `ba+cto` | Cập nhật lại PRD.md/architecture.md cho khớp code thực tế | agent phát hiện không tự sửa doc |

**Quy tắc chọn entry point:** Orchestrator xác định event type từ nguồn phát sinh (issue tracker, crash monitor, PO triage) — KHÔNG bao giờ mặc định chạy full DAG cho mọi việc. Việc nhỏ đi đường ngắn nhất hợp lệ trong bảng trên.

**Runtime Mode cũng có node trong `wbs.json`** (track `runtime`, `node_id` = `BUG042-*` / `CRASH017-*` / `FR009-*`) — không phải cơ chế riêng. Tập unit của track = đóng gói xuôi dòng từ entry unit; `depends_on` = quy tắc giao tập, nên nó **tự loại** unit không tham gia. Ví dụ track `BUG042` sửa lỗi ở `mobile-screen`: `qa` chỉ `depends_on` `BUG042-mobile-screen`, không chờ `dev-be` (vốn không có node trong track này). Chi tiết: `ORCHESTRATOR.md` §7a.

**Ngoại lệ:** `feature_request` size M/L/XL **không** tạo track `runtime` — nó chạy lại đủ track `intake` → Gate 1 → track `build` như một feature mới.
