# skill_generate_wbs

**Mục tiêu:** Sau Gate 1 (BA+CTO signoff), **APPEND** track `build` vào `kernel/memory/wbs.json`.

**Đây là kernel skill** — Orchestrator gọi, không phải agent gọi. Agent không bao giờ ghi `wbs.json`.

**Trigger:** `gate1.passed`

**Input:** `shared/PRD.md` + `shared/architecture.md` (phần đã freeze) + **`shared/contracts/tech-stack.json`** (→ `delivery_targets`, quyết định unit nào tồn tại) + `kernel/memory/project-profile.json` + `kernel/contracts/dag.json` + `agents/*/manifest.json` (để đọc `core`)

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
| `story` | `<STORY_ID>` bỏ dấu gạch | `US014-designer-screen`, `US014-client-screen`, `US014-qa` |
| `project` | `PROJ` | `PROJ-design-system`, `PROJ-client-shell`, `PROJ-devops-infra`, `PROJ-ads-setup` |
| `release` | `REL` | `REL-devops-release` |

`unit` = `role` nếu agent 1 phase, `role-phase` nếu nhiều phase. `node_id` phải **duy nhất toàn file**.

---

## Quy trình

```
0. Xác định role_set — 2 BỘ LỌC ĐỘC LẬP, phải áp CẢ HAI:

   candidate = mọi unit trong dag.json TRỪ po/ba/cto (đã xong ở intake track)

   (a) LỌC THEO AGENT (core / capability) — "agent này có tham gia project không":
       core-ness của 1 unit = agents/<unit.role>/manifest.json .core
         (core khai ở MANIFEST, không khai trong dag.json — bật/tắt là bật/tắt cả agent)
       giữ  { unit có core:true }
          ∪ { unit thuộc agent nằm trong project-profile.active_capability_agents }
       Nếu active_capability_agents chứa agent mà manifest của nó KHÔNG core:false
       -> lỗi, KHÔNG tự sửa, báo về CTO (Gate 2 chặn).

   (b) LỌC THEO DELIVERY TARGET (only_if) — "project này CÓ phần việc đó không":
       ctx.has_client  = tech-stack.json.delivery_targets ∩ {mobile_native, web_app} ≠ ∅
       ctx.has_backend = "backend_service" ∈ delivery_targets
       giữ unit khi MỌI biểu thức trong unit.only_if đều đúng (mảng = AND; rỗng = luôn giữ).
       Biểu thức 'story.Monetization == true' KHÔNG lọc ở bước này (nó theo TỪNG STORY,
       xử lý ở bước 2), chỉ 2 biểu thức tech_stack.* lọc ở đây.

   role_set = candidate sau khi qua CẢ (a) và (b).

   Vì sao 2 bộ lọc không gộp: (a) là "công ty có bật agent đó không" (cấu hình, po ghi),
   (b) là "sản phẩm có phần đó không" (kết luận kỹ thuật, cto ghi). Trước đây chỉ có (a)
   vì kernel MẶC ĐỊNH mọi project là mobile app — nên project web/backend-thuần vẫn sinh
   node native shell. Đọc kỹ: bỏ sót (b) không làm WBS invalid về cú pháp, nó chỉ tạo ra
   node cho việc không tồn tại — và node đó sẽ nằm `ready` mãi mà không ai làm được.

   Kiểm nhanh 3 hình dạng thường gặp:
     delivery_targets = [mobile_native, backend_service] -> đủ cả 5 nhánh như trước đây
     delivery_targets = [web_app]        -> KHÔNG có dev-be; qa chỉ chờ client-screen
     delivery_targets = [backend_service]-> KHÔNG có design-system/designer-screen/
                                            client-shell/client-screen/ads-*;
                                            qa chỉ chờ dev-be

1. Với mỗi User Story đã signoff, gọi skill_estimate_scope.
   PHẢI giữ cả breakdown/reasoning -> field size_reasoning
   (Gate 2 từ chối node có size mà thiếu reasoning).

2. Sinh node theo scope:
   - unit scope=story    -> 1 node cho MỖI story đã signoff
   - unit scope=project  -> ĐÚNG 1 node cho cả project
   - unit scope=release  -> 1 node
   - unit có only_if     -> chỉ tạo khi MỌI biểu thức đúng (mảng = AND):
                            'story.Monetization == true'   -> xét TỪNG story (PRD.md)
                            'tech_stack.has_client == true'/'has_backend == true'
                                                           -> đã lọc ở bước 0(b)

3. Tính depends_on — QUY TẮC GIAO TẬP (giống hệt cho cả 3 loại track):

     raw   = dag.json[unit].depends_on
           + [c.unit for c in conditional_depends_on nếu điều kiện đúng]
     raw   = raw \ {"gate1"}                       # gate1 là mốc, không phải node
     valid = raw ∩ { unit thực sự CÓ NODE trong track này }
     depends_on = [dịch valid sang node_id thật]

   Dịch node_id theo scope của DEPENDENCY (không phải của unit hiện tại):
     dep scope=story   -> <STORY_ID cùng story>-<dep>     vd US014-designer-screen
     dep scope=project -> PROJ-<dep>                       vd PROJ-client-shell

   Ví dụ 1: qa của story US-014, Monetization:false, delivery_targets=[mobile_native,backend_service]
     raw   = [dev-be, client-screen]   (không thêm ads-placement vì cond false)
     valid = cả 2 đều có node trong build track
     -> depends_on = ["US014-dev-be", "US014-client-screen"]

   Ví dụ 2: cùng story, delivery_targets=[web_app] (không có backend riêng)
     raw   = [dev-be, client-screen]
     valid = chỉ client-screen (dev-be bị bước 0(b) loại, KHÔNG có node)
     -> depends_on = ["US014-client-screen"]
     Đây chính là chỗ phép GIAO TẬP tự lo: không cần logic riêng cho từng loại project,
     và cũng là lý do KHÔNG được bỏ bước 0(b) rồi tính bù ở đây — nếu unit vẫn có node
     thì phép giao vẫn giữ nó, và qa sẽ chờ một node không ai làm được.

4. Khởi tạo mỗi node:
   track = "build" ; track_id theo bảng trên ; story_id (null nếu scope != story)
   status = "ready" nếu depends_on rỗng, ngược lại "blocked"
   gate = { name: dag.json[unit].gate, result: null, consecutive_fail: 0, last_error: null }
   message_refs = [] ; started_at = null ; finished_at = null

5. APPEND vào wbs.json.nodes. Cập nhật project_id nếu còn null. KHÔNG sửa node cũ.
```

**Output:** `wbs.json` đã có thêm track `build`, giữ nguyên track `intake`.

**Ghi lại căn cứ:** thêm `wbs.json.build_context = { delivery_targets, has_client, has_backend, active_capability_agents }` khi append track `build`. Không có nó thì người đọc `wbs.json` về sau không phân biệt được "unit này thiếu vì project không cần" với "unit này bị quên" — và Gate 2 phải tự suy lại từ `tech-stack.json` có thể đã bị sửa sau đó.

---

## Verify — xem `kernel/gates/gate2-wbs-valid.md`

Gate 2 chỉ validate **các node vừa append** (track `build`), không validate lại track `intake` đã `done`. Điểm dễ sai nhất mà Gate 2 sẽ bắt: `depends_on` trỏ vào `node_id` không tồn tại → node đó `blocked` vĩnh viễn, scheduler treo im lặng không báo lỗi.
