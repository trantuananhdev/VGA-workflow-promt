# skill_generate_wbs

**Mục tiêu:** Sau Gate 1 (BA+CTO signoff), **APPEND** track `build` vào `kernel/memory/wbs.json`.

**Đây là kernel skill** — Orchestrator gọi, không phải agent gọi. Agent không bao giờ ghi `wbs.json`.

**Trigger:** `gate1.passed`

**Input:** `shared/PRD.md` + `shared/architecture.md` (phần đã freeze) + `kernel/memory/project-profile.json` + `kernel/contracts/dag.json` + `agents/*/manifest.json` (để đọc `core`)

---

## ⚠️ APPEND, KHÔNG GHI ĐÈ

`wbs.json` lúc này **đã tồn tại** và đang chứa track `intake` (node `po`/`ba`/`cto` đã `done`). Skill này:
- **CHỈ thêm** node mới cho track `build`
- **KHÔNG** tạo lại node cho unit `po`/`ba`/`cto` — chúng thuộc track `intake` và đã xong. Tạo lại sẽ khiến `po` (có `depends_on` rỗng) khởi tạo `ready` → Orchestrator spawn lại `po` → chạy vòng.
- **KHÔNG** chạm vào bất kỳ node nào đã tồn tại

---

## Quy ước `node_id` = `<TRACK_ID>-<unit>`

| `scope` của unit (xem `dag.json`) | TRACK_ID | Ví dụ |
|---|---|---|
| `story` | `<STORY_ID>` bỏ dấu gạch | `US014-designer-screen`, `US014-mobile-screen`, `US014-qa` |
| `project` | `PROJ` | `PROJ-design-system`, `PROJ-mobile-shell`, `PROJ-devops-infra`, `PROJ-ads-setup` |
| `release` | `REL` | `REL-devops-release` |

`unit` = `role` nếu agent 1 phase, `role-phase` nếu nhiều phase. `node_id` phải **duy nhất toàn file**.

---

## Quy trình

```
0. Xác định role_set:
   candidate = mọi unit trong dag.json TRỪ po/ba/cto (đã xong ở intake track)
   core-ness của 1 unit = agents/<unit.role>/manifest.json .core
     (core khai ở MANIFEST, không khai trong dag.json — bật/tắt là bật/tắt cả agent)
   role_set = { unit có core:true }
            ∪ { unit thuộc agent nằm trong project-profile.active_capability_agents }
   Nếu active_capability_agents chứa agent mà manifest của nó KHÔNG core:false
   -> lỗi, KHÔNG tự sửa, báo về CTO (Gate 2 chặn).

1. Với mỗi User Story đã signoff, gọi skill_estimate_scope.
   PHẢI giữ cả breakdown/reasoning -> field size_reasoning
   (Gate 2 từ chối node có size mà thiếu reasoning).

2. Sinh node theo scope:
   - unit scope=story    -> 1 node cho MỖI story đã signoff
   - unit scope=project  -> ĐÚNG 1 node cho cả project
   - unit scope=release  -> 1 node
   - unit có only_if     -> chỉ tạo khi điều kiện đúng
                            (ads-placement: chỉ story có "Monetization: true" trong PRD.md)

3. Tính depends_on — QUY TẮC GIAO TẬP (giống hệt cho cả 3 loại track):

     raw   = dag.json[unit].depends_on
           + [c.unit for c in conditional_depends_on nếu điều kiện đúng]
     raw   = raw \ {"gate1"}                       # gate1 là mốc, không phải node
     valid = raw ∩ { unit thực sự CÓ NODE trong track này }
     depends_on = [dịch valid sang node_id thật]

   Dịch node_id theo scope của DEPENDENCY (không phải của unit hiện tại):
     dep scope=story   -> <STORY_ID cùng story>-<dep>     vd US014-designer-screen
     dep scope=project -> PROJ-<dep>                       vd PROJ-mobile-shell

   Ví dụ: qa của story US-014, story này Monetization:false
     raw   = [dev-be, mobile-screen]   (không thêm ads-placement vì cond false)
     valid = cả 2 đều có node trong build track
     -> depends_on = ["US014-dev-be", "US014-mobile-screen"]

4. Khởi tạo mỗi node:
   track = "build" ; track_id theo bảng trên ; story_id (null nếu scope != story)
   status = "ready" nếu depends_on rỗng, ngược lại "blocked"
   gate = { name: dag.json[unit].gate, result: null, consecutive_fail: 0, last_error: null }
   message_refs = [] ; started_at = null ; finished_at = null

5. APPEND vào wbs.json.nodes. Cập nhật project_id nếu còn null. KHÔNG sửa node cũ.
```

**Output:** `wbs.json` đã có thêm track `build`, giữ nguyên track `intake`.

---

## Verify — xem `kernel/gates/gate2-wbs-valid.md`

Gate 2 chỉ validate **các node vừa append** (track `build`), không validate lại track `intake` đã `done`. Điểm dễ sai nhất mà Gate 2 sẽ bắt: `depends_on` trỏ vào `node_id` không tồn tại → node đó `blocked` vĩnh viễn, scheduler treo im lặng không báo lỗi.
