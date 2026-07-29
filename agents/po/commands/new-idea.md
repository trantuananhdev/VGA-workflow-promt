# /new-idea — Cửa vào duy nhất của ý tưởng mới

**Gọi khi:** Con người (Client hoặc Huy) muốn đưa 1 ý tưởng mới vào hệ thống.

> Đây là **PHA 0** của Event Loop (`ORCHESTRATOR.md` §7a) — thời điểm duy nhất mà `wbs.json`
> được khởi tạo lần đầu. Trước bước này hệ thống chưa có node nào để chạy.

**Input người cần cung cấp:**
- Mô tả pain-point/ý tưởng (tự do)
- Mục tiêu đo lường được (nếu chưa có, `po` PHẢI hỏi lại — xem `agents/po/AGENT.md`)
- **Chỉ khi là project MỚI:** có cần capability-agent tuỳ chọn nào không (hiện tại chỉ `ads` — hỏi thẳng *"app có cần quảng cáo không?"*). KHÔNG tự suy diễn từ mô tả ý tưởng.

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
4. Viết Epic vào agents/po/memory/epics.json
5. Gọi skill_estimate_scope (giữ nguyên breakdown + reasoning, không chỉ nhãn size)
6. Emit type: handoff với node_id = INTAKE<nnn>-po
     - size M/L/XL -> to: ba   (đi tiếp track intake, hướng tới Gate 1)
     - size S      -> to: dev-be | mobile  (đường tắt runtime_feeds — Orchestrator sẽ
                      tạo track runtime FR<nnn> thay vì đi tiếp intake)
```

> `project-profile.json` là ngoại lệ duy nhất mà 1 agent được ghi vào `kernel/memory/` —
> vì đó là **khai báo cấu hình project**, không phải trạng thái scheduler. `wbs.json` thì tuyệt đối không.
