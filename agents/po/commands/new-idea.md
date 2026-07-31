# /new-idea — Cửa vào duy nhất của ý tưởng mới

**Gọi khi:** Con người (Client hoặc Huy) muốn đưa 1 ý tưởng mới vào hệ thống.

> Đây là **PHA 0** của Event Loop (`ORCHESTRATOR.md` §7a) — thời điểm duy nhất mà `wbs.json`
> được khởi tạo lần đầu. Trước bước này hệ thống chưa có node nào để chạy.

**Input người cần cung cấp:**
- Mô tả pain-point/ý tưởng (tự do)
- Mục tiêu đo lường được (nếu chưa có, `po` PHẢI hỏi lại — xem `agents/po/AGENT.md`)
- **Chỉ khi là project MỚI:** có cần capability-agent tuỳ chọn nào không (hiện tại chỉ `ads` — hỏi thẳng *"sản phẩm có cần quảng cáo không?"*). KHÔNG tự suy diễn từ mô tả ý tưởng.
- **Chỉ khi là project MỚI: 5 tín hiệu bắt buộc** để `cto` suy ra được loại sản phẩm (xem bước 2 dưới). Hỏi bằng **ngôn ngữ nghiệp vụ**, không hỏi "làm app hay web" — đó là kết luận của `cto`, không phải câu hỏi cho khách.

---

## Bước 1 — Orchestrator (kernel) làm trước, TRƯỚC khi `po` chạy

```
1. Cấp TRACK_ID mới: INTAKE<nnn> (tăng dần, không trùng track cũ trong wbs.json)
2. Tạo track `intake` trong kernel/memory/wbs.json — 3 node:
     INTAKE<nnn>-po   depends_on: []                  -> status: ready
     INTAKE<nnn>-ba   depends_on: [INTAKE<nnn>-po]     -> status: blocked
     INTAKE<nnn>-cto  depends_on: [INTAKE<nnn>-ba]     -> status: blocked
   (gate: po=null, ba=null, cto=gate1 — theo dag.json)
   Nếu wbs.json chưa có nodes -> đây là lần khởi tạo đầu tiên, set created_at.
3. Gate 2 validate track vừa tạo.
4. Vào PHA B: dispatch node INTAKE<nnn>-po.
```

**Agent không tự tạo node.** `po` chỉ nhận boot context và làm việc của mình — invariant "chỉ kernel ghi `wbs.json`".

## Bước 2 — `po` thực hiện

```
1. Ghi ý tưởng thô vào agents/po/memory/INTAKE<nnn>-po.md (một file mỗi node)
2. Xác nhận mục tiêu đo lường được với người — không tự suy diễn
3. NẾU là project mới: hỏi capability-agent tuỳ chọn cần dùng, rồi ghi
   kernel/memory/project-profile.json (active_capability_agents).
   Chỉ liệt kê agent có core:false trong agents/<role>/manifest.json — hiện tại là `ads`.
3b. NẾU là project mới: ghi product_signals vào cùng file đó. 5 tín hiệu BẮT BUỘC
   (cto không suy ra được loại sản phẩm nếu thiếu, và sẽ phải mở Sync Session hỏi lại):
     how_users_arrive              "Người dùng mở nó ra bằng cách nào — tải từ store,
                                    bấm 1 đường link, hay hệ thống khác gọi vào?"
     primary_device               "Họ dùng chủ yếu trên điện thoại hay máy tính?"
     data_shared_between_users    "Dữ liệu của người này người khác có phải thấy không?"
     needs_offline                "Có lúc nào phải dùng được khi mất mạng không?"
     needs_search_engine_discovery"Khách có cần Google tìm ra được / gửi link ai cũng
                                    xem được không?"
   Các tín hiệu còn lại (device_features_needed, compliance_constraints, existing_assets,
   hard_constraints, needs_realtime, expected_scale) hỏi khi liên quan — RỖNG nghĩa là
   "đã hỏi, không cần", khác null nghĩa là "chưa hỏi". Đừng để null nếu đã hỏi.

   TUYỆT ĐỐI KHÔNG ghi tên nền tảng/công nghệ vào đây ("làm app Android", "dùng React").
   po ghi TÍN HIỆU, cto mới ra KẾT LUẬN (agents/cto/skills/decide_tech_stack/SKILL.md).
   Khách tự chỉ định công nghệ thì ghi nguyên văn vào hard_constraints, không ghi thành
   quyết định — cto vẫn phải nêu đánh đổi.
4. Viết Epic vào agents/po/memory/epics.json
5. Gọi skill_estimate_scope (giữ nguyên breakdown + reasoning, không chỉ nhãn size)
6. Emit type: handoff với node_id = INTAKE<nnn>-po
     - size M/L/XL -> to: ba   (đi tiếp track intake, hướng tới Gate 1)
     - size S      -> to: dev-be | client  (đường tắt runtime_feeds — Orchestrator sẽ
                      tạo track runtime FR<nnn> thay vì đi tiếp intake; chọn bên nào
                      tuỳ vị trí việc, và chỉ chọn unit mà project NÀY thực sự có)
```

> `project-profile.json` là ngoại lệ duy nhất mà 1 agent được ghi vào `kernel/memory/` —
> vì đó là **khai báo cấu hình project**, không phải trạng thái scheduler. `wbs.json` thì tuyệt đối không.
